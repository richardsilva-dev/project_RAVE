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
    citations: list[dict[str, str]] | None = None

class ChatCompletionsClient:
    """Minimal OpenAI-compatible client using Python standard library."""
    def __init__(self, settings: Settings):
        self.settings = settings

    def complete(self, system: str, user: str, *, web_search: bool = False) -> LLMResponse:
        if not self.settings.api_key:
            raise RuntimeError("RAVE_API_KEY is missing. Configure it in your environment.")
        if len(system) > 100_000 or len(user) > 1_000_000:
            raise ValueError("LLM prompt exceeds the configured safety limit")
        if web_search:
            if not self.settings.web_search_enabled:
                raise RuntimeError("Web search is disabled in configuration")
            payload = {"model": self.settings.web_search_model, "instructions": system, "input": user,
                "tools": [{"type": "web_search", "search_context_size": "medium"}],
                "tool_choice": "required", "include": ["web_search_call.action.sources"]}
            endpoint = f"{self.settings.base_url}/responses"
        else:
            payload = {"model": self.settings.model, "temperature": self.settings.temperature,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            endpoint = f"{self.settings.base_url}/chat/completions"
        request = urllib.request.Request(endpoint,
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
        citations: list[dict[str, str]] = []
        if web_search:
            chunks = []
            for item in body.get("output", []):
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                for part in item.get("content", []):
                    if not isinstance(part, dict):
                        continue
                    if isinstance(part.get("text"), str):
                        chunks.append(part["text"])
                    for annotation in part.get("annotations", []):
                        cited = annotation.get("url_citation", {}) if isinstance(annotation, dict) else {}
                        if isinstance(cited, dict) and isinstance(cited.get("url"), str):
                            citations.append({"title": str(cited.get("title", "")), "url": cited["url"]})
            content = "\n".join(chunks) or body.get("output_text")
            for item in body.get("output", []):
                if isinstance(item, dict) and item.get("type") == "web_search_call":
                    action = item.get("action", {})
                    for source in action.get("sources", []) if isinstance(action, dict) else []:
                        if isinstance(source, dict) and isinstance(source.get("url"), str):
                            citations.append({"title": str(source.get("title", "")), "url": source["url"]})
        else:
            try:
                content = body["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError("LLM provider returned an invalid Chat Completions response") from exc
        if not isinstance(content, str):
            raise RuntimeError("LLM provider returned no text content")
        if web_search:
            usage = body.get("usage") or {}
            usage = {"prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0)}
        else:
            usage = body.get("usage") or {}
        try:
            tokens = {"prompt_tokens": max(0, int(usage.get("prompt_tokens", 0))),
                "completion_tokens": max(0, int(usage.get("completion_tokens", 0)))}
        except (TypeError, ValueError, AttributeError) as exc:
            raise RuntimeError("LLM provider returned invalid usage metadata") from exc
        unique_citations = list({citation["url"]: citation for citation in citations}.values())
        return LLMResponse(content, tokens, unique_citations)
