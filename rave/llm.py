import json
import re
import logging
import time
import contextvars
import http.client
import urllib.error
import urllib.request
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from threading import BoundedSemaphore
from typing import Any
from .config import Settings
from .budget import RunBudget, RunBudgetExceeded

logger = logging.getLogger(__name__)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    handler_order = 100

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a Bearer authorization header to a redirected host.
        return None


def _open_url(request, timeout):
    opener = urllib.request.build_opener(_NoRedirectHandler())
    return opener.open(request, timeout=timeout)
_active_call_log: contextvars.ContextVar[list[dict[str, Any]] | None] = contextvars.ContextVar("rave_call_log", default=None)
_active_run_budget: contextvars.ContextVar[RunBudget | None] = contextvars.ContextVar("rave_run_budget", default=None)

class capture_llm_calls:
    """Isolate telemetry and one shared budget to one async run."""
    def __init__(self, budget: RunBudget | None = None):
        self.budget = budget

    def __enter__(self):
        self.calls: list[dict[str, Any]] = []
        self.token = _active_call_log.set(self.calls)
        self.budget_token = _active_run_budget.set(self.budget)
        return self.calls

    def __exit__(self, *_):
        _active_call_log.reset(self.token)
        _active_run_budget.reset(self.budget_token)

def current_llm_calls() -> list[dict[str, Any]]:
    return _active_call_log.get() or []


def current_run_budget() -> RunBudget | None:
    return _active_run_budget.get()

@dataclass
class LLMResponse:
    content: str
    usage: dict[str, int]
    citations: list[dict[str, str]] | None = None

class ChatCompletionsClient:
    """Minimal OpenAI-compatible client using Python standard library."""
    def __init__(self, settings: Settings):
        self.settings = settings
        self._request_semaphore = BoundedSemaphore(settings.max_concurrent_requests)

    def complete(self, system: str, user: str, *, web_search: bool = False, max_completion_tokens: int | None = None) -> LLMResponse:
        call_started = time.perf_counter()
        attempts = 0
        if not self.settings.api_key:
            raise RuntimeError("RAVE_API_KEY is missing. Configure it in your environment.")
        if len(system) > 100_000 or len(user) > 1_000_000:
            raise ValueError("LLM prompt exceeds the configured safety limit")
        if web_search:
            if not self.settings.web_search_enabled:
                raise RuntimeError("Web search is disabled in configuration")
            payload = {"model": self.settings.web_search_model,
                "web_search_options": {"search_context_size": self.settings.web_search_context_size},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "max_completion_tokens": self.settings.web_search_max_output_tokens}
        else:
            payload = {"model": self.settings.model, "temperature": self.settings.temperature,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "max_completion_tokens": (self.settings.analysis_max_output_tokens if max_completion_tokens is None else max_completion_tokens)}
        endpoint = f"{self.settings.base_url}/chat/completions"
        request = urllib.request.Request(endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.settings.api_key}", "Content-Type": "application/json"},
            method="POST")
        with self._request_semaphore:
            for attempt in range(3):
                attempts += 1
                reservation = None
                budget = current_run_budget()
                try:
                    timeout = self.settings.timeout_seconds
                    if budget is not None:
                        reservation = budget.reserve(payload["model"], system, user,
                            payload["max_completion_tokens"], web_search)
                        timeout = min(timeout, max(0.001, budget.snapshot()["remaining"]["seconds"]))
                    with _open_url(request, timeout=timeout) as response:
                        try:
                            body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                            self._record_call(system, user, web_search, call_started, attempts,
                                {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
                            raise RuntimeError("LLM provider returned an invalid JSON response") from exc
                    break
                except urllib.error.HTTPError as exc:
                    error_code, error_type = self._safe_error_fields(exc)
                    retry_values = [self._retry_after_seconds(exc.headers.get(header))
                        for header in ("Retry-After", "x-ratelimit-reset-tokens")]
                    retry_after = max((value for value in retry_values if value is not None), default=None)
                    transient_rate_limit = exc.code == 429 and (
                        error_code in {"rate_limit_exceeded", "slow_down"} or error_type == "rate_limit_error"
                    )
                    if transient_rate_limit and attempt < 2:
                        delay = retry_after if retry_after is not None else 2 ** attempt
                        if delay <= 420:
                            logger.warning("Rate limited; retrying after %.1fs", delay)
                            time.sleep(delay)
                            continue
                    details = []
                    if error_code:
                        details.append(f"code={error_code}")
                    if error_type:
                        details.append(f"type={error_type}")
                    if retry_after is not None:
                        details.append(f"retry_after={retry_after:g}s")
                    for header, label in (("x-ratelimit-limit-tokens", "token_limit"),
                        ("x-ratelimit-remaining-tokens", "tokens_remaining"), ("x-ratelimit-reset-tokens", "token_reset")):
                        value = exc.headers.get(header, "")
                        if value and re.fullmatch(r"[0-9A-Za-z.]+", value):
                            details.append(f"{label}={value}")
                    request_id = exc.headers.get("x-request-id", "")
                    if request_id and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request_id):
                        details.append(f"request_id={request_id}")
                    suffix = f" ({', '.join(details)})" if details else ""
                    if exc.code in {401, 403} and budget is not None and reservation is not None:
                        budget.release_reservation(reservation)
                    self._record_call(system, user, web_search, call_started, attempts,
                        {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
                    raise RuntimeError(f"LLM provider returned HTTP {exc.code}{suffix}") from exc
                except urllib.error.URLError as exc:
                    self._record_call(system, user, web_search, call_started, attempts,
                        {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
                    raise RuntimeError(f"Could not reach LLM provider: {exc.reason}") from exc
                except (OSError, http.client.HTTPException) as exc:
                    self._record_call(system, user, web_search, call_started, attempts,
                        {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
                    raise RuntimeError(f"Connection to LLM provider failed: {type(exc).__name__}") from exc
        citations: list[dict[str, str]] = []
        try:
            message = body["choices"][0]["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            self._record_call(system, user, web_search, call_started, attempts,
                {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
            raise RuntimeError("LLM provider returned an invalid Chat Completions response") from exc
        if web_search:
            for annotation in message.get("annotations", []):
                cited = annotation.get("url_citation", {}) if isinstance(annotation, dict) else {}
                if isinstance(cited, dict) and isinstance(cited.get("url"), str):
                    citations.append({"title": str(cited.get("title", "")), "url": cited["url"]})
        if not isinstance(content, str):
            self._record_call(system, user, web_search, call_started, attempts,
                {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
            raise RuntimeError("LLM provider returned no text content")
        usage = body.get("usage") or {}
        try:
            tokens = {"prompt_tokens": max(0, int(usage.get("prompt_tokens", 0))),
                "completion_tokens": max(0, int(usage.get("completion_tokens", 0)))}
        except (TypeError, ValueError, AttributeError) as exc:
            self._record_call(system, user, web_search, call_started, attempts,
                {"prompt_tokens": 0, "completion_tokens": 0}, "FAILED")
            raise RuntimeError("LLM provider returned invalid usage metadata") from exc
        unique_citations = list({citation["url"]: citation for citation in citations}.values())
        self._record_call(system, user, web_search, call_started, attempts, tokens, "COMPLETED")
        budget = current_run_budget()
        if budget is not None and reservation is not None:
            budget.record(tokens, reservation, payload["model"], web_search)
        return LLMResponse(content, tokens, unique_citations)

    def _record_call(self, system: str, user: str, web_search: bool, started: float,
            attempts: int, tokens: dict[str, int], status: str) -> None:
        call_log = _active_call_log.get()
        if call_log is not None:
            call_log.append({"model": self.settings.web_search_model if web_search else self.settings.model,
                "purpose": self._purpose(system, user, web_search), "status": status,
                "prompt_tokens": tokens["prompt_tokens"], "completion_tokens": tokens["completion_tokens"],
                "duration_seconds": time.perf_counter() - started, "request_attempts": attempts})

    @staticmethod
    def _purpose(system: str, user: str, web_search: bool) -> str:
        if "format_repair" in user:
            return "json_repair"
        if "shared web research component" in system:
            return "shared_web_research"
        if "synthesis component" in system:
            return "final_synthesis"
        if "cross_agent_integration" in user:
            return "cross_agent_refinement"
        if "single_agent_baseline" in user:
            return "single_agent_analysis"
        if "RAVE Agent " in system:
            return "agent_initial_research" if web_search else "agent_initial_analysis"
        return "web_search" if web_search else "llm_completion"

    @staticmethod
    def _safe_error_fields(exc: urllib.error.HTTPError) -> tuple[str, str]:
        try:
            payload = json.loads(exc.read(64_000).decode("utf-8", errors="replace"))
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            if not isinstance(error, dict):
                return "", ""
            code = error.get("code")
            error_type = error.get("type")
            code = code if isinstance(code, str) and code.replace("_", "").replace("-", "").isalnum() else ""
            error_type = error_type if isinstance(error_type, str) and error_type.replace("_", "").replace("-", "").isalnum() else ""
            return code[:80], error_type[:80]
        except (AttributeError, OSError, ValueError, TypeError):
            return "", ""

    @staticmethod
    def _retry_after_seconds(value: str | None) -> float | None:
        if not value:
            return None
        try:
            seconds = float(value)
        except ValueError:
            duration = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", value)
            if duration and any(duration.groups()):
                hours, minutes, secs = duration.groups()
                seconds = int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(secs or 0)
                return max(0.0, seconds)
            try:
                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                return None
        return max(0.0, seconds)
