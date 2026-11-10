from dataclasses import dataclass
import os

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
        return cls(api_key=os.getenv("RAVE_API_KEY", ""),
            base_url=os.getenv("RAVE_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            model=os.getenv("RAVE_MODEL", "gpt-4.1-mini"),
            temperature=float(os.getenv("RAVE_TEMPERATURE", "0.2")),
            timeout_seconds=int(os.getenv("RAVE_TIMEOUT_SECONDS", "90")),
            output_dir=os.getenv("RAVE_OUTPUT_DIR", "data/runs"))
