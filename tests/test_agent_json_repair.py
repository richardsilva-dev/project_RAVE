import asyncio
import json
from types import SimpleNamespace

from rave.agents.base import BaseAgent
from rave.communication import MessageBus
from rave.contracts import AgentTask
from rave.llm import LLMResponse


class RepairClient:
    settings = SimpleNamespace(web_search_enabled=True)

    def __init__(self):
        self.calls = []

    def complete(self, system, user, *, web_search=False):
        self.calls.append((system, web_search))
        if web_search:
            return LLMResponse('{"summary": "truncated" "findings": []',
                {"prompt_tokens": 10, "completion_tokens": 8},
                [{"title": "Source", "url": "https://example.org"}])
        return LLMResponse(json.dumps({"summary": "repaired", "findings": [],
            "limitations": [], "open_questions": []}),
            {"prompt_tokens": 4, "completion_tokens": 3})


class StubAgent(BaseAgent):
    def instructions(self):
        return "Research agent instructions"

    def peer_ids(self):
        return []


def test_malformed_research_json_is_repaired_and_keeps_sources():
    client = RepairClient()
    bus = MessageBus("run-1", expected_publishers=1)
    agent = StubAgent("agent-1", "Test", "Testing", client, bus)
    task = AgentTask("task-1", "run-1", "Question", "Specialized question", "Role", "Contribution", "Scope")

    result = asyncio.run(agent.run(task))

    assert result.summary == "repaired"
    assert result.web_sources[0].source_url == "https://example.org"
    assert result.usage == {"prompt_tokens": 14, "completion_tokens": 11}
    assert len(client.calls) == 2


def test_single_line_code_fence_is_parsed():
    agent = StubAgent("agent-1", "Test", "Testing", RepairClient(), MessageBus("run-1", expected_publishers=1))
    assert agent.parse_json('```{"summary": "ok"}```') == {"summary": "ok"}


def test_empty_code_fence_raises_repairable_value_error():
    agent = StubAgent("agent-1", "Test", "Testing", RepairClient(), MessageBus("run-1", expected_publishers=1))
    try:
        agent.parse_json("```")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for an empty code fence")



def test_agent_output_bounds_match_single_agent_baseline():
    import pytest

    finding = {
        "category": "fact", "title": "t", "claim": "c", "explanation": "e",
        "evidence": [], "limitations": [], "open_questions": [],
    }
    too_many_findings = {
        "summary": "s", "findings": [finding] * 11,
        "limitations": [], "open_questions": [],
    }
    with pytest.raises(ValueError, match="more than 10 findings"):
        BaseAgent.validate_result(too_many_findings, "agent-1")

    too_many_evidence = dict(finding)
    too_many_evidence["evidence"] = [
        {"source_title": "s", "source_url": "https://example.org",
         "supporting_excerpt_or_location": "x"} for _ in range(4)
    ]
    result = {"summary": "s", "findings": [too_many_evidence],
              "limitations": [], "open_questions": []}
    with pytest.raises(ValueError, match="more than 3 evidence items"):
        BaseAgent.validate_result(result, "agent-1")
