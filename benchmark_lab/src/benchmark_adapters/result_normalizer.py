from __future__ import annotations

from typing import Any


VALID_STATUSES = {"COMPLETED", "PARTIAL", "INVALID"}


def _status(value: Any) -> str:
    normalized = str(value or "INVALID").upper()
    return normalized if normalized in VALID_STATUSES else "INVALID"


def normalize_rave(raw: dict, *, commit_sha: str | None = None) -> dict:
    metadata = raw.get("metadata") or {}
    status = _status(raw.get("execution_status") or metadata.get("status"))
    integration = raw.get("integration") or {}
    final_output = raw.get("final_output") or {}
    sources = integration.get("web_sources") or final_output.get("web_sources") or []
    return {
        "run_id": raw.get("run_id") or metadata.get("run_id"),
        "system_id": "rave",
        "status": status,
        "final_output": final_output,
        "sources": sources,
        "metadata": {
            "commit_sha": commit_sha,
            "model": metadata.get("model"),
            "configuration": metadata.get("configuration"),
            "calls": metadata.get("calls", []),
            "token_usage": {
                "prompt_tokens": metadata.get("prompt_tokens"),
                "completion_tokens": metadata.get("completion_tokens"),
            },
            "duration_seconds": metadata.get("duration_seconds"),
            "phase_timings": raw.get("phase_timings"),
            "synthesis_status": raw.get("synthesis_status"),
            "synthesis_error": raw.get("synthesis_error"),
            "failed_agents": raw.get("failed_agents", []),
            "native_metadata": metadata,
        },
    }


def normalize_solo(raw: dict, *, commit_sha: str | None = None) -> dict:
    budget = raw.get("budget") or {}
    return {
        "run_id": raw.get("run_id"),
        "system_id": "solo_baseline",
        "status": _status(raw.get("status")),
        "final_output": raw.get("final_output") or {},
        "sources": raw.get("provider_returned_sources", []),
        "metadata": {
            "commit_sha": commit_sha,
            "models": {
                "analysis": raw.get("model"),
                "web_search": raw.get("web_search_model"),
            },
            "calls": raw.get("calls", []),
            "token_usage": {
                "prompt_tokens": budget.get("prompt_tokens"),
                "completion_tokens": budget.get("completion_tokens"),
                "total_tokens": budget.get("total_tokens"),
            },
            "duration_seconds": raw.get("duration_seconds"),
            "failure_reason": raw.get("stop_reason"),
            "native_metadata": {
                "research_mode": raw.get("research_mode"),
                "delegation_enabled": raw.get("delegation_enabled"),
                "agent_count": raw.get("agent_count"),
                "budget": budget,
            },
        },
    }


def normalize_open_deep_research(raw: dict, *, commit_sha: str | None = None) -> dict:
    """Normalize only an explicitly extracted report; never guess from message order."""
    final_output = raw.get("final_output")
    if not isinstance(final_output, dict):
        raise ValueError("Open Deep Research adapter requires an explicitly extracted final_output object")
    metadata = raw.get("metadata") or {}
    sources = raw.get("provider_returned_sources")
    if not isinstance(sources, list):
        sources = []
    return {
        "run_id": raw.get("run_id"),
        "system_id": "open_deep_research",
        "status": _status(raw.get("status")),
        "final_output": final_output,
        "sources": sources,
        "metadata": {
            "commit_sha": commit_sha,
            "models": metadata.get("models"),
            "tools": metadata.get("tools"),
            "calls": metadata.get("calls", []),
            "token_usage": metadata.get("token_usage"),
            "duration_seconds": metadata.get("duration_seconds"),
            "failure_reason": raw.get("failure_reason"),
            "native_metadata": metadata,
        },
    }


def validate_normalized_result(result: dict) -> None:
    required = {"run_id", "system_id", "status", "final_output", "sources", "metadata"}
    if not isinstance(result, dict) or not required.issubset(result):
        raise ValueError("Normalized result is missing required top-level fields")
    if result["system_id"] not in {"rave", "solo_baseline", "open_deep_research"}:
        raise ValueError("Unknown system_id")
    if result["status"] not in VALID_STATUSES:
        raise ValueError("Invalid execution status")
    if not isinstance(result["final_output"], dict) or not isinstance(result["sources"], list):
        raise ValueError("Invalid final_output or sources type")
    if not isinstance(result["metadata"], dict):
        raise ValueError("Invalid metadata type")


def normalize_result(system_id: str, raw: dict, *, commit_sha: str | None = None) -> dict:
    adapters = {
        "rave": normalize_rave,
        "solo_baseline": normalize_solo,
        "open_deep_research": normalize_open_deep_research,
    }
    if system_id not in adapters:
        raise ValueError(f"Unsupported system_id: {system_id}")
    result = adapters[system_id](raw, commit_sha=commit_sha)
    validate_normalized_result(result)
    return result
