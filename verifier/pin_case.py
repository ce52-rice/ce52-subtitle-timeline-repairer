from .checks import cues_problem, plain, result, task_problem, token_ok


def verify_input(value):
    problem = task_problem(plain(value))
    return result(not problem, problem or "valid task")


def verify_output(input_value, output_value, workspace):
    source, pin = plain(input_value), plain(output_value)
    if not isinstance(pin, dict) or set(pin) != {"task", "cues", "prior_runs"}:
        return result(False, "malformed pinned reference")
    problem = task_problem(source) or cues_problem(pin["cues"])
    if problem:
        return result(False, problem)
    if pin["task"] != source:
        return result(False, "reference task differs")
    prior = pin["prior_runs"]
    if not isinstance(prior, list) or not all(token_ok(run) for run in prior) or len(set(prior)) != len(prior):
        return result(False, "prior_runs must contain distinct run tokens")
    if any(cue["start_ms"] >= cue["end_ms"] for cue in pin["cues"]):
        return result(False, "original cue must have positive duration")
    return result(True, "reference is well formed")
