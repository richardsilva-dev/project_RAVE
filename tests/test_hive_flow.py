import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from rave.core.hive_core import HiveCore
from rave.llm import LLMResponse


class ResearchClient:
    settings = SimpleNamespace(model="test-model", web_search_enabled=True)

    def __init__(self):
        self.search_calls = 0
        self.analyzed_agents = []

    def complete(self, system, user, *, web_search=False, max_completion_tokens=None):
        if system.startswith("You are the RAVE Hive Core synthesis component."):
            return LLMResponse(json.dumps({"executive_answer": "Integrated answer", "integrated_analysis": "",
                "collective_integration": "", "evidence_and_sources": [], "gaps_and_limitations": [], "conclusions": ""}),
                {"prompt_tokens": 5, "completion_tokens": 3})
        if system.startswith("You are the RAVE Hive Core shared web research component."):
            self.search_calls += 1
            return LLMResponse("Shared research from official sources.",
                {"prompt_tokens": 8, "completion_tokens": 5}, [
                    {"title": "Source One", "url": "https://example.org/source-1"},
                    {"title": "Source Two", "url": "https://example.org/source-2"}])
        if system.startswith("You are RAVE Agent "):
            agent = system.split("You are RAVE Agent ", 1)[1].split(":", 1)[0]
            prompt = json.loads(user)
            if web_search:
                raise AssertionError("Agents should analyze the shared research corpus without duplicate searches")
            if prompt["phase"] == "independent_investigation":
                self.analyzed_agents.append(agent)
                assert prompt["research_material"]["research_notes"] == "Shared research from official sources."
                assert prompt["research_material"]["research_mode"] == "shared_research"
                assert len(prompt["research_material"]["sources"]) == 2
                summary = f"Research result from agent {agent}"
                citations = prompt["provider_citations"]
            else:
                assert prompt["phase"] == "cross_agent_integration"
                assert prompt["peer_contributions"]
                summary = f"Integrated result from agent {agent}"
                citations = []
            payload = {"summary": summary, "findings": [{"category": "fact",
                "title": f"Finding {agent}", "claim": f"Claim from agent {agent}",
                "explanation": "Evidence-based explanation", "evidence": [],
                "limitations": [], "open_questions": []}], "limitations": [], "open_questions": []}
            return LLMResponse(json.dumps(payload), {"prompt_tokens": 4, "completion_tokens": 2}, citations)
        raise AssertionError("Unexpected LLM request")


def test_three_agents_search_share_and_synthesize(tmp_path, monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.0")
    client = ResearchClient()
    result = asyncio.run(HiveCore(client, str(tmp_path)).run("Small research question", "Keep it concise"))

    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))
    assert client.search_calls == 1
    assert set(client.analyzed_agents) == {"1", "2", "3"}
    assert len(saved["messages"]) == 6
    assert all("Sources consulted" in message["content"] for message in saved["messages"])
    assert len(saved["integration"]["findings"]) == 3
    assert len(saved["integration"]["web_sources"]) == 2
    assert all(len(source["agents"]) == 3 for source in saved["integration"]["web_sources"])
    assert result["final_output"]["executive_answer"] == "Integrated answer"
    assert len(result["final_output"]["web_sources"]) == 2


def test_shared_search_failure_does_not_silently_switch_to_independent(tmp_path, monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.0")
    class FailedSharedSearchClient(ResearchClient):
        def complete(self, system, user, *, web_search=False, max_completion_tokens=None):
            if system.startswith("You are the RAVE Hive Core shared web research component."):
                raise TimeoutError("simulated shared-search timeout")
            raise AssertionError("Agents or synthesis must not run after the shared search fails")

    result = asyncio.run(HiveCore(FailedSharedSearchClient(), str(tmp_path)).run(
        "Small research question", "Keep it concise"))

    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))
    assert result["research_mode"] == "shared_research"
    assert result["execution_status"] == "INVALID"
    assert result["shared_research_error"] == "TimeoutError"
    assert len(saved["failed_agents"]) == 3
    assert saved["agent_results"] == []


def test_agent_runtime_errors_preserve_safe_diagnostics(tmp_path, monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.0")

    class FailedAgentClient(ResearchClient):
        def complete(self, system, user, *, web_search=False, max_completion_tokens=None):
            if system.startswith("You are RAVE Agent "):
                raise RuntimeError("LLM provider returned HTTP 400 (code=invalid_request_error)")
            return super().complete(system, user, web_search=web_search,
                max_completion_tokens=max_completion_tokens)

    result = asyncio.run(HiveCore(FailedAgentClient(), str(tmp_path)).run(
        "Small research question", "Keep it concise"))
    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))

    assert result["execution_status"] == "INVALID"
    assert len(saved["failed_agents"]) == 3
    assert all(agent["error_type"] == "RuntimeError" for agent in saved["failed_agents"])
    assert all(agent["error_message"] == (
        "LLM provider returned HTTP 400 (code=invalid_request_error)")
        for agent in saved["failed_agents"])
