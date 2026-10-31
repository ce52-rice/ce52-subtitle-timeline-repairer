from pathlib import Path
from uuid import uuid4

from slimconfig import build_output

from contract import ReadOutput

from .common import original_cues, save_json, task_dict


def read_cues(value, workspace):
    task = task_dict(value)
    originals = original_cues(task)
    candidates = []
    last_end = None
    for cue in originals:
        start = max(0, min(task["duration_ms"], cue["start_ms"] + task["offset_ms"]))
        end = max(0, min(task["duration_ms"], cue["end_ms"] + task["offset_ms"]))
        if last_end is not None:
            start = max(start, last_end + task["gap_ms"])
        candidates.append({**cue, "start_ms": start, "end_ms": end})
        if start < end:
            last_end = end
    run = uuid4().hex
    result = {"run": run, "task": task, "originals": originals, "candidates": candidates}
    save_json(Path(workspace) / "reports" / (run + ".read.json"), result)
    return build_output(result, ReadOutput)
