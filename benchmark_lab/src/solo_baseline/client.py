from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


@dataclass
class Response:
    content: str
    usage: dict[str, int]
    citations: list[dict]
    attempts: int = 1


class ProviderError(RuntimeError):
    def __init__(self, message: str, attempts: int = 1):
        super().__init__(message)
        self.attempts = attempts


class ChatCompletionsClient:
    """Isolated client using the Chat Completions route and bounded 429 retries."""
    def __init__(self, api_key: str, base_url: str, timeout_seconds: int,
                 temperature: float):
        if not api_key:
            raise ValueError("SOLO_API_KEY is missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    @staticmethod
    def _retry_delay(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", value)
            if match and any(match.groups()):
                hours, minutes, seconds = match.groups()
                return int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(seconds or 0)
            try:
                reset_at = parsedate_to_datetime(value)
                if reset_at.tzinfo is None:
                    reset_at = reset_at.replace(tzinfo=timezone.utc)
                return max(0.0, (reset_at - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None

    def complete(self, *, model: str, system: str, user: str,
                 web_search: bool = False, max_output_tokens: int = 4000) -> tuple[Response, float]:
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_completion_tokens": max_output_tokens,
        }
        if web_search:
            payload["web_search_options"] = {"search_context_size": "low"}
        else:
            payload["temperature"] = self.temperature
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        started = time.perf_counter()
        body = None
        attempts = 0
        for attempt in range(3):
            attempts += 1
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                error_code = ""
                error_type = ""
                try:
                    error_payload = json.loads(exc.read(64000).decode("utf-8", errors="replace"))
                    error = error_payload.get("error", {}) if isinstance(error_payload, dict) else {}
                    if isinstance(error, dict):
                        error_code = str(error.get("code", ""))
                        error_type = str(error.get("type", ""))
                except (ValueError, TypeError, OSError):
                    pass
                retry_values = [
                    self._retry_delay(exc.headers.get("Retry-After")),
                    self._retry_delay(exc.headers.get("x-ratelimit-reset-tokens")),
                ]
                retry_after = max((v for v in retry_values if v is not None), default=None)
                retryable = exc.code == 429 and (
                    error_code in {"rate_limit_exceeded", "slow_down"} or
                    error_type == "rate_limit_error"
                )
                if retryable and attempt < 2:
                    delay = retry_after if retry_after is not None else float(2 ** attempt)
                    if delay <= 420:
                        time.sleep(delay)
                        continue
                raise ProviderError(f"Provider returned HTTP {exc.code}; attempts={attempts}", attempts) from exc
            except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProviderError(f"Provider request failed: {type(exc).__name__}; attempts={attempts}", attempts) from exc
        if body is None:
            raise ProviderError(f"Provider request did not complete; attempts={attempts}", attempts)
        try:
            message = body["choices"][0]["message"]
            content = message["content"]
            if not isinstance(content, str):
                raise TypeError("content is not text")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider response did not contain message text", attempts) from exc
        citations = []
        if web_search:
            for annotation in message.get("annotations", []):
                citation = annotation.get("url_citation", {}) if isinstance(annotation, dict) else {}
                if isinstance(citation, dict) and isinstance(citation.get("url"), str):
                    citations.append({
                        "title": str(citation.get("title", "")),
                        "url": citation["url"],
                        "provenance": "provider_returned_annotation",
                    })
        usage_raw = body.get("usage") or {}
        try:
            usage = {
                "prompt_tokens": int(usage_raw.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(usage_raw.get("completion_tokens", 0) or 0),
            }
        except (TypeError, ValueError, AttributeError) as exc:
            raise ProviderError("Provider returned invalid token usage", attempts) from exc
        return Response(content, usage, citations, attempts), time.perf_counter() - started
