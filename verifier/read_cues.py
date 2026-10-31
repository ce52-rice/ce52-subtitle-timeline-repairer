from pathlib import Path

from . import pin_case
from .checks import cues_problem, expected, plain, read_json, result, task_problem, token_ok


def verify_input(value):
    return pin_case.verify_input(value)


def verify_output(input_value, output_value, workspace):
    task, read = plain(input_value), plain(output_value)
    problem = task_problem(task) or cues_problem(read["originals"]) or cues_problem(read["candidates"])
    if problem:
        return result(False, problem)
    if not token_ok(read["run"]) or read["task"] != task:
        return result(False, "read belongs to a different task or has an invalid run")
    if read["candidates"] != expected(task, read["originals"])[0]:
        return result(False, "candidate timings differ from the rules")
    saved, problem = read_json(Path(workspace) / "reports" / (read["run"] + ".read.json"))
    return result(not problem and saved == read, problem or "read receipt comparison")
