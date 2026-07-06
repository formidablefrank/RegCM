# Story 1.1: Instrument RRTMG's Compute Core

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As regcm5-dev (the model's scientific owner and profiling lead),
I want RRTMG's driver and radiative-transfer kernels wrapped in DEBUG-gated timing instrumentation, complemented by a `perf`/Nsight profiling pass on at least one non-CLM-coupled configuration,
so that I can confirm or correct RRTMG's actual wall-clock cost share instead of assuming the CLM4.5-coupled thesis finding ("not a hotspot") generalizes on its own.

## Acceptance Criteria

1. Given a DEBUG-enabled build of RegCM5, when `time_begin`/`time_end` wrap `mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, and `rrtmg_sw_rad.F90`'s entry points, then a `Testing/` fixture run emits timing output attributable to RRTMG's core routines, not only its outer driver.
2. Given a non-CLM-coupled configuration (e.g. BATS-coupled or the idealized RCE setup), when a `perf --call-graph dwarf` + Nsight Systems profiling pass runs against it, then the profile states RRTMG's measured wall-clock share, confirming or correcting the "not a hotspot" CLM4.5-coupled finding before it is generalized.
3. Given a non-DEBUG production build, when the same code path executes, then no additional timing overhead is observable, per the existing DEBUG-gating convention (NFR-4).

## Tasks / Subtasks

- [ ] Task 1: Instrument the three RRTMG entry points with DEBUG-gated timing (AC: #1, #3)
  - [ ] In `Main/radlib/mod_rrtmg_driver.F90`: add a conditional `use mod_service, only : time_begin, time_end, dbgslen` guarded by `#ifdef DEBUG`/`#endif`; wrap the full body of `rrtmg_driver` (the driver-level entry point called once per radiation timestep from `mod_rad_interface::radiation`, which internally calls `prep_dat_rrtm`, `rrtmg_sw`/`rrtmg_sw_nomcica`, `rrtmg_lw`/`rrtmg_lw_nomcica`, `radout`) with `time_begin`/`time_end`, following the `mod_rad_colmod3.F90` `colmod3` pattern exactly: `character(len=dbgslen) :: subroutine_name = 'rrtmg_driver'` + `integer(ik4) :: indx = 0` declared locally, `call time_begin` immediately after declarations, matching `call time_end` immediately before every exit.
  - [ ] In `Main/radlib/rrtmg_lw_rad.F90`: same pattern, wrapping the body of `rrtmg_lw` (the LW kernel's top-level subroutine — not `inatm`, not the internal `taumol`/`rtrnmc` calls it makes). **This file's module-level `use` section (before `contains`, around line 75) only imports `parkind`'s `im => kind_im, rb => kind_rb` aliases — it does not `use mod_intkinds`, so `ik4` is undefined here.** Add `use mod_intkinds, only : ik4` alongside the new `use mod_service` line, or the file will fail to compile on `integer(ik4) :: indx = 0`.
  - [ ] In `Main/radlib/rrtmg_sw_rad.F90`: same pattern, wrapping the body of `rrtmg_sw` (the SW kernel's top-level subroutine — not `inatm_sw`, not internal `setcoef_sw`/`spcvmc_sw` calls). **Same gap as the LW file: confirm whether `mod_intkinds`/`ik4` is in scope before using it, and add `use mod_intkinds, only : ik4` if not.**
  - [ ] Use distinct label strings per site (`'rrtmg_driver'`, `'rrtmg_lw'`, `'rrtmg_sw'`) so `time_print` output distinguishes driver-level from kernel-level cost.
  - [ ] Confirm every exit path (including any early `return`) calls `time_end` — an unmatched `time_begin` silently corrupts that label's accumulated timing.
- [ ] Task 2: Verify DEBUG build produces attributable timing output and non-DEBUG build is unaffected (AC: #1, #3)
  - [ ] **Precondition — check this before anything else:** every fixture in `Testing/` (including all ten `Testing/CORDEX/*.namelist` files, which set it explicitly, and `test_001.in`/`ideal.in`, which omit it and inherit `mod_params.F90:318`'s default) ships with `irrtm = 0`, which dispatches to `colmod3`, **not** `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw` (`Main/mod_rad_interface.F90:203-206`). Copy whichever fixture you use and set `irrtm = 1` in that copy before running — otherwise this task will show zero new timer entries and silently prove nothing.
  - [ ] Build with `DEBUG` defined via `--enable-debug` at configure time (`configure.ac:351-358`; this is the flag that adds `-DDEBUG` to `AM_CPPFLAGS`), run a small `Testing/` fixture copy with `irrtm = 1` (e.g. `test_001.in`), confirm `time_print` output shows separate entries for `rrtmg_driver`, `rrtmg_lw`, `rrtmg_sw`, distinguishable from `colmod3`'s existing entry (the alternate branch of the same `mod_rad_interface` dispatch).
  - [ ] Build without `DEBUG` (production default, `--enable-debug` omitted), confirm identical behavior to pre-change and no measurable overhead — the non-DEBUG path relies on `mod_service`'s no-op stub module, so nothing beyond a compile check is expected here.
  - [ ] Before relying on `time_print` output, sanity-check that this build's active timer count stays under `mod_service.F90`'s `maxnsubs = 100`: grep the source files actually compiled into this build/fixture combination for `subroutine_name = '` registrations and count them (there is no runtime bounds check beyond `indx < 0`, so exceeding capacity corrupts memory silently rather than erroring) — if it's already close to 100 before this story's 3 additions, flag it to regcm5-dev rather than proceeding.
- [ ] Task 3: Run and report the non-CLM-coupled profiling pass (AC: #2)
  - [ ] Select a non-CLM-coupled `Testing/` configuration (BATS-coupled fixture, or the idealized RCE setup) per AD-2's fixed profiling method: `perf record --call-graph dwarf` (needs `-g` debug symbols) with a FlameGraph rendering, plus an NVIDIA Nsight Systems (`nsys`) pass. **Same precondition as Task 2: set `irrtm = 1` in the namelist copy used for this run** — as shipped, every existing fixture defaults or is explicitly set to `irrtm = 0`, so without this edit the profile would measure `colmod3`'s cost, not RRTMG's, and any "RRTMG is ~0% of runtime" conclusion drawn from it would be a false negative, not a real measurement.
  - [ ] Submit as a Slurm job with a conservative resource request on `dcgp_usr_prod`/`dcgp_qos_dbg` (Intel, account `ICT26_MHPC_0`) or `boost_usr_prod`/`boost_qos_dbg` (NVHPC, account `ICT26_MHPC`) — never on the login node.
  - [ ] Record RRTMG's measured wall-clock share from the profile and state explicitly whether it confirms or corrects the CLM4.5-coupled thesis finding that RRTMG is not a hotspot — this measurement directly feeds Story 7.5's later RRTMG GPU go/no-go checkpoint.
  - [ ] Archive the profiling artifacts via `manage_baseline.py` (not by hand-copying files) under `FAST_BASELINE_ROOT/profiling/`, with full provenance: compiler+flags, MPI library, node/GPU model, problem size.

## Dev Notes

- **Existing instrumentation facility, not a new one:** `Main/mpplib/mod_service.F90` is the whole mechanism — entirely `#ifdef DEBUG`-gated, with a no-op stub module in `#else` so non-DEBUG builds still link. Public API: `time_begin(name, indx)` / `time_end(name_of_section, indx, isize)`, plus `time_reset`/`time_print`, `activate_debug`/`start_debug`/`stop_debug`, and constant `dbgslen = 64` (fixed label length). `indx` must be `integer(ik4)`, initialized to `0` in the caller (implicit `SAVE`); first call self-registers (`n_of_nsubs = n_of_nsubs + 1; indx = n_of_nsubs`).
- **Kind availability differs by file.** `mod_rrtmg_driver.F90` already `use mod_intkinds` at module level (line 20), so `ik4` is in scope there. `rrtmg_lw_rad.F90` and `rrtmg_sw_rad.F90` do not — their module-level use section only brings in `parkind`'s `im`/`rb` aliases (RRTM's own legacy kind system). Add `use mod_intkinds, only : ik4` to both before declaring `integer(ik4) :: indx = 0`; do not substitute `im` for `ik4` for the indx variable — `im` is `parkind`'s own convention for the numerical fields these kernels compute, not the project's DEBUG-instrumentation convention, and mixing the two for a single counter variable is unnecessary.
- **Timer registry has a fixed capacity.** `mod_service.F90` sizes its internal timer arrays at `maxnsubs = 100` (module-level parameter), with self-registration incrementing `n_of_nsubs` on each new label's first call. The codebase already registers roughly 130 distinct timer labels across all source files combined, though only the labels actually exercised by a given build/run (which schemes are compiled in, which code paths execute) count against the live `n_of_nsubs` total at runtime. Adding 3 more registrations narrows headroom further. When running Task 2's DEBUG build, confirm `n_of_nsubs` does not exceed `maxnsubs` for the fixture actually used — if it does, that is a pre-existing capacity issue to flag to regcm5-dev, not something to silently work around.
- **Copy the existing pattern exactly — do not invent a variant.** Confirmed precedents:
  - `Main/radlib/mod_rad_colmod3.F90:223-227` (entry) / `:742-744` (exit), subroutine `colmod3` — the closest template, since `colmod3` is the *other* branch of the same `mod_rad_interface` dispatch this story instruments, and is already DEBUG-timed.
  - `Main/mod_sun.F90:263-267`/`:292-294`, subroutine `solar1`.
  - `Main/radlib/mod_rad_radiation.F90`, subroutines `radcsw`/`radclw`/`radctl` — three entry/exit pairs in one file, confirming the pattern repeats cleanly across multiple subroutines in the same module.
  - Prefer the `colmod3` form (`#ifdef DEBUG`-guarded `use mod_service, only : ...`) over `solar1`'s bare `use mod_service`, since the three target files currently have zero `mod_service` references and the guarded form is the more common existing convention.
- **Never instrument inside a loop body** — matches every existing call site and NFR-4. Timing instrumentation inside `prep_dat_rrtm`'s or `taumol`'s per-column loops would reintroduce the overhead the DEBUG-gating convention exists to avoid, even temporarily.
- **No shipped fixture exercises RRTMG as-is — this is the single most important precondition in this story.** `irrtm` defaults to `0` (`Main/mod_params.F90:318`) and every `Testing/CORDEX/*.namelist` sets it explicitly to `0`; `test_001.in`/`ideal.in` omit it and inherit the same default. `irrtm==0` calls `colmod3`; only `irrtm==1` calls `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw` (`Main/mod_rad_interface.F90:203-206`). Both Task 2 and Task 3 require a namelist copy with `irrtm = 1` — running an unmodified fixture will produce a null result (no new timer entries; ~0% measured RRTMG cost) that is easy to mistake for a real "RRTMG isn't a hotspot" finding rather than what it actually is: RRTMG never ran.
- **McICA variant confirmed correct:** `imcica` defaults to `1` in every fixture checked, so `rrtmg_lw`/`rrtmg_sw` (the McICA-enabled entry points) are the right instrumentation targets, not the `_nomcica` variants also present in `mod_rrtmg_driver.F90`'s call chain.
- **The gap this story closes:** `mod_rad_interface::radiation()` (`Main/mod_rad_interface.F90:198-207`) dispatches `if (irrtm==1) call rrtmg_driver(...) else call colmod3(...)`. `colmod3` already has full DEBUG timing; `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw` currently have none — closing that asymmetry is this story's entire scope.
- **Why this story exists:** an ICTP/SISSA thesis (`_bmad-source/regcm5-optimization.pdf`, Tica 2024–2026) profiled RegCM5-CLM4.5 with `perf`+Nsight and found RRTMG does not appear as a named hotspot in that coupled configuration's flame graph — confirmed hotspots were `getcape`/CAPE-CIN, a CLM-hydrology memset, `interp1d_r8`, and `heatindex`. RRTMG's large code size had made it look like an obvious GPU-port candidate before this measurement (Architecture §7, GPU Candidate Selection). This story gets a direct, non-CLM-coupled measurement rather than assuming the coupled-case finding generalizes. This is evidence-gathering, not a performance fix — do not optimize or restructure RRTMG as part of this story.
- **AC #2 is a separate activity from AC #1/#3.** AC #1/#3 is a code change (add timing wraps, verify overhead-free). AC #2 is an operational task (run `perf`+Nsight on a real Slurm job and report a measured number). Both are required for the story to be done; the DEBUG timing output is complementary evidence to, not a replacement for, the coarser `perf`/Nsight measurement.
- **Scope boundary:** do not touch KPP chemistry timing (Story 1.2) or diagnostic-I/O gather/write timing (Story 1.3) — separate stories, separate files. Story 1.4's published baseline report builds on this story's output but is out of scope here. Touch only `mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, `rrtmg_sw_rad.F90`.
- **Numerical reproducibility:** pure instrumentation (timing calls only, no algorithmic change) — expected bit-exact in both DEBUG and non-DEBUG builds. Any output difference after this change is a defect in the instrumentation, not an expected side effect; no tolerance exception applies.
- **Record all four acceptance-criteria categories in the commit/PR description** (project convention, not optional for a "small" change): **Build** — which compiler(s) (GNU/Intel/NVHPC); **Test** — which `Testing/` fixture, which process count; **Numerical** — state bit-exact explicitly; **Performance** — only claim RRTMG's measured wall-clock share with AC#2's profiling evidence attached (provenance: compiler+flags, MPI library, node/GPU model, problem size).

### Project Structure Notes

- All three target files live under `Main/radlib/` (the radiation-scheme subdirectory of `Main/`, which owns model core + physics libs per project convention).
- No new files are created — only existing files gain `#ifdef DEBUG` blocks and a conditional `use mod_service` line. No namelist, build-system (`configure.ac`/`Makefile.am`), or public-interface changes.
- No conflicts detected between this story and the existing project structure.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` Story 1.1, lines 212-230] — verbatim user story and acceptance criteria
- [Source: `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` FR-1] — requirement and testable consequences
- [Source: `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` Cross-Cutting NFRs, 4th bullet — labeled NFR-4 in `epics.md`'s Requirements Inventory] — DEBUG-only overhead constraint
- [Source: `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` Success Metrics SM-2, Risk Register] — acceptance cross-check and RRTMG/PSrad risk mitigation
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE-SPINE.md` AD-2] — fixed profiling method (`perf --call-graph dwarf` + Nsight Systems). AD-17 also confirms the `time_begin`/`time_end` API and "zero overhead, never inside a loop" rule, but is otherwise Story 1.3/FR-3's I/O-timer-label convention, not this story's concern
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE.md` §5, §7] — profiling method detail; GPU-candidate-selection motivation
- [Source: `Main/radlib/mod_rrtmg_driver.F90`, `Main/radlib/rrtmg_lw_rad.F90`, `Main/radlib/rrtmg_sw_rad.F90`] — files to modify
- [Source: `Main/mpplib/mod_service.F90`] — DEBUG timing facility (`time_begin`/`time_end` API)
- [Source: `Main/radlib/mod_rad_colmod3.F90:223-227,742-744`; `Main/mod_sun.F90:263-267,292-294`; `Main/radlib/mod_rad_radiation.F90`] — existing instrumentation templates to replicate
- [Source: `Main/mod_rad_interface.F90:198-207`] — dispatch seam confirming the coverage gap this story closes
- [Source: `Main/mod_params.F90:318`; `Testing/CORDEX/*.namelist`; `Testing/test_001.in`; `Testing/ideal.in`] — confirms `irrtm` defaults/is set to `0` everywhere; the namelist edit needed for Tasks 2-3 to actually exercise RRTMG
- [Source: `configure.ac:351-358`] — `--enable-debug` is the flag that defines `DEBUG`
- [Source: `_bmad-output/project-context.md` §Debug facility, §Language & Numerical Rules] — DEBUG macro convention, `rkx`/`ik4` kind rules, "never inside a loop body" rule

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
