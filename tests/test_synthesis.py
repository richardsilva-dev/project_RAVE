import asyncio
import json

from rave.core.synthesis import synthesize
from rave.llm import LLMResponse


class FakeClient:
    def complete(self, system, user, *, max_completion_tokens=None):
        prompt = json.loads(user)
        assert max_completion_tokens == 8192
        assert prompt["web_sources"][0]["url"] == "https://example.org/source"
        return LLMResponse(json.dumps({"executive_answer": "answer", "integrated_analysis": "",
            "collective_integration": "", "evidence_and_sources": [], "gaps_and_limitations": [], "conclusions": ""}),
            {"prompt_tokens": 4, "completion_tokens": 3})


def test_synthesis_includes_the_researched_source_catalog():
    integrated = {"local_contributions": {}, "findings": [], "overlaps": [], "web_sources": [
        {"title": "Source", "url": "https://example.org/source", "agents": ["agent-01"]}]}
    output, usage = asyncio.run(synthesize(FakeClient(), "Question?", integrated))
    assert output["executive_answer"] == "answer"
    assert output["web_sources"] == integrated["web_sources"]
    assert usage == {"prompt_tokens": 4, "completion_tokens": 3}
