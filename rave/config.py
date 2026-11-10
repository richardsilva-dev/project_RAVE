from dataclasses import dataclass
import os
from pathlib import Path

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

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        return cls(api_key=os.getenv("RAVE_API_KEY", ""),
            base_url=os.getenv("RAVE_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            model=os.getenv("RAVE_MODEL", "gpt-4.1-mini"),
            temperature=float(os.getenv("RAVE_TEMPERATURE", "0.2")),
            timeout_seconds=int(os.getenv("RAVE_TIMEOUT_SECONDS", "90")),
            output_dir=os.getenv("RAVE_OUTPUT_DIR", "data/runs"))
