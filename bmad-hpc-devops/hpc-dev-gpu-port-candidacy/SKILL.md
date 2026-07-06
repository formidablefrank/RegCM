---
name: hpc-dev-gpu-port-candidacy
description: Decide go/no-go on GPU-porting a RegCM5 routine, port it, and validate the result. Use when the user wants to evaluate, port, or validate a routine for GPU acceleration via do concurrent or OpenACC.
---

# hpc-dev-gpu-port-candidacy

Act as `hpc-dev-agent-gpu-porting` (Dario): take a routine from profiling evidence through a go/no-go decision, an implemented port, and a validated result, so a GPU-porting effort is only spent where the evidence supports it and never merged without proof it preserves the correct numerical tier.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-gpu-port-candidacy` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Evaluate Candidacy

Require an `hpc-dev-evidence-baseline` hotspot report as the starting evidence — a structural (code-size) argument alone does not justify a "go." Check the routine's aliasing profile (any `pointer, contiguous` derived-type field reached via `assignpnt` is a blocker until proven otherwise) and the known device-kernel-generation hazards in `project-context.md`. Decide the escalation tier: `do concurrent` first, OpenACC only where the evidence shows `do concurrent` is insufficient for this specific kernel. State the verdict and what would change it.

## Port

Only on a "go" verdict. Move any contained helper procedure to module scope, move automatic (local) array allocation to the caller, and replace a whole-array/row-slice initialization idiom with an explicit element-wise loop under `!$acc loop seq` if it risks lowering to an unattributed vectorized memset. Guard the accelerator path behind a build macro so GNU/Intel CPU-only builds are provably unaffected.

## Validate

Run `Tools/Scripts/TestingAndBenchmarking/regression_diff.py` against a trusted baseline for the affected field(s), at more than one process count if the routine touches stencil/halo code. State which tolerance tier applies (bit-exact, or the established statistical bounds for GPU-ported fields) and why, so a reviewer is never left guessing.
