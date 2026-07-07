---
name: hpc-test-scientific-correctness-verification
description: Evaluate whether a RegCM5 change preserves scientific behavior — affected fields, tolerance tier, NetCDF metadata, restart reproducibility, decomposition consistency, and physical-scheme consistency. Use when the user wants a scientific-correctness review of a diff touching physics/numerics.
---

# hpc-test-scientific-correctness-verification

Act as `hpc-test-agent-test-architect` (Matteo): evaluate whether a RegCM5 change preserves scientific behavior, producing a report that blocks `hpc-test-trace-and-gate` from PASS on any unresolved concern rather than letting a plausible-looking diff through unaudited.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-scientific-correctness-verification` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Review Stages

Work through each stage in order; each feeds the next:

1. **Identify changed outputs and affected fields.**
2. **Classify fields by sensitivity** — which are precision-critical versus tolerant, per the field-specific tiers this project has established (e.g. `tas`/`ps` tight, `huss` looser).
3. **Choose bitwise or tolerance-based comparison** — bit-exact by default for CPU-only changes; the established statistical MAD/RMSE/rMAD/rRMSE bounds for GPU-ported code. Never a third, invented tier.
4. **Inspect NetCDF variables and metadata** — units, dimensions, and attributes preserved; a variable with no unit comment or a metadata drift is a latent bug, not a formality.
5. **Inspect restart reproducibility** — does a restarted run reproduce a continuous run within the applicable tier?
6. **Inspect domain decomposition consistency** — reuse `hpc-test-mpi-correctness-verification`'s `nproc=1`-vs-`4` comparison rather than re-deriving it.
7. **Summarize unexplained differences** — any residual discrepancy not accounted for by the applicable tier is flagged for escalation, never silently waved through.
8. **Check consistency with RegCM5's numerical scheme and governing physical process** — consult `hpc-dev-agent-code-comprehension` (Gaspare) for the routine's physical/numerical intent and `Doc/ReferenceManual` where current. This stage terminates in the project's existing rule that scientific review means explicit sign-off from regcm5-dev, not an automated verdict — render a recommendation, not a final answer.

## Report

A FAIL at stage 3, 4, or 7, or an unresolved stage-8 concern, blocks `hpc-test-trace-and-gate` from PASS regardless of CI/Slurm status. State findings per stage.
