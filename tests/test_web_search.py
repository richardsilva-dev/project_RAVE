import json
from unittest.mock import patch

from rave.config import Settings
from rave.llm import ChatCompletionsClient


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_responses_web_search_returns_text_sources_and_usage():
    payload = {"output": [
        {"type": "web_search_call", "action": {"sources": [
            {"title": "Source", "url": "https://example.org/source"}]}},
        {"type": "message", "content": [{"type": "output_text", "text": "{\"findings\": []}",
            "annotations": [{"type": "url_citation", "url_citation": {
                "title": "Source", "url": "https://example.org/source"}}]}]},
    ], "usage": {"input_tokens": 12, "output_tokens": 6}}
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model", 0.2, 30,
        "data/runs", True, "search-model")
    client = ChatCompletionsClient(settings)
    with patch("rave.llm.urllib.request.urlopen", return_value=FakeHTTPResponse(payload)) as open_url:
        response = client.complete("system", "question", web_search=True)
    request = open_url.call_args.args[0]
    sent = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "https://api.openai.com/v1/responses"
    assert sent["model"] == "search-model"
    assert sent["tool_choice"] == "required"
    assert response.content == "{\"findings\": []}"
    assert response.citations == [{"title": "Source", "url": "https://example.org/source"}]
    assert response.usage == {"prompt_tokens": 12, "completion_tokens": 6}
