import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from rave.agents import FundamentalsAgent, MechanismAgent, PerspectiveAgent
from rave.communication import MessageBus
from rave.contracts import AgentTask
from rave.core.hive_core import HiveCore
from rave.core.integration import integrate
from rave.core.planner import create_tasks
from rave.llm import LLMResponse


class IndependentResearchClient:
    settings = SimpleNamespace(model="reasoning-model", web_search_enabled=True,
        research_mode="independent_research")

    def __init__(self, fail_search_role=None, fail_refinement_agent=None, share_peer_evidence=False,
            invalid_refinement_agent=None):
        self.calls = []
        self.fail_search_role = fail_search_role
        self.fail_refinement_agent = fail_refinement_agent
        self.share_peer_evidence = share_peer_evidence
        self.invalid_refinement_agent = invalid_refinement_agent

    def complete(self, system, user, *, web_search=False):
        prompt = json.loads(user)
        self.calls.append({"system": system, "prompt": prompt, "web_search": web_search})
        if system.startswith("You are the RAVE Hive Core synthesis component."):
            return LLMResponse(json.dumps({"executive_answer": "answer", "evidence_and_sources": []}),
                {"prompt_tokens": 3, "completion_tokens": 2})
        if system.startswith("You repair JSON formatting only"):
            return LLMResponse("not valid json", {"prompt_tokens": 1, "completion_tokens": 1})
        if web_search:
            role = prompt["role"]
            if role == self.fail_search_role:
                raise RuntimeError("simulated research failure")
            agent_slug = role.lower().replace(" ", "-")
            return LLMResponse(f"Research notes for {role}", {"prompt_tokens": 7, "completion_tokens": 4}, [
                {"title": f"Tool source {role}", "url": f"https://tool.example/{agent_slug}"}])
        if system.startswith("You are RAVE Agent "):
            agent = system.split("You are RAVE Agent ", 1)[1].split(":", 1)[0]
            if prompt["phase"] == "cross_agent_integration":
                initial = prompt["your_initial_findings"]
                own_agent_id = initial[0]["agent_id"] if initial else ""
                if own_agent_id == self.fail_refinement_agent:
                    raise TimeoutError("simulated refinement timeout")
                if own_agent_id == self.invalid_refinement_agent:
                    return LLMResponse("not valid json", {"prompt_tokens": 1, "completion_tokens": 1})
                if self.share_peer_evidence and prompt["peer_contributions"]:
                    peer = json.loads(prompt["peer_contributions"][0]["content"])
                    if peer.get("evidence"):
                        initial[0]["evidence"].append(peer["evidence"][0])
                payload = {"summary": f"Integrated {agent}", "findings": initial,
                    "limitations": [], "open_questions": [],
                    "change_log": [{"finding_id": initial[0]["finding_id"], "action": "retained", "reason": "No change."}]}
            else:
                research = prompt["research_material"]
                assert research["research_mode"] == "independent_research"
                assert research["research_notes"].startswith("Research notes for")
                assert len(research["sources"]) == 1
                tool_url = research["sources"][0]["url"]
                payload = {"summary": f"Initial {agent}", "findings": [{
                    "category": "fact", "title": f"Finding {agent}", "claim": f"Claim {agent}",
                    "explanation": "Details", "evidence": [
                        {"source_title": "Tool citation", "source_url": tool_url,
                            "supporting_excerpt_or_location": "Excerpt returned by model"},
                        {"source_title": "Unlisted URL", "source_url": f"https://model.example/{agent}",
                            "supporting_excerpt_or_location": "URL written in model JSON"}],
                    "evidence_status": "INSUFFICIENT", "status_rationale": "Test fixture",
                    "limitations": [], "open_questions": []}], "limitations": [], "open_questions": []}
            return LLMResponse(json.dumps(payload), {"prompt_tokens": 5, "completion_tokens": 3})
        raise AssertionError(f"Unexpected completion system: {system}")


def make_agents(client, bus):
    return [FundamentalsAgent("agent-01", "Fundamentos", "facts", client, bus),
        MechanismAgent("agent-02", "Mecanismos", "mechanisms", client, bus),
        PerspectiveAgent("agent-03", "Perspectivas", "limits", client, bus)]


def test_independent_research_separates_search_from_reasoning_and_citation_origins():
    async def scenario():
        client = IndependentResearchClient()
        bus = MessageBus("run-independent")
        tasks = create_tasks("run-independent", "Question?", "Scope")
        agents = make_agents(client, bus)
        results = await asyncio.gather(*(agent.run(task) for agent, task in zip(agents, tasks)))
        integration = integrate(results)

        searches = [call for call in client.calls if call["web_search"]]
        reasoning_analyses = [call for call in client.calls if not call["web_search"]
            and call["system"].startswith("You are RAVE Agent ")]
        assert len(searches) == 3
        assert len(reasoning_analyses) == 6  # three initial analyses and three peer refinements
        assert all("specialized research retriever" in call["system"] for call in searches)
        assert all(call["prompt"]["phase"] == "independent_specialized_search" for call in searches)
        assert all(call["prompt"]["phase"] != "independent_specialized_search" for call in reasoning_analyses)
        assert all(len(result.web_sources) == 1 for result in results)
        assert all(result.web_sources[0].citation_provenance == "provider_returned" for result in results)
        evidence = [e for result in results for finding in result.findings for e in finding.evidence]
        assert sum(e.citation_provenance == "provider_returned" for e in evidence) == 3
        assert sum(e.citation_provenance == "model_reported" for e in evidence) == 3
        assert len(integration["web_sources"]) == 3
        assert len(integration["model_reported_references"]) == 3
        assert all(source["reference_origin"] == "model_json"
            for source in integration["model_reported_references"])

    asyncio.run(scenario())


def test_independent_research_failure_is_saved_as_partial(tmp_path):
    client = IndependentResearchClient(fail_search_role="Mecanismos, relações e explicações")
    result = asyncio.run(HiveCore(client, str(tmp_path)).run("Question?", "Scope"))
    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))
    assert result["execution_status"] == "PARTIAL"
    assert saved["execution_status"] == "PARTIAL"
    assert len(saved["agent_results"]) == 2
    assert saved["failed_agents"] == [{"agent_id": "agent-02", "error_type": "RuntimeError"}]
    assert any("execução parcial" in item.lower()
        for item in result["final_output"]["gaps_and_limitations"])


def test_refinement_timeout_preserves_initial_findings_and_marks_hive_partial(tmp_path):
    client = IndependentResearchClient(fail_refinement_agent="agent-03")
    result = asyncio.run(HiveCore(client, str(tmp_path)).run("Question?", "Scope"))
    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))
    agent = next(item for item in saved["agent_results"] if item["agent_id"] == "agent-03")

    assert agent["status"] == "PARTIAL"
    assert agent["refinement_status"] == "FAILED_PRESERVED_INITIAL"
    assert agent["failure_type"] == "TimeoutError"
    assert len(agent["findings"]) == len(agent["initial_findings"]) == 1
    assert saved["execution_status"] == result["execution_status"] == "PARTIAL"
    assert saved["partial_agents"] == [{"agent_id": "agent-03",
        "refinement_status": "FAILED_PRESERVED_INITIAL", "error_type": "TimeoutError"}]
    assert len(saved["integration"]["findings"]) >= 3


def test_invalid_refinement_json_is_also_reported_as_partial(tmp_path):
    client = IndependentResearchClient(invalid_refinement_agent="agent-03")
    result = asyncio.run(HiveCore(client, str(tmp_path)).run("Question?", "Scope"))
    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))
    agent = next(item for item in saved["agent_results"] if item["agent_id"] == "agent-03")

    assert agent["status"] == "PARTIAL"
    assert agent["refinement_status"] == "FAILED_PRESERVED_INITIAL"
    assert len(agent["findings"]) == len(agent["initial_findings"]) == 1
    assert saved["execution_status"] == "PARTIAL"
    assert saved["partial_agents"][0]["agent_id"] == "agent-03"


def test_peer_provider_citation_provenance_survives_refinement():
    async def scenario():
        client = IndependentResearchClient(share_peer_evidence=True)
        bus = MessageBus("run-peer-provenance")
        tasks = create_tasks("run-peer-provenance", "Question?", "Scope")
        results = await asyncio.gather(*(agent.run(task)
            for agent, task in zip(make_agents(client, bus), tasks)))

        received_peer_provider_evidence = []
        for result in results:
            own_urls = {item.source_url for item in result.web_sources}
            for finding in result.findings:
                for evidence in finding.evidence:
                    if evidence.source_url.startswith("https://tool.example/") and evidence.source_url not in own_urls:
                        received_peer_provider_evidence.append(evidence)
        assert received_peer_provider_evidence
        assert all(item.citation_provenance == "provider_returned"
            for item in received_peer_provider_evidence)
        assert all(item.citation_origin_agent_ids for item in received_peer_provider_evidence)
        assert all(item.origin_finding_ids for item in received_peer_provider_evidence)

    asyncio.run(scenario())
