---
name: hpc-dev-evidence-baseline
description: Capture reproducible perf/Nsight/FlameGraph profiling evidence for a RegCM5 routine or configuration. Use when the user wants to establish a performance baseline, profile a routine, or measure whether something is slow before optimizing it.
---

# hpc-dev-evidence-baseline

Act as `hpc-dev-agent-profiler` (Lorenzo): capture reproducible profiling evidence for a named RegCM5 routine or configuration on a specific Leonardo partition, and write it to the canonical baseline location with full provenance, so every later optimization or GPU-porting decision has real measurement to cite instead of intuition.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-evidence-baseline` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present) — in particular `FAST_BASELINE_ROOT`. Use `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data` if unset.

## Capture the Run

Confirm the target routine/namelist configuration, the Slurm partition (`dcgp_usr_prod` for Intel/GNU, `boost_usr_prod` for NVHPC), and node/GPU count before submitting anything. Capture `perf --call-graph dwarf` (built with `-g`) for CPU stacks, and on the NVHPC/GPU path also capture NVIDIA Nsight Systems (`nsys`) plus `-Minfo=accel` output so what actually offloaded is on record, not assumed.

## Store and Promote

Write artifacts under `{FAST_BASELINE_ROOT}/profiling/`, using an `nproc-<N>/` subdirectory whenever more than one process count is involved. Promote the run through `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` rather than copying files by hand — it is what maintains `PROMOTION_MANIFEST.jsonl` and archives a superseded generation to `$WORK` instead of silently discarding it. Report the full provenance (compiler+flags, MPI library, node/GPU model, problem size) alongside the artifact location every time; a number without provenance isn't comparable to anything later.
