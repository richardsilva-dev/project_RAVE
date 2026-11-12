from types import SimpleNamespace

from solo_baseline.agent import SoloResearchAgent
from solo_baseline.client import Response


class FakeClient:
    def __init__(self):
        self.searches = 0
        self.calls = []

    def complete(self, *, model, system, user, web_search=False, max_output_tokens=4000):
        self.calls.append((model, web_search))
        if "Plan a small sequence" in system:
            return Response('{"queries":["query one","query two"],"research_plan":"two focused searches"}',
                            {"prompt_tokens": 10, "completion_tokens": 10}, []), 0.1
        if web_search:
            self.searches += 1
            return Response(f"Research notes {self.searches}",
                            {"prompt_tokens": 20, "completion_tokens": 10},
                            [{"title": f"Source {self.searches}",
                              "url": f"https://example.org/{self.searches}",
                              "provenance": "provider_returned_annotation"}]), 0.2
        if "Analyze only the supplied" in system:
            return Response('{"summary":"summary","findings":[{"claim":"claim","explanation":"evidence","source_urls":["https://example.org/1"],"limitations":[]}],"gaps":[],"next_queries":[]}',
                            {"prompt_tokens": 15, "completion_tokens": 10}, []), 0.1
        if "producing the final report" in system:
            return Response('{"executive_answer":"answer","analysis":"analysis","findings":[],"sources":[],"limitations":[],"conclusions":"conclusion"}',
                            {"prompt_tokens": 20, "completion_tokens": 10}, []), 0.1
        raise AssertionError("Unexpected model call")


def test_solo_is_one_sequential_researcher_without_delegation():
    settings = SimpleNamespace(
        max_search_calls=3, max_model_calls=10, max_total_tokens=1000,
        max_runtime_seconds=60, max_output_tokens_per_call=100,
        model="gpt-4.1-mini", web_search_model="gpt-5-search-api",
    )
    client = FakeClient()
    result = SoloResearchAgent(client, settings).run("Question", "Scope")

    assert result["status"] == "COMPLETED"
    assert result["agent_count"] == 1
    assert result["delegation_enabled"] is False
    assert result["research_mode"] == "single_sequential_researcher"
    assert result["budget"]["actual_search_calls"] == 2
    assert result["budget"]["actual_model_calls"] == 6
    assert client.searches == 2
    assert len(result["provider_returned_sources"]) == 2
