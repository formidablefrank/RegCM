---
title: 'Instrument RRTMG''s Compute Core'
type: 'chore'
created: '2026-08-19'
status: 'done'
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: '39f2085aa8e49254e9691c77703123dcfe88dd45'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** RRTMG's driver and radiative-transfer kernels carry zero DEBUG-gated timing. An ICTP/SISSA thesis (`_bmad-source/regcm5-optimization.pdf`) profiled RegCM5-CLM4.5 and found RRTMG is not a named hotspot in that coupled configuration's flame graph — but that finding was never confirmed in a non-CLM-coupled configuration, and RRTMG's large code size had made it look like an obvious GPU-port candidate before this measurement.

**Approach:** Wrap `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw`'s entry points in `time_begin`/`time_end`, copying the existing `colmod3` DEBUG-timing pattern exactly (`Main/radlib/mod_rad_colmod3.F90`, the sibling branch of the same `mod_rad_interface` dispatch). Verify DEBUG/non-DEBUG compile across GNU/Intel/NVHPC, confirm the three timers fire distinctly on a real run, then run `perf --call-graph dwarf` + Nsight Systems on a non-CLM (BATS) configuration to measure RRTMG's actual wall-clock share.

## Boundaries & Constraints

**Always:** Force `irrtm = 1` in the run namelist — every shipped `Testing/*.in`/`Testing/CORDEX/*.namelist` defaults `irrtm = 0` (dispatches to `colmod3`, not RRTMG), so an unmodified fixture gives a null result indistinguishable from a real "not a hotspot" finding. Use `perf`/Nsight exclusively per AD-2's fixed profiling method. Run every build/execution via Slurm, never the login node. Record Build/Test/Numerical/Performance evidence in the commit/PR description.

**Ask First:** Any fix to a pre-existing bug found outside the three target files (a build failure, a GPU-port defect) needs franco's explicit go-ahead before touching it — this story's scope is RRTMG instrumentation, not general bug-fixing.

**Never:** Touch KPP chemistry timing (Story 4.2) or diagnostic-I/O gather/write timing (Story 4.3) — separate stories, separate files. No algorithmic change to RRTMG itself — this is evidence-gathering only. No timing instrumentation inside a loop body (`prep_dat_rrtm`/`taumol`'s per-column loops) — matches every existing call site and NFR-4.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| DEBUG build, `irrtm=1` fixture | `time_begin`/`time_end` wrap all 3 entry points | `time_print` shows `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw` as separate, populated timers | N/A |
| Non-DEBUG production build | Same code path executes | `-DDEBUG` absent from build log; no observable timing overhead | N/A |
| Unmodified shipped fixture | `irrtm` left at its default (0) | `colmod3` runs instead of RRTMG; zero new timer entries | Must not be mistaken for a real "RRTMG isn't a hotspot" result — this is RRTMG never running |
| Non-CLM-coupled profiling pass | `perf --call-graph dwarf` + Nsight on a BATS configuration | Measured RRTMG wall-clock share reported, confirming or correcting the CLM4.5-coupled thesis finding | N/A |

</frozen-after-approval>

## Code Map

- `Main/radlib/mod_rrtmg_driver.F90:45,378,380,609` -- `rrtmg_driver` entry point; `mod_intkinds` already in scope module-level, only `mod_service` import added
- `Main/radlib/rrtmg_lw_rad.F90:76,81,458,460,688` -- `rrtmg_lw`; needed both `mod_intkinds`/`ik4` and `mod_service` added (only `parkind`'s `im`/`rb` were in scope)
- `Main/radlib/rrtmg_sw_rad.F90:81,82,569,571,946` -- `rrtmg_sw`; same as LW
- `Main/radlib/mcica_random_numbers.F90:91-92` -- Task 1b, franco-requested: `UMASK = -2147483648` (overflows gfortran's positive 4-byte range) rewritten to the portable `-2147483647 - 1` idiom; unblocked GNU verification of the story's own three files
- `Main/mpplib/mod_service.F90` -- existing DEBUG timing facility; `time_begin(name, indx)`/`time_end(name, indx, isize)`, `dbgslen = 64`, `maxnsubs = 100` fixed timer-registry capacity
- `Main/radlib/mod_rad_colmod3.F90:223-227,742-744` (`colmod3`) -- the copied template; the `mod_rad_interface` dispatch's other branch
- `Main/mod_rad_interface.F90:198-207` -- `if (irrtm==1) call rrtmg_driver(...) else call colmod3(...)` -- the dispatch seam this story closes the DEBUG-timing asymmetry on
- `Main/mod_params.F90:318` -- `irrtm` defaults to `0`; every shipped fixture inherits or sets this explicitly
- `configure.ac:500-529` -- `COMPILER_PGI` vendor detection, franco-requested fix (see Spec Change Log)
- `Share/mod_heatindex.F90` -- franco-requested GPU-port fix, applied and verified, then deliberately reverted (see Spec Change Log)

## Tasks & Acceptance

**Execution:**
- [x] Wrap `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw` with `time_begin`/`time_end`, distinct labels (`'rrtmg_driver'`/`'rrtmg_lw'`/`'rrtmg_sw'`), matching `colmod3`'s guard convention -- confirmed single exit (no early `return`) in all three before wrapping
- [x] Fix the pre-existing gfortran build failure in `mcica_random_numbers.F90` (franco-requested, outside original scope) -- unblocks GNU verification
- [x] Verify DEBUG and non-DEBUG builds compile the three instrumented files across GNU, Intel (ifx-only), and NVHPC -- `-DDEBUG` confirmed present only in `--enable-debug` logs
- [x] `maxnsubs` capacity audit for this configuration's compile-time label count -- 125 distinct labels compiled in (BATS/no-CLM45/`irrtm=1`), ~40 actually registered at runtime by end of a real run, comfortably under the `maxnsubs = 100` cap
- [x] Run a real fixture under the DEBUG build and confirm `time_print` shows all three timers as separate, populated entries
- [x] Run the non-CLM-coupled `perf`/Nsight profiling pass and report RRTMG's measured wall-clock share

**Acceptance Criteria:**
- Given a DEBUG-enabled build, when `time_begin`/`time_end` wrap `mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, and `rrtmg_sw_rad.F90`'s entry points, then a real fixture run emits timing output attributable to RRTMG's core routines, not only its outer driver.
- Given a non-CLM-coupled (BATS) configuration, when a `perf --call-graph dwarf` + Nsight Systems pass runs against it, then the profile states RRTMG's measured wall-clock share, confirming or correcting the CLM4.5-coupled thesis finding.
- Given a non-DEBUG production build, when the same code path executes, then no additional timing overhead is observable (NFR-4).

## Spec Change Log

- **`configure.ac`'s `COMPILER_PGI` detection was silently false for every NVHPC build using this project's own documented module stack** (franco-requested fix, well outside the three target files). `FCPROG`'s pattern match (`pgf9*`/`nvf9*`/`pgfortran*`/`nvfortran*`) never matched HPC-X's generic `mpifort` wrapper, so four `configure.ac` blocks gated on `COMPILER_PGI_TRUE` (base `OMPFLAGS`, DEBUG bounds-checking, production optimization flags, the entire `--enable-openacc-*` block) were never applied to any NVHPC build — including verification passes that predate this story. Fixed with an `$FC --version` signature fallback probe. Verified: OpenACC FCFLAGS now apply and compile lines show `-stdpar=gpu -gpu=ccnative,...` where before they showed nothing.
- **`Share/mod_heatindex.F90` (an already-GPU-ported hotspot) failed to compile under `--enable-openacc-debug` on NVHPC** (franco-requested fix, discovered incidentally while verifying the `configure.ac` fix above). Its `!$acc routine seq` procedures called an un-annotated `fatal()` from inside GPU compute regions when `DEBUG` was defined. Fixed by changing all 31 `#ifdef DEBUG` occurrences to `#if defined(DEBUG) && !defined(OPENACC)`, disabling the DEBUG-only diagnostic specifically under GPU compilation. Verified both ways (job 48709086 reverted/CPU-only baseline; job 48720240 fix reapplied, real device codegen confirmed via `-Minfo=accel`). **Franco subsequently removed this fix and deferred it to the GPU-offloading epic** — it is intentionally absent from this story's final delivered state; re-apply when that epic picks up this file.
- **Code review (2026-07-07) found Task 2b's subtask checkboxes unchecked despite the parent task being marked done**, including the `maxnsubs`-capacity precondition. Resolved by performing the audit (see Tasks) and checking the boxes with the finding recorded.
- **Code review corrected several stale claims about the 11 `bin/*.sh` HPC scripts**: they are intentionally untracked/gitignored personal tooling (franco's explicit call), not committed deliverables — the File List and individual entries were corrected to reflect untracked status. Several further script-robustness gaps (missing `Main/regcm` link step, no `irrtm=1` mutation verification, a rank-0 wrapper defaulting to rank `"0"` on missing env vars, `configure`-failure not gating the subsequent `make`) were found and deferred as pre-existing, non-blocking issues in personal verification tooling — see `deferred-work.md`.

## Design Notes

**`mod_service.F90` API and conventions:** `indx` must be `integer(ik4)`, initialized to `0` in the caller (implicit `SAVE` via initializer, the established convention for a file with zero prior `mod_service` references — do not add an explicit `save` or switch to the `idindx`-named convention used by files that already reference `mod_service` elsewhere). First call self-registers (`n_of_nsubs += 1`). Never instrument inside a loop body.

**Why `irrtm=1` matters more than anything else in this story:** `Main/mod_rad_interface.F90:198-207`'s dispatch means an unmodified fixture silently exercises `colmod3`, producing a ~0% "measured" RRTMG cost that looks like, but is not, a real finding. Both the runtime-verification task and the profiling task require a namelist copy with `irrtm=1` forced on.

**Profiling method gotchas (AD-2, `perf`+Nsight), reusable for future profiling stories:** `perf record` must wrap the actual `regcm` process directly, not the outer `mpirun`/`srun` launcher — this cluster bootstraps MPI ranks as independent Slurm job steps, invisible to a `perf`/`nsys` instance tracing the launcher's own process tree; wrap each rank internally instead (`mpirun -n N ./wrapper.sh`). Profiling all ranks individually isn't practical — rank 0 only, full rank/node scope preserved otherwise. `nsys --trace=osrt,mpi` can stall indefinitely under MPI-collective interception on a wrapped rank while other ranks block waiting on it; drop `mpi` from `--trace` (`osrt` only). This cluster's `nsys` (2024.5.1) rejects `--mpi-impl=intel` (use `mpich`, since Intel MPI is MPICH-derived) and its argument parser does not accept a `--` separator before the target command.

**Automake build-parallelism hazard:** recursive `SUBDIRS` builds are not safe with `-j>1` spanning multiple directory levels — a sibling/child directory's link step can start before another directory's library archive has been `ranlib`'d. Build the reduced scope (`external` → `Share` → `Main/mpplib` → `Main/radlib`) as strictly sequential directories, `-jN` only within one flat directory.

## Verification

**Cross-vendor build matrix** (all three vendors, both DEBUG and non-DEBUG, via Slurm on `dcgp_usr_prod`/`boost_usr_prod`):
- GNU gcc/gfortran 12.2.0 + OpenMPI 4.1.6 — PASS (both configs), only after the `mcica_random_numbers.F90` fix
- Intel, ifx-only (`mpiifx`/`mpiicc` with `I_MPI_CC=icx`, no classic `ifort` anywhere — confirmed `grep -c "ifort:"` = 0) + `binutils/2.42` — PASS (both configs)
- NVHPC `nvhpc/25.11` + `hpcx-mpi/2.25.1` (closest available match to the project's stated target of 26.3/HPC-X 2.25) — PASS (both configs), after the `mod_heatindex.F90` fix
- `-DDEBUG` confirmed present only in `--enable-debug` build logs across all three vendors

**Runtime timer verification** (Task 2b): no shipped `Testing/` fixture has usable data on this cluster, so verified against `RegCM-data/EURR12` (EUR-12 CORDEX, 275×275×36, BATS not CLM4.5 — see below) with `irrtm=1` forced on, minimum-valid 24h window. Intel ifx, `--enable-debug`, 224 MPI ranks, `dcgp_usr_prod`. `RUN_EXIT=0`, `RegCM V5 simulation successfully reached end`. Evolution-phase `time_print` table showed all three timers as separate, populated entries (`rrtmg_driver` 65 calls, `rrtmg_lw` 65 calls, `rrtmg_sw` 35 calls — the `!*` prefix on `rrtmg_sw` flags it as active only during daylight timesteps). Two unrelated pre-existing bugs were routed around, not fixed, to keep this run in scope: `mod_clm_snicar.F90` fails under NVHPC `--enable-openacc-stdpar` (same un-annotated-`fatal()`-in-`!$acc loop seq` class as the `mod_heatindex.F90` fix above); `mod_ncio.F90`'s async-netcdf ICBC prefetch path fails under Intel ifx on a non-contiguous-pointer-argument issue. Both sidestepped by dropping `--enable-clm45` and `--enable-async-netcdf` respectively for this run only.

**Profiling pass** (Task 3): `--enable-profile` build (not `--enable-debug` — a distinct production-with-symbols config), same EUR12/BATS/`irrtm=1` configuration, 224 ranks/2 nodes, `dcgp_usr_prod`/`dcgp_qos_lprod` (job 48812653, PASS). **Measured RRTMG wall-clock share: ≈6.0%** (additive `Self%` across all `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw`/McICA symbols in `perf report`). This confirms, not corrects, the CLM4.5-coupled thesis finding — RRTMG is a minor contributor next to the moloch dynamical core (`mod_moloch_mp_wafone_`+`mod_moloch_mp_sound_`, ~17.9% combined), MPI/threading overhead, and roughly on par with `mod_capecin_mp_getcape_new_` (4.2%, the thesis's own confirmed hotspot — cross-validating the profiling method). This is the number Story 10.5's later RRTMG GPU go/no-go checkpoint cites. Artifacts (`RegCM-data/profiling/`, job 48812653, not yet promoted via `manage_baseline.py`): `task3-perf-48812653.data`, `task3-perf-report-48812653.txt`, `task3-flamegraph-48812653.svg`, `task3-nsys-48812653.nsys-rep`.

## Suggested Review Order

**Instrumentation (entry point)**

- Entry point: `rrtmg_driver`'s timer, the outer entry point wrapping the full RRTMG dispatch.
  [`mod_rrtmg_driver.F90:380`](../../Main/radlib/mod_rrtmg_driver.F90#L380)

- The two inner kernels, same pattern, each needing an added `mod_intkinds` import.
  [`rrtmg_lw_rad.F90:460`](../../Main/radlib/rrtmg_lw_rad.F90#L460) · [`rrtmg_sw_rad.F90:571`](../../Main/radlib/rrtmg_sw_rad.F90#L571)

**Out-of-scope fixes franco explicitly requested (not RRTMG instrumentation itself)**

- The one-line portability fix that unblocked GNU verification.
  [`mcica_random_numbers.F90:91`](../../Main/radlib/mcica_random_numbers.F90#L91)

- Root-cause NVHPC vendor-detection fix — four `configure.ac` blocks were silently unapplied to every NVHPC build before this.
  [`configure.ac:514`](../../configure.ac#L514)

**Evidence**

- Measured RRTMG share and how it compares to the thesis's own confirmed hotspots.
  [`spec-4-1-instrument-rrtmgs-compute-core.md`](spec-4-1-instrument-rrtmgs-compute-core.md) (Verification section)

**Peripherals**

- Sprint tracker, already `done`.
  [`sprint-status.yaml:77`](sprint-status.yaml#L77)
