import json
import os
from pathlib import Path
from dataclasses import asdict, is_dataclass
import re
import tempfile

def serialize(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value

def save_run(output_dir: str, run_id: str, payload: dict) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id):
        raise ValueError("run_id contains unsupported characters")
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run_id}.json"
    serialized = json.dumps(serialize(payload), ensure_ascii=False, indent=2)
    fd, temporary = tempfile.mkstemp(prefix=f".{run_id}-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return path
