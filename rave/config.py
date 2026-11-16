from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit

def _load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE lines without overriding existing environment values."""
    file = Path(path)
    if not file.exists():
        return
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'").strip())

@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.2
    timeout_seconds: int = 90
    output_dir: str = "data/runs"
    web_search_enabled: bool = True
    web_search_model: str = "gpt-5-search-api"
    max_concurrent_requests: int = 1
    web_search_context_size: str = "low"
    web_search_max_output_tokens: int = 512
    analysis_max_output_tokens: int = 8192
    synthesis_max_output_tokens: int = 8192

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        try:
            temperature = float(os.getenv("RAVE_TEMPERATURE", "0.2"))
            timeout = int(os.getenv("RAVE_TIMEOUT_SECONDS", "90"))
            max_concurrent = int(os.getenv("RAVE_MAX_CONCURRENT_REQUESTS", "1"))
            web_search_max_output = int(os.getenv("RAVE_WEB_SEARCH_MAX_OUTPUT_TOKENS", "512"))
            analysis_max_output = int(os.getenv("RAVE_ANALYSIS_MAX_OUTPUT_TOKENS", "8192"))
            synthesis_max_output = int(os.getenv("RAVE_SYNTHESIS_MAX_OUTPUT_TOKENS", "8192"))
        except ValueError as exc:
            raise ValueError("RAVE_TEMPERATURE must be numeric and token/time limits integers") from exc
        base_url = os.getenv("RAVE_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("RAVE_BASE_URL must be an absolute HTTP(S) URL without embedded credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("RAVE_BASE_URL must not contain a query string or fragment")
        model = os.getenv("RAVE_MODEL", "gpt-4.1-mini").strip()
        output_dir = os.getenv("RAVE_OUTPUT_DIR", "data/runs").strip()
        web_search_text = os.getenv("RAVE_WEB_SEARCH", "true").strip().lower()
        if web_search_text not in {"true", "false", "1", "0", "yes", "no"}:
            raise ValueError("RAVE_WEB_SEARCH must be true or false")
        web_search_enabled = web_search_text in {"true", "1", "yes"}
        web_search_model = os.getenv("RAVE_WEB_SEARCH_MODEL", "gpt-5-search-api").strip()
        context_size = os.getenv("RAVE_WEB_SEARCH_CONTEXT_SIZE", "low").strip().lower()
        if not model or not output_dir or not 0 <= temperature <= 2 or timeout <= 0 or max_concurrent <= 0 or web_search_max_output <= 0 or analysis_max_output <= 0 or synthesis_max_output <= 0:
            raise ValueError("Model/output directory required; temperature 0..2 and all limits positive")
        if context_size not in {"low", "medium", "high"}:
            raise ValueError("RAVE_WEB_SEARCH_CONTEXT_SIZE must be low, medium, or high")
        if web_search_enabled and not web_search_model:
            raise ValueError("RAVE_WEB_SEARCH_MODEL is required when web search is enabled")
        if web_search_enabled and parsed.hostname != "api.openai.com":
            raise ValueError("Built-in web search requires RAVE_BASE_URL=https://api.openai.com/v1; disable it for compatible providers")
        return cls(os.getenv("RAVE_API_KEY", "").strip(), base_url, model, temperature, timeout,
            output_dir, web_search_enabled, web_search_model, max_concurrent, context_size,
            web_search_max_output, analysis_max_output, synthesis_max_output)
