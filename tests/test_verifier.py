import json
from copy import deepcopy

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import PinOutput, RepairInput, RepairOutput
from tests.helpers import EXPECTED, TASK, save, start


def verdict(workspace, value, output, pin):
    return verifier.verify_task("repair-timeline", value, output, pin, str(workspace))


def test_known_correct_and_tool_verdicts(tmp_path):
    value, pin, read = start(tmp_path)
    given, output = save(tmp_path, value, read, EXPECTED, ["s1"])
    assert plain_output(output)["subtitles"] == EXPECTED
    for name, args, result in [("pin_case", value, pin), ("read_cues", value, read), ("save_repair", given, output)]:
        assert verifier.verify_input(name, args)["valid"]
        assert verifier.verify_output(name, args, result, str(tmp_path))["valid"]
    first = verdict(tmp_path, value, output, pin)
    assert first["valid"] and first["score"] == 1
    assert first == verdict(tmp_path, value, output, pin)


@pytest.mark.parametrize(
    "mutation", ["time", "text", "missing", "extra", "order", "drop", "drop-order", "duplicate", "bool"]
)
def test_reject_wrong_artifact_even_when_saved_matches(tmp_path, mutation):
    value, pin, read = start(tmp_path)
    _, output = save(tmp_path, value, read)
    data = plain_output(output)
    if mutation == "time":
        data["subtitles"][0]["end_ms"] += 1
    elif mutation == "text":
        data["subtitles"][0]["text"] = "Changed"
    elif mutation == "missing":
        data["subtitles"].pop()
    elif mutation == "extra":
        data["subtitles"].append({"id": "x", "start_ms": 1, "end_ms": 2, "text": "x"})
    elif mutation == "order":
        data["subtitles"].reverse()
    elif mutation == "drop":
        data["dropped_ids"] = []
    elif mutation == "drop-order":
        data["dropped_ids"] = ["unknown", "s1"]
    elif mutation == "duplicate":
        data["subtitles"].append(deepcopy(data["subtitles"][0]))
    elif mutation == "bool":
        data["subtitles"][0]["start_ms"] = True
    (tmp_path / "reports" / (read.run + ".json")).write_text(json.dumps(data))
    # Malformed shapes may be rejected by contract construction before verification.
    if mutation == "bool":
        assert not verdict(tmp_path, value, data, pin)["valid"]
    else:
        wrong = build_output(data, RepairOutput)
        assert not verdict(tmp_path, value, wrong, pin)["valid"]


@pytest.mark.parametrize("problem", ["missing", "malformed", "different", "wrong-shape"])
def test_saved_file_problems(tmp_path, problem):
    value, pin, read = start(tmp_path)
    _, output = save(tmp_path, value, read)
    path = tmp_path / "reports" / (read.run + ".json")
    if problem == "missing":
        path.unlink()
    elif problem == "malformed":
        path.write_text("{broken")
    elif problem == "wrong-shape":
        path.write_text("[]")
    else:
        data = plain_output(output)
        data["dropped_ids"] = []
        path.write_text(json.dumps(data))
    assert not verdict(tmp_path, value, output, pin)["valid"]


@pytest.mark.parametrize("problem", ["missing", "changed", "malformed", "wrong-shape"])
def test_read_receipt_problems(tmp_path, problem):
    value, pin, read = start(tmp_path)
    _, output = save(tmp_path, value, read)
    path = tmp_path / "reports" / (read.run + ".read.json")
    if problem == "missing":
        path.unlink()
    elif problem == "malformed":
        path.write_text("{")
    elif problem == "wrong-shape":
        path.write_text("[]")
    else:
        data = json.loads(path.read_text())
        data["originals"][0]["text"] = "tampered"
        path.write_text(json.dumps(data))
    assert not verdict(tmp_path, value, output, pin)["valid"]


def test_reference_and_prior_run(tmp_path):
    value, pin, read = start(tmp_path)
    _, output = save(tmp_path, value, read)
    assert not verdict(tmp_path, value, output, None)["valid"]
    later = build_output({**plain_output(pin), "prior_runs": [read.run]}, PinOutput)
    assert not verdict(tmp_path, value, output, later)["valid"]
    changed = build_output({**TASK, "offset_ms": 0}, RepairInput)
    assert not verdict(tmp_path, changed, output, pin)["valid"]


@pytest.mark.parametrize(
    "case,offset,duration,gap,ids,dropped",
    [
        ("empty", 0, 1, 0, [], []),
        ("tutorial", -60000, 10000, 0, [], ["s1", "s2", "s3"]),
        ("tutorial", 60000, 10000, 0, [], ["s1", "s2", "s3"]),
        ("overlap", 0, 10000, 100, ["a", "c", "e", "f"], ["b", "d"]),
        ("tutorial", -1200, 10000, 0, ["s2", "s3"], ["s1"]),
        ("edges", 0, 1000, 0, ["cross", "unicode"], ["first", "touch", "out", "late"]),
    ],
)
def test_boundaries(tmp_path, case, offset, duration, gap, ids, dropped):
    value, pin, read = start(tmp_path, {"case_id": case, "offset_ms": offset, "duration_ms": duration, "gap_ms": gap})
    _, output = save(tmp_path, value, read)
    assert [cue.id for cue in output.subtitles] == ids
    assert output.dropped_ids == dropped
    assert verdict(tmp_path, value, output, pin)["valid"]
    if case == "overlap":
        assert [(c.start_ms, c.end_ms) for c in output.subtitles] == [
            (0, 900),
            (1000, 1800),
            (2100, 3100),
            (3200, 4500),
        ]


@pytest.mark.parametrize("field,value", [("gap_ms", -1), ("duration_ms", 0), ("offset_ms", 60001), ("gap_ms", True)])
def test_invalid_input(tmp_path, field, value):
    data = {**TASK, field: value}
    assert not verifier.verify_input("read_cues", data)["valid"]


def test_malformed_submission_and_traversal(tmp_path):
    value, pin, read = start(tmp_path)
    _, output = save(tmp_path, value, read)
    for wrong in [None, {}, [], {**plain_output(output), "run": "../outside"}]:
        assert not verdict(tmp_path, value, wrong, pin)["valid"]


def test_save_does_not_fix_wrong_decisions(tmp_path):
    value, pin, read = start(tmp_path)
    given, output = save(tmp_path, value, read, [], [])
    assert output.subtitles == []
    assert verifier.verify_output("save_repair", given, output, str(tmp_path))["valid"]
    assert not verdict(tmp_path, value, output, pin)["valid"]


def test_multiple_runs_are_isolated(tmp_path):
    value, pin, read = start(tmp_path)
    _, first = save(tmp_path, value, read)
    value2, pin2, read2 = start(tmp_path)
    _, second = save(tmp_path, value2, read2)
    assert read.run != read2.run
    assert verdict(tmp_path, value, first, pin)["valid"]
    assert verdict(tmp_path, value2, second, pin2)["valid"]
    assert not verdict(tmp_path, value2, first, pin2)["valid"]


def test_schema_declares_every_field():
    from slimconfig import output_schema

    from contract import TASKS, TOOLS

    for given, made in list(TOOLS.values()) + list(TASKS.values()):
        assert output_schema(given)["type"] == "object"
        assert output_schema(made)["type"] == "object"


@pytest.mark.parametrize("pin", [None, [], {}, {"task": TASK, "cues": []}])
def test_pin_verifier_rejects_malformed_reference(tmp_path, pin):
    assert not verifier.verify_output("pin_case", TASK, pin, str(tmp_path))["valid"]


@pytest.mark.parametrize(
    "cues",
    [
        None,
        [None],
        [{}],
        ["bad"],
        [{"id": "a", "text": "a", "start_ms": "0", "end_ms": 1}],
        [{"id": "a", "text": "a", "start_ms": 1, "end_ms": 1}],
    ],
)
def test_pin_verifier_rejects_malformed_cues_without_crashing(tmp_path, cues):
    pin = {"task": TASK, "cues": cues, "prior_runs": []}
    assert not verifier.verify_output("pin_case", TASK, pin, str(tmp_path))["valid"]


@pytest.mark.parametrize("prior", [None, [None], ["bad"], ["a" * 32, "a" * 32]])
def test_pin_verifier_rejects_malformed_prior_runs(tmp_path, prior):
    pin = {"task": TASK, "cues": [], "prior_runs": prior}
    assert not verifier.verify_output("pin_case", TASK, pin, str(tmp_path))["valid"]
