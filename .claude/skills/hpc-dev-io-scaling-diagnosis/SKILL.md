---
name: hpc-dev-io-scaling-diagnosis
description: Diagnose an I/O bottleneck in a RegCM5 output path and implement an opt-in parallel-I/O namelist switch. Use when the user asks why I/O is slow, wants to enable parallel diagnostic/restart output, or is investigating a specific output-path bottleneck.
---

# hpc-dev-io-scaling-diagnosis

Diagnose which RegCM5 I/O path (diagnostic/history, restart/checkpoint, or CLM land-model history) is the actual bottleneck at a given rank count, using gather/write/wait timing evidence rather than assumption, then — only once the diagnosis is concrete — implement a per-path opt-in namelist switch. The consumer is `hpc-test`'s `hpc-nfr-assess`/`hpc-trace-and-gate`, which decides whether the new switch should become a recommended default; this workflow's job is the evidence and the switch, not that recommendation.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-io-scaling-diagnosis` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present) — in particular `FAST_BASELINE_ROOT`.

## Diagnose

Act as `hpc-dev-agent-profiler` (Lorenzo) for this stage. Require an `hpc-dev-evidence-baseline` run (or a fresh one) that separates `io_gather_<path>`/`io_write_<path>`/`io_wait_<path>` timing from compute time, at the rank counts in question. State where the additional time actually goes relative to serial write — collective-I/O synchronization, striping/chunking mismatch, or metadata contention — rather than leaving it as an unexplained regression.

## Implement the Switch

Act as `hpc-dev-agent-build-portability` (Franco) for this stage, and only proceed here once the diagnosis above is concrete. Follow the existing `do_parallel_netcdf_in`/`do_parallel_netcdf_out` naming convention for the new per-path switch rather than inventing a different shape. Preserve existing output file format and variable naming for downstream consumers unless the run explicitly opts in, and confirm an `mpi-serial` build still compiles and runs unaffected.
