import json
import re
from pathlib import Path

from slimconfig import build_output, plain_output

from contract import RepairOutput

from .common import save_json, validate_task


def save_repair(value, workspace):
    result = plain_output(value)
    validate_task(result["task"])
    run = result["run"]
    if not re.fullmatch(r"[0-9a-f]{32}", run):
        raise ValueError("invalid run token")
    receipt = Path(workspace) / "reports" / (run + ".read.json")
    read = json.loads(receipt.read_text(encoding="utf-8"))
    if read["run"] != run or read["task"] != result["task"]:
        raise ValueError("run belongs to a different task")
    # Deliberately do not repair or judge the submitted candidate selection.
    save_json(Path(workspace) / "reports" / (run + ".json"), result)
    return build_output(result, RepairOutput)
