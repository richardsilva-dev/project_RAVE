from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE lines without overriding explicit environment values."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    web_search_model: str
    timeout_seconds: int
    temperature: float
    max_search_calls: int
    max_model_calls: int
    max_total_tokens: int
    max_runtime_seconds: int
    max_output_tokens_per_call: int
    output_dir: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        def integer(name: str, default: int) -> int:
            try:
                value = int(os.getenv(name, str(default)))
            except ValueError as exc:
                raise ValueError(f"{name} must be an integer") from exc
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")
            return value

        try:
            temperature = float(os.getenv("SOLO_TEMPERATURE", "0.2"))
        except ValueError as exc:
            raise ValueError("SOLO_TEMPERATURE must be numeric") from exc
        if not 0 <= temperature <= 2:
            raise ValueError("SOLO_TEMPERATURE must be between 0 and 2")
        base_url = os.getenv("SOLO_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        if not base_url.startswith("https://"):
            raise ValueError("SOLO_BASE_URL must use HTTPS")
        return cls(
            api_key=os.getenv("SOLO_API_KEY", ""),
            base_url=base_url,
            model=os.getenv("SOLO_MODEL", "gpt-4.1-mini"),
            web_search_model=os.getenv("SOLO_WEB_SEARCH_MODEL", "gpt-5-search-api"),
            timeout_seconds=integer("SOLO_TIMEOUT_SECONDS", 90),
            temperature=temperature,
            max_search_calls=integer("SOLO_MAX_SEARCH_CALLS", 3),
            max_model_calls=integer("SOLO_MAX_MODEL_CALLS", 12),
            max_total_tokens=integer("SOLO_MAX_TOTAL_TOKENS", 30000),
            max_runtime_seconds=integer("SOLO_MAX_RUNTIME_SECONDS", 600),
            max_output_tokens_per_call=integer("SOLO_MAX_OUTPUT_TOKENS_PER_CALL", 4000),
            output_dir=os.getenv("SOLO_OUTPUT_DIR", "artifacts/solo_runs"),
        )
