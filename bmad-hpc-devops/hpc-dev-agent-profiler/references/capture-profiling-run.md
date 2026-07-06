---
name: capture-profiling-run
description: Capture a reproducible profiling run for a target routine/configuration
code: CP
added: 2026-07-05
type: prompt
---

# Capture a Profiling Run

The outcome is a reproducible measurement — captured artifacts plus their full provenance — written to the canonical baseline path with a manifest entry, not a one-off number nobody can reproduce. The consumer is anyone downstream deciding whether to act on this evidence (gpu-porting, build-portability, or a human reviewer), so an unreproducible or unattributed number is worse than saying "not yet measured."

Confirm the target routine/namelist configuration, Slurm partition, and node/GPU count before submitting. Capture `perf --call-graph dwarf` (with `-g` debug symbols) and, on the NVHPC/GPU path, Nsight Systems (`nsys`) plus `-Minfo=accel` to see what actually offloaded. Write artifacts under `{FAST_BASELINE_ROOT}/profiling/`, using an `nproc-<N>/` subdirectory when multiple process counts are involved, and promote the run through `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` rather than copying files by hand — that script is what maintains `PROMOTION_MANIFEST.jsonl` and the archive-on-supersession behavior. State the full provenance (compiler+flags, MPI library, node/GPU model, problem size) alongside the artifact location every time.
