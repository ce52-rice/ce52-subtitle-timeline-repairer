"""Typed plugin declarations; no executable task logic."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    PIN_CASE = "pin_case"
    READ_CUES = "read_cues"
    SAVE_REPAIR = "save_repair"


class Task(Enum):
    REPAIR_TIMELINE = "repair-timeline"


class Case(Enum):
    TUTORIAL = "tutorial"
    OVERLAP = "overlap"
    EDGES = "edges"
    EMPTY = "empty"


@dataclass
class RepairInput(Output):
    case_id: Annotated[Case, "Fixture: tutorial, overlap, edges or empty"]
    offset_ms: Annotated[int, "Integer shift, from -60000 to 60000 milliseconds"]
    duration_ms: Annotated[int, "Video duration, from 1 to 120000 milliseconds"]
    gap_ms: Annotated[int, "Minimum gap between retained cues, from 0 to 5000 milliseconds"]


@dataclass
class CueOutput(Output):
    id: Annotated[str, "Original unique cue ID"]
    start_ms: Annotated[int, "Start in integer milliseconds"]
    end_ms: Annotated[int, "End in integer milliseconds"]
    text: Annotated[str, "Exact original subtitle text"]


@dataclass
class PinOutput(Output):
    task: Annotated[RepairInput, "Exact task input"]
    cues: Annotated[list[CueOutput], "Original fixture cues in processing order"]
    prior_runs: Annotated[list[str], "Run IDs present before this task"]


@dataclass
class CandidateOutput(Output):
    id: Annotated[str, "Copy this ID unchanged"]
    start_ms: Annotated[int, "Proposed start after shift, clipping and overlap/gap adjustment"]
    end_ms: Annotated[int, "Proposed end after shift and clipping"]
    text: Annotated[str, "Copy the exact original text"]


@dataclass
class ReadOutput(Output):
    run: Annotated[str, "This run's token; copy unchanged"]
    task: Annotated[RepairInput, "Exact task input"]
    originals: Annotated[list[CueOutput], "Original fixture records"]
    candidates: Annotated[list[CandidateOutput], "In order: retain only if start_ms < end_ms; otherwise drop"]


@dataclass
class SaveInput(Output):
    run: Annotated[str, "Run token returned by read_cues"]
    task: Annotated[RepairInput, "Exact task input"]
    subtitles: Annotated[list[CueOutput], "Every retained candidate, copied exactly, in order"]
    dropped_ids: Annotated[list[str], "Every dropped candidate ID, in original order"]


@dataclass
class RepairOutput(Output):
    run: Annotated[str, "Run token returned by read_cues"]
    task: Annotated[RepairInput, "Exact task input"]
    subtitles: Annotated[list[CueOutput], "Retained subtitle records saved to this run's file"]
    dropped_ids: Annotated[list[str], "Dropped cue IDs, in original order"]


TOOLS = {
    Tool.PIN_CASE: (RepairInput, PinOutput),
    Tool.READ_CUES: (RepairInput, ReadOutput),
    Tool.SAVE_REPAIR: (SaveInput, RepairOutput),
}
TASKS = {Task.REPAIR_TIMELINE: (RepairInput, RepairOutput)}
