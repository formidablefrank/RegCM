<!-- bmad:context -->
<!-- Verified 2026-08-19 against 8343703bc. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## RegCM5

ICTP's regional climate model — Fortran 90/2003/2008, GNU Autotools build, MPI parallelism (real MPI or the bundled `external/mpi-serial` stub), NetCDF/HDF5 I/O. Source documents (thesis, cluster introspection, build notes) are indexed at `_bmad-source/index.md` — read the relevant one before implementing.

## Policy

- Create a feature branch from `develop` per story; after the story is done, merge into `develop` without deleting the feature branch.
- Stage BMAD-artifact changes and software changes as separate commits — never combined in one.
- No algorithmic change (physics, dynamics, numerics) ships without regression evidence (see Running and verifying), even for "just" a performance optimization.
- Scientific review means explicit sign-off from whoever owns the physics being touched (in practice, franco) — there's no formal review board; don't stall waiting for one, and don't treat its absence as permission to skip the check.

## Where things are

- Specialized `hpc-dev-*`/`hpc-test-*` skills exist for RegCM5 domain work (build matrix, GPU porting, MPI/scientific correctness review, gate decisions) — check whether one fits before ad hoc implementation.
- GPU-offload procedure specifics (device-kernel constraints on `pure`/`routine seq`/visibility) live in `bmad-hpc-devops/hpc-dev-agent-gpu-porting/references/port-routine.md` — read it before porting a routine.

## Running and verifying

- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py` + `manage_baseline.py` are the working regression tools, replacing the archived `Tools/Scripts/archive/testing.py`/`preproc-compare.py` (Python 2, don't run — `archive/` has no README saying so, don't assume they're just dead ends without checking `TestingAndBenchmarking/` first). Default expectation is bit-exact; GPU statistical tolerance is the documented exception.
- `regression_diff.py`'s `compare_variable` reports two zero-length arrays as vacuously `"exact"` — a crashed run with empty output streams reads identically to a genuine bit-exact pass in its `pass: true` report. Don't trust a pass without checking the streams actually had data.
- No CI, no unit-test framework — the smallest trustworthy test is a full `Testing/test_0NN.in` or `ideal.in` run. Validate at more than one process count for any change touching stencil/halo code (`mod_mppparam`'s exchange family) — a decomposition bug can be invisible at `nproc=1`.
- State four acceptance criteria in every commit/PR description (nothing else enforces this): Build (compiler/vendor), Test (which fixture, what nproc), Numerical (bit-exact or stated tolerance), Performance (only with evidence — baseline config, problem size, profiling method).

## Conventions that differ from defaults

- Precision: `rkx` (from `mod_realkinds`) for all reals, `ik4`/`ik8` for integers — never hardcode `real(8)`/`real*8`/`dp`. `Doc/DeveloperGuide/MainDeveloperGuide.tex` and `mod_template.f90` are stale on this point; trust the code.
- Banned: `common`, `include`, `implicit double precision`, `equivalence`, computed `goto`, `entry` statements, vendor-specific extensions.
- Real indentation is 2 spaces — trust the vim modeline's `shiftwidth=2 softtabstop=2 expandtab`, not its `tabstop=8`.
- Acceleration path is `do concurrent` → OpenACC only, escalated only after profiling confirms a hotspot; no OpenMP, no CUDA Fortran. Any accelerator-specific path must be macro-guarded so GNU/Intel CPU builds are unaffected.
- GPU/HPC toolchain target (NVHPC 26.3, HPC-X 2.25, CUDA 12.9, HDF5 1.14.3, netCDF-C 4.9.2, netCDF-Fortran 4.6.1, PnetCDF 1.12.3, binutils 2.42) is pinned in `../RegCM-data/benchmarking/parallel-io-initial/env-nvhpc/spack.yaml`, consumed by `bin/slurm-1-2-build-nvhpc-*.sh`.

## Known pitfalls

- Pointer-aliasing is the primary GPU-port risk — the codebase is saturated with `pointer, contiguous` derived-type fields aliased across modules; treat unproven aliasing as a port blocker.
- Automatic (local, entry-sized) array allocation inside a procedure is unsupported once it compiles to a device kernel — allocate in the caller, pass as an argument. A helper procedure contained inside another must move to module scope first.
- A whole-array/row-slice init idiom (`array(c,:) = 0._rk8`) can lower to a vectorized memset that shows up in a profile as an unattributed hotspot with no call stack — replace with an explicit element-wise loop under `!$acc loop seq` (see `Main/clmlib/clm4.5/mod_clm_hydrology2.F90`).
- Boundary-condition code is under active churn — treat as higher-risk for unsolicited changes; flag rather than silently "fix" or "optimize" it.

<!-- /bmad:context -->
