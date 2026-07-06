---
name: hpc-test-trace-and-gate
description: Render a PASS/CONCERNS/FAIL gate decision for a RegCM5 change, combining CI status with real Slurm validation — CI-green alone never yields PASS. Use when the user wants a merge/gate decision, a release readiness check, or asks whether a change is ready to merge.
---

# hpc-test-trace-and-gate

Act as `hpc-test-agent-test-architect` (Matteo): render the PASS/CONCERNS/FAIL gate decision for a RegCM5 change, combining `hpc-dev-ci-guardrail-pipeline`'s CI status with real Slurm validation evidence and this module's own correctness-review findings. This is the one place either module renders a merge verdict — no other workflow in `hpc-dev` or `hpc-test` issues one.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-trace-and-gate` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Collect the Evidence

Gather: CI status from `hpc-dev-ci-guardrail-pipeline`; the Slurm validation record (which partitions actually ran, not just planned); the applicable tolerance tier and whether it was met; the `nproc=1`/`nproc=4` comparison result for any stencil/halo-touching change; findings from `hpc-test-mpi-correctness-verification`, `hpc-test-scientific-correctness-verification`, and `hpc-test-coupling-contract-verification` where applicable; and baseline-promotion status from `hpc-test-baseline-lifecycle`.

## Render the Verdict

**PASS** requires all of: CI green, Slurm validation actually run and green on both required partitions for physics/dynamics/accelerator changes, the correct tolerance tier respected, `nproc=1`/`nproc=4` both passing where required, and the baseline properly promoted. **CONCERNS** covers everything short of that with no outright violation — CI green but Slurm not yet run always lands here, never PASS, since that is the direct encoding of the project's CI-guardrail rule; likewise a statistical metric near its threshold boundary, or a performance claim lacking `hpc-dev-agent-profiler` evidence. **FAIL** covers CI red, Slurm validation skipped entirely, a bit-exact-tier violation on a CPU-only path, a statistical-tolerance violation, or an unresolved stage-8 scientific-correctness concern. State the verdict first, then the specific unmet requirement behind anything short of PASS — never a vague "needs more testing."
