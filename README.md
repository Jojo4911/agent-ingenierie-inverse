# Reverse engineering agent: from 2D drawing to 3D CAD model

Proof of concept built for Project 15 of the OpenClassrooms AI Engineer program. The agent reads a 2D technical drawing, rebuilds the part as a CadQuery script, runs it in an isolated container and returns a STEP solid. An evaluation script measures that solid against a reference model.

## Scope

- **Geometry**: extruded contours, through and blind holes, rectangular pockets. No fillets, threads, revolved features or assemblies.
- **Input**: clean, standardized drawings, rasterized to PNG.
- **Corpus**: five parts, all drawn by the author. Three were used during development, two were held out and run once.

## Architecture

```text
drawing (PNG)
  -> extraction: vision model -> primitives (JSON)
  -> generation: model -> CadQuery script
  -> execution: MCP server -> Docker sandbox (cq-sandbox) -> STEP file
       on failure with an error message: correction, then one more attempt
  -> evaluation: produced and reference solids measured, then compared
```

`agent.py` runs the pipeline with a bounded retry loop: at most two executions, so at most one correction. The loop stops as soon as a STEP file is produced, when a failure carries no error message, or when attempts are exhausted. Infrastructure failures (`ToolError`) propagate without retry.

## Design constraints

Four rules come from the feasibility spike (`docs/verdict_spike.md`):

1. The model outputs primitives only. Every derived quantity, such as the bounding box or the volume, is recomputed downstream.
2. Success is read from the produced file, never from a return code.
3. The retry loop stops when it has no error message to pass back: without one, the model would rewrite blindly.
4. Verification checks bounding box, through-hole count and volume together. None of them is sufficient alone.

## Installation

Requirements: Python 3.11, [uv](https://docs.astral.sh/uv/), Docker Desktop running. Developed on Windows with Git Bash.

```bash
uv sync
docker build -t cq-sandbox sandbox/
cp .env.example .env
```

Then fill in `.env`: `ANTHROPIC_API_KEY`, `ANTHROPIC_WORKSPACE_ID` and `MODEL_ID`. All measured runs used `claude-opus-5`.

## Usage

From the repository root:

```bash
# Rebuild one part: prints a run report, writes primitives, scripts and STEP files to artifacts/ (git-ignored)
uv run python agent.py corpus/dev/piece_A_plan_2290x1619.png

# Evaluate one part against its reference STEP: writes a JSON trace to evaluations/
uv run python evaluer.py corpus/dev/piece_A_plan_2290x1619.png corpus/dev/piece_A.step
```

## Results

Measured on 10 September 2026, one run per part. Full report, in French: [`docs/rapport_evaluation.md`](docs/rapport_evaluation.md).

| Criterion | Result |
|---|---|
| C2 execution: the script runs and produces a STEP file | 5 of 5 runs, first attempt |
| C3 match: produced solid within tolerance of the reference STEP | 4 of 5 parts: 2 of 3 in development, 2 of 2 held out |
| C1 extraction: primitives checked against ground truth | 2 of 5 parts checked: B wrong in geometry, C correct |

C3 tolerance: 0.5 mm or 1% of the reference value. Part B fails on volume only (-9.87%): every dimension is read correctly, but two are assigned to the wrong feature.

Main limitations:

- A conforming part has the right envelope and amount of material, not necessarily the right hole positions.
- In real use, without a reference model, only the height and the through-hole count can be checked.
- One run per part measures a single draw, not a rate.

Code of the measured runs: commit `2143428`. Later commits change documentation and git tracking only.

## Repository structure

```text
corpus/dev/       parts A, B, C: drawing (PDF, PNG raster), reference STEP, ground truth;
                  A and B also have hand-corrected primitives
corpus/holdout/   parts D, E, held out: same files, run once
prompts/          extraction, generation and correction prompts
sandbox/          Dockerfile and runner of the cq-sandbox image; work/ is the runtime mount, git-ignored
docs/             spike verdict and evaluation report, in French
evaluations/      one JSON trace per measured run
tests/            smoke tests: MCP server calls, and the three exits of the retry loop
agent.py          pipeline: extraction, generation, sandboxed execution, retry loop
mcp_server.py     MCP server (stdio) exposing CadQuery execution in the container
verification.py   measurement and comparison: bounding box, through holes, volume
evaluer.py        end-to-end evaluation of one part against its reference STEP
raster.py         PDF drawing to PNG raster
verify.py         geometric check script from the feasibility spike, kept for traceability
main.py           uv template stub, unused
```
