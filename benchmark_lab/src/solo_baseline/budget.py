from __future__ import annotations

import time


class BudgetExceeded(RuntimeError):
    pass


class Budget:
    """Sequential hard-stop budget for search calls, model calls and wall time.

    Token usage is checked immediately after each response. Per-call output
    tokens are capped before sending; prompt tokens are provider-reported and
    therefore can only be checked after the request has completed.
    """
    def __init__(self, *, max_search_calls: int, max_model_calls: int,
                 max_total_tokens: int, max_runtime_seconds: int,
                 max_output_tokens_per_call: int):
        self.max_search_calls = max_search_calls
        self.max_model_calls = max_model_calls
        self.max_total_tokens = max_total_tokens
        self.max_runtime_seconds = max_runtime_seconds
        self.max_output_tokens_per_call = max_output_tokens_per_call
        self.started = time.monotonic()
        self.search_calls = 0
        self.model_calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls: list[dict] = []

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def before_call(self, kind: str) -> int:
        if time.monotonic() - self.started >= self.max_runtime_seconds:
            raise BudgetExceeded("MAX_RUNTIME_SECONDS")
        if self.model_calls >= self.max_model_calls:
            raise BudgetExceeded("MAX_MODEL_CALLS")
        if kind == "search" and self.search_calls >= self.max_search_calls:
            raise BudgetExceeded("MAX_SEARCH_CALLS")
        remaining = self.max_total_tokens - self.total_tokens
        if remaining <= 0:
            raise BudgetExceeded("MAX_TOTAL_TOKENS")
        self.model_calls += 1
        if kind == "search":
            self.search_calls += 1
        return min(self.max_output_tokens_per_call, remaining)

    def record(self, *, kind: str, model: str, usage: dict, duration_seconds: float,
               status: str = "COMPLETED", citations_count: int = 0,
               request_attempts: int = 1) -> None:
        prompt = max(0, int(usage.get("prompt_tokens", 0) or 0))
        completion = max(0, int(usage.get("completion_tokens", 0) or 0))
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.calls.append({
            "kind": kind,
            "model": model,
            "status": status,
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "duration_seconds": duration_seconds,
            "citations_count": citations_count,
            "request_attempts": request_attempts,
        })
        if self.total_tokens > self.max_total_tokens:
            raise BudgetExceeded("MAX_TOTAL_TOKENS_AFTER_PROVIDER_USAGE")
