from __future__ import annotations

import os
import subprocess
from pathlib import Path


PINNED_ODR_SHA = "1b7d2e80db9faa586165c60e09096dbbfd483a64"


def check_solo() -> list[str]:
    errors = []
    if not os.getenv("SOLO_API_KEY"):
        errors.append("SOLO_API_KEY is not set")
    if not os.getenv("SOLO_MODEL", "gpt-4.1-mini"):
        errors.append("SOLO_MODEL is empty")
    if not os.getenv("SOLO_WEB_SEARCH_MODEL", "gpt-5-search-api"):
        errors.append("SOLO_WEB_SEARCH_MODEL is empty")
    return errors


def check_open_deep_research(lab_root: Path) -> list[str]:
    errors = []
    upstream = lab_root / "comparison_b" / "upstream" / "open_deep_research"
    if not (upstream / "pyproject.toml").exists():
        errors.append("Open Deep Research submodule is not installed")
        return errors
    try:
        sha = subprocess.check_output(
            ["git", "-C", str(upstream), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        if sha != PINNED_ODR_SHA:
            errors.append(f"Open Deep Research SHA mismatch: {sha}")
    except (OSError, subprocess.CalledProcessError):
        errors.append("Could not verify Open Deep Research Git SHA")
    if not (upstream / "uv.lock").exists():
        errors.append("Pinned Open Deep Research uv.lock is missing")
    return errors


def main() -> int:
    lab_root = Path(__file__).resolve().parents[1]
    errors = check_solo() + check_open_deep_research(lab_root)
    if errors:
        for error in errors:
            print(f"BLOCKED: {error}")
        return 1
    print("Preflight passed. This checks configuration only; it does not make paid API calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
