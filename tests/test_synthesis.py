import asyncio
import json

from rave.core.synthesis import synthesize
from rave.llm import LLMResponse


class FakeClient:
    def complete(self, system, user):
        prompt = json.loads(user)
        assert prompt["web_sources"][0]["url"] == "https://example.org/source"
        return LLMResponse(json.dumps({
            "executive_answer": "answer",
            "integrated_analysis": "analysis",
            "collective_integration": "integration",
            "evidence_and_sources": [],
            "gaps_and_limitations": [],
            "conclusions": "conclusion",
        }), {"prompt_tokens": 4, "completion_tokens": 3})


def test_synthesis_includes_the_researched_source_catalog():
    integrated = {"local_contributions": {}, "findings": [], "overlaps": [], "web_sources": [
        {"title": "Source", "url": "https://example.org/source", "agents": ["agent-01"]}]}
    output, usage = asyncio.run(synthesize(FakeClient(), "Question?", integrated))
    assert output["executive_answer"] == "answer"
    assert output["web_sources"] == integrated["web_sources"]
    assert usage == {"prompt_tokens": 4, "completion_tokens": 3}



def test_synthesis_rejects_invalid_json():
    from rave.core.synthesis import SynthesisOutputError, validate_synthesis_output
    import pytest

    with pytest.raises(SynthesisOutputError, match="invalid JSON"):
        validate_synthesis_output("{not-json}")


def test_synthesis_rejects_missing_required_fields():
    from rave.core.synthesis import SynthesisOutputError, validate_synthesis_output
    import pytest

    with pytest.raises(SynthesisOutputError, match="missing required field"):
        validate_synthesis_output(json.dumps({"executive_answer": "answer"}))


def test_synthesis_rejects_wrong_field_types():
    from rave.core.synthesis import SynthesisOutputError, validate_synthesis_output
    import pytest

    invalid = {
        "executive_answer": "answer",
        "integrated_analysis": "analysis",
        "collective_integration": "integration",
        "evidence_and_sources": [],
        "gaps_and_limitations": "must be a list",
        "conclusions": "conclusion",
    }
    with pytest.raises(SynthesisOutputError, match="invalid type"):
        validate_synthesis_output(json.dumps(invalid))
