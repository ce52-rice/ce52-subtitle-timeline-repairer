from pathlib import Path

from .checks import cues_problem, expected, plain, read_json, result, saved_problem, task_problem


def verify_task(arguments, output, reference, workspace):
    task, report, pin = plain(arguments), plain(output), plain(reference)
    problem = task_problem(task)
    if problem:
        return result(False, problem)
    if not isinstance(pin, dict) or set(pin) != {"task", "cues", "prior_runs"} or pin["task"] != task:
        return result(False, "missing or mismatched pinned reference")
    problem = cues_problem(pin["cues"]) or saved_problem(report, workspace)
    if problem:
        return result(False, problem)
    if report["task"] != task:
        return result(False, "submitted task differs")
    if report["run"] in pin["prior_runs"]:
        return result(False, "artifact belongs to a prior run")
    receipt, problem = read_json(Path(workspace) / "reports" / (report["run"] + ".read.json"))
    if problem:
        return result(False, problem)
    if not isinstance(receipt, dict) or set(receipt) != {"run", "task", "originals", "candidates"}:
        return result(False, "malformed read receipt")
    candidates, subtitles, dropped = expected(task, pin["cues"])
    if receipt != {"run": report["run"], "task": task, "originals": pin["cues"], "candidates": candidates}:
        return result(False, "read receipt differs from pinned data or rules")
    if report["subtitles"] != subtitles:
        return result(False, "retained subtitles differ from exact timings, text or order")
    if report["dropped_ids"] != dropped:
        return result(False, "dropped IDs differ from exact drop decisions or order")
    return result(
        True, "Saved artifact and submitted repair satisfy every rule", kept=len(subtitles), dropped=len(dropped)
    )
