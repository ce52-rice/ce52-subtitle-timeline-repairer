from slimconfig import build_output, plain_output

from contract import PinOutput, ReadOutput, RepairInput, RepairOutput, SaveInput
from plugin.pin_case import pin_case
from plugin.read_cues import read_cues
from plugin.save_repair import save_repair

TASK = {"case_id": "tutorial", "offset_ms": -1500, "duration_ms": 10000, "gap_ms": 0}
EXPECTED = [
    {"id": "s2", "start_ms": 0, "end_ms": 1500, "text": "Welcome back."},
    {"id": "s3", "start_ms": 7500, "end_ms": 10000, "text": "See you tomorrow."},
]


def roundtrip(value, cls):
    return build_output(plain_output(value), cls)


def start(workspace, task=None):
    value = build_output(task or TASK, RepairInput)
    pin = roundtrip(pin_case(value, workspace), PinOutput)
    read = roundtrip(read_cues(value, workspace), ReadOutput)
    return value, pin, read


def save(workspace, value, read, subtitles=None, dropped=None):
    if subtitles is None:
        subtitles = [plain_output(cue) for cue in read.candidates if cue.start_ms < cue.end_ms]
    if dropped is None:
        dropped = [cue.id for cue in read.candidates if cue.start_ms >= cue.end_ms]
    given = build_output(
        {"run": read.run, "task": plain_output(value), "subtitles": subtitles, "dropped_ids": dropped}, SaveInput
    )
    output = roundtrip(save_repair(given, workspace), RepairOutput)
    return given, output
