---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-07-04'
sections_completed: ['technology_stack', 'agent_operating_constraints', 'language_numerical_rules', 'architecture_parallelism_rules', 'testing_rules', 'style_rules', 'workflow_rules', 'critical_dont_miss_rules']
status: 'complete'
rule_count: 112
optimized_for_llm: true
---


# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

**Core:**
- Fortran 90/2003/2008 — `.F90` (preprocessed via cpp) and `.f90` (free-format, not preprocessed)
- GNU Autotools build (`configure.ac`, `acinclude.m4`, per-arch `Makefile.am` → `Makefile`), libtool
- MPI parallelism — real MPI, or bundled `external/mpi-serial` stub for serial builds (`MPI08`/`MPI2` macros)
- NetCDF/HDF5 for all I/O

**Target versions (HPC cluster deployment):**
- Compiler: NVHPC 26.3 (OpenACC + Fortran `do concurrent`/stdpar GPU acceleration target)
- MPI: HPC-X 2.25
- CUDA: 12.9
- binutils: 2.42
- HDF5: 1.14.3, netCDF-C: 4.9.2, netCDF-Fortran: 4.6.1, PnetCDF: 1.12.3

**Optional components:**
- OASIS3-MCT coupler (`--enable-oasis`)
- Land models: CLM / CLM45 (`clmlib`, `PreProc/CLM`, `PreProc/CLM45`)
- Chemistry/aerosol packages (`chemlib`, `external/aerosols`)
- Current release: RegCM 5.0.0

No CI pipeline (no `.github/workflows`), no linter/formatter config — style enforced by convention/review only.

**GPU build configuration flags** (`configure.ac`, NVHPC/PGI only):
- `--enable-openacc-managed`: OpenACC with CUDA managed memory (`mem:managed`)
- `--enable-openacc-stdpar`: `do concurrent` GPU offload plus OpenACC, unified memory (`mem:unified`), defines `STDPAR`
- `--enable-openacc-debug`: adds `autocompare`, an NVHPC feature that runs a region on both host and device and reports numerical divergence automatically — not yet used elsewhere in this repository, but directly relevant to GPU-port verification
- `--enable-clm45`: builds the coupled RegCM5–CLM4.5 executable
- `--enable-pnetcdf`: enables parallel NetCDF I/O
- `--enable-async-netcdf`: enables overlapping disk writes with computation
- Source: `_bmad-source/implementation/regcm5-optimization-thesis.pdf` (Master's thesis, GPU porting and optimization of RegCM5, ICTP/SISSA/CINECA, 2024–2026), benchmarked on NVHPC 24.5, CUDA 12.4, HPC-X OpenMPI 2.19 — an earlier environment than the current target versions above

## Critical Implementation Rules

### Agent Operating Constraints

**HPC cluster environment (CINECA Leonardo):**
- VS Code's `code` CLI isn't available here in the login node
- When running Python scripts, load the Python module first using `module load python/3.11.7`
- Consult the `$HPCDOCS` directory before searching the web for cluster-specific questions (modules, compilers, paths, policy)
- Work occurs on a shared login node, subject to resource sharing and fair use policy; enforced limits prevent any single user from consuming the whole node
- Confine login-node activity to planning and light tasks; submit larger job or long-running process as a Slurm job on compute nodes
- Request conservative resource limits in Slurm job submissions. If walltime requested is at most 24 hours then set QoS to `normal`
- For running Slurm jobs with programs compiled with Intel, use `dcgp_usr_prod` partition, `dcgp_qos_dbg` QoS with account `ict26_mhpc`
- For running Slurm jobs with programs compiled with NVHPC, use `boost_usr_prod` partition, `boost_qos_dbg` QoS with account `ict26_mhpc_0`
- Let the user review the Slurm script first before submitting
- Writing a Slurm script to **build** RegCM5? Copy the matching reference, don't start from scratch — Intel: `RegCM-data/benchmarking/parallel-io-initial/build_async_off_intel.sh`; NVHPC: `RegCM-data/benchmarking/parallel-io-initial/build_async_off_nvhpc.sh`; GNU: `bin/slurm-1-2-build-gnu-debug.sh`. Each pins a bisected known-good compiler version and spack toolchain prefix.
- Writing a Slurm script to **run** RegCM5, any of the three compilers? Copy `RegCM-data/benchmarking/parallel-io-initial/submit_sweep.sh` — it encodes QOS/partition/account choices and MPI-IO environment variables found only through failed submissions and crashed jobs.

**Communication style:**
- Write in a register consistent with scholarly books and peer-reviewed journal articles
- Use established words only; do not invent terms, and avoid fancy hyphenated compound words
- Keep responses short, simple, concise, and direct, without significant loss of information
- Responses must be grammatically correct

### Language & Numerical Rules (Fortran)

**Precision & Kinds:**
- Use `rkx` (from `mod_realkinds`) for all real variables — compile-time switchable single/double, not hardcoded precision. Never hardcode `real(8)`, `real*8`, or `dp`/`sp` in new physics/dynamics code.
- Use `ik4`/`ik8` (from `mod_intkinds`) for integer kinds, not bare `integer`.
- `rkx` is the *only* sanctioned precision knob — no local mixed-precision hacks (a manual `real(4)` cast inside otherwise-`rkx` code) without a documented, reviewed exception plus regression evidence.
- ⚠️ `Doc/DeveloperGuide/MainDeveloperGuide.tex` and `mod_template.f90` are stale — they claim hardcoded 64-bit `dp`. Trust the code's `rkx` pattern, not the doc.

**Module Skeleton:**
- `private` immediately after `use` statements; explicit `public ::` allowlist
- Lifecycle pair: `init_mod_<name>` / `release_mod_<name>`
- Module files start with `mod_`, lowercase only

**Banned legacy Fortran (enforced, not just style):**
- `common`, `include`, `implicit double precision`, `real*8`/old-Fortran notation
- Non-standard integer pointers → allocatable arrays or real Fortran pointers
- `equivalence`, computed `goto`, `entry` statements — none tolerate modern optimizers
- Vendor-specific extensions that hurt portability across GNU/Intel/NVHPC/AMD

**GPU-porting hazards:**
- Pointer-aliasing is the #1 risk: this codebase is saturated with `pointer, contiguous` derived-type fields aliased across modules. Before converting any kernel to OpenACC/`do concurrent`, identify whether its data is pointer-reached, and treat unproven aliasing as a blocker.
- Watch for hidden contiguity copies at F77 call boundaries — an assumed-shape slice (e.g. `a(:,2:18:2)`) passed into a legacy F77 routine silently makes a contiguous copy, quietly taxing exactly the hot loop a performance change is trying to fix.
- Any accelerator-specific code path (OpenACC, CUDA Fortran, `do concurrent` GPU intent) must be macro-guarded so GNU/Intel CPU-only builds are unaffected — never let a GPU path silently no-op or change CPU results.

**GPU offload procedure requirements** (confirmed present in this codebase; use these as the reference pattern — `getcape_new` in `Share/mod_capecin.F90`, `mod_clm_hydrology2.F90`, `Share/mod_heatindex.F90`, `Share/mod_interp.F90`):
- The merged pattern offloads via OpenACC (`!$acc parallel loop` at the call site, `!$acc routine seq` on the called procedure), not `do concurrent` — see the `getcape_new` call site in `Main/mod_output.F90`. A procedure offloaded this way must be `pure`; it may remain `public` (confirmed: `getcape_new` is both `public` and offloaded successfully)
- The thesis also documents a `do concurrent`-based variant of the same offload, where an explicit `public` declaration did block kernel generation — that constraint is specific to the `do concurrent` path and does not apply to the OpenACC pattern actually merged here
- Automatic (local, entry-sized) array allocation inside a procedure is unsupported once that procedure compiles to a device kernel — allocate in the caller and pass the array as an argument
- A helper procedure contained inside another procedure must move to module scope before the compiler can generate a device kernel for it
- A whole-array or row-slice initialization idiom (e.g. `array(c,:) = 0._rk8`) can be lowered by `nvfortran` into a vectorized memset (`__c_mset16_avx`) that appears in a profile as an unattributed hotspot with no call stack — replace it with an explicit element-wise loop under `!$acc loop seq`, as already done in `mod_clm_hydrology2.F90`
- Source: `_bmad-source/implementation/regcm5-optimization-thesis.pdf`, Chapters 2–3

**Scientific correctness is a hard constraint, not a style preference:**
- Preserve physical meaning of schemes, namelist behavior, units, boundary conditions
- Numerical reproducibility is a first-class acceptance criterion — non-bitwise changes require an explicit, controlled tolerance policy
- No algorithmic change (physics, dynamics, numerics) without regression tests + scientific review — applies even to "just" a performance optimization
- Regression evidence is mandatory: any precision/accelerator change ships with a comparison against the `Testing/` baseline suite (`test_001`–`016.in`, CORDEX namelists) — bit-exact by default, explicit tolerance if intentionally not; both the CPU-only and accelerated build paths must pass the same baseline
- Boundary-condition code is currently live experimental territory (active churn in recent history) — treat as higher-risk for unsolicited changes; flag rather than silently "fix" or "optimize" it

### Architecture & Parallelism Rules

**Domain decomposition & parallelism:**
- 2D domain decomposition over `(iy, jx)` grid, parameters in `mod_dynparam` (`nproc`/`myid`, `njxcpus`/`niycpus`, `iyp`/`jxp` per-process tile sizes) — any new parallel code must go through this existing decomposition, not invent a new one
- MPI is the parallelism model; `external/mpi-serial` is a drop-in stub for serial builds — code must compile under both, don't assume real MPI is always linked
- Halo/tile-boundary exchange goes through `mod_mppparam`'s `exchange_array_r8/r4`, `real8_2d/3d/4d_exchange` family (and cyclic variants) — any change to a stencil operation (advection, diffusion, anything with `i±1`/`j±1` neighbor access) near a tile boundary must be regression-checked at more than one process count; a decomposition bug can be invisible at `nproc=1`

**Interface seams — two different contracts:**
- Internal: `mod_<subsystem>_interface.F90` modules (`mod_atm_interface`, `mod_cu_interface`, `mod_lm_interface`, `mod_pbl_interface`, `mod_rad_interface`, `mod_che_interface`, `mod_micro_interface`) wire RegCM's own subsystems together — normal review, don't reach across them into a neighboring subsystem's internals
- External: `mod_bmiregcm` (implements the CSDMS BMI 2.0 standard) and `mod_oasis_interface` (OASIS3-MCT coupler) are published contracts other models/couplers call into — a signature change here isn't caught by RegCM's own tests and needs explicit flagging, not routine review

**Portability across 4 compiler vendors is a hard constraint:**
- Code must build correctly under GNU, Intel, and NVHPC at minimum (AMD where feasible) — a change that improves performance on one silently breaking or regressing another is a rejected change, not a tradeoff
- Acceleration path is standard Fortran `do concurrent` → OpenACC, and only that: `do concurrent` is the single loop-parallelism construct — NVHPC compiles it to on-node CPU multicore (`-stdpar=multicore`) or GPU (`-stdpar=gpu`) from the same source depending on build flag, which is why there's no separate OpenMP track — it's already covered, not omitted. Escalate to OpenACC only when `do concurrent` isn't sufficient, and only after profiling confirms the hotspot. No OpenMP, no OpenMP-target, no CUDA Fortran.
- Directory boundaries reflect build stages: `Main/` (model core + physics libs), `Share/` (cross-cutting utilities/constants/precision kinds), `PreProc/` (ICBC/terrain/emissions preprocessing — most active area per git history), `PostProc/`, `external/` (bundled third-party) — a change belongs in the layer that owns the data

### Testing Rules

**Test Organization:**
- No unit test framework at the model level (the one `pFUnit`-style unittest dir found is inside bundled third-party CLM3.5 code, not RegCM's own) — testing is full-model **integration runs**, driven by namelists
- `Testing/` holds the fixture namelists: `test_001`–`016.in` (small regional domains), `ideal.in`/`ideal_profile.in` (idealized cases), `isc24.in`/`isc24_small.in`/`isc24_profile.in` (profiling/benchmark cases), `EUR12_namelist.in` (AD-8's canonical `$FAST` baseline fixture — a version-controlled reference copy of the domain/physics parameters, not a runnable copy: paths are `/set/this/to/where/...` placeholders), plus `Testing/CORDEX/*.namelist` (production-scale CORDEX domain configs, distinct from `EUR12_namelist.in`'s grid) and required input data (`RRTM_DATA/`, `CHEM_DATA/`)

**`regression_diff.py`/`manage_baseline.py` are the working, verified regression tools (Epic 1, 2026-08-19) — use them, not manual NCO/CDO, as the default:**
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py --run-dir RUN --baseline-dir BASE [--nprocs 1,4,16,64,196] [--tolerance-file FILE]` compares NetCDF output field-by-field (MAD/RMSE/rMAD/rRMSE) against a trusted baseline; verified on real Slurm runs (bit-exact same-run, per-field tolerance override, malformed-input handling all confirmed at runtime, not just read from source)
- `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py promote --run-dir RUN --baseline-dir $FAST/franco/RegCM-data/baseline [--nproc N]` populates/updates the trusted baseline, refusing to overwrite without `--force` (verified live, not just documented) — a first trusted baseline is already populated at `$FAST/franco/RegCM-data/baseline/nproc-196/` (EUR12 fixture, `PROMOTION_MANIFEST.jsonl` records every promotion)
- Known gap, not yet fixed: both tools' comparison reports a stream with zero time records on both sides as vacuously "bit-exact" (`np.array_equal` on two empty arrays) — confirmed twice (Stories 1.1, 1.2). Manually confirm each compared stream actually carries non-zero records before trusting an "exact" verdict on it; don't take a `pass: true` headline at face value for every stream
- `Tools/Scripts/archive/testing.py` and `Tools/Scripts/archive/preproc-compare.py` (both archived from their original locations in Story 1.3) are the old, dead tools these supersede — Python 2 non-runnable, and ICBC-v3/v4-only respectively; do not point anyone at them

**How to run a regression comparison:**
- Use the tools above with a `test_00N.in` small domain for fast iteration, a CORDEX namelist or `Testing/EUR12_namelist.in`'s AD-8 fixture for production-scale confidence before anything precision- or performance-sensitive is considered done
- Default expectation is bit-exact reproduction of an unchanged code path; any intentional numerical difference needs the explicit tolerance policy from the Language & Numerical Rules section, applied per-field via `--tolerance-file`, not as a blanket "close enough"
- Multi-process-count comparison (`--nprocs`) is required whenever a change touches stencil/halo code (Architecture & Parallelism Rules) — a single-rank (`nproc=1`) comparison can pass while a decomposition bug at tile boundaries still exists. `nproc=1`/`nproc=4` is genuinely verified only for the ATM stream today (the vacuous-zero-record gap above blocked RAD/SRF/STS at those counts in both Stories 1.1 and 1.2) — treat those two streams as still unverified at low `nproc` until that gap closes

**A documented reproducibility diagnostic workflow exists for CPU-vs-GPU comparison, but it is not yet in this repository:**
- `_bmad-source/implementation/regcm5-optimization-thesis.pdf` (Appendix B) describes a three-script NCO/Python pipeline — concatenate daily NetCDF output, compute the GPU-minus-CPU difference field with `ncdiff`, then compute mean absolute difference (MAD), root-mean-square error (RMSE), and their scale-relative forms (rMAD, rRMSE) per hour and per day, plus geographic error maps. Porting these three scripts into the repository (e.g. under `Tools/Scripts/`) would give GPU-port verification a statistical-tolerance workflow of its own, distinct from `regression_diff.py`'s bit-exact/single-tolerance-table default
- For CPU-only code changes, bit-exact reproduction remains the default expectation (above). For CPU-to-GPU porting specifically, the established precedent in this project is **statistical**, not bitwise, reproducibility: after a 7-day run, the thesis measured relative divergence below 0.1% for near-surface air temperature and surface pressure, and below 5% for near-surface specific humidity. Treat these as reference bounds — a new GPU port should be checked against comparably small, quantified divergence, not assumed correct from a successful compile
- The NVHPC `autocompare` option (`--enable-openacc-debug`, see Technology Stack) offers an automatic first-pass host-versus-device comparison at build time and should be tried before hand-building an NCO-based diff

**Test boundary:**
- There's no meaningful "unit vs integration" split to preserve — the smallest trustworthy test is a full `test_0NN.in`/`ideal.in` run; don't invent isolated unit tests for physics/dynamics routines that aren't validated against a real model run

### Code Quality & Style Rules

**Formatting (no linter/formatter enforces this — it's convention only):**
- 2-space indentation is the real standard, even though every file ends with a vim modeline claiming `tabstop=8` — the modeline's `shiftwidth=2 softtabstop=2 expandtab` is what matters; found in 564 files, so match it exactly: `! vim: tabstop=8 expandtab shiftwidth=2 softtabstop=2`
- Every source file opens with the standard MIT-license banner comment block (`!::::...` borders, "This file is part of ICTP RegCM," license reference) — copy it verbatim into new files, don't paraphrase
- Modern array constructors use square brackets `[ ... ]`, not the legacy `(/ ... /)` form — the codebase has already migrated

**Naming:**
- Module files: `mod_<name>.F90`/`.f90`, always lowercase (Fortran folds case anyway, so uppercase in a new filename is just a footgun)
- `.F90` = preprocessed (has cpp directives, `#ifdef`); `.f90` = free-format, not preprocessed — picking the wrong extension means your `#ifdef DEBUG` block silently becomes dead text instead of a directive

**Documentation — units are the type system:**
- Fortran has no unit-checking, so a trailing comment stating units/physical meaning is mandatory for every new physical variable (dummy argument, module field, or local with physical meaning) — follow the existing style (`! Surface pressure`, `! 1/(mapfx**2 * 4 * dx)`). A variable with no unit comment is a latent bug waiting for someone to guess wrong.

**Debug facility (project-specific, not generic logging):**
- Guarded by the `DEBUG` compile-time macro (`mod_service` module only exists when `DEBUG` is defined) plus a runtime `debug_level` (0–6)
- Debug sections in code are wrapped `#ifdef DEBUG ... #endif` — don't add ad hoc `print`/`write` debug statements outside that convention
- Timing/debug instrumentation (`time_begin`/`time_end`, `start_debug`/`stop_debug`) stays at subroutine entry/exit granularity, matching existing call sites — never insert it inside a loop body, even temporarily while chasing a bug; it silently reintroduces the overhead a performance change is trying to remove
- Default behavior is DEBUG disabled, `debug_level = 0` — don't change these defaults as a side effect of unrelated work

### Development Workflow Rules

**Code changes:**
- Write minimal code that solves the stated problem
- Do not speculate; do not add unrequested functionality

**Change scoping:**
- One story/change touches one subsystem, or one clearly-scoped seam between two (e.g. an F77-interop bug living at an interface-module boundary) — don't let a seam fix silently expand into rewriting both subsystems
- Prefer small transformations over rewrites: loop normalization, data locality, allocation discipline, interface cleanup, I/O separation

**Every story defines four acceptance criteria — written into the commit/PR description, not just discussed:**
- There's no CI or PR template to enforce this structure, so the commit message itself is the record — write it every time, not only for "big" changes
- **Build**: compiles under the required compiler/vendor combination(s)
- **Test**: which `Testing/` namelist(s) it was validated against, and at what process count(s)
- **Numerical**: bit-exact, or an explicit stated tolerance with justification
- **Performance**: only claimed with evidence (below) — not asserted from intuition

**Rigor scales with what's touched, not with how big the claimed win sounds:**
- A change to precision, reduction/summation order, or memory layout gets full numerical scrutiny regardless of whether the performance claim is modest or dramatic — "just a 2% loop reorder" can still change floating-point associativity

**Required evidence for any optimization claim:**
- Baseline: compiler + flags, MPI library, node type, CPU/GPU model
- Problem size: domain decomposition, rank/thread layout
- Measurement: wall time, hotspot profile, memory bandwidth evidence where available
- Regression comparison against a trusted baseline output (manual NCO/CDO — no automated tool exists yet)
- Documented profiling method: `perf record --call-graph dwarf` (needs `-g` debug symbols) with a flame-graph rendering (Brendan Gregg's `FlameGraph` scripts) identifies hot call stacks; NVIDIA Nsight Systems recovers attribution `perf` cannot, since a compiler-runtime symbol (e.g. `nvfortran`'s `__c_mset16_avx`) can appear with no call stack under `perf`; the `-Minfo=accel` compiler flag reports exactly what a given region offloaded and what data movement it generated (see `_bmad-source/implementation/regcm5-optimization-thesis.pdf`, Appendix A)

**"Scientific review" means explicit human sign-off, not a formal board:**
- In this project that means sign-off from whoever owns the physics being touched (in practice, franco) — don't stall waiting for a review process that doesn't exist, and don't treat its absence as permission to skip the check

**No time estimates** — don't frame acceptance criteria or story scope in terms of duration.

**Branching rules**
- Create a new feature branch from `develop` when developing a new story
- After developing the story, do not stage all changes on a single commit. All changes related to BMAD artifacts should be staged on a separate commit and all others changes related to the source code should be staged on another separate commit.
- After marking the story done, checkout the branch `develop` then merge the newly created branch into it, without deleting the feature branch.

### Critical Don't-Miss Rules

**Anti-patterns (cross-referenced):**
- Don't hardcode `real(8)`/`dp` or invent a second local precision — `rkx` is the only knob (Language Rules)
- Don't reach for OpenMP/CUDA Fortran — `do concurrent` → OpenACC only (Architecture Rules)
- Don't trust `Doc/DeveloperGuide/` on precision — it's stale (Language Rules)
- Don't assume a working regression-diff command exists — `archive/testing.py` is dead Python 2 (Testing Rules)
- Don't put debug/timing instrumentation inside a loop body (Style Rules)

**Performance gotchas:**
- Don't `allocate`/`deallocate` scratch arrays inside a time-step or inner loop — the existing `init_mod_*`/`release_mod_*` lifecycle exists precisely so workspace arrays are allocated once and reused; repeated dynamic allocation in a hot path is a classic, easy-to-miss regression
- Don't delete a `#ifdef DEBUG` block because it looks unused in your local build — it's conditionally compiled, not dead code
- Don't move a helper procedure to module scope, or change its `pure`/`!$acc routine seq` annotations, without checking whether that change is load-bearing for GPU-offload kernel generation (Language & Numerical Rules) — in `getcape_new`/`heatindex`/`interp1d_r8` these are not stylistic, they are required for the device kernel to compile
- The "no working regression tool" note above (Testing Rules) applies to general CPU-only code-change regression. For CPU-vs-GPU divergence specifically, a documented workflow exists in `_bmad-source/implementation/regcm5-optimization-thesis.pdf` (not yet ported into this repository) with quantified precedent bounds — don't conflate the two gaps

**Edge cases:**
- Namelist inputs are not defensively parsed — several `Testing/*.in` fixtures ship with literal placeholder paths (e.g. `/set/this/to/where/...`) expected to be edited before use; don't assume malformed/unedited namelist input fails gracefully, and don't "fix" a placeholder path by guessing a real one

**Security:**
- Not a meaningful attack surface in the usual sense — this is a batch HPC scientific model, not a network-facing service. The closest analogue is the Python tooling under `Tools/Scripts/` that parses external data files (namelists, NetCDF, GRIB) — treat malformed input files as a robustness/correctness concern, not a security one, unless a specific script is shown to shell out or eval untrusted content

---

## Custom BMAD Tooling & Skill Routing

Two custom BMAD modules exist for this program, registered in `_bmad/config.yaml`/`_bmad/module-help.csv` exactly like `bmm`/`bmb`/`tea`: `hpc-dev` (`bmad-hpc-devops/`) produces artifacts and executes changes; `hpc-test` (`bmad-hpc-tea/`) designs coverage, audits evidence, and renders gate decisions. **Before implementing a RegCM5 change generically, check this table — if a specialized skill exists for the domain, invoke it instead of ad hoc implementation:**

| Change touches... | Use | Persona |
| --- | --- | --- |
| Understanding existing code / "what does X do" | `hpc-dev-agent-code-comprehension` | Gaspare |
| General RegCM5 Fortran/HPC implementation | `hpc-dev-agent-hpc-software-developer` | Jacopo |
| Profiling / establishing a baseline | `hpc-dev-evidence-baseline` | Lorenzo |
| CPU/GPU crash, hang, memory or thread-safety bug | `hpc-dev-agent-profiler` (debug capability) | Lorenzo |
| GPU-port candidacy or porting | `hpc-dev-gpu-port-candidacy` | Dario |
| Compiler/build-matrix work | `hpc-dev-cross-vendor-build-verification` | Franco |
| I/O scaling or bottleneck diagnosis | `hpc-dev-io-scaling-diagnosis` | Franco |
| Containers or the CI pipeline | `hpc-dev-containerization-release` / `hpc-dev-ci-guardrail-pipeline` | Giacomo |
| Documentation modernization | `hpc-dev-documentation-modernization` | Gaspare (flags) / Jacopo (writes) |
| Any change needing a merge/gate verdict | `hpc-test-trace-and-gate` | Matteo |
| MPI- or decomposition-touching change | `hpc-test-mpi-correctness-verification` | Matteo |
| Physics- or numerics-touching change | `hpc-test-scientific-correctness-verification` | Matteo |
| External-coupling change (OASIS3-MCT/REGESM/CLM/BMI/CISM) | `hpc-test-coupling-contract-verification` | Matteo |

A drafted story that clearly maps to one of these should name the specific skill in its Dev Notes, not leave routing to be re-derived at implementation time.

---

## Source documents

BMAD agents should treat the following source index as the entry point for project-specific evidence, rules, and validation policies:

- `_bmad-source/index.md`

## Required source loading policy

Before proposing or implementing RegCM5 changes:

1. Read the relevant source documents from `_bmad-source/`.
2. Prefer documented project rules over generic software advice. Ask questions if needed.
3. If source documents conflict with the code, report the conflict before changing code.
4. If required evidence is missing, mark the story as `NEEDS EVIDENCE`, not `READY`.

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option or ask questions as needed
- Update this file if new patterns emerge

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-08-19
