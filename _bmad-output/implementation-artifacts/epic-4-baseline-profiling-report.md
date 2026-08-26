---
title: 'Epic 4 Baseline Profiling Report'
story: '4-4-baseline-profiling-run-and-published-report'
created: '2026-08-26'
status: 'complete'
---

# Epic 4 Baseline Profiling Report

## Purpose

This report replaces structural inference with measured evidence. Prior to this story, Epic 10 and 11 hotspot claims rested on the source thesis's CLM4.5-coupled profiling run (an external, ICTP/SISSA dataset) and one partial internal measurement — Story 4.1's Intel/`dcgp_usr_prod` RRTMG pass (job 48812653, `≈6.0%`, pre-dating this epic's DEBUG timers). This story runs the AD-8 canonical EUR12 fixture on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC), reading Stories 4.1–4.3's DEBUG timers directly. **Later stories citing hotspot data should cite this report and the source thesis — not the technical research note's structural inference.**

## Method

Per AD-2's fixed profiling method: `perf record --call-graph dwarf` (`-g` build) + Brendan Gregg FlameGraph rendering, NVIDIA Nsight Systems for GPU/compiler-runtime symbol attribution, `-Minfo=accel` to confirm offload behavior. Both partitions ran the same fixture family — the AD-8 canonical EUR12 CORDEX domain (`RegCM-data/EURR12/EUR12_namelist.in`, 275×275×36, `iproj='ROTLLR'`, `idynamic=3`/MOLOCH), copied and modified only to force `irrtm=1` (an unmodified fixture silently skips RRTMG) and set the run window; chemistry and diagnostic I/O were left at file defaults (off / serial).

**24-simulated-hour minimum window, not a choice.** `Main/mod_params.F90:749` enforces `mod(mdate2-mdate1, 24) == 0` (`'Runtime increments must be modulus 24 hours'`) — confirmed by an actual crash when an earlier fixture draft tried a shorter window. Both fixture copies (`RegCM-data/story4-4/EUR12_story4-4.in`, `EUR12_story4-4_boost.in`) use the minimum valid window, 2009-09-01 00:00 → 2009-09-02 00:00 UTC.

**Two evidence sources, two different questions — do not conflate them.**

1. **`mod_service`'s DEBUG timers** (`Main/mpplib/mod_service.F90`'s `time_print`, unconditionally emitted at end of run) — the **primary evidence for wall-time share**. Each timer's printed value is the average across *all* MPI ranks of that rank's own accumulated total time (`mod_service.F90:280-303`), via `system_clock()` — genuine wall-clock, not CPU time. Low-overhead, purpose-built for exactly this question.
2. **`perf`/Nsight** (rank-0 only, per AD-2's cluster-imposed convention — profiling every rank isn't feasible) — valuable for identifying *specific hot low-level routines* and unattributed compiler-runtime symbols, but **not a reliable source of cross-subsystem percentage share**, for a concrete, measured reason documented below.

**A nesting fact that changes how the DEBUG timers must be read.** `Main/mod_moloch.F90:321-444` wraps the *entire* `moloch()` driver in the `'moloch'` timer, and that driver calls `physical_parametrizations` (line 363), which itself calls radiation/RRTMG, microphysics, PBL, and cumulus. Confirmed independently via `perf`'s own call graph (`mod_moloch_physical_parametrizations_` as a direct child of `mod_moloch_moloch_`). **The `moloch` timer's total already includes `rrtmg_driver`, `microphys`, `holtbl`, and `tiedtkedrv` — they are not separate, additive top-level costs.** Genuinely separate (called from the outer timestep loop, not from within `moloch()`) are: `output` (itself inclusive of `io_gather_hist`/`io_write_hist`/`io_wait_hist`), `bdyin`, `bdyval`, `morelax_external`/`morelax_fraction`, `zenitm`, `solar1`, `solar_irradiance`, `zengocndrv`, `seaice`, `ocn_albedo`.

## dcgp_usr_prod (Intel) — measured wall-time share

Full-link `--enable-debug --enable-clm45` Intel build, 224 ranks (2 nodes × 112). Job 53958861: `RESULT: PASS`, `RegCM V5 simulation successfully reached end`, 48m32s real time.

| Level | Item | Seconds (avg/rank) | Share |
|---|---|---|---|
| Top-level | **MOLOCH driver (dynamics + all physics)** | 1713.63 | **91.2%** |
| Top-level | Output driver (incl. I/O gather/write/wait) | 73.73 | 3.9% |
| Top-level | Boundary data read (`bdyin`) | 90.02 | 4.8% |
| Top-level | Boundary relaxation (`morelax_external`+`morelax_fraction`) | 2.37 | 0.1% |
| Top-level | Solar geometry + ocean (`zenitm`, `zengocndrv`, `seaice`, `ocn_albedo`, `solar1`, `solar_irradiance`) | 0.09 | <0.1% |
| — within MOLOCH — | RRTMG (`rrtmg_driver`, incl. lw/sw) | 189.54 | 11.1% of MOLOCH, 42.5% of physics |
| — within MOLOCH — | *(of which)* `rrtmg_lw` | 59.79 | — |
| — within MOLOCH — | *(of which)* `rrtmg_sw` | 12.13 | — |
| — within MOLOCH — | Microphysics | 179.36 | 10.5% of MOLOCH, 40.2% of physics |
| — within MOLOCH — | Holtslag PBL | 58.58 | 3.4% of MOLOCH, 13.1% of physics |
| — within MOLOCH — | Tiedtke cumulus | 18.72 | 1.1% of MOLOCH, 4.2% of physics |
| — within MOLOCH — | *Pure dynamics (remainder)* | 1267.43 | 74.0% of MOLOCH |
| — within Output — | `io_gather_hist` | 54.05 | — |
| — within Output — | `io_write_hist` / `io_wait_hist` | 0.06 / ~0.00 | — |

Denominator: 1880.01s (MOLOCH + the genuinely separate top-level items). "% of physics" = share of the four physics sub-timers combined (446.20s) — a platform-comparable metric independent of MOLOCH's own total (see the boost table, where MOLOCH's total is not directly readable). `io_wait_hist`'s near-zero value is consistent with Story 4.3's documented finding that `outstream_sync` no-ops when `lsync=.false.` (this fixture's setting).

**Reconciling against real wall-clock time.** The job itself (sacct) ran 2912s; the model's own `cpu_time()`-based "Total elapsed seconds of run" was 1726.85s; the DEBUG timers above sum to 1880.01s. None of the three match, for two different reasons: (1) the ~1032s gap between the job's total and the model's own figure is Slurm/MPI startup, module loading, and shutdown overhead outside the timed run itself; (2) the model's own `cpu_time()` figure is measured on a single rank (the I/O coordinator, `iocpu`) via a different clock than the DEBUG timers' `system_clock()`-based, cross-rank average — if that one rank's own workload happens to sit below the 224-rank average (plausible, since it also spends time on I/O coordination rather than pure compute), its total can legitimately read lower than the DEBUG timers' average. Take the DEBUG-timer sum (1880.01s) as the wall-time-share denominator; the other two figures answer different questions.

Artifacts: `RegCM-data/profiling/s44-dcgp-perf-53958861.data`, `s44-dcgp-flamegraph-53958861.svg`, `s44-dcgp-perf-report-53958861.txt`.

## boost_usr_prod (NVHPC) — measured wall-time share

`bin/regcm-4-3-debug-nvhpc` (Story 4.3's CPU-only binary, refreshed against current `develop` — the original recursive-`make -j` refresh script hit the exact Automake SUBDIRS race documented in this project's build rules; a sequential-per-directory rebuild fixed it). 16 ranks (4 nodes × 4/node). Two independent full 24h runs completed cleanly with consistent results — Nsight pass (job 53958915, 5h11m) and perf pass (job 54143865, ~5h03m model time within a 13h57m job, most of the gap being `perf script`'s DWARF post-processing of a 15GB capture).

| Level | Item | Seconds (avg/rank) | Note |
|---|---|---|---|
| Top-level | **MOLOCH driver (dynamics + all physics)** | ≥5234.09, ≤17,779 (bounds, not a measurement) | overflowed print format on every rank — see below |
| Top-level | Output driver (incl. I/O gather/write/wait) | 303.79 | |
| Top-level | Boundary data read (`bdyin`) | 8.05 | |
| Top-level | Boundary relaxation (`morelax_external`+`morelax_fraction`) | 48.84 | |
| Top-level | Solar geometry + ocean (`zenitm`, `zengocndrv`, `seaice`, `ocn_albedo`, `solar1`, `solar_irradiance`) | 1.12 | |
| — within MOLOCH — | RRTMG (`rrtmg_driver`, incl. lw/sw) | 2010.19 | 38.4% of physics |
| — within MOLOCH — | *(of which)* `rrtmg_lw` | 670.11 | — |
| — within MOLOCH — | *(of which)* `rrtmg_sw` | 954.15 | — |
| — within MOLOCH — | Microphysics | 2220.36 | 42.4% of physics |
| — within MOLOCH — | Holtslag PBL | 781.24 | 14.9% of physics |
| — within MOLOCH — | Tiedtke cumulus | 222.30 | 4.3% of physics |
| — within MOLOCH — | *Physics sub-timers combined* | 5234.09 | firm lower bound on MOLOCH |
| — within Output — | `io_gather_hist` | 42.66 | |
| — within Output — | `io_write_hist` / `io_wait_hist` | 0.40 / ~0.00 | |

**MOLOCH's own total overflowed `time_print`'s fixed `F9.4` field on all 16 ranks** (printed as `*********`, meaning ≥10,000s per rank — the field's representable maximum). It cannot be read directly; a future story wanting an exact figure needs to widen `mod_service.F90`'s print format (shared infrastructure, out of this story's scope). Two bounds are available, **not on the same footing as each other or as dcgp's clean 91.2%**: a firm **≥5234.09s** (the sum of its own known physics sub-timers, using the same `system_clock()`-based, cross-rank-averaged DEBUG timers dcgp's percentage is built from) and an approximate **≤17,779s** (the model's self-reported "Total elapsed seconds of run" minus the other top-level items — this uses Fortran `cpu_time()` on the single I/O-coordinator rank, a different clock and a different scope than the DEBUG timers, per the same caveat given for dcgp above). Because the upper bound comes from a different measurement entirely, this report does not collapse the two bounds into a single point-estimate percentage comparable to dcgp's 91.2% — doing so would present a scope mismatch as a hardware/compiler difference. What is directly comparable across platforms is each physics scheme's share of the *combined physics total* (right-hand column above): RRTMG's 38.4% here against 42.5% on dcgp are consistent with each other, using an apples-to-apples denominator neither run's overflow affects.

Artifacts: `RegCM-data/profiling/s44-boost-nsys-53958915.nsys-rep`, `s44-boost-perf-54143865.data`, `s44-boost-flamegraph-54143865.svg`, `s44-boost-perf-report-54143865.txt`.

## Why perf's rank-0 capture is not a percentage-share source

`perf`/Nsight wrap rank 0 only (AD-2, this cluster's job-step isolation makes profiling every rank impractical). At 224-way decomposition (dcgp), rank 0's own grid tile is small and it spends the bulk of its own wall-clock time in **MPI communication/progress polling**, not compute — its `perf` report's highest single-symbol share is `MPIDI_Progress_test` at 8.62%, with `mod_moloch`/`mod_rrtmg_driver` symbols not appearing in the top ranks at all. At 16-way decomposition (boost), each rank does proportionally far more unique compute and far less communication-wait, so `perf` shows `mod_moloch_moloch_` dominating (76.78% of the *entire captured process*, including model initialization — not directly comparable to the DEBUG timers' evolution-phase-only scope). Even there, `mod_rrtmg_driver_rrtmg_driver_` shows only 0.46% via `perf` — sharply inconsistent with the DEBUG timer's 2010s figure. The likely cause: `pgf90_subchk64nz` (NVHPC's `-Mbounds` runtime bounds-check helper) alone accounts for ~25% of all samples, and the recurring `BFD: Dwarf Error: found dwarf version 'NNNN'` parse failures (present in both boost captures, non-fatal but real) point to imperfect DWARF unwinding through this debug build's heavy runtime-check instrumentation — samples inside deeply-nested, heavily-inlined RRTMG call paths are plausibly misattributed elsewhere in the call graph.

**Conclusion: `mod_service`'s DEBUG timers, not `perf`'s Children%/Self% columns, are the reliable source for this report's (and any future story's) per-subsystem wall-time-share claims on this DEBUG build.** `perf`/Nsight remain valuable for exactly what AD-2 designed them for — identifying specific hot low-level routines (`wafone`, `sound`, `nogtom`'s `solver`) and unattributed compiler-runtime costs — not for cross-subsystem percentage comparison. Neither boost capture showed a dominant unattributed/anonymous-address hotspot analogous to the thesis's `__c_mset16_avx` CLM-hydrology finding (largest unattributed entries were ≤1.2%) — a real, if modest, negative finding: this fixture is BATS-coupled, not CLM4.5-coupled the way the thesis's own run was, so the absence isn't a direct contradiction, but no comparable unattributed memset-pattern hotspot appears here either.

**Two further limits on how far these numbers can be pushed.** First, the `mod_service` DEBUG timers are not immune to the DEBUG build's own overhead — `-O0`/`-Mbounds` disables optimization and adds bounds-checking uniformly, but there is no guarantee that overhead lands evenly across MOLOCH, RRTMG, microphysics, and PBL; the percentages above are shares *of this DEBUG build's* wall time, not necessarily of a production build's. Second, dcgp (224 ranks) and boost (16 ranks) run at more than a 10x difference in decomposition granularity, and MPI overhead and per-rank workload both scale with that — some of the wall-time-share differences attributed here to Intel-vs-NVHPC could instead (or additionally) trace to running the two legs at very different parallelism levels, a variable this story did not hold constant.

**Load imbalance is real and visible in the DEBUG timers' own max/min-per-rank columns**, not just in `perf`'s rank-0 sampling: dcgp's `rrtmg_driver` ranges from 149.54s (rank 223) to 209.63s (rank 82) — a ~40% spread around the 189.54s average — confirming that no single rank's behavior, including rank 0's, represents the domain average.

## Comparison to prior evidence

- **RRTMG.** Measured at 11.1% of MOLOCH's own total on dcgp (10.1% of the full evolution phase, 42.5% of the physics-only total) and 38.4% of the physics-only total on boost. This is not the same figure as Story 4.1's independent `perf`-based ≈6.0% (job 48812653, Intel/dcgp, BATS-coupled) — a real, roughly 1.7x gap on the same dcgp partition, not glossed over: job 48812653 used an `--enable-profile` (optimized, symbols-only) build measured by `perf` sampling, while this report's figure comes from a `--enable-debug` (`-O0`, `-Mbounds`) build measured by direct wall-clock accumulation. DEBUG-build overhead is unlikely to fall evenly across every subsystem, so some divergence between the two measurements is expected; both nonetheless place RRTMG in the same qualitative band — a minor-to-moderate contributor, well short of MOLOCH or even the collective physics parametrizations, consistent with the CLM4.5-coupled thesis finding that RRTMG is not a major hotspot.
- **MOLOCH / dynamics.** Dominant on dcgp (91.2%, cleanly measured) and, by both of boost's bounds, on boost too (at minimum 5234.09s beyond dcgp's own physics-only total of 446.20s, i.e. still the majority of a much longer run even at its floor) — expected for `idynamic=3`, and directionally consistent with Story 4.1's own finding that MOLOCH outweighed RRTMG there too.
- **Thesis's CLM4.5-coupled hotspots** (`getcape`/CAPE-CIN 54%, CLM-hydrology memset ~20%, `interp1d_r8` ~12%, `heatindex` ~8%) are **not directly re-measured by this story** — none of those four routines carry a Story 4.1–4.3 DEBUG timer, and this fixture is BATS-coupled, not CLM4.5-integration-level profiling of those specific kernels. This report extends the epic's evidence base (RRTMG, diagnostic I/O, full evolution-phase subsystem shares, and the rank-0-sampling methodology finding above) rather than re-deriving the thesis's own four figures.

## KPP chemistry coverage — not measured this pass

`cbmz_integrate`/`cb6_integrate` (Story 4.2) are **not exercised or measured in this report**, by design. Story 4.2 documented six distinct real attempts to run a chemistry-enabled configuration to completion, each hitting a different unrelated pre-existing bug, and stopped at franco's direction. Repeating that attempt here would not produce new evidence. Chemistry-timer coverage remains code-inspection-only, unchanged from Story 4.2's own conclusion.

## `-Minfo=accel` — GPU offload confirmation

One `--enable-openacc-managed` NVHPC build (job 53958940) was attempted purely to harvest `-Minfo=accel` compiler evidence — expected to eventually fail, since Story 4.3 already conclusively characterized `Main/mod_bdycod.F90`'s `nvvmCompileProgram` ICE as a systemic NVHPC 26.3 backend defect (nine mitigation attempts, `deferred-work.md`), not something this story should re-chase.

The build instead crashed earlier and differently: a genuine compiler backend segfault (`nvfortran-Fatal-.../fort2 TERMINATED by signal 11`) in `Main/microlib/mod_micro_nogtom.F90`, a file `mod_bdycod.F90`'s own ICE never reached. This is a **new, fifth distinct NVHPC 26.3 GPU-porting defect**, logged to `deferred-work.md` and not investigated further (same Ask-First boundary as `mod_bdycod.F90`).

234 `-Minfo=accel`/`Generating` lines were captured for every file compiled before the crash — `external`, `Share` (including confirmed real offload for `getcape_new` in `mod_capecin.F90`, `mod_heatindex.F90`, and `interp1d_r8`/`interp1d_r4`/`interp1d_r8_new` in `mod_interp.F90`, each emitting genuine `Generating acc routine seq`/`Generating NVIDIA GPU code` lines — note these appeared on the build's stderr stream, not stdout), `Main/mpplib`, `Main/netlib`, `Main/batslib`, `Main/ocnlib`, `Main/chemlib`, `Main/clmlib`, and part of `Main/microlib`. `Main/clmlib/clm4.5/mod_clm_hydrology2.F90` compiled cleanly but carries no `!$acc` directives at all in the current source — it is not an offload target and is not claimed as one here, correcting an assumption carried over from this project's own context notes. This satisfies AD-2's `-Minfo=accel` requirement without a working full GPU binary. Log: `RegCM-data/build-logs/nvhpc-gpu-accel-4-4-53958940.{out,err}`.

## Evidence index

| Artifact | Location |
|---|---|
| dcgp Intel DEBUG binary build | job 53957457, `bin/slurm-4-4-build-intel-debug.sh` |
| dcgp profiling run (perf+FlameGraph) | job 53958861, `RegCM-data/story4-4/logs/dcgp-run-53958861.{out,err}` |
| boost NVHPC binary refresh (sequential build) | job 53957727, `bin/slurm-4-4-refresh-nvhpc-debug.sh` |
| boost profiling run (Nsight Systems) | job 53958915, `RegCM-data/story4-4/logs/boost-nsys-run-53958915.out` |
| boost profiling run (perf+FlameGraph) | job 54143865, `RegCM-data/story4-4/logs/boost-perf-run-54143865.{out,err}` (retry; first attempt, job 54078622, corrupted a 574GB capture at perf's default sampling rate — root-caused and fixed to `-F 99` in `bin/task4-4-rank0-perf-wrap-nvhpc.sh`) |
| GPU-accel `-Minfo=accel` attempt | job 53958940, `RegCM-data/build-logs/nvhpc-gpu-accel-4-4-53958940.{out,err}` |
| Fixtures | `RegCM-data/story4-4/EUR12_story4-4.in` (dcgp), `EUR12_story4-4_boost.in` (boost) |
| New deferred-work findings | `_bmad-output/implementation-artifacts/deferred-work.md` (`mod_micro_nogtom.F90` compiler crash) |
