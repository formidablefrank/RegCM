---
title: 'RegCM5 HPC Modernization'
status: 'final'
created: '2026-07-04'
updated: '2026-07-05'
---

# PRD: RegCM5 HPC Modernization

## 0. Document Purpose

This PRD scopes a modernization program for RegCM5, ICTP's regional climate model, covering defect remediation, refactoring, I/O scaling, selective GPU acceleration, external coupling hardening, and documentation correction. It is written for the model's scientific owner (regcm5-dev, who also holds sign-off authority per the project's governing rules) and for whoever implements each feature, whether that is regcm5-dev alone or an occasional external collaborator (e.g., NVIDIA engineers already contributing to the GPU-porting effort per recent commit history). It builds directly on two existing documents rather than duplicating them: `_bmad-output/project-context.md` (the codebase's governing technical rules) and the technical research note `_bmad-output/planning-artifacts/research/technical-regcm5-hpc-architecture-and-gpu-porting-risk-analysis-research-2026-07-04.md` (the evidence base for every risk and hotspot claim below). Implementation-level detail — file paths, line numbers, solver mechanisms, options considered and rejected — lives in `addendum.md`, not here. Features are grouped; functional requirements (FRs) are numbered globally (FR-1 through FR-38) so they remain stable references for downstream stories even if features are reorganized (FR-33 through FR-38 were added into Features 4.2/4.3/4.6 after FR-8 through FR-32 already existed, so numeric order does not always match document order — the ID is the stable reference, not its position). `[ASSUMPTION]` tags mark inferences made without direct confirmation; all are indexed in §9.

## 1. Vision

RegCM5 is a community regional climate model with a long deployment history and an active, if informal, path toward GPU-accelerated HPC hardware — evidenced by direct NVIDIA engineering contributions already present in its dynamical core. Two forces meet in this codebase today: the discipline of a scientific instrument, where numerical reproducibility and cross-vendor portability are non-negotiable, and the pressure of modern HPC hardware, where compute increasingly means GPUs and I/O increasingly means parallel filesystems at scale. The technical research completed ahead of this PRD found that RegCM5 handles that tension well in places (a disciplined `do concurrent`-first policy for new accelerator work, a genuinely 2D MPI domain decomposition) and poorly in others (an uninstrumented, best-guess view of where compute time actually goes; a dead external coupling contract masquerading as a maintained one; documentation that describes a codebase RegCM5 no longer is).

This modernization program closes that gap deliberately rather than opportunistically. It replaces guesswork about performance hotspots with measurement, extends parallel I/O from a restart-only feature to the model's main diagnostic-output path, scopes GPU acceleration to the subsystems where the evidence supports it rather than assuming success will generalize from the dynamical core, hardens the coupling contracts other models and components actually depend on (OASIS3-MCT, CLM, REGESM) while adding a new one (CISM) deliberately rather than by accretion, and brings the codebase's own documentation back into agreement with the codebase.

The same evidence-over-guesswork discipline extends to how this program validates and distributes its own work, not only to how it measures physics and I/O: an automated regression-diff tool, container images, and a triggered CI pipeline exist because "trust me, I tested it" does not scale past one person's manual NCO/CDO comparisons — they are the infrastructure that makes every other claim in this program checkable by someone other than the person who made it, not a separate modernization agenda bolted on alongside the performance work.

None of this changes what RegCM5 computes for a user who does not opt into a new capability. Every change is bound by the same acceptance discipline already in force for this codebase: bit-exact reproduction by default for CPU-only changes (an established statistical-reproducibility precedent for GPU porting specifically, per Cross-Cutting NFRs), an explicit and reviewed tolerance policy where a change is not bit-exact, and evidence — not intuition — behind every performance claim.

## 2. Target User

### 2.1 Jobs To Be Done

- **As the model's scientific owner and sole reviewer** (regcm5-dev), I need to know where compute time and I/O time actually go, so I can direct modernization effort at what matters instead of what merely looks expensive.
- **As a modeler running production simulations** (e.g., CORDEX-scale regional domains on Leonardo), I need diagnostic output to scale past current rank counts without becoming the bottleneck, and I need every optimization to preserve bit-exact or explicitly-tolerated results.
- **As whoever ports subsystems to GPU** (regcm5-dev, or an external collaborator such as the NVIDIA engineers already active across MOLOCH and the broader GPU-porting footprint documented in Feature 4.3), I need a scoped, evidence-based view of which subsystems are worth porting and which carry a documented risk of failing to parallelize at all, so effort is not sunk into a port that mirrors ICON-A's failed PSrad attempt.
- **As an integrator coupling RegCM5 to another model** (an OASIS3-MCT, CLM, REGESM, or future CISM partner), I need the coupling contract's field list and behavior to be documented and regression-tested, not inferred from source.
- **As a future contributor or maintainer**, I need the developer documentation to describe the codebase as it exists, not as it existed when the documentation was last true.

### 2.2 Non-Users (v1)

- Users of RegCM5's Python post-processing tooling (`Tools/Scripts/regcm_postproc-0.0.1/`) — unaffected by this program; it touches model output consumption, not model execution.
- Users still on the CLM3.5 land-model path — this program formally deprecates further investment there (§5).

### 2.3 Key User Journeys

*Lighter form used throughout: this is technical infrastructure work with a small, well-defined set of operator roles, not a UX-heavy product — each UJ is a single grounded sentence rather than a full scene.*

- **UJ-1.** regcm5-dev profiles a `test_00N.in` baseline run on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC) partitions, and for the first time sees measured — not inferred — time spent in RRTMG, chemistry integration, and diagnostic I/O. Realizes FR-1–FR-4.
- **UJ-2.** A modeler running a CORDEX-scale simulation at high rank count enables parallel diagnostic output and confirms, via the existing NCO/CDO comparison workflow, that results are bit-exact against the prior serial-write path. Realizes FR-5–FR-6.
- **UJ-3.** An NVIDIA collaborator evaluates whether RRTMG is worth porting to GPU, checks the go/no-go criteria against the ICON-A/PSrad precedent and regcm5-dev's baseline profile, and stops before investing further effort once the data says the payoff is uncertain. Realizes FR-9.

## 3. Glossary

- **`do concurrent`** — The Fortran 2008 loop-parallelism construct RegCM5 uses as its sole accelerator directive; NVHPC compiles it to on-node multicore (`-stdpar=multicore`) or GPU (`-stdpar=gpu`) from the same source.
- **OpenACC** — Directive-based accelerator API; configured as available in RegCM5's build (`--enable-openacc`). **Corrected**: far from unused — a repository audit (Feature 4.3) found `!$acc` directives in 90 files (1,476 lines), including the four confirmed hotspots and the halo-exchange layer (FR-11), contributed via the NVIDIA collaboration and already scientifically validated per regcm5-dev. This program's own new work still defaults to `do concurrent` first, escalating to OpenACC only where profiling shows `do concurrent` insufficient — a forward policy for new code, not a description of the codebase's current OpenACC footprint.
- **Halo exchange** — The MPI communication pattern (`exchange_array_r8/r4` and related routines in `Main/mpplib/mod_mppparam.F90`) that synchronizes tile-boundary ("ghost cell") data across RegCM5's 2D domain decomposition.
- **`assignpnt`** — RegCM5's internal pointer-aliasing mechanism (`Share/mod_memutil.F90`) by which physics subsystems share mutable state without copying; the concrete cause of the "pointer-aliasing is the #1 GPU-porting risk" hazard.
- **PnetCDF** — Parallel NetCDF; MPI-IO-based library enabling multiple MPI ranks to write a single NetCDF file concurrently. Currently used in RegCM5 only for restart files, not diagnostic history output.
- **Gather-then-write** — RegCM5's current default diagnostic-output pattern: all ranks' subdomains are gathered (`grid_collect`) onto one designated I/O rank, which then performs a single serial NetCDF write.
- **RRTMG** — RegCM5's primary radiation scheme (Rapid Radiative Transfer Model for GCMs); shares scheme lineage with ICON-A's PSrad, whose GPU port via directives failed to reach acceptable speedup.
- **KPP / DLSODE** — Kinetic PreProcessor-generated chemistry integrators (e.g., CB6r2, CBMZ mechanisms) using the stiff, implicit backward-differentiation-formula solver DLSODE, with data-dependent per-cell iteration counts.
- **BMI** — Basic Model Interface (CSDMS 2.0 standard); RegCM5's implementation (`mod_bmiregcm`) is a dead stub guarded by an undefined macro, not a working external contract.
- **OASIS3-MCT** — External coupler standard; RegCM5's implementation (`mod_oasis_interface`, `--enable-oasis`/`--enable-eclm`) is live and field-rich.
- **REGESM** — A second, independent RegCM5 coupling mechanism (`--enable-cpl`, `mod_update.F90`), architecturally parallel to but distinct from OASIS3-MCT.
- **CISM** — Community Ice Sheet Model; not currently referenced anywhere in the RegCM5 codebase (confirmed by repository search). A new coupling target for this program, not an existing one being hardened.
- **CLM / CLM4.5 / ECLM** — Community Land Model variants bundled in `Main/clmlib/`; CLM4.5 and ECLM are the supported-going-forward tier, CLM3.5 is formally deprecated under this program (§5).
- **`getcape`/CAPE-CIN** — Subroutine (`Share/mod_capecin.F90`) computing Convective Available Potential Energy and Convective Inhibition from a sounding; the single largest confirmed GPU-porting hotspot found to date (54% of wall-clock time in the source thesis's coupled-configuration profile).
- **MAD / RMSE / rMAD / rRMSE** — Mean absolute difference and root-mean-square error between a GPU-ported and reference (CPU) run, and their forms relative to the reference field's own magnitude; the statistical-reproducibility metrics the source thesis uses and this program's tolerance policy (FR-25) adopts, in place of assuming bit-exactness by default.
- **RCE** — Radiative-Convective Equilibrium configuration; an idealized, no-IO, no-lateral-forcing RegCM5 setup used for isolating computational (not physical) performance, distinct from a CLM4.5-coupled production configuration.
- **Flame graph / `perf` / Nsight Systems** — The profiling toolchain (Linux `perf_events` for CPU sampling and stack unwinding, NVIDIA Nsight Systems for GPU/compiler-runtime symbol attribution) this program adopts for Feature 4.1, matching the source thesis's methodology.
- **FORD** — Fortran Documenter; the established tool in the modern Fortran scientific-computing community for generating browsable HTML API documentation (module/procedure cross-references, call graphs) from source-level documentation comments. Adopted under FR-38, complementary to the hand-written developer guide (FR-21).
- **ICBC** — Initial and Boundary Conditions; the input data RegCM5 reads at startup and at boundary-update intervals (`globdatparam` in `Share/mod_dynparam.F90`), distinct from the output paths in Feature 4.2. Its I/O cost was not profiled in the technical research note and is closed out by FR-34.
- **Namelist** — RegCM5's configuration mechanism; ~40+ distinct blocks across `Share/mod_dynparam.F90` and `Main/mod_params.F90`, read with `iostat` error trapping but, for file-path variables specifically, no existence pre-check.
- **`rkx`** — RegCM5's sole sanctioned floating-point precision kind (from `mod_realkinds`), compile-time switchable single/double.
- **Regression-diff tool** — The automated tool this program adds (Feature 4.7) to replace manual NCO/CDO comparison of `Testing/` fixture output against a trusted baseline; usable on-demand on the HPC cluster and invoked by Feature 4.9's CI workflow.
- **Apptainer** — Unprivileged HPC container runtime (successor to Singularity); runs OCI/Docker images (`.sif` format) without a daemon or root access, the mechanism by which Feature 4.8's container images execute on Leonardo and comparable HPC systems.
- **OCI/Docker image** — The portable build/distribution artifact for Feature 4.8; built and runnable directly via Docker on a workstation, and convertible to an Apptainer `.sif` image for HPC execution.
- **Acceptance discipline** — This codebase's mandatory per-change record: Build (compiler/vendor), Test (which `Testing/` fixture, at what process count), Numerical (bit-exact or explicit tolerance), Performance (evidence-backed only). Every FR in this PRD inherits it; see §Constraints and Guardrails.

## 4. Features

### 4.1 Profiling and Evidence Baseline

**Description:** RegCM5 has DEBUG-gated timing instrumentation (`time_begin`/`time_end`) covering dynamics, cumulus, and surface physics, but not the diagnostic-output gather/write path, and radiation/chemistry coverage is partial. That said, this gap is only half the picture: an ICTP/SISSA Master's thesis (Tica, *GPU Porting and Optimization of the RegCM5*, 2024–2026, supervised by Girotto, Di Gioia, and RegCM co-developer Giuliani — source: `_bmad-source/regcm5-optimization.pdf`) already carried out real `perf`- and NVIDIA-Nsight-Systems-based profiling of the RegCM5–CLM4.5 coupled configuration on Leonardo, and its findings materially correct the structural (code-size-based) hotspot inference in the technical research note. This feature adopts that thesis's tooling and evidence as the starting baseline rather than re-deriving it, and extends profiling to what it did not cover. `[ASSUMPTION: instrumentation combines the codebase's existing DEBUG/`time_begin`/`time_end` convention for coarse subroutine-level timing with `perf` (flame graphs via Brendan Gregg's FlameGraph tool, `--call-graph dwarf` for full stack unwinding, requiring `-g` debug builds) and NVIDIA Nsight Systems (`nsys`, needed specifically to attribute compiler-runtime symbols — e.g. `__c_mset16_avx` — that `perf` alone cannot resolve to a source-level calling context) — matching the tooling the source thesis used, not a new profiling facility.]`

**Correction to the prior hotspot ranking**: the thesis's real profiling of a 1003×1003×50, CLM4.5-coupled, ERA5-driven run (16 GPUs + 16 CPU cores, 4 Booster nodes) found RRTMG does **not** appear as a named hotspot in the flame graph at all — the earlier research note's ranking of RRTMG as the leading compute-hotspot candidate was a reasonable inference from code size and call frequency, but is not what measurement shows for this configuration. The confirmed hotspots, in order of wall-clock share, are: (1) the `getcape`/CAPE-CIN diagnostic subroutine (`Share/mod_capecin.F90`, called from `output` in `Main/mod_output.F90`) — **54%** of wall-clock time, the single largest hotspot found, not previously identified anywhere in this program's research; (2) a compiler-generated `__c_mset16_avx` memset from noncontiguous row-slice whole-array initialization in `mod_clm_hydrology2` (CLM-specific, activated only in coupled runs) — ~20%; (3) `interp1d_r8` (`Share/mod_interp.F90`, called from aerosol data reading in `mod_rad_aerosol.F90`) — ~12%; (4) `heatindex` (`mod_heatindex.F90`, called from `collect_output` in `mod_lm_interface`) — ~8%. All four were already GPU-ported and benchmarked by the thesis — three offloading strategies (pure OpenACC, pure `do concurrent`, and a hybrid `do concurrent`+OpenACC-data-region approach) were each tried and found comparably effective specifically for `getcape`; `interp1d_r8` and `heatindex` were offloaded using OpenACC directly, and the merged pattern for all four (per `project-context.md`) is pure OpenACC — yielding a cumulative 7.10× speedup from these four fixes alone, and 14.17× with further optimization the thesis references but does not detail. This does not clear RRTMG of risk — it simply was not measured in this configuration, and the ICON-A/PSrad precedent (Architectural Patterns Analysis) still argues for measuring it directly rather than assuming either outcome — but RRTMG is no longer the presumptive top priority; it is unmeasured, on different footing from the four subroutines above whose cost share is now real, cited data, not inference.

**Functional Requirements:**

#### FR-1: Instrument RRTMG's compute core and confirm its cost share across configurations

The build can produce a DEBUG-enabled binary with `time_begin`/`time_end` wrapping RRTMG's driver and radiative-transfer kernels (`mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, `rrtmg_sw_rad.F90`), complemented by a `perf`/Nsight profiling pass, at minimum on a non-CLM-coupled configuration (e.g. BATS-coupled or the idealized RCE setup the thesis also benchmarked) where the thesis's CLM4.5-coupled result does not apply. Realizes UJ-1.

**Consequences (testable):**
- A DEBUG build run against a `Testing/` fixture emits timing output attributable to RRTMG's core routines, not only its outer driver.
- A `perf`/Nsight profile of at least one non-CLM-coupled configuration states RRTMG's measured wall-clock share, confirming or correcting the "not a hotspot" finding from the CLM4.5-coupled case before it is generalized.
- Non-DEBUG builds are unaffected (zero overhead, per existing convention).

#### FR-2: Instrument KPP chemistry integration

The build can produce a DEBUG-enabled binary with `time_begin`/`time_end` wrapping the KPP-generated integrator entry points (e.g., `mod_cb6_Integrator.F90`, `mod_cbmz_integrator.F90`) for each active gas-phase mechanism. Realizes UJ-1.

**Consequences (testable):**
- Timing output distinguishes chemistry integration time from other chemistry support routines already instrumented (drydep, emission, boundary).

#### FR-3: Instrument diagnostic-output gather/write, and profile the parallel-I/O-slowdown puzzle

The build can produce a DEBUG-enabled binary with `time_begin`/`time_end` wrapping the gather (`grid_collect`) and NetCDF-write phases in `Main/mpplib/mod_ncout.F90`, separately measurable from compute time. This explicitly feeds FR-34 (§4.2): the source thesis measured that enabling parallel write (both HDF5-parallel and PnetCDF-parallel) was consistently *slower* than serial sequential write across every rank count tested (400–800 CPUs, 8–64 GPUs) in the coupled configuration, and named the cause as open future work — this instrumentation is what makes that investigation tractable rather than repeating an unexplained puzzle. Realizes UJ-1.

**Consequences (testable):**
- Timing output separates I/O-rank gather time from write time from compute-rank idle time during a write event, for each of the serial, HDF5-parallel, and PnetCDF-parallel write paths.
- A profile exists that can distinguish where the parallel-write paths spend additional time relative to serial write (e.g., collective-I/O synchronization, metadata operations, or interconnect contention), providing the evidence FR-34 needs to explain the thesis's unresolved finding.

#### FR-4: Baseline profiling run and published report, building on existing thesis data

A baseline run of a representative `Testing/` fixture is executed and profiled (via `perf` and Nsight Systems, matching the source thesis's methodology) on both `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC) partitions, explicitly building on — not repeating from zero — the source thesis's existing CLM4.5-coupled profiling data. The resulting hotspot breakdown is recorded as a short internal report referenced by Features 4.2 and 4.3, extending coverage to configurations and subsystems the thesis did not profile (non-CLM-coupled runs, boundary-condition/ICBC input I/O, higher resolutions). Realizes UJ-1.

**Consequences (testable):**
- The report states, per subsystem and per configuration, measured wall-time share on each partition — not an estimate — explicitly citing the source thesis's existing getcape/CAPE-CIN (54%), CLM-hydrology memset (~20%), `interp1d_r8` (~12%), and `heatindex` (~8%) findings for the CLM4.5-coupled case, rather than restating the technical research note's structural inference.
- Feature 4.3's go/no-go decisions (FR-9) cite this report and the source thesis, not the technical research note's structural inference, as their evidence base.

**Notes:** `[NOTE FOR PM]` This feature deliberately produces no user-facing change. Its value is unblocking evidence-based decisions in Features 4.2 and 4.3 by building on real prior profiling work rather than repeating it from zero; do not skip it under schedule pressure. (Open Question 8's merge-status discrepancy — the research note found zero `!$acc` directives, despite the four hotspot ports now being confirmed present — is resolved; see FR-35.)

### 4.2 I/O Scaling and Optimization

**Description:** RegCM5's default diagnostic-output path gathers all ranks onto one I/O rank before a serial NetCDF write. PnetCDF (true MPI-IO-based parallel writes) already exists in the codebase but is scoped only to restart files. This feature extends parallel-write capability across every RegCM5 output path — diagnostic/history (`mod_ncout.F90`), restart/checkpoint (`mod_savefile.F90`), and land-model history output (CLM4.5/ECLM's own mechanism, when land coupling is active) — while preserving the existing serial gather-write behavior as the default fallback for builds without PnetCDF or without real MPI (`mpi-serial` builds must keep working unmodified, per the portability constraint). The technical research note inferred from output-write cadence alone (3-6 simulated hours) that this was a burst-cost problem, not a sustained one — regcm5-dev's production experience corrects that: I/O measurably dominates wall-clock time in practice at rank counts higher than the `Testing/` fixtures typically exercise. This feature is accordingly treated as a confirmed, not merely hypothesized, bottleneck across all output paths, and a dedicated profiling investigation (FR-34) — closing the boundary-condition/ICBC input-I/O gap the technical research note left open — produces concrete optimization recommendations rather than assuming FR-5/FR-6's parallel-write extension alone is sufficient.

**Functional Requirements:**

#### FR-5: Parallel NetCDF write for diagnostic/history output

Diagnostic and history output (`Main/mpplib/mod_ncout.F90`) can be written via PnetCDF when the build is configured with `--enable-pnetcdf`/`--enable-parallel-nc` and the run enables it, in addition to its current restart-file-only scope. **This capability ships as a tested, documented option, not a promoted default**, until FR-34 explains the source thesis's measured parallel-write slowdown (see FR-34) — recommending it as an improvement before that cause is understood would repeat the same evidence-free-optimization mistake this program exists to eliminate. Realizes UJ-2.

**Consequences (testable):**
- A `Testing/` fixture run with parallel diagnostic output enabled produces NetCDF output that is bit-exact (same field values) against the equivalent serial gather-write run.
- The change is verified at more than one process count, per the project's stencil/parallel-code regression rule.

**Out of Scope:** Compression-parity with netCDF-4 parallel HDF5 output is not required — PnetCDF's classic format tradeoffs (documented in the technical research note) are accepted as-is for this feature.

#### FR-6: Serial gather-write remains the default, working fallback

Builds without PnetCDF, or runs that do not opt into parallel output, continue to use the existing gather-then-write path unmodified. Realizes UJ-2.

**Consequences (testable):**
- A `mpi-serial` (fully serial) build compiles and runs `Testing/` fixtures unaffected by this feature.
- No output format or file-naming change is observable to a user who does not opt into parallel output.

#### FR-7: Evaluate asynchronous NetCDF writes as a complementary optimization

The existing pthread-backed `mod_async_netcdf.F90` facility is evaluated against FR-4's baseline as a lower-effort alternative or complement to PnetCDF for hiding write latency behind computation, and a recommendation (adopt, extend, or leave as-is) is documented.

**Consequences (testable):**
- A written recommendation exists, backed by FR-4 baseline data, stating the measured percentage reduction (or increase) in I/O-attributable wall time async-netcdf delivers versus PnetCDF alone, at the same rank count — a number, not a qualitative "helps"/"doesn't help" judgment.

#### FR-33: Extend I/O scaling to all RegCM5 output paths

Restart/checkpoint output (`Main/mod_savefile.F90`) and land-model history output (CLM4.5/ECLM's own mechanism, e.g. `mod_clm_histflds.F90`, when land coupling is active) are included in this feature's scope alongside diagnostic/history output (FR-5/FR-6), so profiling and parallel-I/O improvements apply uniformly across every output path RegCM5 writes, not diagnostic output alone.

**Consequences (testable):**
- Restart-file writes are profiled (extending FR-3) and evaluated for the same scaling questions as diagnostic output, even though some restart configurations already use PnetCDF — confirming whether current restart I/O performance is itself a bottleneck at high rank counts, rather than assuming it isn't.
- CLM4.5/ECLM's land-model history output path is identified, profiled, and included in FR-34's recommendations when land coupling is enabled.

#### FR-34: I/O profiling and optimization investigation across all output and input paths

A dedicated investigation profiles all RegCM5 I/O paths — diagnostic/history, restart/checkpoint, land-model history (when active), and boundary-condition/ICBC input reads (flagged as unprofiled in the technical research note) — at representative rank counts, and produces a written set of concrete, actionable optimization recommendations informed by FR-3's instrumentation and FR-4's baseline methodology. **This investigation has a specific, already-documented puzzle to resolve first**: the source thesis (`_bmad-source/regcm5-optimization.pdf`) measured that, in the CLM4.5-coupled configuration, both HDF5-parallel and PnetCDF-parallel writes are consistently *slower* than serial sequential write across every tested rank count (e.g., at 800 CPU cores: sequential 3.7 h vs. HDF5-parallel 7.7 h vs. PnetCDF-parallel 4.0 h) — the opposite of what enabling parallel I/O is normally expected to deliver — and the thesis explicitly names understanding this as unresolved future work. Before this feature recommends adopting parallel diagnostic output as a default improvement (as an earlier draft of this PRD assumed), that measured regression must be explained.

**Consequences (testable):**
- A written report states measured I/O time share per path (diagnostic, restart, land-model, boundary-condition input) at more than one rank count, for each of serial, HDF5-parallel, and PnetCDF-parallel write modes.
- The report explains, with profiling evidence (FR-3), why parallel write underperforms serial write in the coupled configuration on Leonardo — e.g., collective-I/O synchronization overhead, striping/chunking mismatch, metadata contention — rather than leaving it as an open mystery inherited from the source thesis.
- Recommendations are concrete (e.g., "enable parallel diagnostic output above N ranks once cause X is fixed," "adjust striping/chunking parameter Y") rather than generic ("improve I/O"), and are conditioned on the explanation above rather than assuming parallel I/O is strictly better.
- Boundary-condition/ICBC input I/O — explicitly flagged as unprofiled and out of scope in the original technical research note — is no longer an open item once this FR completes.

**Feature-specific NFRs:**
- FR-5/FR-6's "adopt parallel write" framing is conditioned on FR-34's findings: if FR-34 confirms parallel write is currently slower for this workload, FR-5 ships as a documented, tested, but *not default-recommended* option pending the fix, rather than being promoted as an improvement on unverified assumptions.
- Any change to `mod_ncout.F90`, `mod_savefile.F90`, or CLM's history output must preserve existing output file format and variable naming for downstream consumers (PostProc, external analysis pipelines) unless a run explicitly opts into a new mode.

### 4.3 Selective GPU Acceleration

**Description:** RegCM5's `do concurrent`-first policy for this program's own new accelerator work is sound and should not be abandoned, but cross-vendor `do concurrent` support is genuinely uneven, so GPU-porting effort must be allocated by evidence, not by assuming one subsystem's success generalizes. The evidence base has changed materially since this PRD's first draft: the source thesis (`_bmad-source/regcm5-optimization.pdf`) already GPU-ported and benchmarked the four confirmed hotspots from Feature 4.1 (`getcape`/CAPE-CIN, the CLM-hydrology memset, `interp1d_r8`, `heatindex`), achieving a cumulative 7.10× speedup from those four fixes and 14.17× with further unpublished optimization — work this program should verify, integrate, and extend rather than repeat. RRTMG, previously treated as the leading GPU-porting risk on structural inference (ICON-A/PSrad precedent), was not observed as a hotspot in the thesis's coupled-configuration profiling; it remains worth measuring directly (FR-1) before either committing effort to it or dismissing the ICON-A precedent as inapplicable. Gas-phase chemistry (KPP/DLSODE) GPU porting is explicitly excluded from this feature (§5) pending FR-2's profiling data.

**Correction (discovered during the follow-on architecture session, resolves Open Question 11):** the "four confirmed hotspots" framing above describes the thesis's own measured, published benchmark set — accurate as far as it goes, but incomplete as a picture of this codebase's actual GPU-porting footprint. A repository-wide audit found `!$acc` directives in 90 files (1,476 lines) — `do concurrent` alone spans a separate, larger footprint (95 files) since it is RegCM5's general parallel-loop construct, not a GPU-porting signal on its own; `!$acc` specifically marks the OpenACC escalation this feature cares about — reflecting over a year of sustained work by NVIDIA engineers (Everett Phillips, Massimiliano Fatica) across MOLOCH, the full CLM4.5 land-model library, cloud/cumulus/microphysics, the ocean library, the PBL library, OASIS coupling, async netCDF I/O, and — materially — the halo-exchange layer itself (`Main/mpplib/mod_mppparam.F90`, including a working GPU-direct exchange implementation; see the corrected FR-11 below). regcm5-dev confirms this broader work has already gone through the project's scientific-validation discipline; FR-35 is rescoped accordingly from "verify four ports" to "verify and document the full existing footprint."

**Functional Requirements:**

#### FR-8: Cross-vendor `do concurrent` parallelization verification

For every `do concurrent` loop added or modified under this program, verification exists that it parallelizes (not merely compiles) under GNU, Intel, and NVHPC, added as a checklist item to the project's existing manual validation process. Realizes UJ-3. **Scope note**: this FR covers `do concurrent` loops specifically (e.g., MOLOCH, advection/tendency code); the four hotspots already ported under FR-35 use OpenACC directly (the pattern actually merged, per `project-context.md`), not `do concurrent`, so their cross-vendor portability concern is OpenACC's own (strongest on NVIDIA), tracked separately, not by this FR.

**Consequences (testable):**
- A documented procedure (`-Minfo=accel` on NVHPC, and the corresponding vendor diagnostic flags on GNU/Intel) exists and is applied to at least the loops touched by FR-10.
- Per-vendor expectations are set correctly, not uniformly: NVHPC's `-stdpar=gpu`/`-stdpar=multicore` is the mature GPU+CPU path; Intel's `ifx` offloads to Intel GPUs via an OpenMP backend (verify CPU and, where an Intel GPU target exists, GPU separately); GNU's `gfortran` has **no `do concurrent` GPU offload path at all** (CPU auto-parallelization only, per the source thesis's own compiler-support table) — a loop is expected to run serial-but-correct on GNU's device path, not silently fail, and this is not a gap to "catch," it is the documented current state of that compiler.
- A loop that compiles under all three vendors but parallelizes only under NVHPC (where GPU parallelization was actually expected, i.e. not GNU) is caught by this procedure before merge, not discovered later as a silent performance regression.

#### FR-9: RRTMG GPU-porting feasibility investigation with go/no-go checkpoint

A scoped investigation evaluates whether RRTMG's radiative-transfer kernels are likely to benefit from `do concurrent`/OpenACC porting, using FR-1's direct measurement (not the earlier structural inference) and the ICON-A/PSrad precedent as explicit inputs, and produces a go/no-go recommendation before any RRTMG porting implementation begins. Given FR-1 found no RRTMG hotspot presence in the CLM4.5-coupled configuration, this investigation should treat "RRTMG is low priority in that configuration" as a live possible outcome, not assume the ICON-A precedent necessarily applies. Realizes UJ-3.

**Confirmed by the follow-on architecture session's repository audit**: RRTMG's own kernel files (`mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, `rrtmg_sw_rad.F90`, and the ~25 supporting `rrtmg_*.F90` files) carry zero `!$acc`/`do concurrent` directives — this FR's core premise stands. The surrounding column-radiation driver (`Main/radlib/mod_rad_colmod3.F90`, cloud/aerosol optical-property preparation that calls into RRTMG, not RRTMG's own math) does carry existing, validated GPU work — a distinct, smaller fact worth noting so a future reader doesn't conflate the two.

**Consequences (testable):**
- The investigation's written output states, with reasoning tied to FR-4's measured data, whether RRTMG porting proceeds, is deferred, or is rejected in favor of a scheme-replacement path (analogous to ICON-A's RTE+RRTMGP move) — not silently assumed.
- If the recommendation is "proceed," it defines the acceptance discipline (Build/Test/Numerical/Performance) that any resulting implementation work must meet.

**Out of Scope:** Implementing a RRTMG replacement scheme (RTE+RRTMGP or equivalent) is out of scope for this PRD even if FR-9 recommends it — that would be a numerics-review-level change warranting its own scoping.

#### FR-10: Continue MOLOCH dynamical-core GPU porting

Ongoing `do concurrent`-based GPU-porting work on `Main/mod_moloch.F90` continues under the existing strategy, with each change meeting the project's full acceptance discipline (build, `Testing/` fixture, numerical tolerance, performance evidence) and FR-8's cross-vendor verification.

**Consequences (testable):**
- Each MOLOCH GPU-porting change ships with a commit/PR record stating Build, Test, Numerical, and Performance per the existing project convention.
- Since MOLOCH's `do concurrent` loops include stencil operations with `i±1`/`j±1` neighbor access near tile boundaries, every such change is additionally regression-checked at more than one MPI process count (per the project's stencil/halo rule) — a single-rank (`nproc=1`) pass is not sufficient evidence, since a decomposition bug can be invisible there.

#### FR-11: Verify and document the existing GPU-direct halo exchange implementation

**Corrected from an earlier draft**, which scoped this FR as a feasibility investigation into whether `Main/mpplib/mod_mppparam.F90`'s halo-exchange routines *could* become GPU-direct-capable, with no implementation committed. A repository audit during the follow-on architecture session found that GPU-direct exchange (exploiting HPC-X 2.25's GPUDirect RDMA path) is already implemented — `mod_mppparam.F90` carries 198 `!$acc` directive lines, including `!$acc data copyin(...)/copyout(...)` and `!$acc host_data use_device(...)` patterns, delivered via a specific, named contribution ("4d exchange implemented on GPU," From Everett@NVIDIA). regcm5-dev confirms this work has already been scientifically validated. This FR is accordingly a verification-and-documentation task, matching FR-35's corrected scope: confirm the existing implementation builds and runs correctly under the project's current target versions (HPC-X 2.25, the version this FR originally cited as the forward-looking target), identify which exchange routines are covered by the GPU-direct path versus still host-buffer-staged, and record the result for FR-8's cross-vendor check and FR-37's reproducibility work.

**Consequences (testable):**
- A short document exists stating which halo-exchange routines in `mod_mppparam.F90` use the GPU-direct path today and which remain host-buffer-staged, confirmed against the current target versions rather than assumed current from when the work was contributed.
- Any exchange routine that does not build or behave as documented under current target versions is logged as a specific, scoped follow-up.
- The document separately notes whether evaluating NVHPC's more advanced unified-virtual-memory mode (`mem:unified`, vs. the `mem:managed` mode the source thesis's benchmarks used) on newer hardware (H100/GH200) is worth its own follow-up investigation, per the thesis's own unresolved future-work item — without committing this program to that evaluation.

#### FR-35: Verify and document the existing GPU-porting work — full repository scope

regcm5-dev confirms the GPU-porting changes for `getcape` (`Share/mod_capecin.F90`), the CLM-hydrology memset fix (`mod_clm_hydrology2`), `interp1d_r8` (`Share/mod_interp.F90`), and `heatindex` (`mod_heatindex.F90`) documented in the source thesis are already present in the codebase this program builds on (resolves Open Question 8) — this reconciles what had looked like a contradiction with the technical research note's "zero `!$acc` directives" finding, which evidently predates this merge.

**Corrected from an earlier draft**, which scoped this FR to only these four subsystems. A repository-wide audit during the follow-on architecture session (`git grep` for `!$acc` directives specifically — `do concurrent` alone is a separate, larger footprint of 95 files, since it is RegCM5's general parallel-loop construct rather than a GPU-porting signal on its own) found the actual footprint is far larger: 90 files, 1,476 directive lines, also covering `Main/mod_moloch.F90` (tracked separately under FR-10), the full CLM4.5 land-model library (30+ files beyond the hydrology memset fix — biogeophysics, canopyfluxes, urban, dust, and more), the cloud/cumulus/microphysics libraries, the ocean library, the PBL library, OASIS coupling code, async netCDF I/O (`Share/mod_async_netcdf.F90`), and the halo-exchange layer (`Main/mpplib/mod_mppparam.F90` — see the corrected FR-11, tracked as its own FR given its direct relevance to FR-8/FR-26's decomposition-and-portability concerns). Git history attributes this to over a year of sustained contribution (2025-04-23 through at least 2026-06-08) from two named NVIDIA engineers, Everett Phillips and Massimiliano Fatica. regcm5-dev confirms this broader work has already gone through the project's scientific-validation discipline (Resolves Open Question 11) — this FR is accordingly a verification-and-documentation task at the full repository scope, not a re-implementation one, and not a fresh scientific-review task: confirm each already-validated GPU-ported subsystem compiles and runs under the project's current target versions (Technology and Dependency Targets, including the NVHPC 24.5→26.3 version gap noted there), and record locations for FR-8's cross-vendor check and FR-37's reproducibility work.

**Consequences (testable):**
- A document exists enumerating every GPU-ported subsystem found in the repository audit (not only the four thesis-documented ones), each with its current location in the tree, confirming it builds under the project's target compiler versions — excluding MOLOCH (tracked under FR-10) and halo exchange (tracked under FR-11), which this document cross-references rather than independently re-verifies.
- Any port that does not build or behave as documented under the current target versions is logged as a specific, scoped follow-up — not silently assumed to still work because it worked under an earlier NVHPC version.
- The document distinguishes, per subsystem, whether it was validated by the source thesis directly (the original four) or through the broader NVIDIA collaboration's own process (regcm5-dev-confirmed, the balance of the 90-file footprint) — a provenance distinction worth preserving even though both are accepted as validated.

#### ~~FR-36: Restore bit-exact reproducibility for the four already-ported GPU hotspots~~ — Retired

Retired after reconciling a genuine conflict: `project-context.md` documents, as an established project precedent, that CPU-to-GPU porting specifically is accepted at statistical (not bitwise) reproducibility, with the source thesis's measured bounds as the reference. regcm5-dev confirmed this precedent governs (not the stricter answer given earlier in review), so the four already-merged GPU ports (`getcape`, `mod_clm_hydrology2`, `interp1d_r8`, `heatindex`) were never non-compliant — they were following the project's own accepted policy for this category of change. No bit-exactness-restoration work is needed. See FR-37 for the regression test that now enforces this policy going forward, and FR-25 for how the tolerance mechanism reflects it.

#### FR-37: Statistical-reproducibility regression test for GPU-ported code

A regression test enforces the project's established statistical-reproducibility policy for CPU-to-GPU porting: `tas` and `ps` rMAD/rRMSE under ~0.1%, `huss` under ~5%, over a 7-model-day `Testing/`-scale run, pinned to the source thesis's measured bounds — using FR-24's regression-diff tool and FR-25's per-field tolerance mechanism. This is the project's actual accepted numerical bar for GPU-ported code (distinct from the bit-exact default that still governs CPU-only changes), not an interim measure pending a stricter fix.

**Consequences (testable):**
- A CI run (once FR-31 exists) or on-demand regression-diff invocation (FR-24) fails if `tas`/`ps` rMAD/rRMSE exceeds ~0.1% or `huss` exceeds ~5% against the GPU-ported baseline, with thresholds pinned to the source thesis's measured values and changeable only with regcm5-dev's explicit sign-off.
- New GPU-porting work under this program (FR-9, FR-10, FR-11) is held to these same thresholds by default — the same reviewed statistical-reproducibility policy, not a fresh case-by-case negotiation each time.
- The test's documentation states plainly that this is the accepted policy for GPU-ported code specifically, per `project-context.md`, so a future reader does not mistake it for an unreviewed or temporary shortcut.

#### FR-12: Configurable GPU target architecture

The hardcoded `PGI_GPU_ARCH="ccnative"` build setting (`configure.ac:140`) becomes a configurable option, so a target GPU's compute capability can be pinned explicitly when auto-detection is insufficient.

**Consequences (testable):**
- A configure-time option exists to override `PGI_GPU_ARCH`; omitting it preserves current auto-detect (`ccnative`) behavior.

**Feature-specific NFRs:**
- No FR in this feature may reduce numerical reproducibility below whichever bar applies (bit-exact for anything not touching the GPU-ported code path; the established statistical bounds in FR-25/FR-37 for GPU-ported code) as a side effect of pursuing performance.

### 4.4 External Coupling Modernization

**Description:** RegCM5 has three coupling-relevant external contracts in three different states — OASIS3-MCT (live, field-rich), REGESM (live, independent field list), and BMI (dead code behind an undefined macro) — plus land-model coupling (CLM4.5/ECLM live, CLM3.5 legacy) and a fourth partner, CISM, with zero current codebase references. This feature documents and regression-hardens what is live, formally resolves what is dormant, and scopes what is new as a design task before implementation, consistent with the project's rule that external-contract changes need explicit flagging rather than routine review.

**Functional Requirements:**

#### FR-13: OASIS3-MCT field-exchange documentation and regression coverage

The current OASIS3-MCT import/export field list (per `--enable-oasis`/`--enable-eclm` build mode) is documented against the live code (not inferred from a prior version), and a `Testing/` fixture exercising `--enable-oasis` passes the project's standard regression comparison.

**Consequences (testable):**
- A field-list document exists, current as of this program's completion, distinguishing base-OASIS fields from ECLM-only additional fields.
- At least one coupled-build regression run is recorded with Build/Test/Numerical evidence.

#### FR-14: REGESM field-exchange documentation and regression coverage

The current REGESM (`--enable-cpl`) import/export field list (`mod_update.F90`'s `imp_data`/`exp_data`) is documented against the live code, and a `Testing/` fixture exercising `--enable-cpl` passes the project's standard regression comparison.

**Consequences (testable):**
- A field-list document exists for REGESM, explicitly distinguished from the OASIS3-MCT field list (§3 Glossary: these are independent mechanisms, not a shared abstraction).

#### FR-15: CLM land-model coupling support-tier clarification

CLM4.5 and ECLM are documented as the supported-going-forward land-model coupling tier; CLM3.5 is marked formally deprecated (no further feature investment, bug-fix-only if at all) in both code comments and user-facing documentation (ties to FR-23).

**Consequences (testable):**
- Build and user documentation state the CLM3.5 deprecation explicitly, with CLM4.5/ECLM as the recommended path.

#### FR-16: CISM coupling — interface design

A coupling interface design for CISM (Community Ice Sheet Model) is produced — field list, coupling cadence, build gating (new `--enable-*` option analogous to existing coupling flags) — before any implementation begins, since this is new capability with no existing code to extend.

**Consequences (testable):**
- A design document exists covering, at minimum, which fields RegCM5 would import from and export to CISM, at what cadence, and which existing coupling mechanism (OASIS3-MCT-style vs. a new path) it would build on.

**Out of Scope:** Implementing CISM coupling is out of scope for this PRD; FR-16 delivers the design that a future implementation phase would consume.

#### FR-17: Resolve BMI status

BMI's dormant, internally-inconsistent implementation (`Main/mod_bmiregcm.F90`) is either (a) brought to genuine CSDMS BMI 2.0 compliance against RegCM5's actual `atm_model` type, with at least one real caller or test driver proving it works, or (b) formally deprecated and removed, with the decision and rationale documented. `[ASSUMPTION: this PRD does not pre-decide (a) vs. (b) — that choice depends on whether a concrete external BMI consumer exists, which is an Open Question (§8), not something inferable from the codebase.]`

**Consequences (testable):**
- The repository no longer contains a `#ifdef DEVELOPMENT`-guarded, never-compilable BMI implementation left in an ambiguous state — it is either working and tested, or removed.

**Feature-specific NFRs:**
- Any field-list documentation produced under this feature (FR-13, FR-14, FR-16) is treated as the authoritative source for that contract going forward, superseding inference from source reading.

### 4.5 Namelist, Build, and Compiler-Identity Hardening

**Description:** No pre-existing bug backlog exists for this program — confirmed with regcm5-dev, who expects defect discovery to come out of Phase 1 profiling (FR-1–FR-4) and the existing `Testing/` fixtures, not an informal list. This feature is accordingly modest in scope: three small, concrete, evidence-based hardening items the technical research surfaced directly (not a general "defect remediation" program), with future defect discovery flowing through that same evidence path rather than an informal list.

**Functional Requirements:**

#### FR-18: File-path namelist existence validation

Namelist variables that name a filesystem path (`dirglob`, `inpglob`, `dirter`, `inpter`, `dirclm`, `cmip6_inp`, and equivalents) are checked for existence immediately after the namelist read, failing fast with a clear diagnostic naming the offending variable and path, instead of surfacing only later as a NetCDF/IO error inside `checkncerr`/`fatal`.

**Consequences (testable):**
- A namelist with a placeholder or mistyped path variable (e.g., an unedited `Testing/*.in` fixture) fails immediately at startup with a message identifying the specific namelist variable and path, not a downstream NetCDF error.
- Existing valid namelists (all current `Testing/` fixtures once correctly edited) are unaffected.

#### FR-19: Long-running memory-growth investigation

Given that explicit `relmem` deallocation exists at only three call sites in all of `Main/` (workspace allocated via `getmem` otherwise lives until process exit), an investigation determines whether this causes measurable memory growth in long-running or ensemble-style jobs, and remediation is scoped only if a real issue is confirmed — this FR does not presuppose a fix is needed.

**Consequences (testable):**
- A written finding states, with measured evidence (e.g., peak RSS over a long `Testing/` or CORDEX-scale run), whether memory growth from unreleased `getmem` allocations is or is not a practical problem.
- If confirmed, remediation scope is defined as a follow-up, not implemented blind under this FR.

#### FR-20: NVHPC compiler-identity correction

The build system's compiler-vendor detection gives NVHPC (`nvfortran`) its own `COMPILER_NVHPC` identity, distinct from `COMPILER_PGI`, without changing any currently-applied compiler flags or behavior.

**Consequences (testable):**
- `configure.ac` reports `COMPILER_NVHPC` for `nvfortran`/`nvf9*` inputs where it previously reported `COMPILER_PGI`.
- All existing OpenACC/`do concurrent`/stdpar flag selection continues to apply identically (this is a naming/identity correction, not a behavior change) — verified by an unchanged build output for at least one `Testing/` fixture.

**Notes:** `[NOTE FOR PM]` FR-20 is intentionally low-risk and low-effort; it is included in Phase 1 (§6) precisely because it unblocks any future NVHPC-specific work (e.g., FR-12) without itself carrying numerical risk.

### 4.6 Documentation Modernization

**Description:** Three documentation gaps were confirmed against the live codebase: a stale developer guide making incorrect claims, an absent record of the GPU-porting research and risk findings this program is built on, and user-facing namelist/run documentation that does not warn users about known pitfalls (e.g., unedited placeholder paths in test fixtures). This feature closes all three.

**Functional Requirements:**

#### FR-21: Correct stale precision and module-lifecycle claims, in the Dev Guide and in `project-context.md` itself

The developer guide's precision claims (currently describing hardcoded 64-bit `dp`, contradicting the actual `rkx`-based system) and module-lifecycle claims (currently describing an `init_mod_*`/`release_mod_*` pattern) are corrected to match the codebase as it exists, per the technical research note's repo-wide finding of **zero** `release_mod_*` definitions anywhere in the tree. This correction is not confined to `Doc/DeveloperGuide/MainDeveloperGuide.tex` — the current `project-context.md` (§ Module Skeleton) still states the same `init_mod_*`/`release_mod_*` pattern as the governing convention, so it needs the identical correction, not just its downstream copy in the Dev Guide.

**Consequences (testable):**
- The guide's precision section describes `rkx` (from `mod_realkinds`) as the sole precision knob.
- Both the guide's module-lifecycle section and `project-context.md`'s Module Skeleton rule describe the actual `allocate_*`/centralized `getmem`/`relmem` pattern, not `init_mod_*`/`release_mod_*`.

#### FR-22: GPU-porting and performance guidance document

A new document captures the `do concurrent`-only accelerator strategy, the per-subsystem risk tiering now grounded in measured data (`getcape`/CAPE-CIN, CLM-hydrology, `interp1d_r8`, and `heatindex` confirmed and largely already ported per the source thesis; RRTMG and chemistry still unmeasured and open per FR-1/FR-2), the cross-vendor verification procedure (FR-8), and the recommended validation sequencing, so future porting decisions build on this program's findings instead of relitigating them.

**Consequences (testable):**
- The document exists in a location a future contributor would find (e.g., alongside `Doc/DeveloperGuide/`), and is referenced from FR-9's and FR-10's acceptance records.

#### FR-38: Adopt FORD for auto-generated API documentation

RegCM5 has no auto-generated API-level documentation today — understanding module and procedure relationships requires reading source directly, or relying on the hand-written (and, per FR-21, partially stale) developer guide. This FR adopts FORD (Fortran Documenter), the established tool for this purpose in the modern Fortran scientific-computing community, to generate browsable HTML documentation (module/procedure cross-references, call graphs, source browsing) from source-level documentation comments. `[ASSUMPTION: this reverses the earlier documentation-scope decision that excluded "deep internal architecture-reference-style docs" by omission — flagged as a direct expansion of that scoping, requested directly rather than inferred.]` FORD's output is complementary to, not a replacement for, FR-21's narrative developer guide — one is auto-generated API reference, the other is hand-written prose explaining precision/lifecycle conventions.

**Consequences (testable):**
- A FORD project configuration file exists at the repository root (or under `Doc/`), configured for at minimum `Main/`, `Share/`, and `PreProc/` (matching the existing build-stage directory boundaries from the Architectural Patterns Analysis), and running FORD against it produces browsable HTML output without error.
- Every module or procedure touched by this program's own FRs (the four already-GPU-ported hotspots, `mod_mppparam`, `mod_dynparam`, the coupling interface modules) carries FORD-compatible documentation comments (`!!`/`!>`) as part of that FR's own completion criteria — this FR does not retrofit annotations across the entire codebase in one pass.
- The generated FORD output is built on demand (e.g., a documented manual step, or alongside FR-31's CI pipeline once it exists) rather than generated once and left to go stale.

**Out of Scope:** Retrofitting FORD-style documentation comments across the full codebase (590+ modules in `Main/` alone, per the technical research note) is out of scope — coverage grows incrementally as this program's own FRs touch code, not as a dedicated documentation sprint.

#### FR-23: User-facing namelist and run documentation

Namelist documentation (e.g., `Doc/README.namelist` or equivalent) is updated to reflect the CLM3.5 deprecation (FR-15) and to explicitly warn that several `Testing/*.in` fixtures ship with literal placeholder paths requiring edits before use, rather than leaving this as tribal knowledge.

**Consequences (testable):**
- A user reading the updated documentation before running an unedited `Testing/*.in` fixture is warned about placeholder paths before encountering the failure FR-18 now catches faster.

### 4.7 Automated Regression Infrastructure

**Description:** RegCM5 has no working *automated, wired-into-the-build* regression-diff tool today: `Tools/Scripts/BuildBot/testing.py` is dead Python 2, and `Tools/Scripts/TestingAndBenchmarking/preproc-compare.py` only compares ICBC initial conditions between RegCM v3 and v4 for 1-month simulations, not general model output. There is, however, existing prior art worth building on rather than replacing: the source thesis (`_bmad-source/regcm5-optimization.pdf`, Appendix B) documents a working Python/NCO reproducibility-diagnostic workflow (`concat_diff_var.py`, `multi_day_stats_generic.py`, `spatial_maps_generic.py`, run inside an `nco-tools` conda environment atop `ncrcat`/`ncdiff`/`ncap2`) that already computes exactly the statistical divergence metrics — mean absolute difference (MAD), root-mean-square error (RMSE), and their scale-relative forms rMAD/rRMSE — this feature needs. This feature hardens and wires in that existing workflow as the project's regression-diff tool, rather than building an unrelated one from scratch. `[ASSUMPTION: "CI" here means an automated regression-diff tool invocable on demand (as a Slurm job or login-node script) against Testing/ fixtures, not an always-on triggered pipeline — the project has no existing trigger infrastructure and the login-node fair-use policy constrains unattended automation. See Open Question 6 to confirm.]`

**Functional Requirements:**

#### FR-24: Automated NetCDF regression-diff tool

A developer can invoke a single tool — built by hardening the source thesis's existing `concat_diff_var.py`/`multi_day_stats_generic.py`/`spatial_maps_generic.py` workflow rather than writing an unrelated one — that runs a specified `Testing/` fixture (or accepts a pre-existing output pair) and reports field-by-field differences against a trusted baseline, replacing manual NCO/CDO invocation as the default comparison method.

**Consequences (testable):**
- Running the tool against an unchanged code path reports bit-exact agreement (zero difference) across all output fields.
- The tool's report format names the specific field(s) and magnitude of any difference found (MAD, RMSE, rMAD, rRMSE, matching the existing thesis metrics), not a single pass/fail bit.
- `Tools/Scripts/BuildBot/testing.py` (dead Python 2) and `Tools/Scripts/TestingAndBenchmarking/preproc-compare.py` (narrow v3/v4 ICBC comparison) are explicitly archived or removed once this tool supersedes them, rather than left in an ambiguous, possibly-still-referenced state.

#### FR-25: Per-field tolerance policy support, using the thesis's MAD/RMSE metrics as the accepted GPU-porting policy

The tool supports an explicit, per-field tolerance specification expressed in the same terms the source thesis already established (MAD, RMSE, and their relative forms rMAD/rRMSE) rather than inventing a new metric. This reflects the project's actual two-tier numerical policy, confirmed with regcm5-dev: **CPU-only changes** default to bit-exact reproduction, per the project's general rule; **CPU-to-GPU porting specifically** has an established, documented precedent (`project-context.md`) of statistical, not bitwise, reproducibility, with the source thesis's measured bounds (`tas`/`ps` rMAD/rRMSE ~0.1%, `huss` ~5%) as the accepted reference — not a defect to fix (FR-37 enforces this as policy, not as an interim ceiling).

**Consequences (testable):**
- A tolerance specification format exists naming a field and its accepted MAD/RMSE (or relative rMAD/rRMSE) deviation; fields from CPU-only code changes default to bit-exact (zero-tolerance) unless regcm5-dev has explicitly reviewed and recorded an exception; fields from GPU-ported code default to the thesis-established statistical bounds (FR-37) unless regcm5-dev tightens them.
- The tool's documentation states which tier (CPU-only bit-exact vs. GPU-porting statistical) applies to a given comparison, so a reviewer is never left guessing which bar a result was checked against.

#### FR-26: Multi-process-count comparison support

The tool can run, or accept output from, the same fixture at more than one process count and compare results, since the project's stencil/halo regression rule requires more-than-single-rank verification for any change touching boundary-exchange code.

**Consequences (testable):**
- A single invocation, or a documented short procedure, produces a pass/fail comparison across at least two distinct `nproc` configurations for a given fixture.

#### FR-27: Baseline management

Trusted baseline outputs for each `Testing/` fixture are stored in a defined, documented location, with a written procedure for updating a baseline once an intentional change has been reviewed and accepted by regcm5-dev.

**Consequences (testable):**
- A baseline output exists for at least the fixtures exercised by this program's own FRs (FR-5/FR-6 I/O, FR-10 MOLOCH GPU, FR-13/FR-14 coupling builds).
- The baseline-update procedure requires an explicit sign-off record, not a silent overwrite.

**Out of Scope:** True continuous/triggered CI (auto-run on every commit or push) is out of scope — see the Non-Goals note above and Open Question 6.

**Notes:** `[NOTE FOR PM]` This feature is foundational to every other feature's acceptance discipline (§ Constraints and Guardrails) and is placed in Phase 1 for that reason, even though it is the heaviest single item in that phase — it is not a small, cheap correction like its Phase 1 neighbors, and should be resourced/estimated as such.

### 4.8 Containerization for Multi-System GPU Portability

**Description:** RegCM5 currently builds only from source via Autotools, requiring an administrator to have already provisioned the exact library stack (NetCDF/HDF5/PnetCDF, MPI, a supported compiler) the model needs — true today on Leonardo via its module system, not guaranteed on another system. This feature packages RegCM5 as container images across the project's supported compiler vendors: separate GNU and Intel CPU-path variants, plus an NVHPC/CUDA GPU-path variant (FR-30). Each is built as an OCI/Docker image (buildable and runnable directly via Docker on a developer workstation) and executable via Apptainer on shared HPC systems that do not permit a Docker daemon or root access. `[ASSUMPTION: an AMD/AOCC CPU container variant is not included by default, consistent with AMD being a "where feasible" target rather than mandatory (§5) — flag if AMD containerization should be added.]`

**Functional Requirements:**

#### FR-28: OCI/Docker build images for GNU and Intel variants

A Docker/OCI image exists for each CPU-path compiler vendor (GNU, Intel) that builds RegCM5 from source against a defined library stack, producing a runnable RegCM5 binary inside the image.

**Consequences (testable):**
- Separate build targets (or build-arg-selected stages) produce a working GNU-compiled image and a working Intel-compiled image, each buildable on a clean host with no RegCM5-specific system state beyond the container.
- Each image passes the same `Testing/` fixture used in FR-4/FR-24's baseline, and the GNU and Intel images' outputs agree within the project's bit-exact-by-default cross-vendor portability policy.

#### FR-29: Apptainer execution on HPC systems

Each Docker/OCI image variant (GNU, Intel, and — once available — the NVHPC/CUDA variant from FR-30) runs under Apptainer without a Docker daemon and without root privileges, for use on shared HPC systems including Leonardo.

**Consequences (testable):**
- An Apptainer `.sif` image built from each OCI image variant runs under a normal (non-root) HPC user account.
- A `Testing/` fixture run through the GNU and Intel Apptainer images on Leonardo produces output matching the corresponding native-build baseline within the project's existing tolerance policy.

#### FR-30: CUDA 12+ GPU-enabled container variant

A third container variant, alongside FR-28's GNU and Intel images, exists supporting NVHPC/CUDA-accelerated execution (CUDA 12 and above), for systems with compatible NVIDIA GPUs beyond Leonardo.

**Consequences (testable):**
- The GPU-enabled image runs a `do concurrent`-accelerated RegCM5 build and produces output matching the CPU-path baseline within the project's tolerance policy, on at least one system with a CUDA 12+ GPU.

**Out of Scope:** Non-NVIDIA GPU vendor containers (AMD ROCm, Intel oneAPI) are out of scope — the project's own AMD support is already "where feasible," not mandatory (§5).

**Feature-specific NFRs:**
- A containerized build/run is additional validation and distribution surface, not a substitute for native validation on the target HPC partitions (Constraints and Guardrails).

**Notes:** `[NOTE FOR PM]` NVHPC HPC SDK's redistribution terms for a distributed container image should be confirmed before committing to bundling the compiler itself (Open Question 7) — if restricted, the image may need to document a build-time NVHPC install step instead of bundling the compiler.

### 4.9 GitHub CI/CD Automated Testing Pipeline

**Description:** This feature adds a GitHub Actions workflow that builds RegCM5 (via Feature 4.8's containers where applicable) and runs Feature 4.7's regression-diff tool against `Testing/` fixtures on every push and pull request — continuous, triggered validation complementing the on-demand HPC-side validation Feature 4.7 alone provides. `[ASSUMPTION: GitHub-hosted runners have no GPU/CUDA access, so triggered CI covers CPU-path builds (GNU/Intel) and CPU-only Testing/ fixtures by default; GPU-path validation (do concurrent parallelization, NVHPC builds) remains scoped to the HPC cluster's own Slurm-based validation unless a self-hosted GPU runner is provisioned. See Open Question 7.]`

**Functional Requirements:**

#### FR-31: GitHub Actions build-and-test workflow

A `.github/workflows/` pipeline builds RegCM5 (at minimum GNU and Intel, via Feature 4.8's containers or equivalent) and runs at least one small `Testing/` fixture through Feature 4.7's regression-diff tool on every push and pull request.

**Consequences (testable):**
- A pull request that breaks the GNU or Intel build, or fails the regression-diff comparison against the stored baseline, is flagged by a failing GitHub check before merge.
- A pull request touching only documentation or non-source files is not required to pass a full simulation run.

#### FR-32: NVHPC/GPU path CI coverage, scoped to availability

NVHPC build verification (compilation only) runs in GitHub Actions where a suitable container/toolchain is available; `do concurrent` parallelization verification (FR-8) and full GPU execution remain scoped to the HPC cluster's Slurm-based validation unless a self-hosted GPU runner is provisioned (Open Question 7).

**Consequences (testable):**
- The workflow's documentation explicitly states which vendors/paths it validates in CI versus which still require a manual or Slurm-based check, so a green GitHub check is never mistaken for full four-vendor-plus-GPU acceptance.

**Out of Scope:** Provisioning a self-hosted GitHub Actions runner on Leonardo or any other HPC allocation is out of scope for this PRD to commit to unilaterally — it carries fair-use, security, and account-scope implications beyond this program's authority (Open Question 7).

**Feature-specific NFRs:**
- A passing GitHub Actions run is necessary but not sufficient evidence of this project's full acceptance discipline; final numerical/performance acceptance for anything touching physics, dynamics, or accelerator code still requires validation on the target HPC partitions per Constraints and Guardrails.

## 5. Non-Goals (Explicit)

- **No new physics parameterizations or numerical schemes.** This program optimizes, hardens, and selectively accelerates existing schemes; it does not add new cumulus, PBL, radiation, or microphysics options.
- **No full OpenACC (or CUDA Fortran) rewrite.** For this program's own new work, `do concurrent` remains the primary and default parallel-loop construct, escalating to OpenACC only where FR-9-style investigation shows `do concurrent` insufficient — a forward policy, not a claim that OpenACC is rare in the existing codebase (Feature 4.3's correction documents 90 files already using it).
- **No GPU-porting of gas-phase chemistry (KPP/DLSODE) integrators in this program.** Their data-dependent, irregular-control-flow solver structure is a known poor fit for SIMT execution; FR-2's profiling data is a prerequisite for even scoping that investigation, and this program stops at profiling for chemistry.
- **No further feature investment in CLM3.5.** Formally deprecated under FR-15; CLM4.5/ECLM is the supported path forward.
- **No CISM coupling implementation.** FR-16 delivers a design only; implementation is a future phase's scope.
- **No mandatory full AMD/AOCC compiler support.** The project context lists AMD as supported "where feasible," not as a hard requirement; this program does not commit to closing that gap (FR-20's NVHPC identity fix is unrelated and does not extend to AMD).
- **No self-hosted GPU runner on Leonardo (or any other HPC allocation) committed as part of this PRD.** Feature 4.9's GitHub Actions pipeline is scoped to CPU-path builds/tests on GitHub-hosted runners by default; provisioning HPC-hosted, GPU-capable runners for full accelerator-path triggered CI has fair-use, security, and account-scope implications this program does not have unilateral authority to decide (Open Question 7).

## 6. Phased Scope

*Framed as phases rather than MVP/vNext: this is solo-paced infrastructure work with no external launch deadline (per Discovery), so phase gates — not a calendar — govern progression. Each phase is intended to be individually shippable and reviewable.*

### Phase 1 — Foundation (low risk, unlocks evidence for later phases)
- FR-1, FR-2, FR-3, FR-4 (profiling and baseline)
- FR-24, FR-25, FR-26, FR-27 (automated regression infrastructure — the heaviest single item in this phase; see § 4.7 Notes)
- FR-18 (namelist path validation)
- FR-20 (NVHPC compiler identity)
- FR-21, FR-23, FR-38 (documentation corrections and FORD adoption)

### Phase 2 — I/O and Memory Hardening (medium risk, depends on Phase 1 evidence for prioritization)
- FR-5, FR-6, FR-7 (diagnostic I/O scaling)
- FR-33 (extend I/O scaling to restart and land-model output)
- FR-34 (I/O profiling and optimization investigation, all output and input paths)
- FR-19 (memory-growth investigation)

### Phase 3 — Selective Acceleration and Containerization (highest uncertainty)
- FR-35 (verify and document the full existing GPU-porting footprint — 90 files, 1,476 directive lines, not only the source thesis's four documented hotspots; confirmed already merged and scientifically validated; a documentation/verification task, not re-implementation)
- ~~FR-36~~ (retired — see Open Question 9's resolution)
- FR-37 (statistical-reproducibility regression test, enforcing the project's established GPU-porting policy)
- FR-8, FR-9, FR-10, FR-11, FR-12 (GPU acceleration)
- FR-22 (GPU-porting guidance document — now written after this phase's findings exist, not before)
- FR-28, FR-29, FR-30 (all container variants: GNU, Intel, and CUDA 12+/NVHPC)
- FR-31 (GitHub Actions CI pipeline — now co-landing with the containers it builds from, rather than preceding them)
- FR-32 (GPU-path CI coverage, scoped/pending Open Question 7's runner decision)

### Phase 4 — External Coupling Modernization (independent track, sequenced last)
- FR-13, FR-14, FR-15 (OASIS3-MCT, REGESM, CLM documentation and regression hardening)
- FR-16 (CISM design)
- FR-17 (BMI resolution)

*This phase has no technical dependency on Phases 1–3 — it is sequenced last by priority choice (solo pacing, no external deadline), not necessity.*

**Out of scope for all phases:** see §5 Non-Goals.

## 7. Success Metrics

*SM IDs are stable references, not sequential by position (matching the FR-numbering convention in §0). SM-10 was never assigned. SM-11 ("the four already-merged GPU ports reach bit-exact agreement") was retired alongside FR-36 when the two-tier reproducibility policy was resolved (Open Question 9) — the four ports were never non-compliant, so a bit-exactness metric for them no longer applies.*

**Primary**
- **SM-1**: Every FR in Features 4.2–4.5 ships with a complete acceptance record (Build, Test, Numerical, Performance) per the project's existing discipline. Target: 100% of merged changes. Validates all FRs.
- **SM-2**: RRTMG core, KPP chemistry integrators, and `mod_ncout.F90` carry timing instrumentation and a published baseline profile. Target: complete before Phase 2 begins. Validates FR-1–FR-4.
- **SM-3**: Diagnostic history output has a tested, documented parallel-write path (PnetCDF), verified bit-exact against serial gather-write at more than one process count. Validates FR-5–FR-6.
- **SM-4**: Every `do concurrent` loop touched under this program is verified to parallelize (not just compile) on GNU, Intel, and NVHPC. Target: 100% of touched loops. Validates FR-8, FR-10.
- **SM-7**: An automated regression-diff tool exists and is used as the default regression-evidence method for every subsequent FR in this program, replacing manual NCO/CDO comparison. Validates FR-24–FR-27.
- **SM-8**: A GitHub Actions workflow gates every pull request with at least a GNU and Intel build plus a regression-diff check; RegCM5 runs successfully inside an Apptainer container on Leonardo producing output within tolerance of the native-build baseline. Validates FR-28, FR-29, FR-31.
- **SM-9**: A written I/O investigation report covers measured time share for every output and input path (diagnostic, restart, land-model history, boundary-condition/ICBC input) at more than one rank count, with concrete optimization recommendations — closing the boundary-condition-I/O open item from the technical research note. Validates FR-33–FR-34.
- **SM-12**: A regression test enforcing the project's established GPU-porting statistical-reproducibility policy (`tas`/`ps` rMAD/rRMSE <0.1%, `huss` <5%) is in place and passing from the start of this program, applied consistently across every already-validated GPU-ported subsystem found by FR-35's full-repository audit (not only the original four) and any new or newly-verified GPU-porting work under FR-9/FR-10/FR-11. Validates FR-37.

**Secondary**
- **SM-5**: `Doc/DeveloperGuide/MainDeveloperGuide.tex` no longer contains the precision or lifecycle claims the technical research found incorrect. Validates FR-21.
- **SM-6**: OASIS3-MCT and REGESM each have a current, documented field list and at least one passing regression run. Validates FR-13–FR-14.
- **SM-13**: FORD generates browsable API documentation without error, covering at minimum every module this program's own FRs touch. Validates FR-38.

**Counter-metrics (do not optimize)**
- **SM-C1**: No merged change may report a wall-time improvement while failing the project's numerical-reproducibility bar — bit-exact by default for CPU-only changes, or the established statistical-reproducibility policy (FR-25/FR-37) for CPU-to-GPU porting specifically. A faster but numerically drifted run outside whichever bar applies is a regression, not a win. Counterbalances SM-1 and SM-4.
- **SM-C2**: RRTMG GPU-porting effort (FR-9) does not continue past its go/no-go checkpoint on the strength of sunk effort alone — a "no-go" backed by FR-4 evidence and the ICON-A precedent is treated as a successful outcome of the investigation, not a failure to complete it. Counterbalances the general pressure to show GPU-porting progress.

`[ASSUMPTION: numeric performance targets (e.g., "N% faster") are deliberately not set here, since no baseline exists yet — that is what Phase 1 delivers. Setting a numeric target before FR-4's baseline would be exactly the kind of unevidenced performance claim this program exists to eliminate.]`

## Cross-Cutting NFRs

- **Numerical reproducibility**: Bit-exact by default for CPU-only changes; the established statistical-reproducibility policy (FR-25/FR-37) for CPU-to-GPU porting specifically. Any difference beyond whichever bar applies requires regcm5-dev's explicit scientific sign-off. Applies to every FR.
- **Cross-vendor portability**: Every change must build correctly under GNU, Intel, and NVHPC at minimum. `do concurrent` changes additionally require FR-8's parallelization verification, not build success alone.
- **Zero behavior change for non-opted-in runs**: FR-5/FR-6 (parallel I/O), FR-9/FR-10 (GPU porting), and FR-13/FR-14 (coupling) must not change output, behavior, or required configuration for a run that does not explicitly opt into the new capability.
- **DEBUG-only instrumentation overhead**: FR-1–FR-3's timing instrumentation must add zero overhead to non-DEBUG production builds, per the existing convention.

## Constraints and Guardrails

**Scientific correctness guardrail**
- Every change is subject to the project's existing acceptance discipline (Build/Test/Numerical/Performance) recorded in the commit or PR description. Until Feature 4.7 delivers the automated regression-diff tool, this remains a discipline enforced by review, not a gate a tool provides; afterward, FR-24–FR-27 make the Numerical and Test criteria mechanically checkable on demand — though not continuously/automatically triggered (see Non-Goals).
- regcm5-dev is the sole scientific reviewer and sign-off authority for this codebase (per the governing project context); this program does not introduce or assume a formal review board.

**HPC platform guardrail**
- Intel-compiled work is validated on `dcgp_usr_prod` / `dcgp_qos_dbg` (account `ICT26_MHPC_0`); NVHPC-compiled work on `boost_usr_prod` / `boost_qos_dbg` (account `ICT26_MHPC`). FR-4's baseline explicitly spans both, since the CPU-vendor and accelerator build paths are validated on physically different partitions.
- Login-node activity stays limited to planning and light tasks; all profiling and regression runs go through Slurm with conservative resource requests, per the cluster's fair-use policy.

**Container/CI guardrail**
- A passing GitHub Actions check (Feature 4.9) is necessary but not sufficient evidence of full acceptance — it validates CPU-path builds and a small regression fixture, not the four-vendor-plus-GPU discipline this project requires for physics/dynamics/accelerator changes. Final acceptance for such changes still requires validation on `dcgp_usr_prod`/`boost_usr_prod`.
- Containerized execution (Docker/Apptainer, Feature 4.8) is an additional distribution and validation surface, not a replacement for native builds on the target HPC partitions.

**Boundary-condition guardrail**
- Boundary-condition code is currently live experimental territory (active churn in recent history, per the governing project context). FR-34's boundary-condition/ICBC input-I/O profiling must flag findings for regcm5-dev's review rather than silently "fixing" or "optimizing" anything it touches there — this applies even if a clear performance win is visible.

**Portability guardrail**
- No FR may introduce a code path that only compiles or only runs correctly under one compiler vendor, except where explicitly scoped as a vendor-specific investigation (e.g., FR-9's NVHPC-side feasibility work), and even then, the existing three-vendor build must remain green throughout.

## Why Now

This program is timed to a specific evidence event, not a market or calendar pressure: the technical research note completed immediately before this PRD closed the "what do we actually know about this codebase" gap that made prior GPU-porting and I/O work necessarily ad hoc. NVHPC 26.3/CUDA 12.9 are now the specified target versions, active NVIDIA collaboration is already touching the dynamical core, and the coupling contracts (OASIS3-MCT, REGESM) and one dormant one (BMI) are now documented well enough to make deliberate decisions about each rather than discovering their state by accident during unrelated work. Doing this now, before further ad hoc GPU patches or coupling changes accumulate on top of an unmeasured baseline, is cheaper than doing it later.

## Stakeholders and Approvals

- **Scientific sign-off**: regcm5-dev, for any change touching physics, dynamics, numerics, or tolerance policy — per the governing project context, this is explicit human sign-off, not a formal board, and its absence is not license to skip the check.
- **External collaborators**: informal contributors (e.g., NVIDIA engineers already active across MOLOCH and the broader GPU-porting footprint documented in Feature 4.3) may propose or implement GPU-porting work under Feature 4.3, but scientific sign-off authority remains with regcm5-dev.

## Risk Register

*Condensed to product-level risk and mitigation; full technical evidence (file paths, line numbers, solver mechanisms) is in `addendum.md` and the technical research note.*

| Risk | Mitigated by |
|---|---|
| `do concurrent` parallelizes unevenly across compiler vendors — a loop can silently run serial, not fail to build | FR-8 |
| Pointer-aliased shared state (`assignpnt`) is invisible to automatic GPU data-residency analysis | FR-9, FR-10 scoping discipline; FR-11 verifies whether the existing, already-validated halo-exchange GPU-direct implementation handles any `assignpnt`-related residency hazard correctly |
| RRTMG shares lineage with ICON-A's PSrad, whose directive-based GPU port failed — though real profiling of the CLM4.5-coupled configuration found no RRTMG hotspot presence at all, so this risk is unconfirmed rather than dismissed | FR-1 (direct measurement), FR-9 go/no-go checkpoint |
| KPP chemistry integrators have data-dependent, irregular control flow — a poor SIMT fit | Excluded from GPU-porting scope (§5) pending FR-2 data |
| GPU-porting footprint was understated (four documented hotspots vs. 90 files/1,476 directive lines actually in the tree, incl. an already-implemented GPU-direct halo exchange) — risk is verification work under-scoped relative to what actually needs checking | FR-35 (rescoped to full repository audit), FR-11 (rescoped to verify the existing GPU-direct exchange, not investigate a hypothetical one) |
| BMI is dead code behind an undefined macro, not a maintained contract | FR-17 |
| RRTMG core, KPP integrators, and diagnostic I/O have zero profiling instrumentation | FR-1, FR-2, FR-3 |
| Governing documentation makes incorrect precision and lifecycle claims | FR-21 |
| No automated regression-diff tool exists; every acceptance record depends on manual, repeated NCO/CDO comparison | FR-24–FR-27 |
| A green GitHub Actions check could be mistaken for full four-vendor-plus-GPU acceptance when it only covers CPU-path builds | FR-32's explicit scope documentation; Feature 4.9 NFR |
| NVHPC HPC SDK's container redistribution terms are unconfirmed | Open Question 7; flagged in FR-30 Notes before implementation |
| Restart, land-model, and boundary-condition/ICBC I/O paths are unprofiled and their scaling behavior at high rank counts is unknown | FR-33–FR-34 |
| Parallel diagnostic I/O (HDF5-parallel and PnetCDF-parallel) is measured *slower* than serial write across all tested rank counts in the coupled configuration, cause unexplained | FR-3, FR-34 |
| GPU-ported code follows an established statistical-reproducibility precedent distinct from the project's CPU-only bit-exact default — risk is applying the two inconsistently or letting GPU-ported divergence drift beyond the thesis's measured bounds unnoticed | FR-25 (two-tier tolerance policy), FR-37 (regression test enforcing the bound) |

## External Coupling Contracts

RegCM5 exposes or is intended to expose four external contracts. This program's obligations differ by contract:

| Contract | Current state | Obligation under this program |
|---|---|---|
| OASIS3-MCT | Live, field-rich | Document + regression-harden (FR-13) |
| REGESM | Live, independent field list | Document + regression-harden (FR-14) |
| CLM / CLM4.5 / ECLM | Live (CLM3.5 legacy) | Clarify support tier, deprecate CLM3.5 (FR-15) |
| CISM | Not present in codebase | Design only, no implementation (FR-16) |
| BMI | Dead stub | Resolve: implement to spec or remove (FR-17) |

A breaking change to any live contract's field list or behavior (OASIS3-MCT, REGESM, CLM4.5/ECLM) requires the same explicit-flagging treatment the governing project context already mandates for external, published contracts — it is not caught by RegCM5's own internal tests.

## Technology and Dependency Targets

*Inherited from the governing project context; restated here because Feature 4.3 and Feature 4.2 depend on them directly. Not re-derived — see `_bmad-output/project-context.md` for the authoritative source.*

- Compilers: GNU, Intel, NVHPC 26.3 (target), AMD where feasible.
- MPI: HPC-X 2.25.
- Accelerator path: CUDA 12.9, `do concurrent` → OpenACC only.
- I/O: HDF5 1.14.3, netCDF-C 4.9.2, netCDF-Fortran 4.6.1, PnetCDF 1.12.3.

**Version-alignment note**: the source thesis's own validated environment (NVHPC 24.5, HPC-X OpenMPI 2.19, CUDA Toolkit 12.4, PnetCDF 1.12.3) is one to two versions behind these stated targets. FR-35's verification step should include re-validating the thesis's GPU ports under the project's actual target versions (NVHPC 26.3/CUDA 12.9/HPC-X 2.25), not assuming behavior carries over unchanged across that version gap.

## 8. Open Questions

1. **BMI resolution direction (FR-17):** Is there a known, concrete external consumer that would use a working BMI interface, or should it be removed outright? This determines whether FR-17 resolves to (a) implement-to-spec or (b) deprecate-and-remove; the PRD deliberately does not pre-decide it.
~~2. Pre-existing bug backlog~~ — Resolved: no such list exists; bug discovery is expected to come out of Phase 1 profiling (FR-1–FR-4) and the existing `Testing/` fixtures, confirmed by regcm5-dev. Feature 4.5 correctly stays scoped to what the research directly surfaced.
3. **CISM coupling sponsor:** Is CISM coupling (FR-16) driven by a specific planned collaboration or paper, or is it exploratory? This affects how much design depth FR-16 should reach before being considered complete.
4. **AMD/AOCC support:** The project context lists AMD as a target "where feasible" but this program treats it as non-mandatory (§5). Should a future phase commit to AMD support explicitly, and if so, on what trigger (e.g., availability of AMD GPU allocation)?
5. **External collaborator process:** NVIDIA engineers have already contributed directly to `mod_moloch.F90` per git history. Should this program formalize how external GPU-porting contributions are reviewed and merged, beyond regcm5-dev's existing sign-off role?
~~6. Triggered CI scope~~ — Resolved: regcm5-dev confirmed triggered CI is wanted, via a GitHub Actions workflow (Feature 4.9), not just an on-demand HPC-side tool. Feature 4.7's regression-diff tool is the mechanism FR-31 invokes; it remains independently usable on-demand on the HPC cluster as well.
~~7. GPU-capable CI runner and NVHPC redistribution~~ — Resolved: regcm5-dev confirmed no self-hosted GPU-capable GitHub Actions runner will be provisioned. Feature 4.9's triggered CI stays permanently scoped to CPU-path builds/tests on GitHub-hosted runners; GPU-path validation (`do concurrent` parallelization, full accelerator execution) remains exclusively the HPC cluster's own Slurm-based validation, as already stated in §5 Non-Goals. The NVHPC redistribution half was resolved separately via web research — AD-18 in the architecture spine (devel-build/runtime-ship container split).
~~8. Merge status of the source thesis's GPU-porting code~~ — Resolved: regcm5-dev confirms the `getcape`, `mod_clm_hydrology2`, `interp1d_r8`, and `heatindex` ports are already present in the codebase this program builds on. FR-35 is scoped as verification/documentation, not re-implementation.
~~9. Numerical tolerance policy for GPU-ported code~~ — Resolved (final): after surfacing a conflict between an earlier chat answer and `project-context.md`'s documented precedent, regcm5-dev confirmed the precedent governs — CPU-only changes stay bit-exact by default; CPU-to-GPU porting specifically is accepted at the source thesis's measured statistical bounds (`tas`/`ps` rMAD/rRMSE ~0.1%, `huss` ~5%). The four already-merged GPU ports were never non-compliant. FR-36 (which assumed bit-exactness was required) is retired; FR-25/FR-37 encode this two-tier policy as the project's actual accepted rule.
10. **Multi-platform performance portability:** The source thesis found unexplained apparent superlinear strong-scaling efficiency on MareNostrum 5 and Leonardo (4→16 GPUs) and benchmarked performance portability across three HPC centers. This program scopes no FR to investigate that anomaly or validate beyond Leonardo (see `addendum.md`) — is that correct, or should a lightweight investigation be added, e.g. if this program's outputs are expected to run on allocations beyond Leonardo?
~~11. GPU-porting footprint completeness~~ — Resolved: a follow-on architecture session's repository-wide audit (`git grep` for `!$acc` directives — `do concurrent` alone is a separate, larger 95-file footprint, since it is RegCM5's general parallel-loop construct rather than a GPU-porting signal on its own) found 90 files and 1,476 directive lines with GPU-porting work, far beyond the four thesis-documented hotspots — including an already-implemented GPU-direct halo exchange (`Main/mpplib/mod_mppparam.F90`) and existing work across MOLOCH, the full CLM4.5 land model, cloud/cumulus/microphysics, the ocean library, the PBL library, OASIS coupling, and async I/O, attributable to over a year of sustained contribution (2025-04-23 through at least 2026-06-08) from two named NVIDIA engineers (Everett Phillips, Massimiliano Fatica). regcm5-dev confirmed this broader work has already gone through the project's scientific-validation discipline, not merely been merged unreviewed. Feature 4.3, FR-9 (footnote only — RRTMG's own kernels remain confirmed unported), FR-11 (rescoped from investigation to verification of an existing implementation), FR-35 (rescoped to the full repository footprint), the Risk Register, and SM-12 were all corrected accordingly.

## 9. Assumptions Index

- §4.1 — Profiling instrumentation follows the existing DEBUG/`time_begin`/`time_end` convention, combined with `perf`/Nsight Systems matching the source thesis's methodology, rather than a new facility.
- §4.4 FR-17 — BMI's resolution direction (implement vs. remove) is deliberately left open pending Open Question 1, not inferred.
- §4.6 FR-38 — Adopting FORD reverses the earlier documentation-scope decision that excluded deep internal API docs by omission; flagged as a direct scope expansion, requested rather than inferred.
- §4.7 — "CI" is interpreted as an on-demand regression-diff tool underlying Feature 4.9's triggered pipeline (resolved — see Open Question 6).
- §4.8 — An AMD/AOCC CPU container variant is not included by default, consistent with AMD being a "where feasible" target rather than mandatory (§5).
- §4.9 — GitHub-hosted runners are assumed to have no GPU/CUDA access, so triggered CI defaults to CPU-path coverage only; confirmed as permanent scope, not merely an assumption, by regcm5-dev (Open Question 7, resolved).
- §7 — No numeric performance targets are set pending Phase 1's baseline; this is a deliberate scoping choice, not an oversight.
- §4.1 (epics-level addition) — FR-39 (Valgrind memory-leak/error check, under Epic 1) does not originate in this PRD. It was added directly during epic creation at franco's explicit request. Recorded here for traceability, not because this PRD itself scopes it.
