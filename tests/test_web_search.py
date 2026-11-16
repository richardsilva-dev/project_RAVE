import asyncio
import io
import json
import urllib.error
from unittest.mock import patch

from rave.config import Settings
from rave.budget import RunBudget
from rave.llm import ChatCompletionsClient, capture_llm_calls, llm_agent_context, _NoRedirectHandler


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_chat_completions_web_search_returns_text_sources_and_usage():
    payload = {"choices": [{"message": {"content": "{\"findings\": []}",
        "annotations": [{"type": "url_citation", "url_citation": {
            "title": "Source", "url": "https://example.org/source"}}]}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 6}}
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model", 0.2, 30,
        "data/runs", True, "search-model")
    client = ChatCompletionsClient(settings)
    with patch("rave.llm._open_url", return_value=FakeHTTPResponse(payload)) as open_url:
        response = client.complete("system", "question", web_search=True)
    request = open_url.call_args.args[0]
    sent = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "https://api.openai.com/v1/chat/completions"
    assert sent["model"] == "search-model"
    assert sent["web_search_options"]["search_context_size"] == "low"
    assert sent["max_completion_tokens"] == 512
    assert sent["messages"][0] == {"role": "system", "content": "system"}
    assert response.content == "{\"findings\": []}"
    assert response.citations == [{"title": "Source", "url": "https://example.org/source"}]
    assert response.usage == {"prompt_tokens": 12, "completion_tokens": 6}


def test_timeout_is_recorded_as_failed_call_with_agent_and_attempts():
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model")
    client = ChatCompletionsClient(settings)
    async def call_in_agent_context():
        with capture_llm_calls() as calls, llm_agent_context("agent-03"):
            with patch("rave.llm._open_url", side_effect=TimeoutError("socket timed out")):
                try:
                    await asyncio.to_thread(client.complete, "system", "question")
                except TimeoutError as exc:
                    assert str(exc) == "LLM request timed out"
                else:
                    raise AssertionError("Expected the timeout to propagate")
            return list(calls)
    calls = asyncio.run(call_in_agent_context())
    assert len(calls) == 1
    assert calls[0]["status"] == "FAILED"
    assert calls[0]["agent_id"] == "agent-03"
    assert calls[0]["request_attempts"] == 1
    assert calls[0]["duration_seconds"] >= 0


def test_quota_error_exposes_safe_code_without_echoing_provider_message():
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model")
    client = ChatCompletionsClient(settings)
    error_body = json.dumps({"error": {"type": "insufficient_quota", "code": "insufficient_quota",
        "message": "private prompt and secret text"}}).encode("utf-8")
    error = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429, "Too Many Requests",
        {}, io.BytesIO(error_body))
    with patch("rave.llm._open_url", side_effect=error) as open_url:
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
    with patch("rave.llm._open_url", side_effect=[rate_limit, success]) as open_url:
        with patch("rave.llm.time.sleep") as sleep:
            response = client.complete("system", "question")
    assert response.content == "ok"
    assert open_url.call_count == 2
    sleep.assert_called_once_with(0.0)


def test_retry_waits_for_later_token_reset_header():
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model")
    client = ChatCompletionsClient(settings)
    limited_body = json.dumps({"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}}).encode()
    rate_limit = urllib.error.HTTPError("https://api.openai.com/v1/responses", 429,
        "Too Many Requests", {"Retry-After": "23", "x-ratelimit-reset-tokens": "27.3s"},
        io.BytesIO(limited_body))
    success = FakeHTTPResponse({"choices": [{"message": {"content": "{\"summary\": \"ok\"}"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    with patch("rave.llm._open_url", side_effect=[rate_limit, success]) as open_url:
        with patch("rave.llm.time.sleep") as sleep:
            response = client.complete("system", "question", web_search=True)
    assert response.content == "{\"summary\": \"ok\"}"
    assert open_url.call_count == 2
    sleep.assert_called_once_with(27.3)


def test_retry_honors_long_server_token_reset():
    settings = Settings("test-key", "https://api.openai.com/v1", "chat-model")
    client = ChatCompletionsClient(settings)
    limited_body = json.dumps({"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}}).encode()
    rate_limit = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429,
        "Too Many Requests", {"Retry-After": "370.375"}, io.BytesIO(limited_body))
    success = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}], "usage": {}})
    with patch("rave.llm._open_url", side_effect=[rate_limit, success]) as open_url:
        with patch("rave.llm.time.sleep") as sleep:
            response = client.complete("system", "question")
    assert response.content == "ok"
    assert open_url.call_count == 2
    sleep.assert_called_once_with(370.375)


def test_analysis_request_uses_configured_output_cap_and_override():
    settings = Settings("test-key", "https://api.openai.com/v1", "gpt-4.1-mini")
    client = ChatCompletionsClient(settings)
    success = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    with patch("rave.llm._open_url", return_value=success) as open_url:
        client.complete("system", "question", max_completion_tokens=1234)
    request = open_url.call_args.args[0]
    sent = json.loads(request.data.decode("utf-8"))
    assert sent["max_completion_tokens"] == 1234


def test_401_releases_reserved_budget_without_echoing_key():
    settings = Settings("test-key", "https://api.openai.com/v1", "gpt-4.1-mini")
    client = ChatCompletionsClient(settings)
    budget = RunBudget(10000, 2, 2, 30, 0.50, 0, 1.25, 10.0)
    body = json.dumps({"error": {"type": "invalid_request_error", "code": "invalid_api_key",
        "message": "do not echo this"}}).encode()
    error = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 401,
        "Unauthorized", {}, io.BytesIO(body))
    with capture_llm_calls(budget):
        with patch("rave.llm._open_url", side_effect=error):
            try:
                client.complete("system", "question")
            except RuntimeError as exc:
                assert "HTTP 401" in str(exc)
                assert "do not echo" not in str(exc)
            else:
                raise AssertionError("Expected invalid API key error")
    snapshot = budget.snapshot()
    assert snapshot["used"]["model_calls"] == 1
    assert snapshot["reserved"]["tokens"] == 0
    assert snapshot["reserved"]["estimated_cost_usd"] == 0


def test_retry_attempts_are_counted_and_failed_reservation_is_retained():
    settings = Settings("test-key", "https://api.openai.com/v1", "gpt-4.1-mini")
    client = ChatCompletionsClient(settings)
    budget = RunBudget(10000, 2, 2, 30, 0.50, 0, 1.25, 10.0)
    rate_limit_body = json.dumps({"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}}).encode()
    rate_limit = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429,
        "Too Many Requests", {"Retry-After": "0"}, io.BytesIO(rate_limit_body))
    success = FakeHTTPResponse({"choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    with capture_llm_calls(budget):
        with patch("rave.llm._open_url", side_effect=[rate_limit, success]):
            with patch("rave.llm.time.sleep"):
                client.complete("system", "question")
    snapshot = budget.snapshot()
    assert snapshot["used"]["model_calls"] == 2
    assert snapshot["used"]["tokens"] == 2
    assert snapshot["reserved"]["tokens"] > 0


def test_authenticated_requests_refuse_redirects():
    handler = _NoRedirectHandler()
    request = urllib.request.Request("https://api.openai.com/v1/chat/completions")
    redirected = handler.redirect_request(
        request, None, 302, "Found", {}, "https://attacker.example/collect"
    )
    assert redirected is None
