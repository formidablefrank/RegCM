---
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md
  - _bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE.md
  - _bmad-output/planning-artifacts/architecture/architecture-RegCM-2026-07-04/ARCHITECTURE-SPINE.md
---

# RegCM5 HPC Modernization - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the RegCM5 HPC Modernization program, decomposing FR-1 through FR-38 (PRD, 9 features, 4 phases) and the 22 architectural decisions (AD-1 through AD-22, Architecture Spine) into implementable stories, plus FR-39 (Valgrind memory-leak/error checking), added during this workflow at franco's request and not present in the PRD. There is no UX design contract — this is HPC batch-model infrastructure work with no user interface. `addendum.md` supplies implementation-level detail (file paths, options considered, known facts) used to sharpen individual stories' acceptance criteria; it does not itself introduce requirements beyond the PRD's FRs.

**Epic and story numbers are stable identifiers, not positional.** Per a Sprint Change Proposal (2026-08-11, "resequencing"), this document's epic *order* was rearranged to reflect a recommended execution sequence — grouped and prioritized at franco's explicit request (testing, then containerization, then CI, then instrumentation, then documentation, then contribution guidelines, then refactoring, then GPU offloading, then remaining epics) — while every epic/story/FR number stays fixed, matching this program's existing rule that "the ID is the stable reference, not its position" (PRD §0). Read this document top to bottom for the recommended build order; use the numbers for cross-references.

## Requirements Inventory

### Functional Requirements

**Feature 4.1 — Profiling and Evidence Baseline**
- FR-1: Instrument RRTMG's compute core (`time_begin`/`time_end` plus a `perf`/Nsight pass) and confirm its measured wall-clock cost share on at least one non-CLM-coupled configuration (e.g. BATS-coupled or RCE), since the CLM4.5-coupled thesis profile found no RRTMG hotspot and that finding does not generalize on its own.
- FR-2: Instrument the KPP-generated chemistry integrator entry points (e.g. `mod_cb6_Integrator.F90`, `mod_cbmz_integrator.F90`) for each active mechanism, distinguishing integration time from already-instrumented chemistry support routines.
- FR-3: Instrument the diagnostic-output gather (`grid_collect`) and NetCDF-write phases in `Main/mpplib/mod_ncout.F90`, separately measurable for the serial, HDF5-parallel, and PnetCDF-parallel write paths, feeding FR-34's investigation.
- FR-4: Execute and publish a baseline profiling run (`perf` + Nsight Systems) of a representative `Testing/` fixture on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC), explicitly building on — not repeating — the source thesis's existing CLM4.5-coupled hotspot data (`getcape`/CAPE-CIN 54%, CLM-hydrology memset ~20%, `interp1d_r8` ~12%, `heatindex` ~8%).
- FR-19: Investigate whether unreleased `getmem` allocations (only 3 `relmem` call sites in all of `Main/`) cause measurable memory growth in long-running/ensemble jobs; scope remediation only if a real issue is confirmed.
- FR-39: Debug and check the code for memory leaks using Valgrind, complementing FR-19's `getmem`/`relmem`-focused investigation with a general memory-error/leak-detection pass.

**Feature 4.2 — I/O Scaling and Optimization**
- FR-5: Add PnetCDF-based parallel write support to diagnostic/history output (`mod_ncout.F90`), shipped as a tested, documented, opt-in capability — not a promoted default — pending FR-34's explanation of the thesis's measured parallel-write slowdown.
- FR-6: Preserve serial gather-write as the unconditional default and working fallback for builds without PnetCDF or runs that don't opt in, including `mpi-serial` builds.
- FR-7: Evaluate the existing `mod_async_netcdf.F90` facility against FR-4's baseline as a lower-effort alternative/complement to PnetCDF, producing a documented, quantified (not qualitative) recommendation.
- FR-33: Extend I/O-scaling scope to restart/checkpoint output (`Main/mod_savefile.F90`) and CLM4.5/ECLM land-model history output, alongside diagnostic/history output.
- FR-34: Profile all RegCM5 I/O paths (diagnostic, restart, land-model history, boundary-condition/ICBC input) at more than one rank count; explain, with FR-3's profiling evidence, why parallel write (HDF5-parallel and PnetCDF-parallel) measures consistently slower than serial write in the coupled configuration; produce concrete, conditioned optimization recommendations.

**Feature 4.3 — Selective GPU Acceleration**
- FR-8: Verify cross-vendor (GNU/Intel/NVHPC) `do concurrent` parallelization — not merely compilation — for every `do concurrent` loop touched under this program, with a documented procedure (`-Minfo=accel` and vendor equivalents) and correct per-vendor expectations (GNU has no GPU offload path for `do concurrent` at all).
- FR-9: Investigate RRTMG's GPU-porting feasibility using FR-1's direct measurement and the ICON-A/PSrad precedent as explicit inputs, producing a go/no-go recommendation before any implementation begins.
- FR-10: Continue MOLOCH's `do concurrent`-based GPU porting (`Main/mod_moloch.F90`) under the existing strategy, with full Build/Test/Numerical/Performance acceptance discipline and multi-process-count stencil/halo verification (`nproc=1` and `nproc=4`) for every change.
- FR-11: Verify and document the already-implemented GPU-direct halo exchange in `Main/mpplib/mod_mppparam.F90` (the `real8_2d/3d/4d_exchange` family) against current target versions (HPC-X 2.25), identifying which routines are GPU-direct vs. still host-buffer-staged.
- FR-12: Make the hardcoded `PGI_GPU_ARCH="ccnative"` build setting (`configure.ac:140`) a configurable option, preserving current auto-detect behavior when unset.
- FR-35: Document and verify the full existing GPU-porting footprint (90 files, 1,476 `!$acc` directive lines — not only the four thesis-documented hotspots) builds under current target versions, distinguishing thesis-validated from broader-NVIDIA-collaboration-validated provenance.
- ~~FR-36~~: Retired — bit-exact-restoration for the four already-merged GPU ports; superseded once the two-tier reproducibility policy (FR-25/FR-37) confirmed those ports were never non-compliant.
- FR-37: Add a regression test enforcing the established statistical-reproducibility policy for GPU-ported code (`tas`/`ps` rMAD/rRMSE < 0.1%, `huss` < 5%, over a 7-model-day run), using FR-24's tool and FR-25's tolerance mechanism.

**Feature 4.5 — Namelist, Build, and Compiler-Identity Hardening**
- FR-18: Validate namelist file-path variables (`dirglob`, `inpglob`, `dirter`, `inpter`, `dirclm`, `cmip6_inp`, equivalents) for existence immediately after namelist read, failing fast with a diagnostic naming the offending variable and path.
- FR-20: Give NVHPC (`nvfortran`) its own `COMPILER_NVHPC` identity in `configure.ac`, distinct from `COMPILER_PGI`, without changing any currently applied compiler flags or behavior.

**Feature 4.6 — Documentation Modernization**
- FR-21: Correct stale precision (`rkx`, not hardcoded `dp`) and module-lifecycle (`allocate_*`/centralized `getmem`/`relmem`, not `init_mod_*`/`release_mod_*`) claims in both the Dev Guide and `project-context.md` itself.
- FR-22: Write a GPU-porting and performance guidance document capturing the `do concurrent`-only strategy, measured per-subsystem risk tiering, FR-8's cross-vendor verification procedure, and recommended validation sequencing — written after Phase 3's findings exist.
- FR-38: Adopt FORD to generate browsable HTML API documentation (module/procedure cross-references, call graphs) for at minimum `Main/`, `Share/`, and `PreProc/`, with FORD-compatible comments added incrementally as this program's own FRs touch code — not a full-codebase retrofit.
- FR-23: Update user-facing namelist/run documentation (e.g. `Doc/README.namelist`) for the CLM3.5 deprecation (FR-15) and the `Testing/*.in` placeholder-path pitfall FR-18 now catches faster.
- FR-41: Provide container build/run documentation for users (running production images) and developers (using the same images to contribute), per FR-40.
- FR-48: Document `Tools/Programs` and `Tools/Scripts` utilities in one findable catalog.
- FR-49: Add build/dependency ergonomics for `Tools/` — top-level Makefile, `c++read` autotools normalization, per-group `requirements.txt`.
- FR-51: Provide a `CONTRIBUTING.md` contributor guide.
- FR-52: Provide `.github/` issue and pull-request templates.

**Feature 4.7 — Automated Regression Infrastructure**
*(Tools/Scripts/TestingAndBenchmarking/manage_baseline.py and regression_diff.py already exist in the working tree as a first cut — see Additional Requirements. Stories for this feature verify, harden, and wire these in rather than building from scratch.)*
- FR-24: Provide a single automated NetCDF regression-diff tool that runs a `Testing/` fixture (or accepts a pre-existing output pair) and reports field-by-field MAD/RMSE/rMAD/rRMSE against a trusted baseline, superseding manual NCO/CDO comparison and archiving/removing the dead `BuildBot/testing.py` and narrow `preproc-compare.py`.
- FR-25: Support an explicit per-field tolerance specification in the tool, expressed in MAD/RMSE/rMAD/rRMSE terms — bit-exact default for CPU-only-change fields, thesis-established statistical bounds for GPU-ported fields — with the applicable tier documented per comparison.
- FR-26: Support multi-process-count comparison (at minimum `nproc=1` and `nproc=4`) in a single invocation or documented short procedure, applying the identical tolerance table at each count.
- FR-27: Store trusted per-fixture baseline outputs in a defined, documented location with a written, sign-off-gated procedure for updating a baseline once an intentional change is reviewed and accepted.

**Feature 4.8 — Containerization for Multi-System GPU Portability**
- FR-28: Provide GNU and Intel OCI/Docker build images, each producing a working RegCM5 binary from a defined library stack on a clean host.
- FR-29: Run each container image variant (GNU, Intel, and — once available — NVHPC/CUDA) under Apptainer without a Docker daemon or root privileges on HPC systems including Leonardo.
- FR-30: Provide a third container variant supporting NVHPC/CUDA-accelerated execution (CUDA 12+), alongside the GNU/Intel images, following NVIDIA's devel-build/runtime-ship pattern.
- FR-40: Production container images (GNU, Intel, NVHPC/CUDA) double as the contributor development environment on a plain, non-HPC, non-GPU workstation — no separate lightweight image is maintained.

**Feature 4.11 — Contributor Unit Testing Framework**
- FR-42: Adopt pFUnit and establish a unit-test pattern, wired into the Autotools build, scoped to pure, side-effect-free routines only.
- FR-43: Author an initial unit-test suite for `getcape_new`, `interp1d_r8`, and `heatindex`.
- FR-44: Provide contributor testing documentation covering both the unit-test suite and Feature 4.7's integration/regression-diff tooling.
- FR-50: Unit and integration tests for `Tools/Programs` and `Tools/Scripts` (pFUnit/pytest for pure functions, integration smoke tests otherwise); depends on FR-49.

**Feature 4.12 — ADIOS2 I/O Backend**
- FR-45: Evaluate and design ADIOS2 integration — build flag, three per-path namelist switches, and a BP-vs-NetCDF comparison plan.
- FR-46: Implement ADIOS2 parallel write for diagnostic/history, restart/checkpoint, and CLM land-model output, opt-in per path.
- FR-47: Provide ADIOS2 backend documentation — build configuration, namelist usage, and reading/converting BP output.

**Feature 4.13 — Continuous Quality Gates: Performance, Memory-Safety, and Dependency Security**
- FR-53: Memory-leak and memory-safety regression gate — Valgrind-in-CI against Story 4.6's baseline, plus a sanitizer build.
- FR-54: Two-tier performance regression gate — CI smoke tier, required Slurm evidence for hot-path changes.
- FR-55: Dependency and container vulnerability scanning — `pip-audit` on `requirements.txt` changes, Trivy on container builds.

**Feature 4.14 — Code Duplication Audit and Generic-Interface Consolidation**
- FR-56: Audit source code for type- and rank-duplicated routines, producing a go/no-go inventory per candidate family.
- FR-57: Consolidate communication-layer duplicated routines (`mod_mppparam.F90`), compile-time mechanisms only, gated by FR-56.
- FR-58: Consolidate I/O-layer duplicated routines (`mod_ncout.F90`/`mod_ncstream.F90`), gated by FR-56 and sequenced after Epic 11/Epic 12.

**Feature 4.9 — GitHub CI/CD Automated Testing Pipeline**
- FR-31: Add a `.github/workflows/` pipeline that builds RegCM5 (at minimum GNU and Intel, via Feature 4.8's containers or equivalent) and runs FR-24's regression-diff tool against at least one small `Testing/` fixture on every push and pull request.
- FR-32: Run NVHPC compile-only verification in CI where a suitable toolchain is available; scope `do concurrent` parallelization verification (FR-8) and full GPU execution to HPC Slurm-based validation, with the workflow's documentation explicitly stating which vendors/paths CI validates versus which still require a manual/Slurm check.

**Feature 4.4 — External Coupling Modernization**
- FR-13: Document the current OASIS3-MCT (`--enable-oasis`/`--enable-eclm`) field-exchange list against live code and pass the project's standard regression comparison on a coupled-build `Testing/` fixture.
- FR-14: Document the current REGESM (`--enable-cpl`, `mod_update.F90`) field-exchange list against live code and pass the project's standard regression comparison on a coupled-build `Testing/` fixture.
- FR-15: Document CLM4.5/ECLM as the supported-going-forward land-coupling tier and CLM3.5 as formally deprecated, in code comments and user-facing documentation.
- FR-16: Produce a CISM (Community Ice Sheet Model) coupling interface design — field list, coupling cadence, build gating — without implementing it.
- FR-17: Resolve BMI's dormant status: either bring `mod_bmiregcm.F90` to genuine CSDMS BMI 2.0 compliance with at least one real caller/test proving it works, or formally deprecate and remove it, with rationale documented.

### NonFunctional Requirements

**Cross-cutting (apply to every FR):**
- NFR-1: Numerical reproducibility — bit-exact by default for CPU-only changes; the established statistical bounds (FR-25/FR-37) for CPU-to-GPU porting specifically; any excess beyond whichever bar applies requires regcm5-dev's explicit scientific sign-off.
- NFR-2: Cross-vendor portability — every change must build correctly under GNU, Intel, and NVHPC at minimum; `do concurrent` changes additionally require FR-8's parallelization verification, not build success alone.
- NFR-3: Zero behavior change for non-opted-in runs — FR-5/FR-6 (parallel I/O), FR-9/FR-10 (GPU porting), and FR-13/FR-14 (coupling) must not change output, behavior, or required configuration for a run that does not explicitly opt into the new capability.
- NFR-4: DEBUG-only instrumentation overhead — FR-1–FR-3's timing instrumentation must add zero overhead to non-DEBUG production builds, per the existing convention.

**Feature-specific:**
- NFR-5 (4.2 I/O): FR-5/FR-6's "adopt parallel write" framing is conditioned on FR-34's findings; any change to `mod_ncout.F90`, `mod_savefile.F90`, or CLM history output must preserve existing output file format and variable naming for downstream consumers unless a run explicitly opts into a new mode.
- NFR-6 (4.3 GPU): No FR in Selective GPU Acceleration may reduce numerical reproducibility below whichever bar applies as a side effect of pursuing performance.
- NFR-7 (4.4 Coupling): Field-list documentation produced under FR-13/FR-14/FR-16 is the authoritative source for that contract going forward, superseding inference from source reading; a breaking change to any live contract's field list requires explicit flagging, not routine review.
- NFR-8 (4.8 Containers): A containerized build/run is additional validation/distribution surface, not a substitute for native validation on the target HPC partitions.
- NFR-9 (4.9 CI): A passing GitHub Actions run is necessary but not sufficient evidence of full acceptance; final numerical/performance acceptance for anything touching physics, dynamics, or accelerator code still requires Slurm validation on `dcgp_usr_prod`/`boost_usr_prod`.

**Process guardrails (Constraints and Guardrails, PRD):**
- NFR-10: Scientific correctness guardrail — every change carries a Build/Test/Numerical/Performance acceptance record in its commit/PR description; regcm5-dev is the sole scientific reviewer and sign-off authority.
- NFR-11: HPC platform guardrail — Intel-compiled work validates on `dcgp_usr_prod`/`dcgp_qos_dbg` (account `ICT26_MHPC_0`); NVHPC-compiled work on `boost_usr_prod`/`boost_qos_dbg` (account `ICT26_MHPC`); login-node activity stays limited to planning/light tasks, with profiling/regression runs submitted through Slurm at conservative resource limits.
- NFR-12: Boundary-condition guardrail — FR-34's boundary-condition/ICBC input-I/O findings must be flagged for regcm5-dev's review rather than silently "fixed" or "optimized," even when a performance win looks obvious.
- NFR-13: Portability guardrail — no FR may introduce a code path that only compiles or only runs correctly under one compiler vendor, except an explicitly scoped vendor-specific investigation (e.g. FR-9's NVHPC-side work), and even then the three-vendor build must remain green throughout.
- NFR-14 (4.6/4.11/4.12 Documentation register): All documentation produced or corrected under this program is written in a register consistent with scholarly books and peer-reviewed journal articles — established words only, no invented terms, no fancy hyphenated compounds, short/simple/concise/direct, grammatically correct. Applies to every documentation-authoring story across Epics 2, 6, 7, and 12.
- NFR-15 (4.11 Unit testing): Unit-test scope is limited to pure, side-effect-free routines with no dependency on module-scope state from model initialization; stateful physics/dynamics/I/O code remains validated only by full-model integration runs (Feature 4.7) — narrows, not reverses, the project's existing testing-boundary rule.
- NFR-16 (4.12 ADIOS2): ADIOS2's BP format is not NetCDF-compatible by default; any "bit-exact against baseline" claim must state explicitly how the comparison was made (native BP-aware compare, or BP-to-NetCDF conversion first) — an unstated or assumed-compatible comparison is not acceptable evidence.
- NFR-17 (4.13 Performance gate): the CI tier is coarse and non-authoritative by design, per AD-4/NFR-9 — it may never be treated as sufficient evidence for a performance claim on its own; the Slurm-evidence tier remains required for hot-path changes.
- NFR-18 (4.13 Memory-safety gate): blocks only on new findings relative to Story 4.6's recorded baseline; pre-existing findings already logged as scoped follow-ups do not retroactively block unrelated merges.
- NFR-19 (4.14 Generic-interface consolidation): never introduces `class(*)`/`select type` runtime polymorphism into or near a `do concurrent`/OpenACC-offloaded code path (AD-26); a discovered behavioral divergence between previously-duplicated bodies is flagged for regcm5-dev's review, not silently fixed.

### Additional Requirements

*(From Architecture — ARCHITECTURE.md / ARCHITECTURE-SPINE.md)*

- No starter/greenfield template applies — this is brownfield modernization of an existing, mature Fortran codebase; Phase 1's first stories are foundation/evidence work, not scaffolding.
- **AD-1** Two-tier numerical reproducibility policy is the single tolerance table `regression_diff.py` must implement: bit-exact default; `tas`/`ps` rMAD/rRMSE < 0.1% and `huss` < 5% for GPU-ported fields specifically; no third tier; a newly GPU-ported field not yet in the table defaults to bit-exact until its own bound is added.
- **AD-2** Profiling method is fixed across all profiling stories: `perf --call-graph dwarf` (`-g` builds) + Brendan Gregg FlameGraph rendering for CPU; NVIDIA Nsight Systems for GPU/compiler-runtime symbol attribution; `-Minfo=accel` to confirm actual offload/data-movement behavior.
- **AD-3** `do concurrent` is the sole loop-parallelism construct; OpenACC escalation only after profiling shows `do concurrent` insufficient for a given kernel (already the merged pattern for the four confirmed hotspots); no OpenMP or CUDA Fortran track.
- **AD-4** A green GitHub Actions check (FR-31/FR-32) is necessary but not sufficient; final acceptance for physics/dynamics/accelerator changes requires Slurm validation on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC).
- **AD-5** GPU-port candidacy has no scoring formula — each subsystem (RRTMG, or any future candidate) gets its own scoped investigation and explicit go/no-go checkpoint.
- **AD-6** Each I/O output path gets its own independent `do_parallel_netcdf_<path>` namelist switch (`do_parallel_netcdf_in`/`_out` already exist for ICBC/restart); `mod_ncout.F90` (FR-5) must add one following that same naming pattern, not a different shape.
- **AD-7** Every native NVHPC build tests both `--enable-openacc-managed` and `--enable-openacc-stdpar` as equally-required build-matrix cells, not one default plus an occasional check.
- **AD-8** The canonical performance/I/O-scaling baseline is the EUR12 namelist (`/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/EUR12_namelist.in`, 275×275×36, ROTLLR, EURR-12) run at 2 nodes on `dcgp_usr_prod`; `Testing/EUR12_namelist.in` is a version-controlled documentation copy, not a competing reference; a claim not measured against this exact fixture/node-count/partition is not comparable evidence. (The fixture now shares the same `franco/RegCM-data/` subtree as AD-9/AD-10's baseline-output and profiling-artifact storage, just its own `EURR12/` subfolder alongside `baseline/` and `profiling/`.)
- **AD-9 / AD-10** Baseline and profiling artifacts are promoted only via `manage_baseline.py` (refuses overwrite without `--force`+`--reason`; appends every promotion to `PROMOTION_MANIFEST.jsonl`); live baselines/profiling data live at `$FAST/franco/RegCM-data/{baseline,profiling}` (no backup, 1 TB project quota, retention = project end + 6 months, currently untracked as a risk); superseded generations archive (never silently discarded) to `$WORK/franco/RegCM-archive/{baseline,profiling}` via `--archive-dir`/`--no-archive`.
- **AD-11** CI (FR-31) uses the separate, smaller `Testing/ideal.in` fixture (100×500×60, NORMER, no ICBC/lateral forcing) with its own in-repo, plain-git baseline — distinct from AD-8's canonical baseline.
- **AD-12 / AD-13** Multi-process-count regression standard is `nproc=1` and `nproc=4` specifically (not `nproc=2`, since RegCM5's auto-decomposition — `set_nproc`, `mod_mppparam.F90:1366-1399` — only splits both grid dimensions at `nproc>=4`); the identical tolerance table applies across process counts, with no separate looser tier for decomposition differences.
- **AD-14** GNU-compiled builds validate on `dcgp_usr_prod` alongside Intel (shared partition/QoS/account); NVHPC-compiled builds validate on `boost_usr_prod`; AMD/AOCC has no assigned partition (non-mandatory).
- **AD-15** NVHPC (26.3)/HPC-X (2.25)/CUDA (12.9)/all I/O libraries (HDF5 1.14.3, netCDF-C 4.9.2, netCDF-Fortran 4.6.1, PnetCDF 1.12.3) are hard-pinned identically across native builds and all container variants, each bump needing full regression evidence; GNU/Intel compiler versions are not hard-pinned — containers use the latest release verified compatible with the pinned I/O stack, re-checked at each rebuild.
- **AD-16** Exit-code convention applies identically to both tools: 0 = pass, 1 = genuine regression/policy failure (including an unreadable output file), 2 = usage/configuration error; `manage_baseline.py` never judges a regression, so every one of its error paths exits 2.
- **AD-17** I/O timing instrumentation naming convention (FR-3/FR-33) is `io_gather_<path>`/`io_write_<path>`/`io_wait_<path>`, `<path>` ∈ {`hist`, `rst`, `clm`} — naming is fixed now; the actual `time_begin`/`time_end` call insertion is a separate, not-yet-implemented Fortran change requiring the project's full acceptance discipline.
- **AD-18** FR-30's GPU container build follows NVIDIA's official multi-stage devel-build/runtime-ship pattern (HPC SDK Container Guide 26.3) — compile against the devel image, ship only the compiled binary and runtime dependencies; never ship the full devel SDK.
- **AD-19** The boundary-condition guardrail (NFR-12) explicitly extends to FR-34's I/O-scaling investigation of boundary-condition/ICBC input reads.
- **AD-20** GPU-direct halo exchange is already implemented and regcm5-dev-confirmed validated (`mod_mppparam.F90`'s `real8_2d/3d/4d_exchange` family, 51 `host_data use_device` occurrences) — FR-11 is verification/documentation of an existing implementation, not a fresh feasibility investigation or design task.
- **AD-21** All three container variants (GNU, Intel, NVHPC/CUDA) build from Ubuntu 24.04 base images, web-verified compatible with NVIDIA's published HPC SDK 26.3 devel image.
- **AD-22** Default OpenACC memory mode for an actual GPU production/profiling run is explicit device memory allocation (plain `--enable-openacc`, no `mem:managed`/`mem:unified`) — distinct from AD-7's build-matrix testing requirement, which still tests both managed and stdpar modes.
- **Existing infrastructure (verify/harden, don't rebuild):** `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` and `regression_diff.py` already exist in the working tree (currently untracked) as a working first cut of FR-24–FR-27, per the Architecture doc's own account ("built and tested this session"). Feature 4.7 stories scope to: confirm both tools work against `Testing/` fixtures per their documented interface, populate/extend the tolerance table (AD-1), commit the files, and wire `regression_diff.py` into FR-31's CI workflow — not a from-scratch build.
- **Documentation gap noted, not itself an FR:** `docs/bmad-source/index.md` — the source-document entry point `project-context.md` names as authoritative — does not yet exist in the repository. Worth a small housekeeping story under Feature 4.6 (FR-21/FR-38 neighborhood) so the governing rule and the actual repository state agree.
- **Addendum-sourced technical detail available for sharpening acceptance criteria** (not new requirements): the `do concurrent`/OpenACC porting hazard list (automatic-array allocation, module-scope+`pure`+`!$acc routine seq` helpers, explicit `!$acc data create(...)` for predictable data movement) for FR-9/FR-10/FR-11/FR-35 stories; the parallel-I/O-slowdown puzzle's known starting facts (sequential fastest, PnetCDF-parallel often slowest, at every tested rank count) for FR-34; the BMI options-considered table for FR-17; the RRTMG three-way options table (directive port / scheme replacement / no GPU porting) for FR-9; the `assignpnt` pointer-aliasing mechanism detail for any GPU-porting story; the OASIS3-MCT/REGESM field lists (superseded by FR-13/FR-14's own output once produced) as a starting point, not the final documented answer.

### UX Design Requirements

Not applicable — no UX design contract exists for this program. RegCM5 HPC Modernization is backend/infrastructure work (profiling, I/O, GPU acceleration, coupling contracts, regression tooling, containers, CI) with no user interface; the PRD itself frames user journeys as single-sentence operator interactions with a batch HPC model, not UI flows (PRD §2.3).

### FR Coverage Map

FR-1: Epic 4 - Instrument and measure RRTMG's compute core
FR-2: Epic 4 - Instrument KPP chemistry integration
FR-3: Epic 4 - Instrument diagnostic-output gather/write
FR-4: Epic 4 - Baseline profiling run and published report
FR-19: Epic 4 - Long-running memory-growth investigation
FR-39: Epic 4 - Valgrind memory-leak/error checking
FR-24: Epic 1 - Automated NetCDF regression-diff tool
FR-25: Epic 1 - Per-field tolerance policy support
FR-26: Epic 1 - Multi-process-count comparison support
FR-27: Epic 1 - Baseline management
FR-5: Epic 11 - Parallel NetCDF write for diagnostic/history output
FR-6: Epic 11 - Serial gather-write remains the default fallback
FR-7: Epic 11 - Evaluate async-netcdf as complementary optimization
FR-33: Epic 11 - Extend I/O scaling to restart and land-model output
FR-34: Epic 11 - I/O profiling and optimization investigation
FR-21: Epic 6 - Correct stale precision/lifecycle documentation
FR-23: Epic 6 - User-facing namelist and run documentation
FR-38: Epic 6 - Adopt FORD for auto-generated API documentation
FR-28: Epic 3 - OCI/Docker build images for GNU and Intel
FR-29: Epic 3 - Apptainer execution on HPC systems
FR-30: Epic 3 - CUDA 12+ GPU-enabled container variant
FR-31: Epic 3 - GitHub Actions build-and-test workflow
FR-32: Epic 3 - NVHPC/GPU-path CI coverage, scoped to availability
FR-18: Epic 5 - File-path namelist existence validation
FR-20: Epic 5 - NVHPC compiler-identity correction
FR-8: Epic 10 - Cross-vendor `do concurrent` parallelization verification
FR-9: Epic 10 - RRTMG GPU-porting feasibility investigation
FR-10: Epic 10 - Continue MOLOCH dynamical-core GPU porting
FR-11: Epic 10 - Verify existing GPU-direct halo exchange
FR-12: Epic 10 - Configurable GPU target architecture
FR-22: Epic 10 - GPU-porting and performance guidance document
FR-35: Epic 10 - Verify and document full existing GPU-porting footprint
~~FR-36~~: Retired - not mapped to any epic
FR-37: Epic 10 - Statistical-reproducibility regression test
FR-13: Epic 13 - OASIS3-MCT field-exchange documentation and regression
FR-14: Epic 13 - REGESM field-exchange documentation and regression
FR-15: Epic 13 - CLM land-model coupling support-tier clarification
FR-16: Epic 13 - CISM coupling interface design
FR-17: Epic 13 - Resolve BMI status
FR-40: Epic 3 - Production container images double as the contributor development environment
FR-41: Epic 6 - Container build/run documentation for users and developers
FR-42: Epic 2 - Adopt pFUnit and establish a unit-test pattern
FR-43: Epic 2 - Initial unit-test suite for representative pure routines
FR-44: Epic 2 - Contributor testing documentation (unit and integration)
FR-45: Epic 12 - Evaluate and design ADIOS2 integration
FR-46: Epic 12 - Implement ADIOS2 parallel write, opt-in, all output paths
FR-47: Epic 12 - ADIOS2 backend documentation
FR-48: Epic 6 - Tools/ scripts and programs documentation
FR-49: Epic 6 - Tools/ build and run ergonomics (Makefile, c++read normalization, requirements.txt)
FR-50: Epic 6 - Unit and integration tests for Tools/ scripts and programs (Story 6.6, relocated from Epic 2 on 2026-08-11)
FR-51: Epic 7 - Contributor guide for an open-source scientific codebase
FR-52: Epic 7 - Issue and merge-request rules and templates
FR-53: Epic 8 - Memory-leak and memory-safety regression gate
FR-54: Epic 8 - Two-tier performance regression gate
FR-55: Epic 8 - Dependency and container vulnerability scanning
FR-56: Epic 9 - Audit source code for type- and rank-duplicated routines
FR-57: Epic 9 - Consolidate communication-layer duplicated routines
FR-58: Epic 9 - Consolidate I/O-layer duplicated routines (sequenced after Epic 11/Epic 12)

## Epic List

*Recommended execution order (see the Overview note above on stable numbering vs. position). Franco's priority: testing, then containerization, then CI, then instrumentation, then documentation, then contribution guidelines, then refactoring, then GPU offloading, then remaining epics — with one explicit deviation: Epic 5 is elevated ahead of its literal "remaining" grouping (low-risk, and the original PRD itself notes FR-20 unblocks Epic 10's GPU work). A dependency audit on 2026-08-11 (second pass) found that an earlier placement of Epic 8 directly after Epic 5 — tried briefly at franco's request — put it ahead of three of its own dependencies (Epic 6's Story 6.5, Epic 7's Story 7.1); it is placed here instead, immediately after Epic 7, where every one of its dependencies is satisfied and no story needs a deferred-until annotation. A remaining exception, Epic 2's former Story 9.4 (needed Epic 6's Story 6.5), was resolved on a third pass (2026-08-11) not by reordering but by relocating the story itself into Epic 6, where the dependency is now internal to one epic — see Epic 6's Story 6.6. Epic 9's Story 9.3 (needs Epic 11 and Epic 12) remains a genuine exception, individually flagged where it occurs, since moving Epic 9 later would misplace Stories 9.1/9.2, which have no such dependency.*

### Epic 1: Automated Regression Infrastructure
Any developer runs one command to get an automated, tolerance-aware, multi-process-count regression comparison against a trusted baseline, replacing manual NCO/CDO comparison and the dead `BuildBot/testing.py`/narrow `preproc-compare.py` scripts. Standalone; makes every later epic's Numerical/Test acceptance criteria mechanically checkable. Scoped as verify/harden/wire-in — `manage_baseline.py` and `regression_diff.py` already exist untracked in the working tree as a first cut.
**FRs covered:** FR-24, FR-25, FR-26, FR-27

### Epic 2: Contributor Testing Infrastructure
A contributor gets a fast, isolated pFUnit unit-test suite for RegCM5's pure utility routines alongside Epic 1's existing full-model regression tooling, with one document explaining which to run for which kind of change. Introducing a unit-test framework narrows, not reverses, the project's existing "integration-only" testing convention; Story 2.1 corrects that convention's documentation and carries regcm5-dev's explicit sign-off. No technical dependency on any of the original eight epics. Story 9.4 (`Tools/` unit and integration tests) moved to Epic 6 on 2026-08-11, since its only dependency (Epic 6's Story 6.5) sits there — eliminating a cross-epic dependency rather than merely flagging it.
**FRs covered:** FR-42, FR-43, FR-44

### Epic 3: Multi-Vendor Containers and CI Gate
A developer or HPC operator gets RegCM5 built and running as GNU, Intel, and NVHPC/CUDA container images under Docker or Apptainer on any compatible system, with every pull request automatically gated by a GNU+Intel build plus a regression-diff check before merge. Builds on Epic 1's regression-diff tool for its CI check; otherwise standalone — does not require Epic 10's GPU verification to package a container. Covers both the "containerization" and "CI" priority slots as one epic: Story 3.4 (CI) already depends internally on Stories 3.1/3.3 (the images it builds and tests), so containers-before-CI is the story order within this epic regardless.
**FRs covered:** FR-28, FR-29, FR-30, FR-31, FR-32

### Epic 4: Profiling and Memory Evidence Baseline
Gives regcm5-dev a measured, not inferred, picture of where compute time, I/O time, and memory go — RRTMG, KPP chemistry, diagnostic I/O gather/write, and long-running/leaked-memory behavior — on both the Intel (`dcgp_usr_prod`) and NVHPC (`boost_usr_prod`) partitions. Standalone: produces a published baseline report that Phases 2–3 (Epics 10 and 11) cite as their evidence base; requires nothing from any later epic.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-19, FR-39

### Epic 5: Namelist and Build Hardening
A modeler gets a fast, clear failure on a misconfigured namelist path instead of a downstream NetCDF error, and the build system correctly identifies NVHPC as its own compiler vendor rather than misreporting it as PGI. Standalone; both stories are independent of each other. Elevated ahead of its literal "remaining epics" grouping in this sequence: both stories are low-risk and foundational, and the original PRD itself states FR-20 is placed early "precisely because it unblocks any future NVHPC-specific work" — i.e., Epic 10's GPU acceleration work, which follows later in this sequence.
**FRs covered:** FR-18, FR-20

### Epic 6: Documentation Modernization
A future contributor or external collaborator can trust the developer guide's precision and module-lifecycle claims, browse FORD-generated API docs for the modules this program touches, get warned about namelist placeholder-path pitfalls before hitting them, find one document explaining how to build and run RegCM5 via its container images, find a catalog and build ergonomics for the `Tools/` utilities, and get unit/integration test coverage for those same utilities. Six stories; 4.1–4.5 are mutually independent, and 4.6 (relocated from Epic 2 on 2026-08-11, since its only dependency is 4.5) depends on 4.5 within this same epic. Epic 8's Story 8.3 also depends on this epic's Story 6.5.
**FRs covered:** FR-21, FR-23, FR-38, FR-41, FR-48, FR-49, FR-50

### Epic 7: Community Contribution Process
A new contributor to this open-source scientific codebase finds a contribution guide plus issue and pull-request templates codifying what a good issue or merge request looks like. Extracted from Epic 6 (Documentation) into its own epic per franco's explicit priority split between "documentation" and "contribution guidelines." Standalone; its one story has no dependency of its own, but Epic 8's Stories 8.1/8.2 depend on it (see those stories) — both satisfied by this epic's position immediately before Epic 8.
**FRs covered:** FR-51, FR-52

### Epic 8: Performance, Memory-Safety, and Dependency Security Regression Gates
A pull request touching RegCM5 is automatically checked for gross performance regression and new memory-leak/memory-safety findings in CI, and gated on required Slurm-based performance evidence for changes touching profiled hotspots or dynamics/I/O/GPU code — extending Epic 4's Story 4.6 and Epic 3's Story 3.4 from one-time checks into continuously-enforced regression gates. Dependency and container images gain vulnerability scanning, scoped to what this codebase actually distributes. Builds on Epic 4 (Story 4.6, FR-4/AD-8 baseline), Epic 6 (Story 6.5's `requirements.txt`), Epic 7 (Story 7.1's pull-request template), and Epic 3 (Story 3.1/3.3 containers, Story 3.4 CI) — all satisfied earlier in this sequence, following the dependency audit noted above.
**FRs covered:** FR-53, FR-54, FR-55

### Epic 9: Code Duplication Audit and Generic-Interface Consolidation
A future contributor finds fewer hand-duplicated routine bodies to keep in sync in the communication and I/O layers, consolidated via compile-time mechanisms only — never runtime polymorphism near GPU-offloaded code. Story 9.1 (audit) has no dependency and can start immediately; Story 9.2 (communication layer, `mod_mppparam.F90`) depends only on Story 9.1's go decision; Story 9.3 (I/O layer, `mod_ncout.F90`/`mod_ncstream.F90`) depends on Story 9.1 *and* on Epic 11's and Epic 12's own changes to those files landing first (both later in this sequence), to avoid concurrent edits confounding regression evidence.
**FRs covered:** FR-56, FR-57, FR-58

### Epic 10: Selective GPU Acceleration and Verification
Whoever ports RegCM5 subsystems to GPU (regcm5-dev or an external collaborator) gets a verified and documented existing GPU-porting footprint, a measurement-grounded go/no-go on RRTMG, continued cross-vendor-verified MOLOCH porting, a verified GPU-direct halo exchange, a configurable GPU target architecture, the statistical-reproducibility regression test enforcing the project's established tolerance policy, and a written guidance document capturing what this phase learned. Builds on Epic 4's baseline (FR-4) and Epic 1's regression tool (FR-37), both satisfied earlier in this sequence; also benefits from Epic 5's FR-20 (NVHPC compiler identity), immediately preceding it. Highest-uncertainty epic in the program, per the PRD's own framing.
**FRs covered:** FR-8, FR-9, FR-10, FR-11, FR-12, FR-22, FR-35, FR-37

### Epic 11: Diagnostic, Restart, and Land-Model I/O Scaling
A modeler running CORDEX-scale simulations at high rank counts can opt into parallel diagnostic, restart, and CLM land-model history output; gets an evidence-based explanation for the source thesis's measured parallel-write slowdown; and receives concrete, conditioned optimization recommendations — while every non-opted-in run keeps working exactly as before. Builds on Epic 4's I/O instrumentation (FR-3, satisfied earlier); stands alone otherwise. Not named in franco's explicit priority list — placed in the "remaining epics" group, ahead of Epic 12 and Epic 9's Story 9.3, both of which depend on it.
**FRs covered:** FR-5, FR-6, FR-7, FR-33, FR-34

### Epic 12: ADIOS2 I/O Backend Integration
A modeler or contributor opts into ADIOS2 as a diagnostic, restart, or CLM land-model output backend alongside the existing netCDF/PnetCDF path, with build and namelist documentation explaining how to enable and consume it, while every non-opted-in run keeps working exactly as before. Builds on Epic 11's per-path opt-in and naming conventions (immediately preceding) and Epic 1's regression tooling for its own comparison evidence; does not require Epic 11's Story 11.4 to complete first. Not named in franco's explicit priority list — placed in the "remaining epics" group.
**FRs covered:** FR-45, FR-46, FR-47

### Epic 13: External Coupling Modernization
An integrator coupling RegCM5 to OASIS3-MCT, REGESM, CLM, or a future CISM partner gets a documented, regression-tested field-exchange contract instead of one inferred from source; CLM3.5 is clearly marked deprecated; a CISM interface design exists for a future implementation phase; and BMI's dormant status is resolved one way or the other. No technical dependency on any other epic — sequenced last by priority choice, confirmed with franco during the original planning session and reaffirmed unchanged by this resequencing.
**FRs covered:** FR-13, FR-14, FR-15, FR-16, FR-17

## Epic 1: Automated Regression Infrastructure

Any developer runs one command for automated, tolerance-aware regression comparison, replacing manual NCO/CDO and the two dead/narrow legacy scripts. Standalone; makes every later epic's Numerical/Test acceptance criteria mechanically checkable. Scoped as verify/harden/wire-in — the tools already exist untracked.

### Story 1.1: Verify and Commit the Regression-Diff Tool

As a developer validating a RegCM5 change,
I want the existing `regression_diff.py` tool (currently untracked) verified against a real `Testing/` fixture and committed to version control,
So that automated, tolerance-aware regression comparison is the default Numerical/Test evidence method, not a script sitting outside git.

**Acceptance Criteria:**

**Given** `regression_diff.py` in its current, untracked state
**When** it is run against two runs of the same unchanged `Testing/` fixture (e.g. `test_001.in`) as `--run-dir`/`--baseline-dir`
**Then** it reports bit-exact agreement across all shared NetCDF fields and exits 0

**Given** the tool's per-field tolerance table (`tas`/`ps` rMAD/rRMSE < 0.1%, `huss` < 5%)
**When** a `--tolerance-file` overrides a subset of fields
**Then** the override is honored per-field, and every field not named in either the default table or the override defaults to bit-exact (AD-1)

**Given** the tool's own top-of-file comment documents a `compare` subcommand that doesn't exist in `main()`'s actual parser
**When** this story completes
**Then** the comment is corrected to match the real invocation (`--run-dir`/`--baseline-dir` on the top-level parser, no subcommand)

**Given** both scripts are currently untracked
**When** this story completes
**Then** `regression_diff.py` and `manage_baseline.py` are committed under `Tools/Scripts/TestingAndBenchmarking/`

### Story 1.2: Verify Multi-Process-Count Comparison

As a developer touching stencil or halo-exchange code,
I want `regression_diff.py --nprocs` verified against real output at `nproc=1,4,16,64,196`,
So that AD-12's fixed minimum pair is confirmed working end-to-end, and the tool is also proven at the higher rank counts this program's own I/O-scaling and GPU work will actually run at.

**Acceptance Criteria:**

**Given** a `Testing/` fixture run at `nproc=1,4,16,64,196`, each output placed under its own `nproc-<N>/` subdirectory of `--run-dir` and `--baseline-dir`
**When** `regression_diff.py --run-dir RUN --baseline-dir BASE --nprocs 1,4,16,64,196` is invoked
**Then** the single invocation reports a pass/fail comparison for all five process counts, applying the identical tolerance table to each (AD-13) — no looser tier at higher counts

**Given** the same unchanged fixture at every process count
**When** the comparison runs
**Then** it reports bit-exact agreement at all five, confirming no existing decomposition bug at higher rank counts before this tool becomes the project's default check

**Given** AD-12 fixes `nproc=1` and `nproc=4` as the required minimum pair
**When** `nproc=16/64/196` are added to this story's coverage
**Then** they are additional coverage beyond that minimum, not a replacement for it — a divergence appearing only at 16/64/196 (not at 1/4) is still a real regression, not a lower-priority one

### Story 1.3: Retire the Legacy Regression Scripts

As a developer looking for the project's regression tool,
I want the dead `Tools/Scripts/BuildBot/testing.py` (Python 2, non-runnable) and the narrow `preproc-compare.py` (ICBC v3/v4 only) moved to `Tools/Scripts/archive/` now that `regression_diff.py` supersedes them,
So that no one mistakes either leftover script for a working, general-purpose tool, while the code stays available for historical reference.

**Acceptance Criteria:**

**Given** `regression_diff.py` is verified (Stories 1.1–1.2) and committed
**When** this story completes
**Then** `testing.py` and `preproc-compare.py` are moved to `Tools/Scripts/archive/` (created if it doesn't yet exist), with a commit message recording their prior location and why they were archived — not deleted outright

**Given** a future contributor searches `Tools/Scripts/TestingAndBenchmarking/` and `Tools/Scripts/BuildBot/` for "the regression tool"
**When** they look
**Then** they find only `regression_diff.py`/`manage_baseline.py` in `TestingAndBenchmarking/`, with the legacy scripts relocated to `Tools/Scripts/archive/` and no longer in their original locations

### Story 1.4: Establish Trusted Baselines for Testing/ Fixtures

As a developer relying on `regression_diff.py` for acceptance evidence,
I want `manage_baseline.py promote` used to establish trusted baselines at `$FAST` for at least the fixtures this program's own FRs exercise,
So that FR-27 is satisfied by an actual populated baseline, not just tooling capable of promoting one.

**Acceptance Criteria:**

**Given** no baseline currently exists at `$FAST` (`franco/RegCM-data/baseline` doesn't yet exist)
**When** a `Testing/` fixture representative of FR-5/FR-6 (I/O), FR-10 (MOLOCH GPU), and FR-13/FR-14 (coupling builds) runs to completion
**Then** its output is promoted via `manage_baseline.py promote --run-dir RUN --baseline-dir $FAST/franco/RegCM-data/baseline [--nproc N]`, appearing in `PROMOTION_MANIFEST.jsonl` with the current RegCM git commit recorded

**Given** AD-8's canonical fixture copy `Testing/EUR12_namelist.in` does not currently exist in this repository
**When** this story completes
**Then** either the file is added, or the gap is explicitly flagged to regcm5-dev as a blocker for Epic 11's I/O-scaling claims — not silently assumed present

**Given** a second promotion attempt over an existing baseline
**When** `manage_baseline.py promote` runs without `--force`
**Then** it refuses the overwrite (AD-9), confirming the safety behavior works as documented, not only as read from source

## Epic 2: Contributor Testing Infrastructure

A contributor gets a fast, isolated pFUnit unit-test suite for RegCM5's pure utility routines alongside Epic 1's existing full-model regression tooling, with one document explaining which to run for which kind of change. Added via Sprint Change Proposal 2026-08-11, at franco's explicit request; no technical dependency on any of the original eight epics.

### Story 2.1: Adopt pFUnit and Establish a Unit-Test Pattern

As a contributor making a small, isolated change to a pure Fortran routine,
I want a pFUnit-based unit-test target wired into the Autotools build,
So that I can validate a single routine's correctness without running a full `Testing/` fixture.

**Acceptance Criteria:**

**Given** pFUnit (pFUnit4) added as a build dependency
**When** the unit-test target (e.g. `make check` or equivalent) runs
**Then** it builds and executes the unit-test suite, reporting pass/fail per test case, independent of any `Testing/` fixture

**Given** the bundled CLM3.5 pFUnit-style test directory already present in the tree (per the governing project context)
**When** this story's convention is established
**Then** it is documented as prior art informing, not directly reused from, the new RegCM5-owned unit-test target — CLM3.5 is deprecated (PRD §5) and is not a dependency of the new framework

**Given** the governing project context's Testing Rules section currently states "there's no meaningful unit vs. integration split... don't invent isolated unit tests for physics/dynamics routines that aren't validated against a real model run"
**When** this story lands
**Then** that section is corrected to describe the narrower scope this epic actually establishes: unit tests apply only to pure, side-effect-free routines with no module-state dependency; full-model integration runs remain the only validation for stateful physics/dynamics/I/O code — not a blanket reversal of the prior rule (NFR-15)

**Given** this is a testing-boundary policy change
**When** the story is accepted
**Then** its commit/PR record carries regcm5-dev's explicit sign-off, per NFR-10

### Story 2.2: Author Initial Unit-Test Suite for Representative Pure Routines

As a contributor learning the unit-test pattern,
I want an initial suite of unit tests covering `getcape_new`, `interp1d_r8`, and `heatindex` — the same three routines already confirmed `pure` under the project's merged GPU-offload pattern,
So that the pattern has concrete, working examples before other contributors are asked to add their own.

**Acceptance Criteria:**

**Given** `getcape_new` (`Share/mod_capecin.F90`), `interp1d_r8` (`Share/mod_interp.F90`), and `heatindex` (`Share/mod_heatindex.F90`)
**When** this story lands
**Then** each has at least one unit test exercising representative input/output pairs, independent of a full model run

**Given** a routine that is not pure, or depends on module-scope state populated only by model initialization
**When** candidates for this story are selected
**Then** it is excluded — this story does not force unit-test coverage onto stateful physics/dynamics code, matching Story 2.1's corrected scope (NFR-15)

**Given** the unit-test suite
**When** it runs against an unchanged codebase
**Then** all tests pass, establishing a clean starting baseline for future contributions

### Story 2.3: Contributor Testing Documentation (Unit and Integration Workflows)

As a contributor preparing a pull request,
I want one document explaining how to run both the new unit-test suite (Stories 2.1–2.2) and the existing regression-diff/baseline tooling (Epic 1), including which one applies to which kind of change,
So that I know exactly what to run before opening a pull request, without guessing.

**Acceptance Criteria:**

**Given** a contributor changing a pure utility routine
**When** they consult this documentation
**Then** it directs them to the unit-test suite (`make check` or equivalent) as the fast first check

**Given** a contributor changing stateful physics/dynamics/I/O code
**When** they consult this documentation
**Then** it directs them to Epic 1's `regression_diff.py` workflow against a `Testing/` fixture, per the project's established integration-only rule for that code category

**Given** NFR-14's documentation register
**When** this document is written
**Then** it uses established words only, no invented terms or fancy hyphenated compounds, and is short, simple, concise, direct, and grammatically correct

## Epic 3: Multi-Vendor Containers and CI Gate

A developer or HPC operator gets RegCM5 built and running as GNU, Intel, and NVHPC/CUDA container images under Docker or Apptainer on any compatible system, with every pull request automatically gated by a GNU+Intel build plus a regression-diff check before merge. Builds on Epic 1's regression-diff tool for its CI check; otherwise standalone — does not require Epic 10's GPU verification to package a container.

### Story 3.1: GNU and Intel OCI/Docker Build Images

As a developer without RegCM5's exact library stack pre-provisioned,
I want a Docker/OCI image for each of GNU and Intel that builds RegCM5 from source against a defined library stack, from a clean host,
So that I can get a working RegCM5 binary without an administrator having already set up the model's dependencies.

**Acceptance Criteria:**

**Given** a Docker/OCI image definition for the GNU variant
**When** it's built on a clean host with no RegCM5-specific system state beyond the container
**Then** it produces a working RegCM5 binary, built against the pinned I/O library stack (HDF5 1.14.3, netCDF-C 4.9.2, netCDF-Fortran 4.6.1, PnetCDF 1.12.3) and the latest GNU release verified compatible with that stack (AD-15)

**Given** the same for the Intel variant
**When** built
**Then** it produces a working binary too, using `FC=ifx F77=ifx CC=icx --disable-fortran-type-check` to build netCDF-Fortran/PnetCDF cleanly (the known Intel-specific configure issue, not a RegCM5 bug)

**Given** both images
**When** each runs the same `Testing/` fixture used in Epic 4's baseline / Epic 1's regression-diff tool
**Then** their outputs agree within the project's bit-exact-by-default cross-vendor portability policy

**Given** AD-21's requirement that all container variants share one base OS
**When** the GNU and Intel images are built
**Then** both use an Ubuntu 24.04 base image — establishing the shared-base convention Story 3.3's NVHPC/CUDA variant will also follow, verified independently when that story lands

**Given** FR-40's requirement that production images double as the contributor development environment
**When** each image is run under plain Docker on a non-HPC workstation, with no Slurm and no HPC-specific tuning
**Then** it builds and runs a `Testing/` fixture successfully — confirming the same image serves development, not only production validation, so no separate lightweight image is needed

### Story 3.2: Apptainer Execution on Leonardo

As an HPC user on a shared system without a Docker daemon or root access,
I want each Docker/OCI image variant runnable under Apptainer,
So that I can execute RegCM5 on Leonardo (or a comparable HPC system) without privileges the platform doesn't grant.

**Acceptance Criteria:**

**Given** the GNU and Intel OCI images (Story 3.1)
**When** each is converted to an Apptainer `.sif` image
**Then** it runs under a normal (non-root) HPC user account on Leonardo, without a Docker daemon

**Given** a `Testing/` fixture run through the GNU and Intel Apptainer images on Leonardo
**When** compared against the corresponding native-build baseline (Epic 1's `regression_diff.py`)
**Then** output matches within the project's existing tolerance policy (AD-1)

### Story 3.3: CUDA 12+ GPU-Enabled Container Variant

As someone running RegCM5 on a CUDA-capable system beyond Leonardo,
I want a third container variant supporting NVHPC/CUDA-accelerated execution, following NVIDIA's official devel-build/runtime-ship pattern,
So that a `do concurrent`-accelerated RegCM5 build is available as a portable image, not only as a Leonardo-specific native build.

**Acceptance Criteria:**

**Given** NVIDIA's HPC SDK Container Guide 26.3 devel/runtime multi-stage pattern (AD-18)
**When** the NVHPC/CUDA image is built
**Then** it compiles against the full devel SDK image, then copies only the compiled binary and its runtime dependencies into a separate runtime-stage image — the devel SDK itself is never shipped in the distributed image

**Given** the pinned stack (NVHPC 26.3, HPC-X 2.25, CUDA 12.9)
**When** the image is built
**Then** these versions are hard-pinned identically to the native NVHPC build (AD-15), from an Ubuntu 24.04 base (AD-21, matching NVIDIA's published `nvcr.io/nvidia/nvhpc:26.3-devel-cuda_multi-ubuntu24.04` image)

**Given** the GPU-enabled image
**When** it runs a `do concurrent`-accelerated RegCM5 build on at least one system with a CUDA 12+ GPU
**Then** output matches the CPU-path baseline within the project's two-tier tolerance policy (AD-1)

**Given** the same containerized image and the equivalent native NVHPC build on the same hardware
**When** wall-clock runtime is measured at `nproc=1,4,16,64,144,224`
**Then** the containerized run's overhead relative to native is documented as a measured percentage per process count — not assumed negligible just because the build/output-correctness checks passed

**Given** this container's GPU-side execution
**When** compared to native validation on `boost_usr_prod`
**Then** it's treated as additional validation/distribution surface, not a substitute for native HPC-partition validation (NFR-8)

**Given** Story 3.2's Apptainer conversion mechanism, established for the GNU and Intel images
**When** this NVHPC/CUDA image is also converted to Apptainer
**Then** it runs the same way, without modification to that mechanism — confirming it is generic across all three variants, not GNU/Intel-specific

**Given** FR-40's requirement that production images double as the contributor development environment, and this image's build against the full NVHPC/CUDA devel stack
**When** it is run under plain Docker on a workstation with no GPU present
**Then** it builds and runs a `Testing/` fixture via the CPU-only `-stdpar=multicore` path successfully — confirming a contributor without GPU hardware can still use this image for development, not only for GPU-execution validation

### Story 3.4: GitHub Actions Build-and-Test Workflow

As a contributor opening a pull request,
I want a `.github/workflows/` pipeline that builds RegCM5 (GNU and Intel via Story 3.1's containers, plus NVHPC compile-only verification where available) and runs Epic 1's regression-diff tool against `Testing/ideal.in` on every push and pull request, with the workflow's own documentation stating exactly which vendors/paths it validates,
So that a broken build or regression is flagged before merge, and a green check is never mistaken for full four-vendor-plus-GPU acceptance.

**Acceptance Criteria:**

**Given** a pull request that breaks the GNU or Intel build, or fails the regression-diff comparison against `Testing/ideal.in`'s stored baseline (AD-11)
**When** CI runs
**Then** the PR is flagged by a failing GitHub check before merge

**Given** a pull request touching only documentation or non-source files
**When** CI runs
**Then** it is not required to pass a full simulation run

**Given** `Testing/ideal.in`'s own in-repo, plain-git baseline (AD-11)
**When** CI runs the regression-diff tool
**Then** it compares against that baseline specifically — not AD-8's canonical EUR12 fixture, which is out of CI's scope entirely

**Given** a suitable NVHPC container/toolchain available to GitHub-hosted runners
**When** CI runs
**Then** it verifies NVHPC compilation succeeds — compile-only; `do concurrent` parallelization verification (Epic 10's FR-8) and full GPU execution remain exclusively the HPC cluster's own Slurm-based validation, not something CI attempts to replicate

**Given** the workflow's own documentation
**When** a contributor reads it
**Then** it states plainly which vendors/paths are validated in CI (GNU/Intel build+test, NVHPC compile-only) versus which still require a manual/Slurm check — so a green check is never mistaken for full four-vendor-plus-GPU acceptance (AD-4, NFR-9)

## Epic 4: Profiling and Memory Evidence Baseline

Gives regcm5-dev a measured, not inferred, picture of where compute time, I/O time, and memory go — RRTMG, KPP chemistry, diagnostic I/O gather/write, and long-running/leaked memory — on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC). Standalone: produces a published baseline report Epics 10 and 11 cite as evidence; requires nothing from any later epic.

### Story 4.1: Instrument RRTMG's Compute Core

As regcm5-dev (the model's scientific owner and profiling lead),
I want RRTMG's driver and radiative-transfer kernels wrapped in DEBUG-gated timing instrumentation, complemented by a `perf`/Nsight profiling pass on at least one non-CLM-coupled configuration,
So that I can confirm or correct RRTMG's actual wall-clock cost share instead of assuming the CLM4.5-coupled thesis finding ("not a hotspot") generalizes on its own.

**Acceptance Criteria:**

**Given** a DEBUG-enabled build of RegCM5
**When** `time_begin`/`time_end` wrap `mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, and `rrtmg_sw_rad.F90`'s entry points
**Then** a `Testing/` fixture run emits timing output attributable to RRTMG's core routines, not only its outer driver

**Given** a non-CLM-coupled configuration (e.g. BATS-coupled or the idealized RCE setup)
**When** a `perf --call-graph dwarf` + Nsight Systems profiling pass runs against it
**Then** the profile states RRTMG's measured wall-clock share, confirming or correcting the "not a hotspot" CLM4.5-coupled finding before it is generalized

**Given** a non-DEBUG production build
**When** the same code path executes
**Then** no additional timing overhead is observable, per the existing DEBUG-gating convention (NFR-4)

### Story 4.2: Instrument KPP Chemistry Integration

As regcm5-dev,
I want the KPP-generated chemistry integrator entry points (`mod_cb6_Integrator.F90`, `mod_cbmz_integrator.F90`) wrapped in DEBUG-gated timing for each active mechanism,
So that chemistry integration time is visible separately from already-instrumented chemistry support routines (drydep, emission, boundary).

**Acceptance Criteria:**

**Given** a DEBUG-enabled build with an active gas-phase mechanism (CB6r2 or CBMZ)
**When** a `Testing/` fixture exercising that mechanism runs
**Then** timing output separates integration time from the other, already-instrumented chemistry support routines

**Given** a non-DEBUG production build
**When** the same run executes
**Then** instrumentation adds no measurable overhead (NFR-4)

### Story 4.3: Instrument Diagnostic-Output Gather and Write

As regcm5-dev,
I want the gather (`grid_collect`) and NetCDF-write phases in `Main/mpplib/mod_ncout.F90` wrapped in DEBUG-gated timing, separately measurable across the serial, HDF5-parallel, PnetCDF-parallel, and async-netcdf write paths,
So that Epic 11's I/O investigation (FR-34) and its async-netcdf evaluation (FR-7) both have the profiling evidence they need.

**Acceptance Criteria:**

**Given** a DEBUG-enabled build
**When** a diagnostic-output write event occurs under each of the serial, HDF5-parallel, and PnetCDF-parallel paths
**Then** timing output separates I/O-rank gather time, write time, and compute-rank idle time during that event, for each path

**Given** the existing pthread-backed async-netcdf facility (`Share/mod_async_netcdf.F90`)
**When** a diagnostic-output write event occurs with async-netcdf enabled
**Then** timing output separately measures the same gather/write/wait phases for that path, so Epic 11's FR-7 evaluation has real profiling data instead of a qualitative impression

**Given** AD-17's fixed naming convention
**When** instrumentation calls are added
**Then** labels follow `io_gather_hist`/`io_write_hist`/`io_wait_hist` (the `hist` path only — `rst`/`clm` labels are Epic 11's FR-33 scope, not this story's); the async-netcdf path is distinguished within that same labeling scheme, not a separate naming convention

**Given** a non-DEBUG production build
**When** the instrumented code path executes
**Then** no additional overhead is observable (NFR-4), and instrumentation calls stay at gather/write/wait granularity — never inside a loop body

### Story 4.4: Baseline Profiling Run and Published Report

As regcm5-dev,
I want a baseline profiling run of a representative `Testing/` fixture executed and profiled on both `dcgp_usr_prod` and `boost_usr_prod`, building on — not repeating — the source thesis's existing CLM4.5-coupled profiling data,
So that Epics 10 and 11 cite measured evidence instead of the technical research note's structural inference.

**Acceptance Criteria:**

**Given** Stories 4.1–4.3's instrumentation is in place
**When** the baseline run executes on `dcgp_usr_prod` and `boost_usr_prod`
**Then** a short internal report states, per subsystem and per configuration, measured wall-time share on each partition — not an estimate — explicitly citing the source thesis's `getcape`/CAPE-CIN (54%), CLM-hydrology memset (~20%), `interp1d_r8` (~12%), and `heatindex` (~8%) findings for the CLM4.5-coupled case

**Given** the report is published
**When** Epic 10's FR-9 (RRTMG go/no-go) or any later story cites hotspot data
**Then** it cites this report and the source thesis, not the technical research note's structural inference

**Given** AD-2's fixed profiling method
**When** the profiling pass runs
**Then** it uses `perf --call-graph dwarf` (`-g` builds) with FlameGraph rendering, NVIDIA Nsight Systems for GPU/compiler-runtime symbol attribution, and `-Minfo=accel` to confirm offload behavior

### Story 4.5: Long-Running Memory-Growth Investigation

As regcm5-dev,
I want an investigation into whether unreleased `getmem` allocations (only 3 `relmem` call sites in all of `Main/`) cause measurable memory growth in long-running or ensemble-style jobs,
So that remediation is scoped only if a real issue is confirmed, not assumed.

**Acceptance Criteria:**

**Given** a long-running or CORDEX-scale `Testing/` fixture
**When** peak RSS is measured over the run's duration
**Then** a written finding states, with measured evidence, whether memory growth from unreleased `getmem` allocations is or is not a practical problem

**Given** the finding confirms a real issue
**When** remediation is scoped
**Then** it is defined as a follow-up story, not implemented blind under this story

**Given** the finding does not confirm a real issue
**When** the investigation concludes
**Then** no remediation work is scoped — the finding stands as the answer

### Story 4.6: Valgrind Memory-Leak and Error Check

As regcm5-dev,
I want RegCM5 checked for memory leaks and memory errors using Valgrind (Memcheck),
So that I have a general, tool-based memory-correctness pass complementing Story 4.5's `getmem`/`relmem`-specific investigation.

**Acceptance Criteria:**

**Given** a debug build of RegCM5 and a `Testing/` fixture sized for Valgrind's runtime overhead (e.g. `test_001.in` or `ideal.in`)
**When** the run executes under Valgrind's Memcheck tool
**Then** a written finding lists every distinct leak/error class Valgrind reports (definitely-lost, indirectly-lost, invalid read/write, uninitialized-value use), each with its call-stack location

**Given** a finding is a genuine leak or memory error
**When** it is recorded
**Then** it is logged as a specific, scoped follow-up — this story surfaces and documents, it does not fix

**Given** Valgrind's overhead makes a full production-scale run impractical
**When** a fixture is selected
**Then** the choice is documented as this story's scope, not silently assumed representative of production runs

**Given** Memcheck's own leak/error report (above) is the authoritative finding
**When** a visual, call-graph-level inspection pass is also wanted
**Then** the same fixture additionally runs under Valgrind's Callgrind tool, with its output (`callgrind.out.*`) opened in KCachegrind for visual inspection — noting KCachegrind visualizes Callgrind's call-graph/cost data, not Memcheck's leak report directly, so this is a complementary visual pass alongside, not a substitute for, Memcheck's own leak/error findings above

## Epic 5: Namelist and Build Hardening

A modeler gets a fast, clear failure on a misconfigured namelist path instead of a downstream NetCDF error, and the build system correctly identifies NVHPC as its own compiler vendor rather than misreporting it as PGI. Standalone; both stories are independent of each other.

### Story 5.1: Fail Fast on Invalid Namelist File Paths

As a modeler starting a run,
I want namelist variables naming a filesystem path (`dirglob`, `inpglob`, `dirter`, `inpter`, `dirclm`, `cmip6_inp`, and equivalents) checked for existence immediately after the namelist read,
So that I get a clear, immediate diagnostic naming the offending variable and path, instead of a confusing downstream NetCDF/IO error inside `checkncerr`/`fatal`.

**Acceptance Criteria:**

**Given** a namelist with a placeholder or mistyped path variable (e.g. an unedited `Testing/*.in` fixture)
**When** the run starts
**Then** it fails immediately at startup with a message identifying the specific namelist variable and the path it pointed to, not a downstream NetCDF error

**Given** all current `Testing/` fixtures, correctly edited (real paths substituted for placeholders)
**When** they start
**Then** they are unaffected by this validation — no false positives on valid paths

**Given** the full set of path-naming namelist variables (`dirglob`, `inpglob`, `dirter`, `inpter`, `dirclm`, `cmip6_inp`, and equivalents)
**When** the check runs
**Then** every one of them is checked, not just a subset

### Story 5.2: Correct NVHPC Compiler-Identity Detection

As a build-system maintainer,
I want `configure.ac`'s compiler-vendor detection to give `nvfortran`/`nvf9*` its own `COMPILER_NVHPC` identity, distinct from `COMPILER_PGI`, without changing any currently-applied flags,
So that NVHPC-specific work has a real vendor identity to key off, instead of aliasing to PGI.

**Acceptance Criteria:**

**Given** the current build system's compiler-vendor detection
**When** `nvfortran` or `nvf9*` is detected
**Then** `configure.ac` reports `COMPILER_NVHPC`, not `COMPILER_PGI`

**Given** all existing OpenACC/`do concurrent`/stdpar flag selection logic
**When** the identity correction is applied
**Then** flag selection continues to apply identically — this is a naming/identity correction only, not a behavior change

**Given** at least one `Testing/` fixture built before and after this change
**When** compared
**Then** build output is unchanged, confirming no side effect from the rename

**Given** future NVHPC-specific work (e.g. Epic 10's configurable GPU architecture story)
**When** it needs to key off compiler identity
**Then** `COMPILER_NVHPC` is available as a distinct identity — though that later story doesn't strictly require this one to land first, since `PGI_GPU_ARCH`'s override mechanism works independently of the identity naming

## Epic 6: Documentation Modernization

A future contributor or external collaborator can trust the developer guide's precision and module-lifecycle claims, browse FORD-generated API docs for the modules this program touches, get warned about namelist pitfalls before hitting them, find one document explaining how to build and run RegCM5 via its container images, find a catalog and build ergonomics for the `Tools/` utilities, and get unit/integration test coverage for those same utilities. Stories 6.1–6.5 are mutually independent; Story 6.6 was relocated here from Epic 2 (2026-08-11) because its only dependency, Story 6.5, lives in this epic — turning a cross-epic dependency into a normal in-epic one. Epic 8's Story 8.3 also depends on this epic's Story 6.5. Every story in this epic is written in the scholarly, concise register NFR-14 requires.

### Story 6.1: Correct Stale Precision and Module-Lifecycle Documentation

As a future contributor or external collaborator,
I want the Dev Guide's precision section and `project-context.md`'s Module Skeleton rule corrected to describe `rkx` (not hardcoded `dp`) and the `allocate_*`/`getmem`/`relmem` pattern (not `init_mod_*`/`release_mod_*`),
So that I can trust the governing documentation instead of being misled by claims that predate the actual codebase.

**Acceptance Criteria:**

**Given** `Doc/DeveloperGuide/MainDeveloperGuide.tex`'s current precision section describes hardcoded 64-bit `dp`
**When** this story completes
**Then** it describes `rkx` (from `mod_realkinds`) as the sole precision knob, compile-time switchable single/double

**Given** the guide's module-lifecycle section currently describes `init_mod_*`/`release_mod_*`
**When** this story completes
**Then** it describes the actual `allocate_*`/centralized `getmem`/`relmem` pattern, matching the repo-wide finding of zero `release_mod_*` definitions

**Given** `project-context.md`'s own Module Skeleton rule states the same stale claim
**When** this story completes
**Then** `project-context.md` is corrected identically to the Dev Guide — not left as a downstream-only fix

**Given** both documents after correction
**When** a reader checks precision or lifecycle conventions
**Then** the two documents agree with each other and with the actual codebase — no discrepancy left between them

**Given** NFR-14's documentation register
**When** this story's corrected text is written
**Then** it uses established words only, no invented terms or fancy hyphenated compounds, and is short, simple, concise, direct, and grammatically correct

### Story 6.2: Warn Users About Namelist Pitfalls and the CLM3.5 Deprecation

As a modeler running RegCM5 for the first time,
I want the user-facing namelist documentation (`Doc/README.namelist` or equivalent) updated to state the CLM3.5 deprecation and warn about `Testing/*.in` fixtures shipping with literal placeholder paths,
So that I'm warned about known pitfalls before hitting them, not left to discover them the hard way.

**Acceptance Criteria:**

**Given** the updated namelist documentation
**When** a user reads it before running an unedited `Testing/*.in` fixture
**Then** they are warned about placeholder paths requiring edits before use, ahead of Epic 5's namelist-validation story catching the failure at runtime

**Given** CLM4.5/ECLM's status as the supported-going-forward land-coupling tier (a policy already set at the PRD level, §5 Non-Goals — not something Epic 13 newly decides, only formalizes in code comments via its own Story 13.3)
**When** the documentation is updated
**Then** it states the CLM3.5 deprecation explicitly, with CLM4.5/ECLM as the recommended path

**Given** this story may land before Epic 13's Story 13.3 adds the corresponding code-comment markers
**When** the CLM3.5 deprecation note is written
**Then** it's phrased as the project's already-decided policy (the decision itself isn't new or contingent on Epic 13), but if Story 13.3 hasn't landed yet, it notes the code-level deprecation markers as pending rather than implying the codebase already reflects the deprecation uniformly

**Given** NFR-14's documentation register
**When** this documentation is written
**Then** it uses established words only, no invented terms or fancy hyphenated compounds, and is short, simple, concise, direct, and grammatically correct

### Story 6.3: Adopt FORD for Auto-Generated API Documentation

As a future contributor exploring RegCM5's module and procedure relationships,
I want a FORD project configuration and all its generated output kept inside `docs/`, covering `Main/`, `Share/`, `PreProc/`, `PostProc/`, and `external/`, with FORD-compatible comments on the modules this program's own stories touch,
So that I can browse cross-references and call graphs from one predictable location instead of hunting for scattered output or reading source directly.

**Acceptance Criteria:**

**Given** a FORD project configuration file at `docs/ford.md`, with its `output_dir` set to `docs/public/`
**When** FORD runs against it, configured for `Main/`, `Share/`, `PreProc/`, `PostProc/`, and `external/`
**Then** it produces browsable HTML output under `docs/public/` without error, with no FORD artifacts left at the repository root or scattered elsewhere, and `Tools/` (Python, not Fortran) excluded from coverage

**Given** modules touched by this program's own stories (the four already-GPU-ported hotspots, `mod_mppparam`, `mod_dynparam`, the coupling interface modules)
**When** this story completes
**Then** each carries FORD-compatible documentation comments (`!!`/`!>`) — this story does not retrofit annotations across the full 590+-module codebase in one pass (explicitly out of scope)

**Given** the generated FORD output under `docs/public/`
**When** it is produced
**Then** it's built on demand (a documented manual step, or alongside Epic 3's CI once it exists) rather than generated once and left to go stale

**Given** NFR-14's documentation register
**When** FORD-compatible comments are written under this story
**Then** they use established words only, no invented terms or fancy hyphenated compounds, and are short, simple, concise, direct, and grammatically correct

### Story 6.4: Container Build and Run Documentation for Users and Developers

As a user or a contributor without RegCM5's exact library stack pre-provisioned,
I want documentation explaining how to pull and run Epic 3's production container images (GNU, Intel, NVHPC/CUDA) as a user, and how to build and use the same images to develop and contribute, on either a basic workstation or HPC,
So that I can get a working RegCM5 run or a build-ready contribution environment without reverse-engineering the Dockerfiles.

**Acceptance Criteria:**

**Given** a user with no RegCM5 build experience
**When** they follow this documentation
**Then** they pull a production container image and run a `Testing/` fixture inside it, on either a basic workstation via Docker or on Leonardo via Apptainer (Story 3.2)

**Given** a contributor without HPC access
**When** they follow this documentation
**Then** they build a production image locally via Docker and compile a code change inside it, using Story 3.1/3.3's images per FR-40 — no separate lightweight image exists to document instead

**Given** the NVHPC/CUDA image specifically
**When** a contributor without a GPU follows this documentation
**Then** it states plainly that the image's CPU-only path (`-stdpar=multicore`) is usable for development without GPU hardware, per FR-40

**Given** NFR-14's documentation register
**When** this documentation is written
**Then** it uses established words only, no invented terms or fancy hyphenated compounds, and is short, simple, concise, direct, and grammatically correct

### Story 6.5: Document and Streamline the Tools/ Scripts and Programs

As a user or contributor wanting to use one of RegCM5's auxiliary Programs/Scripts utilities,
I want a documented catalog of what exists under `Tools/`, plus a top-level build for `Tools/Programs`, an autotools-normalized `c++read`, and a per-group `requirements.txt` for `Tools/Scripts`' Python tool groups,
So that I can find, build, and run the utility I need without reading source or guessing dependencies.

**Acceptance Criteria:**

**Given** `Tools/Programs` and `Tools/Scripts` (excluding `TestingAndBenchmarking/`, already Epic 1's territory, and `regcm_postproc-0.0.1`, an explicit PRD Non-User)
**When** this story completes
**Then** a single catalog document lists every utility/script group by purpose with a one-line description and an invocation example, linking to (not duplicating) any existing per-subfolder README

**Given** `Tools/Programs`' 11 existing per-utility Makefiles
**When** this story completes
**Then** a top-level `Tools/Programs/Makefile` builds every one of them, without modifying any existing per-utility Makefile

**Given** `c++read`'s current hand-written Makefile (hardcoded `g++`, an external `ncxx4-config` dependency, no `Makefile.am`/`Makefile.in`)
**When** this story completes
**Then** it is normalized to the same `Makefile.am` → `Makefile.in` → `Makefile` autotools pattern already used by `CheckSun`, `RegCM_read`, and `timeseries`, still detecting netCDF-C++4 via `ncxx4-config`

**Given** an audit of `Tools/Scripts/Python/`, `pyplotter/`, and `pyrunner/`'s actual imports
**When** this story completes
**Then** each has its own `requirements.txt` reflecting that group's real dependencies — `pycordexer`'s existing Makefile is left unmodified

**Given** NFR-14's documentation register
**When** the catalog is written
**Then** it uses established words only, no invented terms or fancy hyphenated compounds, and is short, simple, concise, direct, and grammatically correct

### Story 6.6: Unit and Integration Tests for Tools/ Scripts and Programs

As a contributor changing a `Tools/Programs` or `Tools/Scripts` utility,
I want a unit test for its pure functions and an integration smoke test running it against sample data,
So that I can confirm my change did not break the utility, the same way Epic 1's regression-diff tool confirms a core-model change did not break the model.

*Relocated from Epic 2 (where it was Story 9.4) into this epic on 2026-08-11, since its only dependency, Story 6.5, lives here — turning a cross-epic dependency into a normal in-epic one.*

**Acceptance Criteria:**

**Given** Story 6.5 (top-level `Tools/Programs/Makefile`, `c++read`'s autotools normalization, per-group `requirements.txt`)
**When** this story begins
**Then** its tests build and run against exactly the dependencies and build targets Story 6.5 declared

**Given** a `Tools/Programs` Fortran utility or `Tools/Scripts` Python script containing at least one pure, side-effect-free function
**When** this story completes
**Then** that function has a unit test — pFUnit (reusing Epic 2's Story 2.1 framework) for Fortran, pytest for Python — run independent of executing the whole utility

**Given** every utility/script covered by this story
**When** it runs against a small sample input
**Then** an integration smoke test confirms successful completion and the existence of its expected output file — not full numerical correctness, matching the project's existing "smallest trustworthy test is a full run" convention for non-pure code (NFR-15)

**Given** `c++read`'s normalized `Makefile.am`/`Makefile.in` build (Story 6.5)
**When** this story adds its integration smoke test
**Then** it exercises the autotools-built binary, not the old hand-written Makefile's target

## Epic 7: Community Contribution Process

A new contributor to this open-source scientific codebase finds a contribution guide plus issue and pull-request templates codifying what a good issue or merge request looks like. Extracted from Epic 6 (Documentation Modernization) via a Sprint Change Proposal (2026-08-11, "resequencing"), at franco's explicit request to prioritize documentation and contribution guidelines as two separate tiers. Standalone; carries no dependency of its own, but Epic 8's Stories 8.1/8.2 depend on this epic's Story 7.1 (see those stories).

### Story 7.1: Contribution Guide, Issue, and Merge-Request Rules

As a new contributor to this open-source scientific codebase,
I want a contribution guide plus issue and pull-request templates that codify what a good issue or merge request looks like,
So that I know how to propose a change and what evidence it needs, without reverse-engineering the project's conventions from source and prior commits.

**Acceptance Criteria:**

**Given** a first-time contributor
**When** they read `CONTRIBUTING.md`
**Then** they find the project's acceptance discipline (Build/Test/Numerical/Performance, NFR-10) and the review/sign-off model (regcm5-dev's sole scientific sign-off) stated plainly, with pointers to `project-context.md` and the Dev Guide as the source of truth for coding conventions — not a duplicated copy of those rules

**Given** `.github/ISSUE_TEMPLATE/`
**When** a contributor opens a new issue
**Then** the template prompts for reproduction steps and the `Testing/` fixture and compiler/vendor combination involved

**Given** `.github/PULL_REQUEST_TEMPLATE.md`
**When** a contributor opens a pull request
**Then** the template prompts for the same Build/Test/Numerical/Performance record NFR-10 already requires, and states explicitly that a green CI check (Epic 3) is necessary but not sufficient for merge (AD-4)

**Given** NFR-14's documentation register
**When** this guide and these templates are written
**Then** they use established words only, no invented terms or fancy hyphenated compounds, and are short, simple, concise, direct, and grammatically correct

## Epic 8: Performance, Memory-Safety, and Dependency Security Regression Gates

A pull request touching RegCM5 is automatically checked for gross performance regression and new memory-leak/memory-safety findings in CI, and gated on required Slurm-based performance evidence for changes touching profiled hotspots or dynamics/I/O/GPU code. Dependency and container images gain vulnerability scanning, scoped to what this codebase actually distributes — not a claim that the Fortran physics core is a generically "security-scanned" artifact, per `project-context.md`'s existing position. Added via Sprint Change Proposal 2026-08-11, at franco's explicit request; builds on Epic 4's Story 4.6 and FR-4/AD-8 baseline, Epic 7's Story 7.1 (pull-request template), Epic 6's Story 6.5 (`requirements.txt`), and Epic 3's Story 3.1/3.3 (containers) and Story 3.4 (CI) — all satisfied earlier in this sequence.

### Story 8.1: Memory-Leak and Memory-Safety Regression Gate

As a contributor opening a pull request,
I want Story 4.6's one-time Valgrind pass turned into a repeatable CI check for new leaks/errors, plus a GNU `-fsanitize=address,undefined` build variant catching out-of-bounds access and undefined behavior,
So that a change introducing a new memory-safety issue is caught before merge, not discovered later.

**Acceptance Criteria:**

**Given** Story 4.6's recorded findings (the pre-existing leak/error baseline)
**When** this gate runs
**Then** it fails only on new findings not already present in that recorded baseline — not on every pre-existing issue Story 4.6 already logged as a scoped follow-up (NFR-18)

**Given** the CI fixture (`Testing/ideal.in`, AD-11)
**When** a pull request is opened
**Then** Valgrind Memcheck runs against it in CI (or, if Valgrind's overhead is impractical in CI per Story 4.6's own finding, a documented lighter-weight equivalent) and reports pass/fail against the recorded baseline

**Given** a GNU build configured with `-fsanitize=address,undefined`
**When** the CI fixture runs under it
**Then** any out-of-bounds array access or undefined-behavior finding fails the check, distinct from and complementary to the Valgrind check

**Given** this story's gate
**When** it fails
**Then** the pull-request template (Epic 7's Story 7.1) states this failure blocks merge, consistent with the acceptance discipline NFR-10 already requires

### Story 8.2: Performance Regression Gate — CI Smoke Tier and Required Slurm Evidence

As a contributor opening a pull request touching performance-sensitive code,
I want a coarse, automatic CI timing check on the small CI fixture, and a required Slurm-based performance run against the canonical baseline for changes touching profiled hotspots or dynamics/I/O/GPU code,
So that gross regressions are caught automatically, and real performance claims are still backed by evidence from the actual target hardware — extending, not overriding, AD-4/NFR-9.

**Acceptance Criteria:**

**Given** `Testing/ideal.in` (AD-11) and a stored wall-clock baseline for it
**When** a pull request's CI run completes
**Then** it reports the run's wall-clock time against that baseline with a generous tolerance band (wide enough to absorb GitHub-hosted-runner noise) and fails only on a gross regression, not routine variance (NFR-17)

**Given** a change touching a subsystem Epic 4's FR-4 baseline profiled as a hotspot, or touching dynamics/I/O/GPU code
**When** the pull request is opened
**Then** the pull-request template (Epic 7's Story 7.1) requires a Slurm-based performance run against AD-8's canonical EUR12 baseline as attached evidence, checked by regcm5-dev at review (NFR-10) — not automatically enforced by GitHub Actions

**Given** a change that does not touch profiled hotspots or dynamics/I/O/GPU code
**When** the pull-request template is filled in
**Then** the Slurm-evidence requirement is explicitly waivable, stating why it doesn't apply, rather than blocking every unrelated change

**Given** this story's two-tier design
**When** documented
**Then** it states plainly that the CI smoke tier is a coarse tripwire, not a substitute for Slurm evidence, matching AD-4's existing "necessary but not sufficient" framing exactly, not a new invented policy

### Story 8.3: Dependency and Container Vulnerability Scanning

As a contributor or user relying on RegCM5's Python tooling or container images,
I want the `requirements.txt` files (Epic 6/Epic 2) scanned for known-vulnerable dependencies, and Epic 3's container images scanned for vulnerable packages,
So that a real, concrete class of vulnerability is caught, scoped to what this codebase actually distributes rather than a generic scan with no meaningful target.

**Acceptance Criteria:**

**Given** every `requirements.txt` file added under Epic 6 (Story 6.5) and used by Epic 2's pytest tooling
**When** a pull request touches one
**Then** a dependency-vulnerability scan (e.g. `pip-audit`) runs in CI and fails on a known-vulnerable pinned version

**Given** Epic 3's GNU/Intel/NVHPC-CUDA container images
**When** a new image is built
**Then** a container vulnerability scan (e.g. Trivy) runs and reports known-vulnerable packages in the image, gating the container-build pipeline (Story 3.1/3.3) rather than the main model build

**Given** `project-context.md`'s existing position that this codebase is not a meaningful attack surface in the usual sense
**When** this story's scope is documented
**Then** it states explicitly that this gate covers dependency/container supply-chain exposure only — not a claim that the Fortran physics core itself is scanned for "security vulnerabilities" in the generic sense, which Story 8.1's sanitizer check addresses instead, on its own terms (memory-safety, not "security")

## Epic 9: Code Duplication Audit and Generic-Interface Consolidation

A future contributor finds fewer hand-duplicated routine bodies to keep in sync in the communication and I/O layers, consolidated via compile-time mechanisms only — never runtime polymorphism near GPU-offloaded code. Added via Sprint Change Proposal 2026-08-11, at franco's explicit request. A quick evidence check during proposal drafting found `Main/mpplib/mod_mppparam.F90` alone has 42 duplicate-named subroutines across a real4/real8 type axis and a 2D/3D/4D rank axis, already wrapped in generic interfaces at the call site; `mod_ncout.F90`/`mod_ncstream.F90` carry a parallel rank-duplication pattern, also already interface-wrapped; and `assignpnt` (`Share/mod_memutil.F90`) is already consolidated via a generic interface and is excluded from scope as this project's own documented "#1 GPU-porting risk."

### Story 9.1: Audit Source Code for Type- and Rank-Duplicated Routines

As regcm5-dev,
I want a repository-wide audit of communication, pointer-assignment, computation, and I/O code for type/rank-duplicated routine bodies, scored by duplication pattern, GPU-porting risk, and consolidation feasibility,
So that Stories 9.2 and 9.3 (and any future consolidation story) proceed on a confirmed go/no-go inventory instead of a blind, codebase-wide refactor.

**Acceptance Criteria:**

**Given** `Main/mpplib/mod_mppparam.F90`, `Main/mpplib/mod_ncout.F90`, `Share/mod_ncstream.F90`, `Share/mod_memutil.F90`, and any computation-layer code the audit finds
**When** the audit runs
**Then** it produces a written inventory naming every candidate routine family, its duplication pattern (type-axis, rank-axis, or both), whether any `do concurrent`/OpenACC-offloaded code path reaches it, and a go/no-go recommendation

**Given** `assignpnt`'s existing generic interface and its documented status as this project's own "#1 GPU-porting risk"
**When** the audit covers it
**Then** it is included in the inventory marked no-go, with that status as the stated reason — not silently omitted, and not recommended for consolidation

**Given** the "computation" category named in the original request
**When** the audit completes
**Then** it states concretely what, if anything, qualifies as a candidate there — no consolidation story is created for computation code unless this audit confirms a real candidate exists, matching Story 4.5's investigate-then-scope-only-if-confirmed pattern

**Given** this story's own findings
**When** it completes
**Then** Stories 9.2 and 9.3 are updated to reference the confirmed candidate list, and any additional consolidation story the audit justifies is proposed as a follow-up, not pre-committed here

### Story 9.2: Consolidate Communication-Layer Duplicated Routines

As a future contributor maintaining `mod_mppparam.F90`,
I want the confirmed subset of its 42 duplicate-named subroutines consolidated into fewer hand-maintained bodies via compile-time mechanisms only,
So that a bug fix or change no longer needs to be applied by hand to every real4/real8 and rank variant separately.

**Acceptance Criteria:**

**Given** Story 9.1's audit
**When** this story begins
**Then** it consolidates exactly the candidates marked go for `mod_mppparam.F90`, not the full 42-subroutine set by default

**Given** AD-26's generic-interface consolidation policy
**When** consolidation is implemented
**Then** it uses compile-time mechanisms only — generic interfaces (already established here, e.g. `interface exchange_array`) or preprocessor-generated bodies — never `class(*)`/`select type` runtime polymorphism, since AD-3's `do concurrent`/OpenACC device-kernel generation requires concrete, monomorphic types

**Given** every consolidated routine
**When** compared against its pre-refactor body
**Then** it produces bit-exact output (AD-1), and every existing public interface name and signature is preserved unchanged — zero behavior change for any existing caller

**Given** this code is halo-exchange-adjacent
**When** the change is verified
**Then** it is regression-checked at `nproc=1` and `nproc=4` minimum (AD-12/AD-13), per the project's existing stencil/halo rule

**Given** consolidation surfaces a behavioral divergence between previously-duplicated bodies
**When** found
**Then** it is flagged for regcm5-dev's review as a found bug, not silently "fixed" as part of the refactor (NFR-19)

### Story 9.3: Consolidate I/O-Layer Duplicated Routines

As a future contributor maintaining `mod_ncout.F90`/`mod_ncstream.F90`,
I want the confirmed subset of their rank-duplicated routines consolidated the same way, once Epic 11's and Epic 12's own changes to these files have landed,
So that the I/O layer gains the same maintainability benefit without three epics editing the same files concurrently.

**Acceptance Criteria:**

**Given** Epic 11's Story 11.3/11.4 and Epic 12's Story 12.2
**When** this story is considered for sprint planning
**Then** it does not begin until both have completed — a hard dependency, not a scheduling preference

**Given** Story 9.1's audit
**When** this story begins
**Then** it consolidates exactly the candidates marked go for `mod_ncout.F90`/`mod_ncstream.F90` (e.g. `setup_var_2d`/`_3d`/`_4d`, `writevar2d/3d/4d_output_stream`), not every rank-duplicated routine by default

**Given** AD-26's generic-interface consolidation policy and the existing `interface setup_var`/`interface writevar_output_stream` call-site pattern
**When** consolidation is implemented
**Then** it follows the same compile-time-only constraint as Story 9.2, with the same bit-exactness and public-interface-preservation requirements (AD-1, NFR-19)

## Epic 10: Selective GPU Acceleration and Verification

Whoever ports RegCM5 subsystems to GPU (regcm5-dev or an external collaborator) gets a verified and documented existing GPU-porting footprint, a measurement-grounded go/no-go on RRTMG, continued cross-vendor-verified MOLOCH porting, a verified GPU-direct halo exchange, a configurable GPU target architecture, the statistical-reproducibility regression test enforcing the project's established tolerance policy, and a written guidance document capturing what this phase learned. Builds on Epic 4's baseline (FR-4) and Epic 1's regression tool (FR-37); highest-uncertainty epic in the program, per the PRD's own framing. FR-8's own consequence requires the cross-vendor check to be applied to loops touched by FR-10, so MOLOCH porting (7.3) precedes cross-vendor verification (7.4); FR-22 (7.8) stays last since it synthesizes this epic's own findings.

### Story 10.1: Verify and Document the Full Existing GPU-Porting Footprint

As whoever ports RegCM5 to GPU next,
I want every existing GPU-ported subsystem (the full 90-file, 1,476-directive-line footprint, not only the four thesis-documented hotspots) verified to build under current target versions and documented with location and validation provenance,
So that I know what's already there and trustworthy before deciding where to port next.

**Acceptance Criteria:**

**Given** a repository-wide audit for `!$acc` directives (distinct from `do concurrent`'s separate 95-file footprint, not a GPU-porting signal on its own)
**When** the audit runs
**Then** it enumerates every GPU-ported subsystem found — the four hotspots, plus the full CLM4.5 land-model library, cloud/cumulus/microphysics, ocean, PBL, OASIS coupling, and async netCDF I/O

**Given** each enumerated subsystem
**When** checked against current target versions (NVHPC 26.3, HPC-X 2.25, CUDA 12.9 — a gap from the source thesis's validated NVHPC 24.5/CUDA 12.4)
**Then** the document states whether it still builds and behaves as documented, not assumed unchanged

**Given** a port that doesn't build or behave as documented
**When** found
**Then** it's logged as a specific, scoped follow-up — not silently assumed to still work

**Given** each subsystem's validation history
**When** documented
**Then** it distinguishes thesis-validated (the original four) from NVIDIA-collaboration-validated (regcm5-dev-confirmed) provenance

**Given** the halo-exchange layer and MOLOCH
**When** this document is written
**Then** it cross-references Stories 10.2 and 10.3 rather than re-verifying either — this story owns the rest of the footprint

**Given** each enumerated subsystem's data-handling approach
**When** the audit documents it
**Then** it also states which memory management mode the subsystem currently relies on — explicit device memory (`!$acc data`/`copyin`/`copyout`/`create`), CUDA managed memory (`mem:managed`), or NVHPC's unified memory (`mem:unified`) — since AD-22 fixes explicit memory as the production/profiling default while AD-7 requires the build matrix to test both managed and stdpar configurations, and a subsystem's assumptions about which mode it was written under matter for both

### Story 10.2: Verify and Document the Existing GPU-Direct Halo Exchange

As regcm5-dev,
I want the already-implemented GPU-direct halo exchange in `mod_mppparam.F90` verified under current target versions (HPC-X 2.25), with which routines are GPU-direct versus host-buffer-staged documented,
So that Story 10.4 and Story 10.7 have a confirmed, current-version answer instead of an inherited assumption.

**Acceptance Criteria:**

**Given** the `real8_2d/3d/4d_exchange` family and directional variants
**When** checked against HPC-X 2.25
**Then** a short document states which routines use the GPU-direct path today and which remain host-buffer-staged

**Given** the simpler `exchange_array_r8`/`exchange_array_r4` primitives
**When** documented
**Then** they're correctly noted as plain host-memory MPI calls — GPU-direct is scoped to the packed multi-dimensional family, not universal

**Given** any exchange routine that doesn't build or behave as documented
**When** found
**Then** it's logged as a specific, scoped follow-up

**Given** NVHPC's `mem:unified` mode (vs. the thesis's `mem:managed`)
**When** this document is written
**Then** it notes whether evaluating that mode on newer hardware is worth its own follow-up — without committing this program to it

**Given** the halo-exchange routines' existing `!$acc data copy(ml) create(...)` pattern
**When** the audit runs
**Then** it confirms this pattern assumes explicit device memory (per AD-22), and states whether the routines have also been verified to behave correctly when built under the `mem:managed` and `mem:stdpar` configurations AD-7 requires as build-matrix cells — not only under the explicit-memory production default

### Story 10.3: Continue MOLOCH Dynamical-Core GPU Porting

As whoever ports RegCM5 to GPU,
I want ongoing `do concurrent`-based GPU-porting work on `mod_moloch.F90` to continue under the existing strategy, with each change meeting the full acceptance discipline,
So that MOLOCH's GPU port keeps advancing without silently regressing correctness or portability.

**Acceptance Criteria:**

**Given** a MOLOCH GPU-porting change
**When** it ships
**Then** it carries a commit/PR record stating Build, Test, Numerical, and Performance evidence (NFR-10)

**Given** MOLOCH's stencil loops with i±1/j±1 neighbor access near tile boundaries
**When** such a loop changes
**Then** it's regression-checked at `nproc=1`, `nproc=4` (AD-12's required minimum pair), and additionally at `nproc=16`, `64`, `144`, `224` — the higher counts are additional coverage beyond AD-12's minimum, not a replacement for it

**Given** this program's target versions
**When** a change is verified
**Then** it builds under GNU, Intel, and NVHPC (NFR-2), with GPU parallelization expected only where NVHPC is the target

**Given** MOLOCH's GPU-ported code
**When** built and run under each of the three memory management modes (explicit device memory, `mem:managed`, `mem:unified`)
**Then** it produces correct, numerically-compliant output under all three — not verified against only whichever mode happens to be the default, since AD-7 already requires both managed and stdpar configurations as build-matrix cells regardless of AD-22's production default

### Story 10.4: Cross-Vendor do concurrent Parallelization Verification

As whoever ports RegCM5 to GPU,
I want a documented procedure confirming every `do concurrent` loop touched under this program actually parallelizes — not merely compiles — under GNU, Intel, and NVHPC, applied at minimum to Story 10.3's MOLOCH changes,
So that a loop silently running serial on one vendor is caught before merge.

**Acceptance Criteria:**

**Given** a `do concurrent` loop touched by Story 10.3
**When** the verification procedure runs
**Then** it uses `-Minfo=accel` on NVHPC and corresponding diagnostic flags on GNU/Intel, added as a checklist item to the existing manual validation process

**Given** per-vendor expectations
**When** applied
**Then** they're set correctly, not uniformly: NVHPC's `-stdpar` is the mature path; Intel's `ifx` offloads via an OpenMP backend; GNU has no `do concurrent` GPU offload path at all — serial-but-correct on GNU is the documented state, not a gap

**Given** a loop compiling under all three vendors but parallelizing only under NVHPC where expected
**When** this procedure runs
**Then** it's caught before merge, not discovered later as a silent regression

**Given** the four already-merged hotspots use OpenACC directly, not `do concurrent`
**When** this FR's scope is considered
**Then** they're explicitly out of scope here — tracked under Story 10.1 instead

**Given** a `do concurrent` loop's GPU offload behavior
**When** the cross-vendor verification procedure runs
**Then** it confirms parallelization under each of explicit device memory, `mem:managed`, and `mem:unified` — not only the mode the loop happened to be developed under, since a loop parallelizing correctly under one memory mode but silently failing or diverging under another is exactly the kind of regression this procedure exists to catch

### Story 10.5: RRTMG GPU-Porting Feasibility Investigation with Go/No-Go Checkpoint

As whoever decides where to invest GPU-porting effort next,
I want a scoped investigation evaluating RRTMG's GPU-porting potential using Epic 4's direct measurement and the ICON-A/PSrad precedent,
So that a go/no-go recommendation exists before any implementation begins.

**Acceptance Criteria:**

**Given** Epic 4's measurement finding no RRTMG hotspot in the CLM4.5-coupled configuration
**When** this investigation runs
**Then** it treats "low priority in that configuration" as a live outcome, not an assumption that ICON-A's precedent applies regardless

**Given** RRTMG's kernels carry zero `!$acc`/`do concurrent` directives today
**When** the investigation concludes
**Then** it states, with reasoning tied to Epic 4's data, whether porting proceeds, is deferred, or is rejected in favor of scheme replacement

**Given** the column-radiation driver already carries validated GPU work distinct from RRTMG's own math
**When** written
**Then** it notes that distinction so a future reader doesn't conflate the two

**Given** a "proceed" recommendation
**When** concluded
**Then** it defines the acceptance discipline any resulting implementation must meet — implementation itself is out of this story's scope

**Given** a "no-go" recommendation backed by evidence
**When** reached
**Then** it's treated as a successful outcome (SM-C2), not a failure to complete

**Given** RRTMG's go/no-go feasibility assessment
**When** the investigation weighs whether porting is worthwhile
**Then** it also considers feasibility across each of the three memory management modes — a kernel that's a poor fit for managed/unified automatic inference (per the thesis's own experience with `getcape`'s implicit-copy behavior) might still be feasible under explicit control, or vice versa, and the recommendation should state which mode(s), if any, make porting viable

### Story 10.6: Configurable GPU Target Architecture

As a build-system user targeting a specific GPU generation,
I want the hardcoded `PGI_GPU_ARCH="ccnative"` setting (`configure.ac:140`) to become configurable,
So that I can pin a target GPU's compute capability when auto-detection is insufficient.

**Acceptance Criteria:**

**Given** the current hardcoded setting
**When** this story completes
**Then** a configure-time option exists to override it

**Given** the option is omitted
**When** configure runs
**Then** current auto-detect (`ccnative`) behavior is preserved unchanged

### Story 10.7: Statistical-Reproducibility Regression Test for GPU-Ported Code

As regcm5-dev,
I want a regression test enforcing the established statistical-reproducibility policy (`tas`/`ps` rMAD/rRMSE < 0.1%, `huss` < 5%, 7-model-day run), using Epic 1's tool and tolerance mechanism,
So that GPU-ported code's divergence is checked against the project's actual accepted bar.

**Acceptance Criteria:**

**Given** Story 10.1's confirmation that the four hotspots build under current versions
**When** this test runs against them
**Then** it fails if thresholds are exceeded, pinned to the thesis's values, changeable only with regcm5-dev's sign-off

**Given** new GPU-porting work (Story 10.3's MOLOCH work, any Story 10.5 RRTMG outcome)
**When** it produces GPU-ported output
**Then** it's held to the same thresholds by default — no fresh case-by-case negotiation

**Given** a field newly GPU-ported but not yet in the tolerance table
**When** this test runs against it
**Then** it defaults to bit-exact (AD-1) until its own bound is added

**Given** this test's documentation
**When** read
**Then** it states plainly this is the accepted GPU-porting policy, not an unreviewed shortcut

### Story 10.8: GPU-Porting and Performance Guidance Document

As a future contributor deciding whether to port another subsystem,
I want a document capturing the strategy on using `do concurrent` and OpenACC, measured risk tiering, the cross-vendor procedure, and recommended sequencing,
So that future decisions build on this program's findings instead of relitigating them.

**Acceptance Criteria:**

**Given** Stories 10.1–10.7 have all completed
**When** this document is written
**Then** it synthesizes their findings — footprint, halo-exchange status, MOLOCH progress, the cross-vendor procedure, RRTMG's outcome, the configurable architecture option, and the reproducibility policy — rather than being written before that evidence exists

**Given** the document's audience
**When** placed
**Then** it lives alongside `Doc/DeveloperGuide/` (or Epic 6's `docs/` restructuring), referenced from Stories 10.3 and 10.5's acceptance records

**Given** the source thesis's own hard-won `do concurrent`-vs-OpenACC lessons (automatic-array allocation unsupported inside an offloaded procedure; helper procedures needing module scope, `pure`, and `!$acc routine seq`; NVHPC's implicit data-movement inference being inconsistent enough that explicit `!$acc data create(...)` regions outperformed relying on `do concurrent` alone) and the finding that all three strategies tried for `getcape` (pure OpenACC, pure `do concurrent`, hybrid) delivered comparable speedups even though the pattern actually merged is OpenACC
**When** this document is written
**Then** it captures `do concurrent` versus OpenACC directives as RegCM5's own two-pronged accelerator strategy — when each is used, the concrete porting hazards specific to each, and that OpenACC is the pattern actually merged for the four hotspots while `do concurrent` remains the default for new work (per AD-3) — not just a restatement of "do concurrent first, escalate to OpenACC," but the *why* behind it

**Given** Stories 10.1 and 10.2's audits of memory-management-mode usage across the existing GPU-porting footprint
**When** this document is written
**Then** it captures RegCM5's memory-management strategy for GPU porting — explicit device memory as the default for production/profiling runs (AD-22), both `--enable-openacc-managed` and `--enable-openacc-stdpar` as required build-matrix test configurations regardless of that runtime default (AD-7), and the source thesis's own finding that NVHPC's implicit data-movement inference under `do concurrent` alone was inconsistent enough to motivate explicit `!$acc data create(...)` regions — so a future porting decision knows which mode to design for, and why

## Epic 11: Diagnostic, Restart, and Land-Model I/O Scaling

A modeler running CORDEX-scale simulations at high rank counts can opt into parallel diagnostic, restart, and CLM land-model history output; gets an evidence-based explanation for the source thesis's measured parallel-write slowdown; and receives concrete, conditioned optimization recommendations — while every non-opted-in run keeps working exactly as before. Builds on Epic 4's I/O and async-netcdf instrumentation (Stories 4.3, 4.4).

### Story 11.1: Evaluate Async-NetCDF as a Complementary I/O Optimization

As regcm5-dev,
I want the existing `mod_async_netcdf.F90` facility evaluated against Epic 4's baseline and its own profiling data,
So that a documented, quantified recommendation — adopt, extend, or leave as-is — exists instead of a qualitative impression.

**Acceptance Criteria:**

**Given** Story 4.3's async-netcdf instrumentation and Story 4.4's baseline run
**When** the async path is profiled against a representative `Testing/` fixture
**Then** a written recommendation states the measured percentage reduction (or increase) in I/O-attributable wall time async-netcdf delivers versus PnetCDF alone, at the same rank count — a number, not a qualitative judgment

**Given** the recommendation is adopt, extend, or leave-as-is
**When** it is recorded
**Then** Story 11.4's investigation can cite it as one input among the paths compared

### Story 11.2: Extend I/O Timing Instrumentation to Restart and CLM Land-Model History

As regcm5-dev,
I want `time_begin`/`time_end` instrumentation added to `Main/mod_savefile.F90` and CLM4.5/ECLM's history-output module, following AD-17's naming (`io_gather_rst`/`io_write_rst`/`io_wait_rst` and the `clm` equivalents),
So that Story 11.4 can evaluate restart and land-model I/O under the same scaling questions as diagnostic output.

**Acceptance Criteria:**

**Given** a DEBUG-enabled build
**When** a restart-file write event occurs (with or without the existing `do_parallel_netcdf_out` path enabled)
**Then** timing output separates gather/write/wait time, labeled `io_gather_rst`/`io_write_rst`/`io_wait_rst`

**Given** a DEBUG-enabled, land-coupled (CLM4.5/ECLM) build
**When** a CLM history write event occurs
**Then** timing output separates gather/write/wait time, labeled with the `clm` equivalents

**Given** restart output already has a PnetCDF path predating this program
**When** this story instruments it
**Then** no new namelist switch is introduced for restart — only timing instrumentation is added to the already-switchable path

**Given** a non-DEBUG production build
**When** the instrumented code executes
**Then** no additional overhead is observable (NFR-4), calls stay at gather/write/wait granularity — never inside a loop body

### Story 11.3: Parallel NetCDF Write for Diagnostic Output, Opt-In

As a modeler running CORDEX-scale simulations at high rank counts,
I want diagnostic/history output (`mod_ncout.F90`) to support a PnetCDF parallel-write path, gated by a new `do_parallel_netcdf_hist` namelist switch (matching the existing `do_parallel_netcdf_in`/`_out` convention), shipped as a tested, documented option rather than a promoted default,
So that I can opt into parallel diagnostic output today, while the project waits for Story 11.4 to explain the measured parallel-write slowdown before recommending it.

**Acceptance Criteria:**

**Given** a build configured with `--enable-pnetcdf`/`--enable-parallel-nc`
**When** a run sets `do_parallel_netcdf_hist = .true.`
**Then** diagnostic/history output is written via PnetCDF instead of gather-then-serial-write

**Given** a `Testing/` fixture run with parallel diagnostic output enabled
**When** compared against the equivalent serial run at `nproc=1`, `nproc=4` (AD-12's required minimum pair), and additionally at `nproc=16`, `64`, `144`, `224`, using Epic 1's `regression_diff.py --nprocs`
**Then** output is bit-exact across all fields at every process count tested — a CPU-only change, no statistical tolerance applies (AD-1); the higher counts are additional coverage beyond AD-12's minimum, not a replacement for it

**Given** a build without PnetCDF, or a run that doesn't set the switch (including `mpi-serial` builds)
**When** it executes
**Then** it uses the existing gather-then-write path unmodified, no observable output/naming change (FR-6, NFR-3)

**Given** this capability's documentation
**When** a reader consults it
**Then** it states plainly this is a tested, opt-in option, not a promoted default, pending Story 11.4's findings

### Story 11.4: I/O Profiling and Optimization Investigation Across All Paths

As regcm5-dev,
I want diagnostic, restart, CLM land-model, async-netcdf, and boundary-condition/ICBC input paths all profiled at more than one rank count, on this program's own canonical baseline fixture (AD-8), checking whether the source thesis's parallel-write-slower-than-serial finding holds here too and explaining it with profiling evidence,
So that recommendations are concrete and evidence-based, grounded in this project's own measurements rather than a different configuration's numbers.

**Acceptance Criteria:**

**Given** Stories 4.3 and 11.2's instrumentation covering diagnostic, restart, and CLM paths, plus Story 11.1's async-netcdf profiling
**When** each path is profiled at more than one rank count, across serial, HDF5-parallel, PnetCDF-parallel, and async-netcdf modes, on this program's own canonical baseline fixture rather than the source thesis's CLM4.5-coupled configuration
**Then** a written report states measured I/O time share per path and mode, as directly measured on this fixture — not the source thesis's own numbers, which were measured on a different configuration (different domain, node count, and coupling setup) and aren't directly comparable evidence

**Given** the source thesis found parallel write (HDF5-parallel, PnetCDF-parallel) measured slower than serial at every rank count it tested, in its own CLM4.5-coupled configuration
**When** this investigation runs on this program's own baseline fixture instead
**Then** it independently confirms or contradicts whether the same pattern holds here, and explains it with profiling evidence (e.g. collective-I/O sync overhead, striping/chunking mismatch, metadata contention) — treated as a hypothesis to check, not a finding assumed to carry over unchanged, and not left as an open mystery either way

**Given** boundary-condition/ICBC input reads fall under this investigation
**When** findings touch that code
**Then** they are flagged for regcm5-dev's review, never silently "fixed" or "optimized" (NFR-12, AD-19)

**Given** the investigation's conclusions, including where async-netcdf fits relative to PnetCDF per path
**When** recommendations are written
**Then** they are concrete and conditioned on the explanation above (e.g. "enable parallel diagnostic output above N ranks once cause X is fixed," "prefer async-netcdf over PnetCDF for path Y") — not a generic "improve I/O"

**Given** this story completes
**When** Story 11.3's documentation is revisited
**Then** it is updated to reflect the conclusion — continuing to withhold, or lifting, the "not a promoted default" caveat

## Epic 12: ADIOS2 I/O Backend Integration

A modeler or contributor opts into ADIOS2 as a diagnostic, restart, or CLM land-model output backend alongside the existing netCDF/PnetCDF path, with documentation explaining how to enable and consume it, while every non-opted-in run keeps working exactly as before. Added via Sprint Change Proposal 2026-08-11, at franco's explicit request; builds on Epic 11's per-path opt-in and naming conventions (AD-6, AD-17) and Epic 1's regression tooling for its own comparison evidence, but does not require Epic 11's Story 11.4 to complete first.

### Story 12.1: Evaluate and Design ADIOS2 Integration

As regcm5-dev,
I want a scoped design for ADIOS2 integration — build flag, three per-path namelist switches, and a plan for comparing ADIOS2's BP output against the existing NetCDF baseline,
So that implementation (Story 12.2) has a concrete, reviewed shape before any code is written.

**Acceptance Criteria:**

**Given** the existing `--enable-pnetcdf`/`--enable-async-netcdf` build-flag pattern
**When** the ADIOS2 design is written
**Then** it specifies `--enable-adios2` following the same shape, plus the ADIOS2 library version to pin (added to the architecture's version-pinning table, AD-15/AD-23)

**Given** AD-6's per-path namelist-switch naming convention
**When** the design specifies the runtime switches
**Then** it names three independent switches — `do_adios2_hist`, `do_adios2_rst`, `do_adios2_clm` — covering diagnostic/history, restart/checkpoint, and CLM land-model history output

**Given** ADIOS2's BP output format is not NetCDF-compatible
**When** the design addresses regression comparison
**Then** it states explicitly, per path, whether Epic 1's `regression_diff.py` will be extended to read BP directly or whether a BP-to-NetCDF conversion step precedes comparison — not left unstated (NFR-16)

**Given** this design's conclusions
**When** Story 12.2 begins
**Then** it implements exactly the scoped switches, flag, and comparison path this story defines, not a broader shape

### Story 12.2: Implement ADIOS2 Parallel Write for Diagnostic, Restart, and CLM Land-Model Output, Opt-In

As a modeler wanting to evaluate ADIOS2 as an I/O backend,
I want diagnostic/history, restart/checkpoint, and CLM land-model history output to support writing via ADIOS2 when each path's switch is set and the build is configured with `--enable-adios2`,
So that I can compare ADIOS2's I/O performance against the existing netCDF/PnetCDF path on my own workload, for whichever output path I care about.

**Acceptance Criteria:**

**Given** a build configured with `--enable-adios2`
**When** a run sets `do_adios2_hist`, `do_adios2_rst`, or `do_adios2_clm` to `.true.`
**Then** the corresponding output path is written via ADIOS2 (BP format) instead of the netCDF/PnetCDF path, independently per switch

**Given** CLM land-model history output specifically
**When** `do_adios2_clm` is set
**Then** it applies only to land-coupled (CLM4.5/ECLM) builds, matching FR-33's existing phrasing for that path

**Given** Story 12.1's comparison plan
**When** a `Testing/` fixture run with a given path's ADIOS2 switch enabled is compared against the equivalent netCDF run at `nproc=1` and `nproc=4` (AD-12)
**Then** field values agree bit-exactly, using the comparison method Story 12.1 specified for that path

**Given** a build without `--enable-adios2`, or a run that doesn't set a given path's switch
**When** it executes
**Then** that path uses the existing netCDF/PnetCDF path unmodified — no observable output/naming change (NFR-3)

**Given** this capability's documentation (Story 12.3)
**When** a reader consults it
**Then** it states plainly this is a tested, opt-in option per path, not a promoted default

### Story 12.3: ADIOS2 I/O Backend Documentation

As a modeler or contributor evaluating ADIOS2,
I want documentation covering the build flag, all three namelist switches, and how to read or convert BP output for downstream consumers (PostProc, external analysis pipelines),
So that I can use the new backend without reverse-engineering its integration from source.

**Acceptance Criteria:**

**Given** a reader unfamiliar with ADIOS2
**When** they consult this documentation
**Then** it explains `--enable-adios2`, all three namelist switches, and at least one concrete method to read or convert BP output for a chosen path

**Given** NFR-14's documentation register
**When** this document is written
**Then** it uses established words only, no invented terms or fancy hyphenated compounds, and is short, simple, concise, direct, and grammatically correct

## Epic 13: External Coupling Modernization

An integrator coupling RegCM5 to OASIS3-MCT, REGESM, CLM, or a future CISM partner gets a documented, regression-tested field-exchange contract instead of one inferred from source; CLM3.5 is clearly marked deprecated; a CISM interface design exists for a future implementation phase; and BMI's dormant status is resolved one way or the other. No technical dependency on any other epic — sequenced last by priority choice (confirmed with franco), not necessity.

### Story 13.1: OASIS3-MCT Field-Exchange Documentation and Regression Coverage

As an integrator coupling RegCM5 to another model via OASIS3-MCT,
I want the current OASIS3-MCT field list documented against live code, and a `Testing/` fixture exercising `--enable-oasis` passing the standard regression comparison,
So that I have an authoritative, current contract instead of one inferred from source reading.

**Acceptance Criteria:**

**Given** the live `--enable-oasis`/`--enable-eclm` build mode's field list
**When** documented
**Then** it distinguishes base-OASIS fields from ECLM-only additional fields (atmospheric T/U/V/Q, geopotential height, runoff, snow, soil moisture/temperature, albedo, CH4 flux, dust/VOC flux, dry-deposition velocity)

**Given** at least one `--enable-oasis` coupled-build `Testing/` fixture
**When** it runs
**Then** it passes the standard regression comparison (Epic 1's tool), recorded with Build/Test/Numerical evidence

**Given** this field-list document
**When** produced
**Then** it supersedes the technical research note's and addendum's own placeholder field lists as the authoritative source going forward (NFR-7)

### Story 13.2: REGESM Field-Exchange Documentation and Regression Coverage

As an integrator coupling RegCM5 to another model via REGESM,
I want the current REGESM (`--enable-cpl`) field list (`mod_update.F90`'s `imp_data`/`exp_data`) documented against live code, and a `Testing/` fixture exercising `--enable-cpl` passing the standard regression comparison,
So that REGESM's contract is documented on its own terms, not conflated with OASIS3-MCT's.

**Acceptance Criteria:**

**Given** `mod_update.F90`'s `imp_data`/`exp_data` types
**When** documented
**Then** the current field list is produced

**Given** this field list
**When** compared to OASIS3-MCT's (Story 13.1)
**Then** it's presented as an independent mechanism on an independent code path — not unified into a shared abstraction, since that would be a design change beyond this program's scope

**Given** at least one `--enable-cpl` coupled-build `Testing/` fixture
**When** it runs
**Then** it passes the standard regression comparison, recorded with Build/Test/Numerical evidence

### Story 13.3: CLM Land-Model Coupling Support-Tier Clarification

As a modeler choosing a land-model coupling option,
I want CLM4.5/ECLM documented as the supported-going-forward tier, and CLM3.5 marked formally deprecated in code comments,
So that the deprecation is an explicit, discoverable decision, and Epic 6's Story 6.2 has a formal policy to cite.

**Acceptance Criteria:**

**Given** CLM3.5's code paths
**When** this story completes
**Then** they carry code comments explicitly marking CLM3.5 deprecated, with CLM4.5/ECLM named as recommended

**Given** Epic 6's Story 6.2 already updates user-facing documentation citing this FR
**When** this story completes
**Then** the code-level marker and user-facing documentation agree — this story is the source-of-truth decision Story 6.2 references, not a duplicate of it

**Given** "formally deprecated" per this program's definition
**When** applied to CLM3.5
**Then** it means no further feature investment and bug-fix-only support if at all — not immediate removal, which is out of this story's scope

### Story 13.4: CISM Coupling Interface Design

As a future integrator connecting RegCM5 to the Community Ice Sheet Model,
I want a coupling interface design — field list, cadence, build gating (a new `--enable-*` option) — produced before any implementation begins,
So that a future implementation phase has a deliberate design to consume, not a start from zero.

**Acceptance Criteria:**

**Given** CISM has zero current codebase references (confirmed by repository search)
**When** this design is produced
**Then** it covers, at minimum, which fields RegCM5 would import from and export to CISM, at what cadence, and which existing coupling mechanism it would build on

**Given** this is a design task
**When** this story completes
**Then** no CISM implementation exists yet — implementation is explicitly out of scope, reserved for a future phase

**Given** Open Question 3 (whether CISM coupling is driven by a specific collaboration or is exploratory)
**When** this design is scoped
**Then** the answer determines design depth — confirmed with regcm5-dev, not assumed

### Story 13.5: Resolve BMI Status

As a future maintainer encountering `mod_bmiregcm.F90`,
I want BMI's dormant, inconsistent implementation resolved — either brought to genuine CSDMS BMI 2.0 compliance with a real caller/test, or formally deprecated and removed — with rationale documented,
So that the repository no longer contains a guarded, never-compilable implementation left in an ambiguous state.

**Acceptance Criteria:**

**Given** Open Question 1 is unresolved in the PRD (whether a concrete external BMI consumer exists)
**When** this story begins
**Then** the choice between implement-to-spec and deprecate-and-remove is confirmed with regcm5-dev first — not pre-decided, per the PRD's own explicit stance

**Given** no concrete external consumer is confirmed
**When** the decision is deprecate-and-remove
**Then** the guarded, non-compilable implementation is removed, with rationale documented (referencing the addendum's options-considered table)

**Given** a concrete external consumer is confirmed
**When** the decision is implement-to-spec
**Then** the implementation is brought to genuine compliance against RegCM5's actual `atm_model` type, with at least one real caller or test driver proving it works

**Given** either outcome
**When** this story completes
**Then** the repository no longer contains BMI in its current ambiguous state — either working and tested, or removed entirely
