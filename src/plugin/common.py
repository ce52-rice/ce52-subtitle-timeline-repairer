import json
from pathlib import Path

from slimconfig import plain_output


def task_dict(value):
    return plain_output(value)


def validate_task(task):
    if task["case_id"] not in ("tutorial", "overlap", "edges", "empty"):
        raise ValueError("unknown case")
    for field, low, high in (("offset_ms", -60000, 60000), ("duration_ms", 1, 120000), ("gap_ms", 0, 5000)):
        if type(task[field]) is not int or not low <= task[field] <= high:
            raise ValueError(f"{field} must be an integer from {low} to {high}")


def original_cues(task):
    validate_task(task)
    return json.loads((Path(__file__).parent / "data" / (task["case_id"] + ".json")).read_text(encoding="utf-8"))


def run_ids(workspace):
    folder = Path(workspace) / "reports"
    return sorted(p.name.removesuffix(".read.json") for p in folder.glob("*.read.json")) if folder.exists() else []


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
