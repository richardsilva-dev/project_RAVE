import io
import json
import urllib.error
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


def test_quota_error_exposes_safe_code_without_echoing_provider_message():
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model")
    client = ChatCompletionsClient(settings)
    error_body = json.dumps({"error": {"type": "insufficient_quota", "code": "insufficient_quota",
        "message": "private prompt and secret text"}}).encode("utf-8")
    error = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429, "Too Many Requests",
        {}, io.BytesIO(error_body))
    with patch("rave.llm.urllib.request.urlopen", side_effect=error) as open_url:
        try:
            client.complete("system", "question")
        except RuntimeError as exc:
            assert "code=insufficient_quota" in str(exc)
            assert "private prompt" not in str(exc)
        else:
            raise AssertionError("Expected quota error")
    assert open_url.call_count == 1


def test_transient_rate_limit_retries_then_completes():
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model")
    client = ChatCompletionsClient(settings)
    limited_body = json.dumps({"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}}).encode()
    rate_limit = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429,
        "Too Many Requests", {"Retry-After": "0"}, io.BytesIO(limited_body))
    success = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    with patch("rave.llm.urllib.request.urlopen", side_effect=[rate_limit, success]) as open_url:
        with patch("rave.llm.time.sleep") as sleep:
            response = client.complete("system", "question")
    assert response.content == "ok"
    assert open_url.call_count == 2
    sleep.assert_called_once_with(0.0)
