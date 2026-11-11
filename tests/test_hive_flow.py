import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from rave.core.hive_core import HiveCore
from rave.llm import LLMResponse


class ResearchClient:
    settings = SimpleNamespace(model="test-model", web_search_enabled=True)

    def __init__(self):
        self.search_agents = []

    def complete(self, system, user, *, web_search=False):
        if system.startswith("You are the RAVE Hive Core synthesis component."):
            return LLMResponse(json.dumps({"executive_answer": "Integrated answer"}),
                {"prompt_tokens": 5, "completion_tokens": 3})
        if system.startswith("You are RAVE Agent "):
            agent = system.split("You are RAVE Agent ", 1)[1].split(":", 1)[0]
            prompt = json.loads(user)
            if web_search:
                self.search_agents.append(agent)
                summary = f"Research result from agent {agent}"
                citations = [{"title": f"Source {agent}", "url": f"https://example.org/{agent}"}]
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


def test_three_agents_search_share_and_synthesize(tmp_path):
    client = ResearchClient()
    result = asyncio.run(HiveCore(client, str(tmp_path)).run("Small research question", "Keep it concise"))

    saved = json.loads(Path(result["result_path"]).read_text(encoding="utf-8"))
    assert len(client.search_agents) == 3
    assert set(client.search_agents) == {"1", "2", "3"}
    assert len(saved["messages"]) == 6
    assert all("Sources consulted" in message["content"] for message in saved["messages"])
    assert len(saved["integration"]["findings"]) == 3
    assert len(saved["integration"]["web_sources"]) == 3
    assert result["final_output"]["executive_answer"] == "Integrated answer"
    assert len(result["final_output"]["web_sources"]) == 3
