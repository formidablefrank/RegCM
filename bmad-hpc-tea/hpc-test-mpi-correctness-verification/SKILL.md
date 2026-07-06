---
name: hpc-test-mpi-correctness-verification
description: Review a RegCM5 change for MPI correctness — ranks, communicators, collectives, send/receive ordering, reductions, and decomposition tests. Use when the user wants an MPI correctness review of a diff touching parallel/decomposed code.
---

# hpc-test-mpi-correctness-verification

Act as `hpc-test-agent-test-architect` (Matteo): review a proposed RegCM5 change for MPI correctness, producing a report a reviewer can act on without re-deriving the analysis, and a test-plan slice `hpc-test-test-design`/`hpc-test-regression-automate` can consume directly.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-mpi-correctness-verification` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Review Stages

Work through each stage on the change under review; these genuinely build on each other, so keep them in order:

1. **Identify ranks, communicators, decomposed arrays, and halo regions** touched by the change — `mod_dynparam`'s `nproc`/`myid`/`njxcpus`/`niycpus`/`iyp`/`jxp`, and `mod_mppparam`'s halo-exchange routine family.
2. **Inspect collective calls and rank participation** — every rank must reach a given collective symmetrically; a rank-conditional skip of a collective is a deadlock risk, not a style issue.
3. **Inspect send/receive ordering and synchronization** — `mpi_isend`/`mpi_irecv` pairing and wait completion, watching for mismatched blocking sends.
4. **Inspect reductions and numerical order sensitivity** — whether a sum/max reduction's order changes with rank count in a way that affects the applicable tolerance tier.
5. **Define rank-layout tests** — the specific `nproc` counts this change must be exercised at (minimum `nproc=1` and `nproc=4`, since that's the smallest count where RegCM5's auto-decomposition performs a genuine 2D split).
6. **Define decomposition-comparison tests** — concrete `regression_diff.py` invocations comparing output across the process counts from stage 5, using the same tolerance tier as any other comparison (a bit-exact-tier divergence across process counts indicates a real decomposition bug, not an accepted artifact).

## Report

State findings per stage, not as a single pass/fail. Hand the rank-layout and decomposition-comparison tests (stages 5-6) to `hpc-test-test-design`/`hpc-test-regression-automate` as a ready-to-use test-plan slice.
