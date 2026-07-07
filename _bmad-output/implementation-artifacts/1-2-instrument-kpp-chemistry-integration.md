---
baseline_commit: 9db31274be9fbafaca7d655a416f92b2ce98f367
---

# Story 1.2: Instrument KPP Chemistry Integration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As regcm5-dev,
I want the KPP-generated chemistry integrator entry points (`mod_cb6_Integrator.F90`, `mod_cbmz_integrator.F90`) wrapped in DEBUG-gated timing for each active mechanism,
so that chemistry integration time is visible separately from already-instrumented chemistry support routines (drydep, emission, boundary).

## Acceptance Criteria

1. Given a DEBUG-enabled build with an active gas-phase mechanism (CB6r2 or CBMZ), when a `Testing/`-equivalent fixture exercising that mechanism runs, then timing output separates integration time from the other, already-instrumented chemistry support routines.
2. Given a non-DEBUG production build, when the same run executes, then instrumentation adds no measurable overhead (NFR-4).

## Tasks / Subtasks

- [ ] Task 1: Instrument CBMZ's `integrate` entry point — the only mechanism actually reachable at runtime (AC: #1, #2)
  - [ ] In `Main/chemlib/GAS_CBMZ_NEW/mod_cbmz_integrator.F90`, wrap the body of `subroutine integrate` (line 145) with `time_begin`/`time_end`, following the `colmod3`/RRTMG-story template: `#ifdef DEBUG`-guarded `use mod_service, only : time_begin, time_end, dbgslen` plus an unconditional `use mod_intkinds, only : ik4` (this file currently has zero `mod_service`/`mod_intkinds` references — same "zero prior references" case as `rrtmg_lw_rad.F90`/`rrtmg_sw_rad.F90` in Story 1.1, where the guarded form was preferred).
  - [ ] Use the label `'cbmz_integrate'`, not bare `'integrate'` — `mod_cb6_Integrator.F90`'s entry point is *also* literally named `INTEGRATE`, and `mod_service`'s timer registry is a single flat namespace, so an unqualified label would collide if both mechanisms are ever compiled into the same binary (see Task 2's note — not currently possible, but don't bake in an ambiguous label as a footgun for whenever it is).
  - [ ] Confirm `integrate` (cbmz) has a single `end subroutine` exit and no early `return` (verified during story creation — it does; re-verify before editing in case the file has since changed).
- [ ] Task 2: Instrument CB6r2's `INTEGRATE` entry point, and flag that it cannot currently be build/run-verified (AC: #1, code-review-only for this mechanism)
  - [ ] In `Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90`, wrap the body of `SUBROUTINE INTEGRATE` (line 78) the same way: `#ifdef DEBUG`-guarded `use mod_service, only : time_begin, time_end, dbgslen` plus unconditional `use mod_intkinds, only : ik4`. Label: `'cb6_integrate'`.
  - [ ] **Do not** wire `GAS_CB6r2` into `configure.ac`/`Main/chemlib/Makefile.am` to make this testable — confirmed during story creation that `GAS_CB6r2` is currently orphaned from the build entirely (its own `Makefile.am` exists and defines `libcb6.a`, but `Main/chemlib/Makefile.am`'s `SUBDIRS` only lists `GAS_CBMZ_NEW`, and `configure.ac`'s `AC_CONFIG_FILES` never generates `Main/chemlib/GAS_CB6r2/Makefile`). Wiring it in is a build-system change with its own scope and risk, not an instrumentation change — flag it as a gap for regcm5-dev, don't silently fix it under this story.
  - [ ] Record in Completion Notes that AC #1's CB6r2 half is satisfied by code inspection (pattern matches the verified-working CBMZ instrumentation exactly) but not by an actual `time_print` run, and state why.
- [ ] Task 3: Verify DEBUG and non-DEBUG builds compile both instrumented files correctly, across GNU/Intel/NVHPC (AC: #1 compile-time half, #2)
  - [ ] Reuse the vendor/module-load setup already established and verified in Story 1.1 (GNU gcc/gfortran 12.2.0 + OpenMPI 4.1.6; Intel `mpiifx`/`mpiicc` with `I_MPI_CC=icx`, `binutils/2.42`; NVHPC `nvhpc/25.11` + `hpcx-mpi/2.25.1`, on a GPU node for `configure`/compile).
  - [ ] Confirm `-DDEBUG` appears only in `--enable-debug` build logs and is absent from default builds, for both new files, on all three vendors.
  - [ ] `GAS_CB6r2` will not build via the normal chain (Task 2) — compile it standalone if a compile-time-only check is wanted (e.g. `gfortran -c` against its own dependency chain), or accept code-review-only verification per Task 2's note; don't spend effort wiring the full autotools chain just to compile-check one file.
- [ ] Task 4: Construct a namelist that actually exercises CBMZ gas-phase chemistry, and run it under a DEBUG build (AC: #1 runtime half)
  - [ ] **No shipped `Testing/*.in` or `Testing/CORDEX/*.namelist` fixture exercises gas-phase chemistry as-is.** Confirmed during story creation: every fixture with `ichem = 1` (`test_008.in`) sets `chemsimtype = 'DUST'` (aerosol-only, dust chemistry, not gas-phase) or `'SULF'` (sulfate-only); none use `chemsimtype = 'CBMZ'`. This is the same class of precondition Story 1.1 hit with `irrtm` — running an unmodified fixture will produce a null result (chemistry mechanism never dispatches to `integrate`), not a real "no overhead" finding.
  - [ ] `chemsimtype = 'CBMZ'` (string namelist value, checked in `Main/chemlib/mod_che_common.F90:376`) combined with `ichem = 1` and `igaschem` set to 1 (set automatically by the `'CBMZ'` branch itself — don't set `igaschem` directly in the namelist) is what actually reaches `mod_che_chemistry::chemistry` → `chemmain` → `integrate`.
  - [ ] `test_008.in` still ships with placeholder paths (`/set/this/to/...`) per the project's known edge case (`project-context.md`, "Edge cases") — either edit a copy with real data paths (following Story 1.1's `EUR12_task2b.in` pattern) or use another real-data fixture already staged from Story 1.1 (`RegCM-data/EURR12/`), with `chemsimtype`/`ichem` forced to the CBMZ values above. Story 1.1's own `EUR12_task2b.in` has no `ichem` line at all (defaults to 0) — it is not reusable as-is for this story and needs its own chemistry-enabled copy.
  - [ ] Run via Slurm (never the login node) and confirm `time_print` shows `cbmz_integrate` as a distinct, populated timer entry, separate from the already-registered `drydep_aero`/`drydep_gas`/`chem_emission`/`emis_tend`/`che_init_bdy`/`chem_bdyin`/`chem_bdyval_*` labels.
  - [ ] While reviewing the run's timer table, sanity-check `n_of_nsubs` stays under `mod_service.F90`'s `maxnsubs = 100` cap (Story 1.1 found ~40 runtime-registered labels for a non-chemistry BATS run; this run adds chemistry's own support-routine labels plus `cbmz_integrate`, so headroom should still be comfortable, but confirm rather than assume).
- [ ] Task 5: Confirm zero overhead in a non-DEBUG production build (AC: #2)
  - [ ] Run the same chemistry-enabled fixture under a `--enable-profile` or default (non-DEBUG) build and confirm no `#ifdef DEBUG` code executes (no new timer output, no behavior change) — same verification style as Story 1.1's Task 2a/2b split between compile-time and runtime confirmation.

## Dev Notes

- **Routing:** this is a general RegCM5 Fortran instrumentation change — route through `hpc-dev-agent-hpc-software-developer` (Jacopo) per `project-context.md`'s skill-routing table, not ad hoc.
- **Existing instrumentation facility, unchanged from Story 1.1:** `Main/mpplib/mod_service.F90`, entirely `#ifdef DEBUG`-gated with a no-op stub in `#else` so non-DEBUG builds still link. Public API: `time_begin(name, indx)` / `time_end(name, indx, isize)`, `dbgslen = 64` fixed label length, `maxnsubs = 100` fixed timer-registry capacity.
- **Two existing conventions for the guard, pick the one matching zero-prior-use files (this story's case):**
  - `Main/radlib/rrtmg_lw_rad.F90`/`rrtmg_sw_rad.F90` (Story 1.1): unconditional `use mod_intkinds, only : ik4`, `#ifdef DEBUG`-guarded `use mod_service, only : time_begin, time_end, dbgslen`, `integer(ik4) :: indx = 0` (implicit `SAVE` via initializer) — used because those files had zero prior `mod_service` references. **This story's two target files are in the same situation** (neither currently references `mod_service` or `mod_intkinds`) — use this form.
  - `Main/chemlib/mod_che_drydep.F90`/`mod_che_emission.F90`/`mod_che_bdyco.F90` (pre-existing, this story's own subsystem): bare unconditional `use mod_service` at module level (these files already use it elsewhere for other subroutines), `integer(ik4), save :: idindx = 0` declared inside the `#ifdef DEBUG` block. Cited here only so the dev agent recognizes it as a *different*, also-valid local precedent — don't mix the two styles within the same file, and don't add a bare unconditional `use mod_service` to the KPP integrator files, since (unlike drydep/emission/bdyco) they need it for nothing else.
- **Per-column call-site instrumentation is the established, reviewed pattern in this exact subsystem — not a violation of "never inside a loop body."** `mod_che_chemistry::chemistry` calls `chemmain`/`chemmain_cb6` inside a triple-nested `k`/`i`/`j` grid loop (`Main/chemlib/mod_che_chemistry.F90`, `do k = kmin, kz; do i = ici1, ici2; do j = jci1, jci2; ... call chemmain(...)`), and `chemmain`/`chemmain_cb6` themselves call `integrate`/`INTEGRATE` inside their own adaptive `kron: do while (t < tend)` substep loop. This mirrors `mod_che_drydep.F90`'s `drydep_aero(i, ...)`, which is also called per-column and is already `time_begin`/`time_end`-instrumented at its own subroutine boundary. The rule from Story 1.1 ("never instrument inside a loop body") means: don't add timer calls *inside* a per-element computation inside `integrate`/`INTEGRATE`'s own body (e.g. inside `DLSODE`'s internal Newton iteration) — wrapping the whole `integrate`/`INTEGRATE` call at its own entry/exit, even though the caller invokes it repeatedly, is the correct and only established granularity.
- **`GAS_CB6r2` is currently dead code, unreachable from any build** — confirmed by inspection during story creation: `Main/chemlib/Makefile.am`'s `SUBDIRS = GAS_CBMZ_NEW` (no `GAS_CB6r2`), and `configure.ac`'s `AC_CONFIG_FILES` list generates `Main/chemlib/Makefile` and `Main/chemlib/GAS_CBMZ_NEW/Makefile` only — never `Main/chemlib/GAS_CB6r2/Makefile`, even though that directory has its own complete `Makefile.am` defining `libcb6.a`. `mod_cb6_main1::chemmain_cb6` (the driver that would call `INTEGRATE`) is never called from anywhere in `Main/`. This means AC #1's CB6r2 half can only be verified by code inspection matching the working CBMZ pattern, not by an actual DEBUG run — say so explicitly in the story's completion record rather than implying both mechanisms were runtime-verified equally.
- **No shipped fixture exercises gas-phase chemistry — this story's equivalent of Story 1.1's `irrtm` precondition.** `chemsimtype` (checked in `Main/chemlib/mod_che_common.F90`) selects among `'DCCB'`, `'CBMZ'`, `'POLLEN'`, `'DUST'`, `'SULF'`, etc.; only the `'CBMZ'` branch sets `igaschem = 1` and drives `mod_cbmz_main1::chemmain` → `integrate`. Every `Testing/*.in` fixture with `ichem = 1` uses `'DUST'` or `'SULF'`, not `'CBMZ'` — running one unmodified will add zero chemistry-integration timer entries, which would look like (but is not) a "no overhead" result.
- **Account/partition guardrail — trust `project-context.md`, not `prd.md`, on the mapping.** `prd.md`'s Cross-Cutting NFRs / HPC platform guardrail section states Intel↔`ICT26_MHPC_0`/NVHPC↔`ICT26_MHPC`; this is the stale, reversed pairing Story 1.1 found and had corrected. `project-context.md`'s current text (Intel→`dcgp_usr_prod`/account `ict26_mhpc`, NVHPC→`boost_usr_prod`/account `ict26_mhpc_0`) reflects the live `sacctmgr show associations` data and is authoritative.
- **Scope boundary:** do not touch RRTMG timing (Story 1.1, done) or diagnostic-I/O gather/write timing (Story 1.3, backlog) — separate stories, separate files. Do not wire `GAS_CB6r2` into the build system (see above) or attempt any GPU-porting-related change — KPP/DLSODE chemistry is explicitly excluded from this program's GPU-porting scope (`ARCHITECTURE.md` §7: "data-dependent, irregular iteration structure is a known poor fit for SIMT execution"), so this is evidence-gathering only, same framing as Story 1.1.
- **Numerical reproducibility:** pure instrumentation (timing calls only, no algorithmic change) — expected bit-exact in both DEBUG and non-DEBUG builds. Any output difference after this change is a defect in the instrumentation, not an expected side effect.
- **Record all four acceptance-criteria categories in the commit/PR description** (project convention, not optional): **Build** — which compiler(s); **Test** — which fixture (state it's a modified/new chemistry-enabled copy, not a shipped `Testing/` fixture as-is) and process count; **Numerical** — state bit-exact explicitly; **Performance/overhead** — confirm no measurable overhead in production builds, not claimed from intuition.

### Project Structure Notes

- Target files live under `Main/chemlib/GAS_CB6r2/` and `Main/chemlib/GAS_CBMZ_NEW/` — subdirectories of `Main/chemlib/` (chemistry/aerosol library, per project convention that `Main/` owns model core + physics libs).
- No new files created for the instrumentation itself — only `#ifdef DEBUG` blocks and conditional `use` lines added to the two existing KPP-generated integrator files.
- `GAS_CB6r2`'s absence from the build system (`configure.ac`, `Main/chemlib/Makefile.am`) is a pre-existing structural gap, not something this story's scope extends to fixing — flagged in Dev Notes, not remediated here.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` Story 1.2, lines 232-246] — verbatim user story and acceptance criteria
- [Source: `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` FR-2] — requirement and testable consequence
- [Source: `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` Cross-Cutting NFRs, "DEBUG-only instrumentation overhead" — NFR-4 in `epics.md`'s Requirements Inventory] — zero-overhead-in-production constraint
- [Source: `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` HPC platform guardrail] — stale/reversed Intel↔NVHPC account mapping; superseded by `project-context.md`
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE.md` §7] — KPP/DLSODE chemistry explicitly excluded from GPU-porting scope; this story is evidence-gathering only
- [Source: `Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90:78-145`] — `SUBROUTINE INTEGRATE`, single exit, no `mod_service`/`mod_intkinds` currently in scope
- [Source: `Main/chemlib/GAS_CBMZ_NEW/mod_cbmz_integrator.F90:145-193`] — `subroutine integrate`, single exit, no `mod_service`/`mod_intkinds` currently in scope
- [Source: `Main/chemlib/GAS_CB6r2/mod_cb6_Main.F90:221-227`; `Main/chemlib/GAS_CBMZ_NEW/mod_cbmz_main.F90` (`chemmain`/`kron` loop)] — the adaptive substep loop that calls `INTEGRATE`/`integrate`; confirms call-site granularity
- [Source: `Main/chemlib/mod_che_chemistry.F90:41-103`] — `chemistry` subroutine's `k`/`i`/`j` grid loop calling `chemmain`; confirms per-column call-site precedent already used by `drydep_aero`
- [Source: `Main/chemlib/mod_che_drydep.F90:359-392`, `Main/chemlib/mod_che_emission.F90:47-72`, `Main/chemlib/mod_che_bdyco.F90:110-119`] — existing chemistry-subsystem DEBUG-instrumentation convention (bare `use mod_service`, `save`-declared local `idindx`) — the story's "already-instrumented chemistry support routines"
- [Source: `Main/chemlib/mod_che_common.F90:210,360-393`] — `chemsimtype` string namelist variable; confirms `'CBMZ'` is the branch that sets `igaschem = 1` and is the only mechanism reachable at runtime
- [Source: `Main/chemlib/Makefile.am:21`; `configure.ac:998`; `Main/chemlib/GAS_CB6r2/Makefile.am`] — confirms `GAS_CB6r2` is not built by the current autotools chain
- [Source: `Testing/test_008.in:82,93`, `Testing/test_011.in`, `Testing/test_013.in`] — confirms no shipped fixture uses `chemsimtype = 'CBMZ'`
- [Source: `RegCM-data/EURR12/EUR12_task2b.in`] — Story 1.1's real-data fixture, confirmed to have no `ichem` line (defaults off) and therefore not directly reusable for this story
- [Source: `_bmad-output/implementation-artifacts/1-1-instrument-rrtmgs-compute-core.md`, Dev Notes and Completion Notes] — DEBUG-guard convention precedent, `maxnsubs` capacity precedent, real-fixture-construction precedent (placeholder-path workaround), corrected account/partition mapping
- [Source: `_bmad-output/project-context.md` §Debug facility, §Custom BMAD Tooling & Skill Routing, §Agent Operating Constraints] — DEBUG macro convention, skill routing, corrected Slurm account/partition mapping

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
