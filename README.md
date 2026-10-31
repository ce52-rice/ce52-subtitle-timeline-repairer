# Subtitle Timeline Repairer

An original COMP 480/580 plugin by Charlie Esparza. It repairs tiny synthetic subtitle timelines and verifies both the submitted records and the saved JSON artifact. No video, external data service, model API client or secret belongs in this repository. The fixture text is invented.

## Tools

- `pin_case`: reference-only tool; pins the original cue list, task and pre-existing run IDs before the agent starts. Not exposed to the task agent.
- `read_cues`: reads originals, computes timing candidates and saves a per-run receipt. The model chooses which candidates survive and copies existing typed values.
- `save_repair`: saves the agent's proposed selection unchanged to `reports/<run>.json` under the framework-provided workspace. It does not correct mistakes.
- Task `repair-timeline`: agent runner using `read_cues`, `save_repair`, then framework `submit`. Reference: `pin_case`.

### Exact task rules

Choose `case_id` from `tutorial`, `overlap`, `edges`, `empty`; `offset_ms` is an integer from -60000 to 60000, `duration_ms` from 1 to 120000, and `gap_ms` from 0 to 5000. All times are integer milliseconds. Preserve original record order; do not sort by time.

For each original cue: add the offset to both endpoints; clip both to [0, duration_ms]; if a cue has previously been retained, raise this cue's start to at least that retained cue's end plus gap_ms. Do not extend its end or re-clip the adjusted start. Retain it exactly when start < end, otherwise drop it. A dropped cue does not update the previous retained end. Preserve the IDs and text exactly. The first retained cue does not require a leading gap. Output lists must preserve original order. A candidate's adjusted start may exceed video duration when it must be dropped.

`read_cues` computes numeric candidates. The agent classifies each candidate, copies the retained rows and lists dropped IDs. A deterministic verifier independently derives the required result from pinned original inputs, checks receipt integrity, requires a saved artifact equal to the submission, and rejects prior runs. Different task settings produce different outcomes; no expected answer is embedded in task tools.

Example input (paste these settings when asking RUSH Lab to run the task):

```json
{"case_id":"tutorial","offset_ms":-1500,"duration_ms":10000,"gap_ms":0}
```

Expected retained cues: s2 at 0..1500 and s3 at 7500..10000, with original text. Drop s1.

Second input, exercising overlaps:

```json
{"case_id":"overlap","offset_ms":0,"duration_ms":10000,"gap_ms":100}
```

Keep a at 0..900, c at 1000..1800, e at 2100..3100, f at 3200..4500. Drop b and d.

## Layout

- `contract.py`, `nanoagent.yaml`: typed contracts and current `nanoagent.plugin/v0001` manifest.
- `src/plugin/`: MCP server, one module per tool, small synthetic fixture files and scripted smoke runner.
- `verifier/`: deterministic standard-library checks with no network, model, clock, randomness or writes.
- `tests/`: typed contract roundtrips, incorrect/missing/malformed/boundary tests and real MCP stdio test.
- `ui/`, `product/`: schema-based renderer and product metadata.
- `pyproject.toml`, `uv.lock`, `.env`, `.gitignore`, `LICENSE`: reproducible packaging. `.env` contains no required secrets.

## Develop and run

Python 3.12+, Git and uv. Open a terminal at the directory containing this README, contract.py and nanoagent.yaml. WSL/Ubuntu is appropriate for local development on Windows.

```bash
uv sync --frozen --extra dev
uv run --frozen python -m plugin.smoke
uv run --frozen pytest -q
uv run --frozen ruff check .
uv lock --check
```

The smoke runner uses a temporary workspace and a handwritten correct answer; it prints the result and local verifier verdict. The full tests start an actual MCP server over stdio. No test calls an LLM or OpenRouter. Dependency installation can use the internet; installed tests use local data. A scripted smoke result is not an actual model attempt or proof of hosted RUSH Lab validation.

If dependency metadata changes, run `uv lock` and sync again. Runtime is exactly `uv run --frozen python -m plugin`; NanoAgent supplies NANOAGENT_WORKSPACE. The server waits for MCP messages, so starting it directly is not a useful smoke test.

### Publish and validate

Create a separate public GitHub repository for this plugin and push the files, including the hidden .env and .gitignore (neither contains secrets). Exclude .venv, caches, report outputs and credentials. Open RUSH Lab Marketplace, Submit Your Artifact, and submit the repository URL after reviewing the terms. If packaging checks fail, retain the exact error. Publication is not runtime validation. Depending on workspace policy, staff may need to add the plugin before it is available to run.

Ask the plugin to run `repair-timeline` with the example settings above. Inspect the result card and its verifier verdict. Save the task input, model output and real verdict for the PDF report. Run the overlap and empty cases as additional validation when budget permits. Do not claim an unobserved hosted run succeeded. UI labels may differ between desktop releases.

Keep execution logs and report evidence outside the plugin repository. For example, first create an evidence directory alongside the plugin, then redirect smoke output there. Do not include the course API key in this package.

### Limitations

This is a bounded subtitle-selection task over four synthetic fixtures, not an audio alignment system. JSON is the saved artifact; SRT formatting, video playback and translation are out of scope. Numeric processing belongs to tools, while the model selects and copies candidates; it is not a benchmark of unaided timestamp arithmetic. The independent verifier shares no production timing code, but both implementations can still share conceptual specification errors. Source fixtures are trusted package data and pinned before the agent runs. Prior-run checks prevent ordinary stale-result reuse; this is not cryptographic proof against an adversary with arbitrary access to all host files. Actual desktop integration and hosted model behavior must be validated separately.
