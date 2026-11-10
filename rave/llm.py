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
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"LLM provider returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach LLM provider: {exc.reason}") from exc
        content = body["choices"][0]["message"]["content"]
        usage = body.get("usage") or {}
        return LLMResponse(content or "", {"prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0))})
