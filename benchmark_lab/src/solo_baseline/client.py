from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class Response:
    content: str
    usage: dict[str, int]
    citations: list[dict]


class ProviderError(RuntimeError):
    pass


class ChatCompletionsClient:
    """Small, isolated client using the same Chat Completions route as RAVE."""
    def __init__(self, api_key: str, base_url: str, timeout_seconds: int,
                 temperature: float):
        if not api_key:
            raise ValueError("SOLO_API_KEY is missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

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
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Never include provider response bodies, headers or credentials in logs.
            raise ProviderError(f"Provider returned HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Provider request failed: {type(exc).__name__}") from exc
        try:
            message = body["choices"][0]["message"]
            content = message["content"]
            if not isinstance(content, str):
                raise TypeError("content is not text")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider response did not contain message text") from exc
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
        usage = {
            "prompt_tokens": int(usage_raw.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage_raw.get("completion_tokens", 0) or 0),
        }
        return Response(content, usage, citations), time.perf_counter() - started
