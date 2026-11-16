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
            return LLMResponse(json.dumps({"executive_answer": "Integrated answer"}),
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
                assert prompt["shared_web_research"]["research_notes"] == "Shared research from official sources."
                assert len(prompt["shared_web_research"]["sources"]) == 2
                summary = f"Research result from agent {agent}"
                citations = prompt["shared_web_research"]["sources"]
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
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.00")
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


def test_shared_search_failure_does_not_fall_back_to_agent_search(tmp_path, monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.00")
    client = ResearchClient()

    def fail_search(*args, **kwargs):
        raise RuntimeError("simulated shared search failure")

    monkeypatch.setattr("rave.core.hive_core.perform_shared_research", fail_search)
    result = asyncio.run(HiveCore(client, str(tmp_path)).run("Small research question", "Keep it concise"))

    assert result["execution_status"] == "FAILED"
    assert result["agent_results"] == []
    assert result["final_output"]["executive_answer"] == ""
    assert result["shared_research_error"] == "RuntimeError"
    assert client.analyzed_agents == []
