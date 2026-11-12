import pytest

from benchmark_adapters.result_normalizer import normalize_result


def test_rave_partial_status_is_not_promoted_to_completed():
    result = normalize_result("rave", {
        "run_id": "rave-test",
        "execution_status": "PARTIAL",
        "synthesis_status": "FAILED",
        "final_output": {"executive_answer": ""},
        "integration": {"web_sources": []},
        "metadata": {"status": "PARTIAL", "calls": []},
    })
    assert result["status"] == "PARTIAL"
    assert result["metadata"]["synthesis_status"] == "FAILED"


def test_solo_preserves_provider_citation_provenance():
    source = {"url": "https://example.org", "provenance": "provider_returned_annotation"}
    result = normalize_result("solo_baseline", {
        "run_id": "solo-test",
        "status": "COMPLETED",
        "final_output": {"executive_answer": "answer"},
        "provider_returned_sources": [source],
        "budget": {},
        "calls": [],
    })
    assert result["sources"] == [source]


def test_open_deep_research_requires_explicit_final_output():
    with pytest.raises(ValueError, match="explicitly extracted"):
        normalize_result("open_deep_research", {"status": "COMPLETED"})
