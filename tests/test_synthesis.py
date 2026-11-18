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



def test_synthesis_bounds_large_context_without_dropping_source_provenance():
    from types import SimpleNamespace

    class BoundedFakeClient:
        def complete(self, system, user, *, max_completion_tokens=None):
            prompt = json.loads(user)
            assert len(prompt["findings"]) == 24
            assert prompt["omitted_findings_count"] == 6
            assert len(prompt["findings"][0]["evidence"]) == 2
            assert prompt["findings"][0]["evidence"][0]["source_url"] == "https://example.org/0"
            assert len(prompt["findings"][0]["explanation"]) <= 1200
            return LLMResponse(json.dumps({
                "executive_answer": "bounded answer", "integrated_analysis": "",
                "collective_integration": "", "evidence_and_sources": [],
                "gaps_and_limitations": [], "conclusions": ""
            }), {"prompt_tokens": 10, "completion_tokens": 5})

    findings = [
        SimpleNamespace(
            finding_id=f"f-{i}", agent_id="agent-01", category="category",
            title="title", claim="claim", explanation="x" * 5000,
            evidence_status="SUPPORTED", status_rationale="rationale",
            origin_finding_ids=[f"f-{i}"], independent_source_count=1,
            candidate_source_url_count=1,
            evidence=[SimpleNamespace(source_url=f"https://example.org/{j}", title="s", excerpt="e" * 5000)
                      for j in range(4)],
            limitations=["limitation"] * 8
        ) for i in range(30)
    ]
    integrated = {"local_contributions": {"large": "y" * 10000}, "findings": findings,
                  "overlaps": [], "web_sources": [{"url": "https://example.org/catalog"}]}
    output, usage = asyncio.run(synthesize(BoundedFakeClient(), "Question?", integrated))
    assert output["executive_answer"] == "bounded answer"
    assert usage == {"prompt_tokens": 10, "completion_tokens": 5}
