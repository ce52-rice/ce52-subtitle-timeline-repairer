from contract import Task, Tool

from . import pin_case, read_cues, save_repair, task
from .checks import result

TOOLS = {Tool.PIN_CASE: pin_case, Tool.READ_CUES: read_cues, Tool.SAVE_REPAIR: save_repair}


def verify_input(tool, value):
    return TOOLS[Tool(tool)].verify_input(value)


def verify_output(tool, input_value, output_value, workspace):
    return TOOLS[Tool(tool)].verify_output(input_value, output_value, workspace)


def verify_task(task_name, arguments, output, reference, workspace):
    if Task(task_name) != Task.REPAIR_TIMELINE:
        return result(False, "unknown task")
    return task.verify_task(arguments, output, reference, workspace)
