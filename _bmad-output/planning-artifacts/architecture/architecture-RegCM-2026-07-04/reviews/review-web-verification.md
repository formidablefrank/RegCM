# Web-Verification Review: ARCHITECTURE-SPINE.md

(Background subagent for this lens failed on a session-limit API error before
producing output; done inline instead, per the reviewer-gate fallback. All
searches below were run from the main session, which was unaffected by the
limit that took down the background agent pool.)

## Verdict

Every technology claim newly asserted this session checks out against current
official sources; nothing found to be fabricated or stale.

## Checked this session (re-confirmed, with sources)

1. **GCC/gfortran 16.1** -- released 2026-04-30, current stable major release
   for 2026. [gcc.gnu.org/releases.html](https://gcc.gnu.org/releases.html)

2. **Intel oneAPI Toolkit 2026.0 / ifx 2026.0.0** -- current release, Base Kit
   and HPC Toolkit merged into a single oneAPI Toolkit as of 2026.0; ifx fully
   supports Fortran through 2018 plus partial 2023.
   [intel.com Fortran Compiler 2026 release notes](https://www.intel.com/content/www/us/en/developer/articles/release-notes/fortran-compiler/2026.html)

3. **ifx build caveat for netCDF-Fortran 4.6.1 / PnetCDF 1.12.3** --
   confirmed real, not fabricated: a known `sizeof(off_t)` configure issue
   with Intel compilers building netcdf-fortran, and PnetCDF's configure
   script silently defaulting to `gfortran` unless `FC`/`F77`/`F90` are set
   explicitly.
   [Intel Community: pnetcdf configure error using icx and ifx](https://community.intel.com/t5/Intel-Fortran-Compiler/pnetcdf-configure-error-using-icx-and-ifx/td-p/1489151),
   [Unidata netcdf-fortran issue #436](https://github.com/Unidata/netcdf-fortran/issues/436)

4. **NVIDIA HPC SDK Container Guide 26.3, devel/runtime multi-stage
   redistribution pattern (AD-18)** -- re-confirmed directly for this review:
   "devel" images contain the full SDK (not freely redistributable);
   "runtime" images contain only components licensed for redistribution;
   NVIDIA's own recommended pattern is a multi-stage build -- compile against
   devel, ship only the binary + runtime dependencies via the runtime-stage
   image, selecting the runtime image matching the CUDA version used to
   build. Matches AD-18's Rule text exactly.
   [HPC SDK Container Guide 26.3](https://docs.nvidia.com/hpc-sdk/container-guide/index.html)

5. **HPC-X 2.25 / CUDA 12.9 pairing (inherited from project-context.md, not
   newly asserted this session, but checked anyway for this gate)** --
   confirmed: HPC SDK 26.1 defaults to HPC-X 2.25.1, and the 26.1/26.3 HPC SDK
   release packages bundle CUDA 12.9(U1) components alongside CUDA 13.1 --
   this is a real, current, actually-shipped combination, not an invented
   pairing.
   [NVIDIA HPC SDK Release Notes](https://docs.nvidia.com/hpc-sdk/release-notes/index.html),
   [CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)

## Not independently re-verified this session

- NVHPC 26.3, binutils 2.42, HDF5 1.14.3, netCDF-C 4.9.2, netCDF-Fortran
  4.6.1, PnetCDF 1.12.3 -- these are pre-existing `project-context.md`/PRD
  facts, not claims this session introduced, so re-verifying them is outside
  this lens's purpose (catching *this session's* unverified assertions).
  Spot-checking HPC-X/CUDA above found no reason to doubt the rest of the
  pinned set.

## Findings

None. No stale, fabricated, or unverifiable technology claim found among
what this session actually asserted.
