import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from .config import Settings

@dataclass
class LLMResponse:
    content: str
    usage: dict[str, int]

class ChatCompletionsClient:
    """Minimal OpenAI-compatible client using Python standard library."""
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, system: str, user: str) -> LLMResponse:
        if not self.settings.api_key:
            raise RuntimeError("RAVE_API_KEY is missing. Configure it in your environment.")
        if len(system) > 100_000 or len(user) > 1_000_000:
            raise ValueError("LLM prompt exceeds the configured safety limit")
        payload = {"model": self.settings.model, "temperature": self.settings.temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        request = urllib.request.Request(f"{self.settings.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.settings.timeout_seconds) as response:
                body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # Provider error bodies can echo credentials or submitted prompts.
            raise RuntimeError(f"LLM provider returned HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach LLM provider: {exc.reason}") from exc
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM provider returned an invalid Chat Completions response") from exc
        if not isinstance(content, str):
            raise RuntimeError("LLM provider returned non-text message content")
        usage = body.get("usage") or {}
        try:
            tokens = {"prompt_tokens": max(0, int(usage.get("prompt_tokens", 0))),
                "completion_tokens": max(0, int(usage.get("completion_tokens", 0)))}
        except (TypeError, ValueError, AttributeError) as exc:
            raise RuntimeError("LLM provider returned invalid usage metadata") from exc
        return LLMResponse(content, tokens)
