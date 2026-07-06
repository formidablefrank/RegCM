---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-07-06'
stepsCompleted: ['document-discovery', 'prd-analysis', 'epic-coverage-validation', 'ux-alignment', 'epic-quality-review', 'final-assessment']
status: 'complete'
files_included:
  prd: '_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md'
  architecture_spine: '_bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE-SPINE.md'
  architecture_narrative: '_bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE.md'
  epics: '_bmad-output/planning-artifacts/epics.md'
  ux: null
---

# Implementation Readiness Assessment Report

**Date:** 2026-07-06
**Project:** RegCM

## Document Inventory

**PRD:**
- `prds/prd-RegCM-2026-07-04/prd.md` (92,514 bytes, modified 2026-07-05 19:53) — whole document, used for assessment

**Architecture (companion pair):**
- `architecture/architecture-RegCM-2026-07-04/ARCHITECTURE-SPINE.md` (26,121 bytes, 2026-07-05 22:59) — terse decision record, used for assessment
- `architecture/architecture-RegCM-2026-07-04/ARCHITECTURE.md` (22,295 bytes, 2026-07-05 22:56) — narrative companion, used for assessment

**Epics & Stories:**
- `epics.md` (86,204 bytes, modified 2026-07-06 02:37) — whole document, used for assessment

**UX Design:**
- Not found. Treated as not applicable — RegCM is a batch HPC scientific model with no user interface.

**Duplicates found:** none

## PRD Analysis

*Source: `prds/prd-RegCM-2026-07-04/prd.md`, read in full (650 lines). The PRD numbers FRs globally FR-1 through FR-38 as stable IDs, not sequential by document position (FR-33 through FR-38 were added later into earlier features); that numbering is preserved as-is below rather than renumbered.*

### Functional Requirements

**Feature 4.1 — Profiling and Evidence Baseline**
- **FR-1**: Instrument RRTMG's compute core (`mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, `rrtmg_sw_rad.F90`) with DEBUG-gated `time_begin`/`time_end` timing, complemented by a `perf`/Nsight profiling pass on at least one non-CLM-coupled configuration, to confirm or correct RRTMG's cost share now that the source thesis found no RRTMG hotspot in the CLM4.5-coupled case.
- **FR-2**: Instrument KPP-generated chemistry integrator entry points (e.g. `mod_cb6_Integrator.F90`, `mod_cbmz_integrator.F90`) with DEBUG-gated timing, distinguishing integration time from other already-instrumented chemistry support routines.
- **FR-3**: Instrument the diagnostic-output gather (`grid_collect`) and NetCDF-write phases in `Main/mpplib/mod_ncout.F90`, separately measurable from compute time, specifically to feed FR-34's investigation of why parallel write measured slower than serial write in the source thesis.
- **FR-4**: Execute and profile a baseline run of a representative `Testing/` fixture on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC) partitions, building on (not repeating) the source thesis's existing profiling data, and record a short internal report referenced by Features 4.2 and 4.3.

**Feature 4.2 — I/O Scaling and Optimization**
- **FR-5**: Diagnostic/history output (`mod_ncout.F90`) can be written via PnetCDF when built with `--enable-pnetcdf`/`--enable-parallel-nc` and the run enables it; ships as a tested, documented option, not a promoted default, until FR-34 explains the thesis's measured parallel-write slowdown.
- **FR-6**: Serial gather-write remains the unmodified default fallback for builds without PnetCDF or runs that do not opt into parallel output, including `mpi-serial` builds.
- **FR-7**: Evaluate the existing pthread-backed `mod_async_netcdf.F90` facility against FR-4's baseline as a lower-effort alternative/complement to PnetCDF, producing a documented adopt/extend/leave-as-is recommendation with a measured percentage number.
- **FR-33**: Extend I/O-scaling scope to restart/checkpoint output (`mod_savefile.F90`) and land-model history output (CLM4.5/ECLM's own mechanism) alongside diagnostic/history output, so profiling and parallel-I/O improvements apply uniformly.
- **FR-34**: Dedicated investigation profiling all RegCM5 I/O paths (diagnostic/history, restart/checkpoint, land-model history, boundary-condition/ICBC input) at representative rank counts, that must first explain the source thesis's measured HDF5-parallel/PnetCDF-parallel-slower-than-serial finding before recommending parallel I/O as a default, and produce concrete optimization recommendations.

**Feature 4.3 — Selective GPU Acceleration**
- **FR-8**: Verify, for every `do concurrent` loop added or modified under this program, that it parallelizes (not merely compiles) under GNU, Intel, and NVHPC, added as a checklist item to the existing manual validation process; scoped to `do concurrent` loops specifically, not the four OpenACC-based hotspot ports.
- **FR-9**: Scoped investigation evaluating whether RRTMG's radiative-transfer kernels are likely to benefit from `do concurrent`/OpenACC porting, using FR-1's direct measurement and the ICON-A/PSrad precedent, producing a go/no-go recommendation before any RRTMG porting implementation begins.
- **FR-10**: Continue ongoing `do concurrent`-based GPU-porting work on `Main/mod_moloch.F90` under the existing strategy, each change meeting the full acceptance discipline (Build/Test/Numerical/Performance) and FR-8's cross-vendor verification, plus multi-process-count regression checks for stencil operations near tile boundaries.
- **FR-11**: Verify and document the existing GPU-direct halo-exchange implementation in `Main/mpplib/mod_mppparam.F90` (198 `!$acc` directive lines) — confirm it builds/runs correctly under current target versions (HPC-X 2.25), identify which exchange routines are GPU-direct-capable versus host-buffer-staged, and record results for FR-8 and FR-37.
- **FR-12**: Make the hardcoded `PGI_GPU_ARCH="ccnative"` build setting (`configure.ac:140`) a configurable option, preserving current auto-detect behavior when omitted.
- **FR-13**: Document the current OASIS3-MCT import/export field list against the live code (per `--enable-oasis`/`--enable-eclm`) and pass the project's standard regression comparison for a `Testing/` fixture exercising `--enable-oasis`. *(Listed under 4.4 in the PRD body but cross-referenced here for numeric continuity — see Feature 4.4 below.)*
- **FR-35**: Verify and document the existing GPU-porting work at full repository scope (90 files, 1,476 `!$acc` directive lines — not only the four thesis-documented hotspots) — confirm each already-validated ported subsystem builds/runs under current target versions, excluding MOLOCH (FR-10) and halo exchange (FR-11), which it cross-references.
- ~~**FR-36**~~: Retired — bit-exactness restoration for the four already-ported GPU hotspots is unnecessary; the project's established statistical-reproducibility precedent already governs GPU-ported code, and the four ports were never non-compliant.
- **FR-37**: Regression test enforcing the project's established statistical-reproducibility policy for CPU-to-GPU porting (`tas`/`ps` rMAD/rRMSE <~0.1%, `huss` <~5%, over a 7-model-day run), using FR-24's regression-diff tool and FR-25's per-field tolerance mechanism, applied by default to all new GPU-porting work (FR-9, FR-10, FR-11).

**Feature 4.4 — External Coupling Modernization**
- **FR-13**: Document the current OASIS3-MCT import/export field list against the live code (per `--enable-oasis`/`--enable-eclm`, distinguishing base-OASIS from ECLM-only fields), and pass the project's standard regression comparison for a `Testing/` fixture exercising `--enable-oasis`.
- **FR-14**: Document the current REGESM (`--enable-cpl`) import/export field list (`mod_update.F90`'s `imp_data`/`exp_data`), explicitly distinguished from the OASIS3-MCT field list, and pass the standard regression comparison for a `Testing/` fixture exercising `--enable-cpl`.
- **FR-15**: Document CLM4.5 and ECLM as the supported-going-forward land-model coupling tier; mark CLM3.5 formally deprecated (no further feature investment, bug-fix-only if at all) in code comments and user-facing documentation.
- **FR-16**: Produce a CISM (Community Ice Sheet Model) coupling interface design — field list, coupling cadence, build gating (new `--enable-*` option) — before any implementation begins. Implementation is explicitly out of scope.
- **FR-17**: Resolve BMI's dormant, internally-inconsistent implementation (`Main/mod_bmiregcm.F90`) to either (a) genuine CSDMS BMI 2.0 compliance with at least one real caller/test driver, or (b) formal deprecation and removal, with rationale documented; direction not pre-decided (Open Question 1).

**Feature 4.5 — Namelist, Build, and Compiler-Identity Hardening**
- **FR-18**: Check namelist variables naming a filesystem path (`dirglob`, `inpglob`, `dirter`, `inpter`, `dirclm`, `cmip6_inp`, equivalents) for existence immediately after the namelist read, failing fast with a clear diagnostic naming the offending variable/path.
- **FR-19**: Investigate whether the absence of `relmem` deallocation outside three call sites causes measurable memory growth in long-running/ensemble jobs, with remediation scoped only if a real issue is confirmed (not presupposed).
- **FR-20**: Give NVHPC (`nvfortran`) its own `COMPILER_NVHPC` identity in the build system, distinct from `COMPILER_PGI`, without changing any currently-applied compiler flags or behavior.

**Feature 4.6 — Documentation Modernization**
- **FR-21**: Correct the developer guide's stale precision claims (hardcoded 64-bit `dp`) and module-lifecycle claims (`init_mod_*`/`release_mod_*`) to match the codebase's actual `rkx`/`allocate_*`/`getmem`/`relmem` pattern — applies to both `Doc/DeveloperGuide/MainDeveloperGuide.tex` and `project-context.md`'s own Module Skeleton section.
- **FR-22**: Produce a GPU-porting and performance guidance document capturing the `do concurrent`-only accelerator strategy, measured per-subsystem risk tiering, the cross-vendor verification procedure (FR-8), and recommended validation sequencing.
- **FR-38**: Adopt FORD (Fortran Documenter) to generate browsable HTML API documentation (module/procedure cross-references, call graphs) for at minimum `Main/`, `Share/`, and `PreProc/`, complementary to (not replacing) FR-21's narrative guide; coverage grows incrementally as this program's own FRs touch code, not via a full-codebase retrofit.
- **FR-23**: Update namelist documentation (e.g. `Doc/README.namelist`) to reflect the CLM3.5 deprecation (FR-15) and explicitly warn that several `Testing/*.in` fixtures ship with literal placeholder paths requiring edits before use.

**Feature 4.7 — Automated Regression Infrastructure**
- **FR-24**: Provide a single invocable tool — hardening the source thesis's existing `concat_diff_var.py`/`multi_day_stats_generic.py`/`spatial_maps_generic.py` workflow — that runs a specified `Testing/` fixture (or accepts a pre-existing output pair) and reports field-by-field differences against a trusted baseline, replacing manual NCO/CDO comparison; supersedes and retires the dead `BuildBot/testing.py` and narrow `preproc-compare.py`.
- **FR-25**: Support an explicit per-field tolerance specification in MAD/RMSE/rMAD/rRMSE terms, reflecting the project's two-tier policy: CPU-only changes default to bit-exact (zero-tolerance) unless regcm5-dev records an exception; GPU-ported fields default to the thesis-established statistical bounds (FR-37) unless regcm5-dev tightens them.
- **FR-26**: Support running, or accepting output from, the same fixture at more than one process count and comparing results, per the project's stencil/halo multi-rank regression rule.
- **FR-27**: Store trusted baseline outputs for each `Testing/` fixture in a defined, documented location, with a written procedure for updating a baseline that requires an explicit regcm5-dev sign-off record, not a silent overwrite.

**Feature 4.8 — Containerization for Multi-System GPU Portability**
- **FR-28**: Provide a Docker/OCI image for each CPU-path compiler vendor (GNU, Intel) that builds RegCM5 from source and produces a runnable binary; each image's output agrees within the cross-vendor bit-exact-by-default policy against the same `Testing/` fixture used in FR-4/FR-24's baseline.
- **FR-29**: Ensure each Docker/OCI image variant (GNU, Intel, and the NVHPC/CUDA variant from FR-30) runs under Apptainer without a Docker daemon or root privileges on shared HPC systems including Leonardo, producing output matching the native-build baseline within tolerance.
- **FR-30**: Provide a third container variant supporting NVHPC/CUDA-accelerated execution (CUDA 12+), producing output from a `do concurrent`-accelerated build matching the CPU-path baseline within tolerance, on at least one system with a CUDA 12+ GPU.

**Feature 4.9 — GitHub CI/CD Automated Testing Pipeline**
- **FR-31**: Add a `.github/workflows/` pipeline that builds RegCM5 (at minimum GNU and Intel) and runs at least one small `Testing/` fixture through FR-24's regression-diff tool on every push and pull request, flagging build or regression failures before merge.
- **FR-32**: Run NVHPC build verification (compilation only) in GitHub Actions where a suitable toolchain is available; `do concurrent` parallelization verification (FR-8) and full GPU execution remain scoped to the HPC cluster's Slurm-based validation unless a self-hosted GPU runner is provisioned (resolved: none will be).

**Total active FRs: 37** (FR-1 through FR-38, minus retired FR-36; FR-13 appears once in the numbering — cross-referenced above under both 4.3's risk-register mention and its home in 4.4).

### Non-Functional Requirements

*The PRD does not use a separate `NFR-n` numbering scheme; NFRs appear as an unnumbered "Cross-Cutting NFRs" section plus "Feature-specific NFRs" per feature, and as a "Constraints and Guardrails" section. Extracted verbatim below, numbered here only for traceability during this assessment.*

**Cross-Cutting NFRs (§ Cross-Cutting NFRs):**
- **NFR-1 (Numerical reproducibility)**: Bit-exact by default for CPU-only changes; the established statistical-reproducibility policy (FR-25/FR-37) for CPU-to-GPU porting specifically. Any difference beyond whichever bar applies requires regcm5-dev's explicit scientific sign-off. Applies to every FR.
- **NFR-2 (Cross-vendor portability)**: Every change must build correctly under GNU, Intel, and NVHPC at minimum. `do concurrent` changes additionally require FR-8's parallelization verification, not build success alone.
- **NFR-3 (Zero behavior change for non-opted-in runs)**: FR-5/FR-6, FR-9/FR-10, and FR-13/FR-14 must not change output, behavior, or required configuration for a run that does not explicitly opt into the new capability.
- **NFR-4 (DEBUG-only instrumentation overhead)**: FR-1–FR-3's timing instrumentation must add zero overhead to non-DEBUG production builds.

**Feature-specific NFRs:**
- **NFR-5** (Feature 4.2): FR-5/FR-6's "adopt parallel write" framing is conditioned on FR-34's findings; any change to `mod_ncout.F90`, `mod_savefile.F90`, or CLM's history output must preserve existing output file format and variable naming for downstream consumers unless a run explicitly opts into a new mode.
- **NFR-6** (Feature 4.3): No FR in this feature may reduce numerical reproducibility below whichever bar applies as a side effect of pursuing performance.
- **NFR-7** (Feature 4.4): Field-list documentation produced under FR-13/FR-14/FR-16 is treated as the authoritative source for that contract going forward, superseding inference from source reading.
- **NFR-8** (Feature 4.8): A containerized build/run is additional validation and distribution surface, not a substitute for native validation on the target HPC partitions.
- **NFR-9** (Feature 4.9): A passing GitHub Actions run is necessary but not sufficient evidence of full acceptance discipline; final numerical/performance acceptance for physics/dynamics/accelerator changes still requires validation on target HPC partitions.

**Constraints and Guardrails (§ Constraints and Guardrails) — function as binding NFRs:**
- **NFR-10 (Scientific correctness guardrail)**: Every change is subject to Build/Test/Numerical/Performance acceptance discipline recorded in the commit/PR description; regcm5-dev is sole scientific reviewer and sign-off authority.
- **NFR-11 (HPC platform guardrail)**: Intel-compiled work validated on `dcgp_usr_prod`/`dcgp_qos_dbg` (account `ICT26_MHPC_0`); NVHPC-compiled work on `boost_usr_prod`/`boost_qos_dbg` (account `ICT26_MHPC`); login-node activity stays limited to planning/light tasks, all profiling/regression runs go through Slurm with conservative resource requests.
- **NFR-12 (Container/CI guardrail)**: A passing GitHub Actions check is necessary but not sufficient; containerized execution is additional surface, not a substitute for native HPC validation.
- **NFR-13 (Boundary-condition guardrail)**: FR-34's boundary-condition/ICBC input-I/O profiling must flag findings for regcm5-dev's review rather than silently "fixing" or "optimizing" anything it touches, even given a clear performance win.
- **NFR-14 (Portability guardrail)**: No FR may introduce a code path that only compiles or runs correctly under one compiler vendor, except an explicitly scoped vendor-specific investigation (e.g. FR-9), and even then the existing three-vendor build must remain green throughout.

**Total NFRs/Guardrails: 14** (4 cross-cutting + 5 feature-specific + 5 guardrails).

### Additional Requirements

- **Non-Goals (§5, 7 items)**: no new physics/numerics; no full OpenACC/CUDA Fortran rewrite; no GPU-porting of KPP/DLSODE chemistry; no further CLM3.5 investment; no CISM coupling implementation (design only); no mandatory full AMD/AOCC support; no self-hosted GPU CI runner committed.
- **Phased scope (§6)**: FRs are grouped into 4 phases (Foundation; I/O and Memory Hardening; Selective Acceleration and Containerization; External Coupling Modernization) with Phase 4 explicitly independent of technical sequencing.
- **Success Metrics (§7)**: SM-1 through SM-9, SM-12, SM-13 (primary/secondary) plus SM-C1/SM-C2 (counter-metrics) map to specific FR groups and are usable as acceptance-validation cross-checks against epic completion.
- **External Coupling Contracts table (§ External Coupling Contracts)**: current state and obligation for each of OASIS3-MCT, REGESM, CLM/CLM4.5/ECLM, CISM, BMI.
- **Technology and Dependency Targets (§ Technology and Dependency Targets)**: restates compiler/MPI/accelerator/I/O library target versions, flagging that the source thesis's validated environment is 1–2 versions behind current targets — relevant to FR-35's re-validation scope.
- **Open Questions (§8)**: 4 remain genuinely open (Q1 BMI direction, Q3 CISM sponsor, Q4 AMD trigger, Q5 external-collaborator process, Q10 multi-platform performance-portability anomaly) after 6 were resolved during PRD/architecture reconciliation.
- **Risk Register (§ Risk Register)**: 13 risks each mapped to a mitigating FR — usable as an independent cross-check that epic coverage addresses every named risk, not only every FR.

### PRD Completeness Assessment

- The PRD is unusually mature for this checkpoint: `status: final`, all Open Questions but 4 resolved with recorded rationale, retirements (FR-36) and corrections (FR-11, FR-35, FR-9) tracked explicitly rather than silently edited out.
- Every FR carries testable consequences and maps to a named user journey (UJ-1–UJ-3) or feature rationale — no bare, unverifiable requirement statements found.
- Traceability aids already exist in-document: the Risk Register and Success Metrics both cross-reference FR IDs, which sharpens (rather than substitutes for) the epic-coverage check in Step 3.
- One structural quirk to flag, not a defect: FR-13 is introduced by number inside Feature 4.3's risk-register narrative before its substantive definition under Feature 4.4 — both are captured above; epic coverage should trace to the Feature 4.4 definition as authoritative.
- No FR/NFR appears undefined, contradictory, or missing acceptance criteria as written. Completeness assessment: **PRD is ready to serve as the coverage baseline for Step 3.**

## Epic Coverage Validation

*Source: `epics.md`, read in full (1055 lines: Requirements Inventory, FR Coverage Map, 8 Epics, 39 Stories with acceptance criteria). Cross-checked both the document's own FR Coverage Map (lines 132–172) and the actual story-level acceptance criteria — a line in a coverage map is a claim, not evidence, so each PRD FR below is verified against the story text that is supposed to realize it, not just the map entry.*

### Coverage Matrix

| FR | PRD Requirement | Epic/Story Coverage | Status |
|---|---|---|---|
| FR-1 | Instrument RRTMG's compute core | Epic 1 / Story 1.1 | ✓ Covered |
| FR-2 | Instrument KPP chemistry integration | Epic 1 / Story 1.2 | ✓ Covered |
| FR-3 | Instrument diagnostic-output gather/write | Epic 1 / Story 1.3 | ✓ Covered |
| FR-4 | Baseline profiling run and published report | Epic 1 / Story 1.4 | ✓ Covered |
| FR-5 | Parallel NetCDF write for diagnostic/history output | Epic 3 / Story 3.3 | ✓ Covered |
| FR-6 | Serial gather-write remains the default fallback | Epic 3 / Story 3.3 | ✓ Covered |
| FR-7 | Evaluate async-netcdf as complementary optimization | Epic 3 / Story 3.1 | ✓ Covered |
| FR-8 | Cross-vendor `do concurrent` parallelization verification | Epic 7 / Story 7.4 | ✓ Covered |
| FR-9 | RRTMG GPU-porting feasibility investigation, go/no-go | Epic 7 / Story 7.5 | ✓ Covered |
| FR-10 | Continue MOLOCH dynamical-core GPU porting | Epic 7 / Story 7.3 | ✓ Covered |
| FR-11 | Verify existing GPU-direct halo exchange | Epic 7 / Story 7.2 | ✓ Covered |
| FR-12 | Configurable GPU target architecture | Epic 7 / Story 7.6 | ✓ Covered |
| FR-13 | OASIS3-MCT field-exchange documentation and regression | Epic 8 / Story 8.1 | ✓ Covered |
| FR-14 | REGESM field-exchange documentation and regression | Epic 8 / Story 8.2 | ✓ Covered |
| FR-15 | CLM land-model coupling support-tier clarification | Epic 8 / Story 8.3 | ✓ Covered |
| FR-16 | CISM coupling interface design | Epic 8 / Story 8.4 | ✓ Covered |
| FR-17 | Resolve BMI status | Epic 8 / Story 8.5 | ✓ Covered |
| FR-18 | File-path namelist existence validation | Epic 6 / Story 6.1 | ✓ Covered |
| FR-19 | Long-running memory-growth investigation | Epic 1 / Story 1.5 | ✓ Covered |
| FR-20 | NVHPC compiler-identity correction | Epic 6 / Story 6.2 | ✓ Covered |
| FR-21 | Correct stale precision/module-lifecycle documentation | Epic 4 / Story 4.1 | ✓ Covered |
| FR-22 | GPU-porting and performance guidance document | Epic 7 / Story 7.8 | ✓ Covered |
| FR-23 | User-facing namelist and run documentation | Epic 4 / Story 4.2 | ✓ Covered |
| FR-24 | Automated NetCDF regression-diff tool | Epic 2 / Story 2.1 (+ 2.3 retirement of legacy scripts) | ✓ Covered |
| FR-25 | Per-field tolerance policy support | Epic 2 / Story 2.1 (tolerance-table AC) | ✓ Covered |
| FR-26 | Multi-process-count comparison support | Epic 2 / Story 2.2 | ✓ Covered |
| FR-27 | Baseline management | Epic 2 / Story 2.4 | ✓ Covered |
| FR-28 | OCI/Docker build images, GNU and Intel | Epic 5 / Story 5.1 | ✓ Covered |
| FR-29 | Apptainer execution on HPC systems | Epic 5 / Story 5.2 | ✓ Covered |
| FR-30 | CUDA 12+ GPU-enabled container variant | Epic 5 / Story 5.3 | ✓ Covered |
| FR-31 | GitHub Actions build-and-test workflow | Epic 5 / Story 5.4 | ✓ Covered |
| FR-32 | NVHPC/GPU-path CI coverage, scoped to availability | Epic 5 / Story 5.4 (CI-scope AC) | ✓ Covered |
| FR-33 | Extend I/O scaling to restart and land-model output | Epic 3 / Story 3.2 (+ 3.4 evaluation) | ✓ Covered |
| FR-34 | I/O profiling and optimization investigation | Epic 3 / Story 3.4 | ✓ Covered |
| FR-35 | Verify/document full existing GPU-porting footprint | Epic 7 / Story 7.1 | ✓ Covered |
| ~~FR-36~~ | Retired in PRD (bit-exact restoration, superseded) | Correctly excluded — `~~FR-36~~: Retired — not mapped to any epic` | ✓ Correctly retired |
| FR-37 | Statistical-reproducibility regression test | Epic 7 / Story 7.7 | ✓ Covered |
| FR-38 | Adopt FORD for auto-generated API documentation | Epic 4 / Story 4.3 | ✓ Covered |

**FRs in epics but not in PRD:**

| FR | Epic/Story | Note |
|---|---|---|
| FR-39 | Epic 1 / Story 1.6 (Valgrind memory-leak/error check) | Added during epic-creation at franco's explicit request (per `epics.md` Overview, line 14) — not a PRD gap, a deliberately out-of-band addition. Flagged here per this step's protocol, not as a defect. Recommend a short PRD addendum entry or footnote so a future reader of the PRD alone doesn't miss that FR-39 exists — currently only discoverable via the epics document. |

### NFR/Guardrail Coverage (secondary check, beyond this step's core FR scope)

All 14 NFRs/guardrails extracted in Step 2 reappear in `epics.md`'s own Requirements Inventory (§NonFunctional Requirements, verbatim/paraphrased with identical numbering NFR-1–NFR-13, plus the same 5 process guardrails) and are substantively exercised in story acceptance criteria — e.g. NFR-4 cited in Stories 1.1/1.2/1.3/3.2; NFR-3/FR-6 in Story 3.3; NFR-7 in Story 8.1; NFR-8 in Story 5.3; NFR-9/AD-4 in Story 5.4; NFR-10 in Story 7.3; NFR-12/AD-19 in Story 3.4. NFR-11 (HPC platform guardrail) is addressed operationally (partition names appear throughout) but not cited by ID in any single story — reasonable, since it governs *how* work is executed on Slurm rather than being a deliverable a story completes.

### Missing Requirements

None. Every active PRD FR (37 of 37) traces to at least one epic and story with matching acceptance criteria. No FR is claimed covered in the map but actually absent from story text, and no FR is silently dropped.

### Coverage Statistics

- Total PRD FRs (active, excluding retired FR-36): **37**
- FRs covered in epics (verified at story level, not just the coverage map): **37**
- Coverage percentage: **100%**
- Additional FRs in epics beyond PRD scope: **1** (FR-39, disclosed and attributed to a direct franco request)
- NFRs/guardrails re-confirmed in epics: **14 of 14**

## UX Alignment Assessment

### UX Document Status

Not Found. Confirmed at Step 1's document discovery (no whole or sharded `*ux*.md` anywhere under `planning-artifacts/`) and re-confirmed here — no UI-related terms found describing an actual interface anywhere in the PRD, architecture, or epics.

### Is UX Implied?

No. Explicit statements across all three documents converge on the same conclusion, not merely an absence of evidence:
- **PRD §2.3**: "Lighter form used throughout: this is technical infrastructure work with a small, well-defined set of operator roles, not a UX-heavy product — each UJ is a single grounded sentence rather than a full scene." All three user journeys (UJ-1–UJ-3) describe a scientist or engineer running Slurm jobs and reading profiling/regression output, not interacting with any UI.
- **PRD §2.2 Non-Users**: explicitly excludes users of RegCM5's own Python post-processing tooling as out of scope for this program — the one component with any user-facing surface is explicitly not what this program touches.
- **Architecture (`ARCHITECTURE.md` §1)**: "RegCM5 is a Fortran HPC batch scientific model, not a service: it runs to completion as an SPMD MPI job, not as a long-lived process." No client, API, or interactive surface is described anywhere in either architecture document.
- **`epics.md` §UX Design Requirements**: states outright, "Not applicable — no UX design contract exists for this program. RegCM5 HPC Modernization is backend/infrastructure work... with no user interface."

This is a batch HPC scientific model invoked via namelist + Slurm submission; its "users" are namelist authors and log/output readers, not UI consumers. No FR across all 37 introduces a web, CLI-interactive, or GUI surface — even FR-24's regression-diff tool and FR-38's FORD documentation are non-interactive, script-invoked/generated artifacts.

### Alignment Issues

None — there is nothing to align, since no UX contract exists and none is implied by the PRD, architecture, or epics.

### Warnings

None. Absence of a UX document is not a gap for this project type; treating it as one would be a false positive against a project with no user interface.

## Epic Quality Review

*Applied the create-epics-and-stories standards (user value, epic independence, no forward dependencies, story sizing, AC quality) against all 8 epics and 39 stories in `epics.md`. One domain-adaptation note up front: the standard's red-flag list ("Infrastructure Setup," "API Development" = technical milestones with no user value) is calibrated for consumer/product software. RegCM5 is HPC scientific infrastructure whose PRD explicitly names its users as operator roles (regcm5-dev, a modeler, an integrator, a GPU-porting contributor) — every epic below was checked for a genuine named-persona benefit sentence, not given a pass merely because the domain is technical. 7 of 8 epics pass that check cleanly; the one exception is noted below, not waived.*

### Epic Structure Validation

| Epic | User-Value Framing | Independence | Verdict |
|---|---|---|---|
| 1. Profiling and Memory Evidence Baseline | "Gives regcm5-dev a measured, not inferred, picture..." — named persona, concrete benefit | Standalone; explicitly requires nothing from later epics | ✓ Pass |
| 2. Automated Regression Infrastructure | "Any developer runs one command to get..." — named persona, concrete benefit | Standalone | ✓ Pass |
| 3. Diagnostic, Restart, and Land-Model I/O Scaling | "A modeler running CORDEX-scale simulations... can opt into..." | Backward dependency only, on Epic 1 (Stories 1.3/1.4) — correct direction | ✓ Pass |
| 4. Documentation Modernization | "A future contributor or external collaborator can trust..." | Standalone; stories mutually independent | ✓ Pass |
| 5. Multi-Vendor Containers and CI Gate | Epic-level summary is system-centric ("RegCM5 builds and runs as...") rather than persona-first — see Minor Concerns | Backward dependency only, on Epic 2 (regression tool for CI check) | 🟡 Pass with note |
| 6. Namelist and Build Hardening | "A modeler gets a fast, clear failure..." | Standalone; stories independent of each other | ✓ Pass |
| 7. Selective GPU Acceleration and Verification | "Whoever ports RegCM5 subsystems to GPU... gets a verified and documented..." | Backward dependency only, on Epics 1 and 2; internal story order explicitly justified (7.3 before 7.4 because FR-8 needs FR-10's loops to check) | ✓ Pass |
| 8. External Coupling Modernization | "An integrator coupling RegCM5 to OASIS3-MCT... gets a documented, regression-tested field-exchange contract..." | Explicitly "No technical dependency on Epics 1–7" | ✓ Pass |

No epic requires a higher-numbered epic to function. No circular dependencies found. All cross-epic references run backward (a later epic citing an earlier epic's already-completed output), which is the correct direction.

### Story Quality Assessment

- All 39 stories use proper "As a [named persona], I want..., So that..." framing — no "Setup all models"-style non-user stories found.
- Story sizing is reasonable throughout; large-sounding stories are explicitly scoped down where needed (e.g. Story 4.3 excludes full FORD-comment retrofit across 590+ modules; Story 7.1 is an audit/verification task over regcm5-dev-already-validated code, not new implementation, which justifies its full-repository scope).
- Brownfield indicators are present and correct for this codebase: `epics.md` explicitly states "No starter/greenfield template applies," and Epic 8/Epic 2 both contain integration-with-existing-systems and migration/compatibility stories (coupling contracts; retiring legacy scripts), matching brownfield expectations.
- Database-table-creation-timing check: not applicable — no database exists in this HPC batch model.

### Dependency Analysis

**Within-epic story sequencing** — checked all 39 stories for forward references (an earlier story requiring a later, not-yet-completed story to function):

- No critical forward-dependency violations found. Every backward-looking "Given Story N.x completed" reference points to a lower-numbered story within the same epic (e.g. Story 2.3 correctly requires 2.1–2.2; Story 7.8 correctly requires 7.1–7.7 and is explicitly placed last "since it synthesizes this epic's own findings").
- Two soft, non-blocking cross-references were checked closely and found correctly handled rather than defective:
  - Story 4.2 (Epic 4) anticipates Epic 8's Story 8.3 (sequenced later) and explicitly hedges: "if Story 8.3 hasn't landed yet, it notes the code-level deprecation markers as pending" — this is conditional wording that keeps Story 4.2 independently completable regardless of Epic 8's timing, not a hard dependency.
  - Story 6.2 explicitly disclaims a dependency some might assume: "though that later story doesn't strictly require this one to land first" (re: Epic 7's configurable-GPU-architecture story) — good hygiene, ruling out a false dependency rather than creating one.
- One forward reference is a genuine, if minor, AC-testability issue — see Major Issues below (Story 5.2).

### Findings by Severity

#### 🔴 Critical Violations

None found.

#### 🟠 Major Issues

1. **Systematic Given/When/And instead of Given/When/Then across nearly all 39 stories.** The prescribed BDD structure is Given/When/Then; the actual convention used throughout `epics.md` closes almost every acceptance criterion with "**And** [outcome]" instead of "**Then** [outcome]" (e.g. Story 1.1 AC3: "...**When** the same code path executes **And** no additional timing overhead is observable"; the same pattern recurs in Stories 1.2, 1.3, 2.1, 3.2, and effectively every story in the document). This is cosmetic — the outcome is still stated unambiguously in every case checked, so testability itself is not impaired — but it is a structural deviation from the standard applied with total consistency (i.e., not a one-off typo but the document's actual house style), so it is flagged as Major rather than Minor. **Recommendation:** either accept this as the project's deliberate AC-writing convention (in which case it should be documented as such, e.g. in a stories-authoring note) or do a mechanical pass replacing the final "**And**" with "**Then**" in each AC group before implementation begins.

2. **Story 5.2's third acceptance criterion is not verifiable at the time Story 5.2 is completed.** It reads: "**Given** Story 5.3's NVHPC/CUDA variant, once it exists, **When** it is also converted to Apptainer, **Then** it runs the same way — this story's Apptainer mechanism is generic across all three variants, not GNU/Intel-specific." Story 5.3 does not exist yet when Story 5.2 is being completed (5.2 precedes 5.3), so this AC cannot actually be checked until 5.3 lands — it is a design-intent claim wearing AC clothing, not a testable acceptance criterion for Story 5.2 itself. **Recommendation:** move this claim into Story 5.3's own acceptance criteria (e.g. "Given the Apptainer mechanism established in Story 5.2, When the NVHPC/CUDA image is converted, Then it runs the same way without modification to that mechanism"), leaving Story 5.2 with only its two genuinely self-contained ACs.

#### 🟡 Minor Concerns

1. **Epic 5's epic-level summary is system-centric rather than persona-first**, unlike the other 7 epics: "RegCM5 builds and runs as GNU, Intel, and NVHPC/CUDA container images... and every pull request is automatically gated..." reads as a technical capability statement rather than "As a developer, I get...". This is cosmetic — the epic's own stories (5.1–5.4) each restore proper persona framing ("As a developer without RegCM5's exact library stack pre-provisioned...", "As an HPC user on a shared system...", "As a contributor opening a pull request...") — so no user-value gap actually exists underneath, only in how the epic's own one-line summary is phrased. **Recommendation:** reword Epic 5's summary line to lead with a persona, purely for internal consistency with Epics 1–4 and 6–8.

2. **Story 3.3's "not a promoted default" framing is revisited by Story 3.4's own acceptance criteria** ("Given this story completes, When Story 3.3's documentation is revisited, Then it is updated to reflect the conclusion"). Story 3.3 remains independently shippable as written (it ships the conservative, non-default framing on its own), so this is not a forward-dependency violation — but it is a soft coupling worth the implementer's awareness: Story 3.3's documentation is provisional pending Story 3.4's findings, and re-touching that documentation is technically part of Story 3.4's own scope, not an automatic side effect.

### Compliance Checklist Summary

| Check | Result |
|---|---|
| Epics deliver user value (named persona + benefit) | 7/8 clean; 1/8 (Epic 5) clean at story level, epic-summary phrasing only |
| Epic independence (no epic requires a later epic) | 8/8 pass |
| Story sizing appropriate | 39/39 pass |
| No forward dependencies breaking story independence | 38/39 pass (Story 5.2's AC3 flagged) |
| Acceptance criteria in proper Given/When/Then form | Systematic Given/When/And deviation — flagged as Major, not blocking |
| FR traceability maintained | 39/39 stories cite their FR(s) explicitly |
| Brownfield indicators present and correct | Confirmed — no starter template applies; integration/migration stories present |

## Summary and Recommendations

### Overall Readiness Status

**READY.**

The PRD, Architecture, and Epics/Stories for RegCM5 HPC Modernization are aligned and complete enough to begin Phase 1 implementation. Coverage is 100% (37 of 37 active FRs, verified at the story-acceptance-criteria level, not merely claimed in a coverage map), no epic depends on a later epic, and no critical structural defect was found across four assessment passes. The issues below are real but are polish-level — none blocks starting Phase 1, and each has a specific, low-effort fix.

### Critical Issues Requiring Immediate Action

None. No 🔴-severity finding was produced by any step of this assessment.

### Issues Worth Addressing (not blocking)

1. **🟠 Major — Systematic Given/When/And instead of Given/When/Then.** Nearly every acceptance criterion across all 39 stories closes with "**And** [outcome]" rather than "**Then** [outcome]." Cosmetic (outcomes remain unambiguous), but consistent enough to be the document's de facto house style rather than a typo. Fix: either document it as a deliberate convention, or do one mechanical pass before story hand-off.
2. **🟠 Major — Story 5.2's third acceptance criterion cannot be verified when Story 5.2 is completed**, since it asserts behavior for Story 5.3's not-yet-existing NVHPC/CUDA container. Fix: move that claim into Story 5.3's own acceptance criteria.
3. **🟡 Minor — Epic 5's epic-level summary is system-centric, not persona-first**, unlike the other 7 epics (its own stories are fine). Fix: reword the one summary line for consistency.
4. **🟡 Minor — Story 3.3 ships a provisional "not a promoted default" framing that Story 3.4 later revisits.** Not a forward-dependency defect (3.3 is independently shippable), but the implementer should know Story 3.3's documentation is provisional pending Story 3.4's findings.
5. **Disclosure, not a defect — FR-39 (Valgrind memory-leak/error check, Epic 1 / Story 1.6) exists in `epics.md` but not in the PRD.** Already transparently attributed there to a direct request from franco during epic creation. Recommend adding a short addendum note to the PRD itself so a future reader of the PRD alone isn't surprised by an FR in the epics that has no PRD-side origin.

### Recommended Next Steps

1. Before Phase 1 story hand-off, do the mechanical Given/When/Then pass across `epics.md` (or explicitly ratify the current And-terminated style as intentional) — cheap now, tedious to retrofit once stories are in flight.
2. When Story 5.3 is drafted/started, migrate Story 5.2 AC3's forward-looking claim into Story 5.3's own acceptance criteria, and drop it from 5.2.
3. Add a one-line addendum entry to the PRD recording FR-39's existence and origin, so the PRD and epics stay mutually self-explanatory without cross-referencing each other's history.
4. Proceed to Phase 1 (Epics 1, 2, 6, and the start of 4) — no planning-side blocker stands in the way.

### Final Note

This assessment identified 4 issues (2 Major, 2 Minor) across one category (Epic Quality Review) plus one disclosed-but-non-defective scope addition (FR-39), out of four assessment passes (Document Discovery, PRD Analysis, Epic Coverage Validation, UX Alignment, Epic Quality Review) covering 37 FRs, 14 NFRs/guardrails, 22 architectural decisions, 8 epics, and 39 stories. None of the identified issues blocks proceeding to implementation; all are addressable in parallel with, not before, Phase 1 work.

---

**Assessment completed:** 2026-07-06
**Assessor:** BMad Implementation Readiness workflow, on behalf of franco




