import json
from pathlib import Path
from dataclasses import asdict, is_dataclass

def serialize(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value

def save_run(output_dir: str, run_id: str, payload: dict) -> Path:
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run_id}.json"
    path.write_text(json.dumps(serialize(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
