from slimconfig import build_output

from contract import PinOutput

from .common import original_cues, run_ids, task_dict


def pin_case(value, workspace):
    task = task_dict(value)
    return build_output({"task": task, "cues": original_cues(task), "prior_runs": run_ids(workspace)}, PinOutput)
