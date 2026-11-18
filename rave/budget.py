"""Thread-safe run-wide token, request and estimated-cost guard for one RAVE execution."""
from dataclasses import dataclass, field
import math
import os
import time
from threading import RLock


MAX_ALLOWED_RUN_COST_USD = 0.50
WEB_SEARCH_USD_PER_CALL = 0.01


class RunBudgetExceeded(RuntimeError):
    """Raised before or after a provider call when a run-wide limit is reached."""


@dataclass
class RunBudget:
    max_tokens: int
    max_searches: int
    max_model_calls: int
    max_seconds: float
    max_cost_usd: float
    search_input_reserve_tokens: int
    search_input_rate: float
    search_output_rate: float
    started: float = field(default_factory=time.monotonic)
    tokens: int = 0
    searches: int = 0
    calls: int = 0
    cost_usd: float = 0.0
    reserved_tokens: int = 0
    reserved_cost_usd: float = 0.0
    _lock: RLock = field(default_factory=RLock, repr=False, compare=False)

    @classmethod
    def from_env(cls) -> "RunBudget":
        def positive_int(name: str, default: int) -> int:
            try:
                value = int(os.getenv(name, str(default)))
            except ValueError as exc:
                raise ValueError(f"{name} must be a positive integer") from exc
            if value <= 0:
                raise ValueError(f"{name} must be a positive integer")
            return value

        def positive_float(name: str, default: float | None) -> float:
            raw = os.getenv(name)
            if raw is None or not raw.strip():
                if default is None:
                    raise ValueError(f"{name} must be explicitly configured in the local .env")
                raw = str(default)
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError(f"{name} must be a positive number") from exc
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive number")
            return value

        max_cost = positive_float("RAVE_MAX_RUN_COST_USD", MAX_ALLOWED_RUN_COST_USD)
        if max_cost > MAX_ALLOWED_RUN_COST_USD:
            raise ValueError(f"RAVE_MAX_RUN_COST_USD cannot exceed USD {MAX_ALLOWED_RUN_COST_USD:.2f}")
        return cls(
            max_tokens=positive_int("RAVE_MAX_RUN_TOKENS", 80000),
            max_searches=positive_int("RAVE_MAX_RUN_SEARCHES", 3),
            max_model_calls=positive_int("RAVE_MAX_RUN_MODEL_CALLS", 12),
            max_seconds=positive_float("RAVE_MAX_RUN_SECONDS", 180.0),
            max_cost_usd=max_cost,
            search_input_reserve_tokens=positive_int("RAVE_SEARCH_INPUT_RESERVE_TOKENS", 16384),
            # No published dedicated GPT-5 Search API token-rate row: require local
            # values from the user's applicable billing record; never guess.
            search_input_rate=positive_float("RAVE_SEARCH_INPUT_USD_PER_1M", None),
            search_output_rate=positive_float("RAVE_SEARCH_OUTPUT_USD_PER_1M", None),
        )

    def reserve(self, model: str, system: str, user: str, output_tokens: int, web_search: bool):
        with self._lock:
            elapsed = time.monotonic() - self.started
            if elapsed >= self.max_seconds:
                raise RunBudgetExceeded("run_time_budget_exceeded")
            if self.calls >= self.max_model_calls:
                raise RunBudgetExceeded("run_model_call_budget_exceeded")
            if web_search and self.searches >= self.max_searches:
                raise RunBudgetExceeded("run_search_budget_exceeded")
            if output_tokens <= 0:
                raise RunBudgetExceeded("invalid_output_token_reservation")
            local_input = len((system + user).encode("utf-8"))
            input_reserve = local_input + (self.search_input_reserve_tokens if web_search else 0)
            token_reserve = input_reserve + output_tokens
            if self.tokens + self.reserved_tokens + token_reserve > self.max_tokens:
                raise RunBudgetExceeded("run_token_budget_reservation_exceeded")
            if model == "gpt-4.1-mini":
                input_rate, output_rate = 0.40, 1.60
            elif model == "gpt-5-search-api":
                input_rate, output_rate = self.search_input_rate, self.search_output_rate
            else:
                raise RunBudgetExceeded(f"no_price_configured_for_model:{model}")
            estimated_cost = (input_reserve * input_rate + output_tokens * output_rate) / 1_000_000
            if web_search:
                estimated_cost += WEB_SEARCH_USD_PER_CALL
            if self.cost_usd + self.reserved_cost_usd + estimated_cost > self.max_cost_usd:
                raise RunBudgetExceeded("run_cost_budget_reservation_exceeded")
            # Count each attempt, including retries. Failed transient attempts retain
            # their reservation conservatively; only definitive auth rejection releases it.
            self.calls += 1
            if web_search:
                self.searches += 1
            self.reserved_tokens += token_reserve
            self.reserved_cost_usd += estimated_cost
            return token_reserve, estimated_cost

    def release_reservation(self, reservation) -> None:
        """Release a reservation only after a definitive 401/403 rejection."""
        if reservation is None:
            return
        reserved_tokens, reserved_cost = reservation
        with self._lock:
            self.reserved_tokens = max(0, self.reserved_tokens - reserved_tokens)
            self.reserved_cost_usd = max(0.0, self.reserved_cost_usd - reserved_cost)

    def record(self, usage: dict[str, int], reservation, model: str, web_search: bool) -> None:
        if reservation is None:
            raise RunBudgetExceeded("missing_request_budget_reservation")
        input_tokens = int(usage["prompt_tokens"])
        output_tokens = int(usage["completion_tokens"])
        if input_tokens < 0 or output_tokens < 0:
            raise RunBudgetExceeded("provider_returned_invalid_token_usage")
        if model == "gpt-4.1-mini":
            input_rate, output_rate = 0.40, 1.60
        elif model == "gpt-5-search-api":
            input_rate, output_rate = self.search_input_rate, self.search_output_rate
        else:
            raise RunBudgetExceeded(f"no_price_configured_for_model:{model}")
        actual_cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
        if web_search:
            actual_cost += WEB_SEARCH_USD_PER_CALL
        reserved_tokens, reserved_cost = reservation
        with self._lock:
            self.reserved_tokens = max(0, self.reserved_tokens - reserved_tokens)
            self.reserved_cost_usd = max(0.0, self.reserved_cost_usd - reserved_cost)
            self.tokens += input_tokens + output_tokens
            self.cost_usd += actual_cost
            if self.tokens + self.reserved_tokens > self.max_tokens:
                raise RunBudgetExceeded("provider_usage_exceeded_reserved_token_budget")
            if self.cost_usd + self.reserved_cost_usd > self.max_cost_usd:
                raise RunBudgetExceeded("provider_usage_exceeded_reserved_cost_budget")
            if time.monotonic() - self.started > self.max_seconds:
                raise RunBudgetExceeded("run_time_budget_exceeded_during_call")

    def snapshot(self) -> dict:
        with self._lock:
            remaining_seconds = max(0.0, self.max_seconds - (time.monotonic() - self.started))
            return {
                "limits": {
                    "max_tokens": self.max_tokens,
                    "max_searches": self.max_searches,
                    "max_model_calls": self.max_model_calls,
                    "max_seconds": self.max_seconds,
                    "max_cost_usd": self.max_cost_usd,
                },
                "used": {
                    "tokens": self.tokens,
                    "searches": self.searches,
                    "model_calls": self.calls,
                    "estimated_cost_usd": round(self.cost_usd, 8),
                },
                "pricing": {
                    "gpt-4.1-mini": {"input_usd_per_1m": 0.40, "output_usd_per_1m": 1.60},
                    "gpt-5-search-api": {
                        "input_usd_per_1m": self.search_input_rate,
                        "output_usd_per_1m": self.search_output_rate,
                    },
                    "web_search_usd_per_call": WEB_SEARCH_USD_PER_CALL,
                    "search_rate_source": "explicit local .env configuration; verify against the billing record",
                },
                "reserved": {
                    "tokens": self.reserved_tokens,
                    "estimated_cost_usd": round(self.reserved_cost_usd, 8),
                },
                "remaining": {
                    "tokens": max(0, self.max_tokens - self.tokens - self.reserved_tokens),
                    "searches": max(0, self.max_searches - self.searches),
                    "model_calls": max(0, self.max_model_calls - self.calls),
                    "seconds": remaining_seconds,
                    "cost_usd": round(max(0.0, self.max_cost_usd - self.cost_usd - self.reserved_cost_usd), 8),
                },
                "note": (
                    "Local estimate only; provider-side search context is variable. "
                    "Enable an independent OpenAI project spend limit."
                ),
            }
