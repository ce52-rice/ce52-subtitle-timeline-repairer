import json
import re
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path


def result(valid, message, **details):
    return {"valid": valid, "score": float(valid), "message": message, "details": details}


def plain(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    return value


def task_problem(task):
    if not isinstance(task, dict) or set(task) != {"case_id", "offset_ms", "duration_ms", "gap_ms"}:
        return "malformed task"
    if task["case_id"] not in ("tutorial", "overlap", "edges", "empty"):
        return "unknown case"
    for field, low, high in (("offset_ms", -60000, 60000), ("duration_ms", 1, 120000), ("gap_ms", 0, 5000)):
        if type(task[field]) is not int or not low <= task[field] <= high:
            return field + " is outside the integer limits"
    return None


def cues_problem(cues):
    if not isinstance(cues, list) or len(cues) > 20:
        return "cues must be a list of at most 20 entries"
    seen = set()
    for cue in cues:
        if not isinstance(cue, dict) or set(cue) != {"id", "start_ms", "end_ms", "text"}:
            return "malformed cue"
        if not isinstance(cue["id"], str) or not cue["id"] or cue["id"] in seen:
            return "cue IDs must be nonempty and unique"
        if not isinstance(cue["text"], str):
            return "cue text must be a string"
        if type(cue["start_ms"]) is not int or type(cue["end_ms"]) is not int:
            return "cue times must be integers"
        seen.add(cue["id"])
    return None


def token_ok(run):
    return isinstance(run, str) and re.fullmatch(r"[0-9a-f]{32}", run) is not None


def read_json(path):
    path = Path(path)
    if not path.is_file():
        return None, "missing file"
    try:
        text = path.read_text(encoding="utf-8")
        if len(text) > 200000:
            return None, "oversized file"
        return json.loads(text), None
    except (ValueError, UnicodeError, OSError):
        return None, "malformed or unreadable JSON"


def expected(task, originals):
    # Independent implementation: work in shifted coordinates, then enforce
    # constraints through lower/upper bounds. No production tool imports.
    candidates, retained, dropped = [], [], []
    previous = []
    for cue in originals:
        a = cue["start_ms"] + task["offset_ms"]
        b = cue["end_ms"] + task["offset_ms"]
        a = 0 if a < 0 else min(a, task["duration_ms"])
        b = 0 if b < 0 else min(b, task["duration_ms"])
        lower_bounds = [a]
        if previous:
            lower_bounds.append(previous[-1] + task["gap_ms"])
        a = max(lower_bounds)
        candidate = {"id": cue["id"], "start_ms": a, "end_ms": b, "text": cue["text"]}
        candidates.append(candidate)
        if b > a:
            retained.append(candidate)
            previous.append(b)
        else:
            dropped.append(cue["id"])
    return candidates, retained, dropped


def report_problem(report):
    if not isinstance(report, dict) or set(report) != {"run", "task", "subtitles", "dropped_ids"}:
        return "malformed report"
    if not token_ok(report["run"]):
        return "invalid run token"
    problem = task_problem(report["task"]) or cues_problem(report["subtitles"])
    if problem:
        return problem
    ids = report["dropped_ids"]
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids) or len(ids) != len(set(ids)):
        return "dropped_ids must contain distinct strings"
    return None


def saved_problem(report, workspace):
    if report_problem(report):
        return report_problem(report)
    saved, problem = read_json(Path(workspace) / "reports" / (report["run"] + ".json"))
    if problem:
        return problem
    problem = report_problem(saved)
    if problem:
        return problem
    if saved != report:
        return "submitted report differs from saved artifact"
    return None
