from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import SoloResearchAgent
from .client import ChatCompletionsClient
from .config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the isolated single-researcher RAVE baseline.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--scope", default="Investigate the question without expanding beyond necessity.")
    args = parser.parse_args()
    settings = Settings.from_env()
    client = ChatCompletionsClient(settings.api_key, settings.base_url,
                                   settings.timeout_seconds, settings.temperature)
    result = SoloResearchAgent(client, settings).run(args.question, args.scope)
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result['run_id']}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": result["run_id"], "status": result["status"],
                      "result_path": str(path), "total_tokens": result["budget"]["total_tokens"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
