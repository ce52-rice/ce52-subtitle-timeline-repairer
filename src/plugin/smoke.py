"""Run a scripted local check. This is not an LLM attempt or a hosted verdict."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from slimconfig import build_output, plain_output

import verifier
from contract import RepairInput, SaveInput

from .pin_case import pin_case
from .read_cues import read_cues
from .save_repair import save_repair


def main():
    with TemporaryDirectory(prefix="subtitle-smoke-") as folder:
        workspace = Path(folder)
        given = build_output(
            {"case_id": "tutorial", "offset_ms": -1500, "duration_ms": 10000, "gap_ms": 0}, RepairInput
        )
        reference = pin_case(given, workspace)
        read = read_cues(given, workspace)
        selected = build_output(
            {
                "run": read.run,
                "task": plain_output(given),
                "subtitles": [
                    {"id": "s2", "start_ms": 0, "end_ms": 1500, "text": "Welcome back."},
                    {"id": "s3", "start_ms": 7500, "end_ms": 10000, "text": "See you tomorrow."},
                ],
                "dropped_ids": ["s1"],
            },
            SaveInput,
        )
        output = save_repair(selected, workspace)
        verdict = verifier.verify_task("repair-timeline", given, output, reference, folder)
        print(
            json.dumps(
                {
                    "kind": "scripted local smoke; no model",
                    "input": plain_output(given),
                    "artifact": plain_output(output),
                    "verdict": verdict,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        if not verdict["valid"]:
            raise SystemExit(1)
        print("PASS: local tools saved a correct artifact and the verifier accepted it. No model calls.")


if __name__ == "__main__":
    main()
