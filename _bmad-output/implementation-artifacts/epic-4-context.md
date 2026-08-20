# Epic 4 Context: Profiling and Memory Evidence Baseline

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

RegCM5's GPU-porting and I/O-optimization decisions have so far rested on a single, external source thesis's CLM4.5-coupled profiling run plus structural inference — this epic replaces inference with direct measurement. It instruments RRTMG, KPP chemistry integration, and diagnostic-output gather/write with DEBUG-gated timing, runs a baseline profiling pass on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC), and separately investigates whether unreleased `getmem` workspace allocations cause real memory growth and whether Valgrind surfaces genuine leaks/errors. It is standalone — produces a published baseline report that Epics 10 (GPU acceleration) and 11 (I/O scaling) cite as their evidence base, and requires nothing from any later epic.

## Stories

- Story 4.1: Instrument RRTMG's Compute Core
- Story 4.2: Instrument KPP Chemistry Integration
- Story 4.3: Instrument Diagnostic-Output Gather and Write
- Story 4.4: Baseline Profiling Run and Published Report
- Story 4.5: Long-Running Memory-Growth Investigation
- Story 4.6: Valgrind Memory-Leak and Error Check

## Requirements & Constraints

- Timing instrumentation (RRTMG, KPP chemistry, diagnostic I/O) must add zero overhead to non-DEBUG production builds — the existing `#ifdef DEBUG` convention, not a new mechanism.
- RRTMG's CLM4.5-coupled "not a hotspot" finding must be confirmed or corrected on at least one non-CLM-coupled configuration before it is treated as generalizable — the coupled-only result does not by itself justify deprioritizing RRTMG everywhere. RRTMG also shares scheme lineage with ICON-A's PSrad, whose directive-based GPU port failed — this program's Risk Register treats that as an unconfirmed, not dismissed, risk pending this epic's own direct measurement (Epic 10's FR-9 go/no-go checkpoint consumes it).
- KPP chemistry timing must distinguish integration time from the chemistry support routines (drydep, emission, boundary) already instrumented — not lump them together.
- Diagnostic-I/O instrumentation must separate I/O-rank gather time, write time, and compute-rank idle time, for each of the serial, HDF5-parallel, and PnetCDF-parallel write paths — this is the evidence Epic 11's I/O-scaling investigation needs to explain the source thesis's finding that parallel write was measured *slower* than serial write at every tested rank count.
- The baseline profiling report must state measured wall-time share per subsystem and per partition — not an estimate — and explicitly cite the source thesis's own confirmed hotspots for the CLM4.5-coupled case: `getcape`/CAPE-CIN (54%), a CLM-hydrology memset (~20%), `interp1d_r8` (~12%), `heatindex` (~8%). Later epics' hotspot claims (e.g. Epic 10's RRTMG go/no-go) must cite this report and the source thesis, not the earlier structural-inference research note.
- The memory-growth investigation does not presuppose a fix is needed — remediation is scoped as a follow-up only if measured evidence (e.g. peak RSS over a long run) confirms a real problem.
- The Valgrind pass surfaces and documents leaks/errors; it does not fix them — confirmed issues become scoped follow-up work.
- Profiling method is fixed, not a per-story choice: `perf --call-graph dwarf` (needs `-g`) with Brendan Gregg FlameGraph rendering for CPU stacks, NVIDIA Nsight Systems for GPU/compiler-runtime symbol attribution `perf` cannot resolve, `-Minfo=accel` to confirm what a region actually offloaded.

## Technical Decisions

- The instrumentation facility is `Main/mpplib/mod_service.F90`, entirely `#ifdef DEBUG`-gated with a no-op stub in `#else`: `time_begin(name, indx)`/`time_end(name, indx, isize)`, `dbgslen = 64` fixed label length, `maxnsubs = 100` fixed timer-registry capacity with no bounds check (a pre-existing, shared-infrastructure gap, not owned by any one story in this epic).
- Two valid guard conventions coexist and must not be mixed within a file: a file with no prior `mod_service` reference uses a guarded `use mod_service` plus `integer(ik4) :: indx = 0` (implicit `SAVE` via initializer); a file that already references `mod_service` elsewhere (e.g. `mod_che_drydep.F90`, `mod_che_emission.F90`, `mod_che_bdyco.F90`) uses a bare unconditional `use` plus an explicit `integer(ik4), save :: idindx = 0`.
- Diagnostic-I/O timer labels follow a fixed naming convention: `io_gather_<path>`/`io_write_<path>`/`io_wait_<path>`, `<path>` in `{hist, rst, clm}` — chosen to read clearly within the debug output's truncated name field. Only the naming is fixed at the planning level; the actual instrumentation calls in `mod_ncout.F90`/`mod_savefile.F90`/CLM's history module are separate, story-level Fortran changes.
- No shipped `Testing/` fixture exercises RRTMG or gas-phase chemistry as-is: `irrtm` and `chemsimtype` both default to values that skip them, so an unmodified fixture run produces a null (near-zero) measured cost that looks like, but is not, a real "not a hotspot" finding. Every instrumentation/profiling story in this epic must force the relevant namelist flag on in its own working fixture copy.
- Gas-phase chemistry (KPP/DLSODE) GPU porting is explicitly out of scope for this program's accelerator work — a known poor fit for SIMT execution given its data-dependent, irregular iteration structure — so Story 4.2 is evidence-gathering only, not preparation for a GPU port.
- Never instrument inside a loop body — matches every existing `mod_service` call site across the codebase and applies uniformly to every story in this epic.

## Cross-Story Dependencies

- Story 4.4 (baseline run and report) depends on Stories 4.1-4.3's instrumentation being in place first — it profiles using their timers, not just raw `perf`/Nsight output.
- Story 4.6 (Valgrind) complements, not duplicates, Story 4.5 (memory-growth investigation) — Callgrind/KCachegrind gives a visual call-graph pass alongside Memcheck's own leak/error report, while Story 4.5 targets the specific `getmem`/`relmem` allocation pattern; the two use different tools and can proceed independently.
- Downstream, outside this epic: Epic 8's continuous performance/memory-safety CI gates extend Story 4.6's one-time Valgrind baseline into an enforced check. Epic 10's GPU-acceleration work (RRTMG go/no-go, MOLOCH porting) cites this epic's FR-4 baseline report as its evidence base. Epic 11's I/O-scaling investigation builds directly on Story 4.3's gather/write/wait instrumentation to explain the source thesis's parallel-write-slowdown finding.
