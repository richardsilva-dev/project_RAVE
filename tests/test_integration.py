from rave.contracts import AgentResult, Evidence, Finding
from rave.core.integration import integrate


def test_integration_finds_shared_claims_and_deduplicates_sources():
    first = Finding("f-1", "r-1", "agent-01", "t-1", "fact", "Claim", "Same claim")
    second = Finding("f-2", "r-1", "agent-02", "t-2", "fact", "Claim", "Same claim")
    results = [
        AgentResult("agent-01", "A", "facts", "t-1", "COMPLETED", "summary", [first],
            web_sources=[Evidence("Source", "https://example.org/a")]),
        AgentResult("agent-02", "B", "mechanisms", "t-2", "COMPLETED", "summary", [second],
            web_sources=[Evidence("Source", "https://example.org/a")]),
    ]
    output = integrate(results)
    assert output["overlaps"] == [{"claim": "same claim", "agents": ["agent-01", "agent-02"]}]
    assert len(output["web_sources"]) == 1
    assert output["web_sources"][0]["url"] == "https://example.org/a"
    assert output["web_sources"][0]["agents"] == ["agent-01", "agent-02"]



def test_integration_deduplicates_tracking_variants_and_fragments():
    first = Finding("f-1", "r-1", "agent-01", "t-1", "fact", "Claim", "Claim A",
        evidence=[Evidence("Source", "https://EXAMPLE.org/report/?utm_source=chatgpt.com#section")])
    second = Finding("f-2", "r-1", "agent-02", "t-2", "fact", "Claim", "Claim B",
        evidence=[Evidence("Source", "https://example.org/report?fbclid=tracking")])
    results = [
        AgentResult("agent-01", "A", "facts", "t-1", "COMPLETED", "summary", [first],
            web_sources=[Evidence("Source", "https://EXAMPLE.org/report/?utm_source=chatgpt.com#section")]),
        AgentResult("agent-02", "B", "mechanisms", "t-2", "COMPLETED", "summary", [second],
            web_sources=[Evidence("Source", "https://example.org/report?fbclid=tracking")]),
    ]
    output = integrate(results)
    assert len(output["web_sources"]) == 1
    assert output["web_sources"][0]["url"] == "https://example.org/report"
    assert set(output["web_sources"][0]["agents"]) == {"agent-01", "agent-02"}
    assert len(output["web_sources"][0]["original_urls"]) == 2
    assert first.independent_source_count == 1
    assert second.independent_source_count == 1
