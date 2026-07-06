---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'RegCM5 HPC Architecture and GPU-Porting Risk Analysis'
research_goals: 'Produce a technical research note covering build system, compiler assumptions, MPI usage, OpenMP/accelerator directives, NetCDF/I/O paths, and physics/dynamics subsystems; enumerate likely performance hotspots (I/O and computation) and risks for refactoring or GPU acceleration, governed by _bmad-output/project-context.md'
user_name: 'regcm5-dev'
date: '2026-07-04'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-07-04
**Author:** regcm5-dev
**Research Type:** technical

---

## Research Overview

This report analyzes RegCM5, ICTP's regional climate model, as a Fortran HPC codebase, covering its build system, compiler and accelerator assumptions, MPI and I/O architecture, physics and dynamics subsystems, and the risks bearing on refactoring or GPU porting. Research combined direct inspection of the RegCM5 source tree (build files, module structure, physics and dynamics code) with web-verified facts about external dependencies (NVHPC `do concurrent`/OpenACC, PnetCDF/netCDF-4 parallel I/O, HPC-X MPI) and GPU-porting precedents from comparable regional and global climate models, governed throughout by the constraints recorded in `_bmad-output/project-context.md`.

Four findings stand out. First, the codebase's central design decision — `do concurrent` as the sole loop-parallelism construct, escalating to OpenACC only if needed — is implemented consistently and not yet undermined by stray OpenACC use, but its correctness depends on `do concurrent` support that differs by compiler vendor, which a build-only check across GNU/Intel/NVHPC does not verify. Second, the default diagnostic-output path is a serial gather-then-write bottleneck, made tolerable in practice by an infrequent (3-6 hour) write cadence rather than by design. Third, radiation (RRTMG) and gas-phase chemistry (KPP/DLSODE) are the two subsystems most likely to dominate compute cost, and simultaneously the two subsystems with no timing instrumentation at all — so a GPU-porting decision about either would today rest on no measured evidence. Fourth, RegCM's RRTMG radiation scheme shares its lineage with ICON-A's PSrad scheme, whose directive-based GPU port failed to reach acceptable speedup and required a full scheme replacement — a directly relevant precedent for RegCM's own radiation-porting risk.

Full findings, evidence, and citations are organized below by research step (Technology Stack, Integration Patterns, Architectural Patterns, Implementation/Hotspots). A consolidated risk register, recommendations, executive summary, and methodology notes appear in the Research Synthesis section at the end of this document.

---

## Technical Research Scope Confirmation

**Research Topic:** RegCM5 HPC Architecture and GPU-Porting Risk Analysis
**Research Goals:** Produce a technical research note covering build system, compiler assumptions, MPI usage, OpenMP/accelerator directives, NetCDF/I/O paths, and physics/dynamics subsystems; enumerate likely performance hotspots (I/O and computation) and risks for refactoring or GPU acceleration, governed by `_bmad-output/project-context.md`.

**Technical Research Scope:**

- Architecture Analysis — module layering (`Main/`, `Share/`, `PreProc/`, `PostProc/`, `external/`), domain decomposition, subsystem interfaces
- Implementation Approaches — build system (Autotools/libtool), compiler assumptions across GNU/Intel/NVHPC/AMD, precision-kind discipline (`rkx`)
- Technology Stack — MPI (real + `mpi-serial` stub), NetCDF/HDF5/PnetCDF I/O, `do concurrent`/OpenACC accelerator path
- Integration Patterns — internal interface modules (`mod_*_interface`) vs. external published contracts (BMI, OASIS3-MCT)
- Performance Considerations — likely I/O and compute hotspots, halo-exchange costs, GPU-porting hazards

**Research Methodology:**

- Primary source: direct code inspection (build files, module structure, physics/dynamics source), cross-checked against `project-context.md`'s governing rules
- Web search supplements verification of external dependency facts (NVHPC `do concurrent`/OpenACC semantics, PnetCDF/netCDF-4 parallel I/O, HPC-X MPI, CUDA 12.9) — not RegCM itself, which is not documented on the public web at the needed depth
- Confidence level framework for uncertain information

**Scope Confirmed:** 2026-07-04

---

## Technology Stack Analysis

_Note: the template's generic "database/cloud/frontend framework" categories do not apply to a batch HPC Fortran model. Categories below are adapted to what RegCM5 actually is: build system, compiler/accelerator path, MPI, and file-based I/O._

### Programming Language & Build System

RegCM5 (`configure.ac:1`, `AC_INIT([RegCM],[5.0.0])`) is Fortran 90/2003/2008, built with GNU Autotools + libtool (`configure.ac:25`, `LT_INIT`) via a large project-specific `configure.ac` (987 lines) and `acinclude.m4` (551 lines) defining custom macros (`AX_PROG_NC_CONFIG`, `RR_PATH_NETCDF`, `RR_NETCDF4`, `RR_CDF5`, `ACX_MPI`, `RR_PATH_PNETCDF`, `RCM_MPI_CHECK_MPI3`).

Configure surface: `--with-netcdf/--with-hdf5/--with-szip`, `--with-oasis-path/--with-oasis-comm`, `--enable-mpiserial`, `--enable-singleprecision`, `--enable-openacc[-debug|-managed|-stdpar]`, `--enable-oasis`, `--enable-eclm`, `--enable-clm/--enable-megan`, `--enable-clm45`, `--enable-cpl` (REGESM coupling), `--enable-parallel-nc`, `--enable-pnetcdf`, `--enable-nc4-filters`, `--enable-cdf5`, `--enable-async-netcdf`, `--enable-debug`, microarchitecture flags (`--enable-knl/zen3/bdw/nhl/skl`).

There are no per-vendor `Makefile.am` variants — one shared `makeinc` fragment is included everywhere; vendor branching lives in `configure.ac` via `AM_CONDITIONAL`. The single exception is `Main/clmlib/Makefile.am:158` (`if COMPILER_GNU ... -fno-range-check -DG95`), a historical G95-compatibility shim for bundled CLM3.5 code.
_Source: repository `configure.ac`, `acinclude.m4`_

### Compiler Assumptions & the Accelerator Path

Vendor detection is string-matching on the Fortran compiler basename (`configure.ac:502-522`): `gfortran*`→`COMPILER_GNU`, `ifort*`/`mpiifort*`→`COMPILER_INTEL`, `ifx*`/`mpiifx*`→`COMPILER_INTEL_LLVM`, and `pgf9*`/`nvf9*`/`pgfortran*`/`nvfortran*`→`COMPILER_PGI`. **NVHPC's `nvfortran` is classified as "PGI"** — a naming holdover from RegCM's PGI-compiler heritage (PGI became NVHPC after NVIDIA's acquisition) rather than a first-class NVHPC identity. No `COMPILER_NVHPC` or AMD/AOCC branch exists, so AMD portability (named as a target in the governing project context) has no configure-time hook today.

OpenACC/stdpar flags sit entirely under the "PGI" conditional (`configure.ac:834-864`): mode 1 `-acc=gpu -gpu=$PGI_GPU_ARCH,lineinfo -Minfo=accel`; mode 4 (stdpar) `-stdpar=gpu -gpu=$PGI_GPU_ARCH,lineinfo,mem:unified -Minfo=accel`. `PGI_GPU_ARCH="ccnative"` is hardcoded with a `TODO` marking it not user-configurable (`configure.ac:140`) — a latent gap if a target GPU's compute capability ever needs pinning explicitly. No compiler-identity macros (`__NVCOMPILER`, `__GFORTRAN__`, `__INTEL_COMPILER`) appear in `Main/`/`Share/`/`PreProc/` source — compiler differences stay confined to build flags, not scattered `#ifdef` blocks in physics code, consistent with the four-vendor portability constraint.

The accelerator strategy matches the governing context exactly and no more: `do concurrent` is the only parallel-loop construct, used in 96 files (85 `Main/`, 9 `Share/`, 1 `PreProc/`), heaviest in `Main/mod_moloch.F90` (112 occurrences) and `Main/mod_advection.F90`/`mod_tendency.F90`. There are **zero** `!$acc`/`!$ACC` directives anywhere in the repository, despite `--enable-openacc` existing as an option — GPU offload today is pursued purely through NVHPC's auto-parallelization of standard `do concurrent` under `-stdpar=gpu`. Current NVIDIA documentation confirms this path is live and supported: "You can compile DO CONCURRENT programs with the -stdpar flag, which enables parallelism on an NVIDIA GPU... the same code can be compiled with multiple compilers and run efficiently on both multicore CPUs and NVIDIA GPUs." Git history shows this is active work, not aspirational — commit `10e6d3390` ("From Everett@NVIDIA") patches `mod_moloch` to avoid mid-loop allocation and adds missing GPU loops in `collect_output`.
_Source: repository `configure.ac`; [NVIDIA HPC Compilers User's Guide 26.1](https://docs.nvidia.com/hpc-sdk/pdf/hpc261ug.pdf); [Accelerating Fortran DO CONCURRENT with GPUs and the NVIDIA HPC SDK](https://developer.nvidia.com/blog/accelerating-fortran-do-concurrent-with-gpus-and-the-nvidia-hpc-sdk/)_

### MPI & Communication

`Main/mpplib/mod_mppparam.F90` (~20,600 lines) is the single parallelism seam: `use mpi` unless `MPI_SERIAL`; `USE_MPI3` (probed by testing for `mpi_ineighbor_alltoallv`) gates neighbor-collective calls. No `mpi_f08` usage — the code stays on the older `mpi`/`mpif.h` interface. `external/mpi-serial/` is a genuine functional single-rank MPI implementation in C (`mpi.c`, `comm.c`, `collective.c`, `group.c`, `pack.c`, `send.c`, `recv.c`, `req.c`), not a stub that errors out — this is what lets serial builds compile and run unmodified.

Halo exchange is centralized behind `exchange_array`→`exchange_array_r8/r4`, `exchange_lrbt/exchange_lr/exchange_bt/exchange_lb/exchange_rt`, `exchange_bdy_lr/exchange_bdy_bt`, dispatching to `real8_2d/3d/4d_exchange` (and `real4` variants), with `grid_distribute/grid_collect/subgrid_distribute/subgrid_collect` for full-domain scatter/gather. Every stencil touching a tile boundary funnels through this one seam.

HPC-X 2.25 (the project's target MPI) layers UCX (transport acceleration) and HCOLL (collective acceleration) on top of standard MPI; HCOLL auto-enables GPU buffer support when a CUDA runtime is present in the job, with GPUDirect RDMA multicast for broadcast over GPU buffers. RegCM's halo exchange as written targets host-memory MPI buffers — it is not GPU-aware in the sense of passing device pointers directly into MPI calls, so realizing HPC-X's GPU-direct path would require either CUDA-aware buffer passing at the `exchange_array_r8` call sites or explicit host staging. This is an open question for the GPU-porting effort, not something the `do concurrent`-only strategy already solves.
_Source: repository `Main/mpplib/mod_mppparam.F90`; [NVIDIA HPC-X Software Toolkit Rev 2.25](https://docs.nvidia.com/networking/display/hpcvx225)_

### I/O & Storage (NetCDF / HDF5 / PnetCDF)

I/O is NetCDF-centric (80 files call `use netcdf`/`nf90_*`), with three tiers: (1) default serial NetCDF from one designated I/O rank; (2) genuine parallel NetCDF via PnetCDF (`use pnetcdf`, `nfmpi_*`), gated by `#ifdef PNETCDF`, in exactly two modules — `Main/mod_savefile.F90` (restart files) and `Share/mod_ncstream.F90`; (3) a pthread-backed asynchronous-write layer (`Share/mod_async_netcdf.F90`) as an alternative to true parallel I/O.

The main history/diagnostic output path (`Main/mpplib/mod_ncout.F90`, 4645 lines) is a gather-then-write pattern: non-I/O ranks return early (`if (.not. parallel_out .and. myid /= iocpu) return`), and `grid_collect` gathers subdomains onto one rank (`iocpu`) before a single NetCDF write. **The default output path is serial from one rank, not domain-parallel, regardless of compute rank count.** PnetCDF is opt-in and currently scoped to restart/checkpoint files and the ncstream path, not general diagnostic output.

This aligns with the published PnetCDF-vs-netCDF4 tradeoff: PnetCDF (MPI-IO-based, two-phase collective I/O) typically outperforms serial gather-then-write at scale, but its write time still rises with node count from inter-node collective overhead, while netCDF-4 parallel (via parallel HDF5) trades some of that performance for compression support PnetCDF's classic format lacks. For RegCM, the practical implication is that the *default* configuration (serial gather-write) is almost certainly the binding I/O constraint at high rank counts — well before any PnetCDF-vs-netCDF4 choice becomes the limiting factor. Enabling `--enable-parallel-nc`/`--enable-pnetcdf` for history output, not just restarts, is the more consequential lever.
_Source: repository `Main/mpplib/mod_ncout.F90`, `Main/mod_savefile.F90`, `Share/mod_ncstream.F90`; [Parallel netCDF: A Scientific High-Performance I/O Interface](https://www.researchgate.net/publication/1956512_Parallel_netCDF_A_Scientific_High-Performance_IO_Interface); [PnetCDF/E3SM-IO benchmark](https://github.com/Parallel-NetCDF/E3SM-IO)_

### Physics & Dynamics Subsystems

Three dynamical cores selectable via `idynamic` (`Share/mod_dynparam.F90:558-580`): 1 = MM4 hydrostatic, 2 = MM5 nonhydrostatic, 3 = MOLOCH nonhydrostatic (`Main/mod_moloch.F90`) — MOLOCH is the newest and, per the `do concurrent` density above and recent git history, the one under active GPU-porting.

Physics interfaces and scheme choices: cumulus (`mod_cu_interface`: Kuo, Grell, Betts-Miller, Emanuel, Tiedtke, Kain-Fritsch, plus shallow convection), PBL (`mod_pbl_interface`: Holtslag, UW-TCM, GFS, MYJ, Shin-Hong), radiation (`mod_rad_interface`: RRTMG vs. CCM3-derived `colmod3`), microphysics (`mod_micro_interface`: SUBEX, WSM5, WSM7, WDM7, NOGTOM), land surface (`mod_lm_interface`: BATS vs. CLM/CLM45/ECLM plus a lake model), chemistry/aerosol (`mod_che_interface`, `Main/chemlib/`: dust/sea-salt/SOx/carbon aerosol, dry/wet deposition, CBMZ/CBMZ_NEW/CB6r2 gas mechanisms). Each subsystem is namelist-switch-selected, matching the `mod_<subsystem>_interface.F90` internal-seam contract.
_Source: repository `Main/mod_cu_interface.F90`, `mod_pbl_interface.F90`, `mod_rad_interface.F90`, `mod_micro_interface.F90`, `mod_lm_interface.F90`, `mod_che_interface.F90`, `Share/mod_dynparam.F90`_

### External/Bundled Dependencies

`external/` holds `mpi-serial/`, an MPI-M "simple plumes" aerosol climatology (`aerosols/`), the CSDMS BMI 2.0 Fortran binding (`bmi.f90`), and `mpistub.F90`. Separately, `Main/clmlib/` bundles complete CLM3.5 and CLM4.5 land-model source trees directly in the main build tree (119 files for CLM4.5 alone), including CLM3.5's own bundled copy of the Model Coupling Toolkit (MCT). No bundled linear-algebra library exists.
_Source: repository `external/`, `Main/clmlib/`_

---

## Integration Patterns Analysis

_Note: RegCM5 is a monolithic batch Fortran model, not a web/microservices system — there is no REST/gRPC/message-queue layer to analyze. "Integration patterns" here means the real analogues: the internal module-to-module data contracts, and the external coupling standards (BMI, OASIS3-MCT, REGESM) RegCM implements._

### External Contract: BMI (Basic Model Interface) — dormant, internally inconsistent

`external/bmi.f90` (`module bmif_2_0`) is a faithful transcription of the CSDMS BMI 2.0 Fortran spec (abstract type `bmi` with ~40 deferred procedures: `initialize`, `update`, `finalize`, `get/set_value*`, `get_grid_*`, etc.) — CSDMS itself confirms BMI 2.0 is the current standard, built on Fortran 2003 type-extension so a model "imports it as a type from a module... and its methods overridden."

`Main/mod_bmiregcm.F90` implements `bmi_regcm extends(bmi)` — but the **entire module body is wrapped in `#ifdef DEVELOPMENT ... #else` / an empty 4-line stub `#endif`** (lines 16, 979-987), and `DEVELOPMENT` is never defined anywhere in `configure.ac` or any `Makefile.am` — the compiled module is always the empty stub. Worse, the guarded-out "real" implementation is leftover boilerplate from the upstream `bmi-fortran` tutorial example (a toy heat-equation "plate" model — references `%temperature`, `%alpha`, `%dx`, `%dy`, `%dt`), while the actual `atm_model` type it would need (`Main/mod_regcm_interface.F90:62-65`) only has `model_name`/`model_longname` fields — the guarded code would not compile even with `DEVELOPMENT` defined. No caller anywhere in the tree references `bmiregcm`/`bmi_regcm`/`bmif_2_0` outside this one file and its Makefile target (`libbmi.a`).

**This is a load-bearing finding for the governing risk model**: `_bmad-output/project-context.md` treats `mod_bmiregcm` as a "published contract other models/couplers call into" requiring explicit flagging on change. In fact it is dormant and already broken — there is no live external consumer to protect, but anyone asked to "wire up BMI" would be building on a stub that doesn't compile once activated, not extending a working interface.
_Source: repository `external/bmi.f90`, `Main/mod_bmiregcm.F90`, `Main/mod_regcm_interface.F90`; [CSDMS bmi-fortran](https://github.com/csdms/bmi-fortran); [bmi 2.0 documentation](https://bmi.csdms.io/en/stable/bmi.spec.html)_

### External Contract: OASIS3-MCT coupler — real, actively maintained, feature-gated

`Main/mod_oasis_interface.F90` (`oasisxregcm_init/finalize/header/params/def/rcv_all/snd_all/sync_wait`) plus `Main/oasislib/` implement a genuine, currently-functional OASIS3-MCT coupling layer, gated by `--enable-oasis` (`-DOASIS`) and `--enable-eclm` (`-DOASIS -DECLM`, full land coupling) in `configure.ac:206-235`, linking `-lpsmile.$OASIS_CHAN -lmct -lmpeu -lscrip`.

Exchanged fields are namelist-toggled (`/oasisparam/`): imports include SST, roughness length, friction velocity (`l_cpl_im_sst/wz0/wust`); exports include 10 m wind, 2 m T/Q, SLP, momentum stress, evaporation, precipitation, net water flux, latent/sensible heat flux, up/down long/shortwave, air density (`l_cpl_ex_*`, `RCM_SST`/`RCM_TAUX`-style OASIS variable names). Under `#ifdef ECLM` a much larger set (atmospheric T/U/V/Q, geopotential height, runoff, snow, soil moisture/temperature, albedo, CH4 flux, dust/VOC flux, dry-deposition velocity) is added for full land coupling. This matches the published OASIS3-MCT pattern used by comparable regional climate models (e.g. COSMO-CLM/CCLM couples to CLM, VEG3D, NEMO-MED12/NORDIC, TRIMNP+CICE, and MPI-ESM through the same unified interface, with measured coupling overhead below 7% of stand-alone cost) — RegCM's implementation is architecturally consistent with the field of practice, not a bespoke one-off.

A **second, separate** coupling mechanism, REGESM, is also present: `configure.ac:279-283` (`--enable-cpl`, `-DCPL`, "Supply this option if you plan on using REGESM"). `Main/mod_regcm_interface.F90` guards `use mod_update, only: rcm_get, rcm_put` behind `#ifdef CPL`; `Main/mod_update.F90` defines `imp_data`/`exp_data` derived types (SST, sea-ice thickness, surface fluxes, momentum, precipitation, runoff, etc.) for what is architecturally an ESMF/RegESM-style coupling path, parallel to but distinct from OASIS3-MCT. A change to either coupling surface needs to be flagged against both, since they are independent code paths with independent field lists, not a shared abstraction.
_Source: repository `Main/mod_oasis_interface.F90`, `Main/oasislib/`, `configure.ac`, `Main/mod_regcm_interface.F90`, `Main/mod_update.F90`; [The COSMO-CLM 4.8 regional climate model coupled via OASIS3-MCT](https://www.researchgate.net/publication/301539917_The_COSMO-CLM_48_regional_climate_model_coupled_to_regional_ocean_land_surface_and_global_earth_system_models_using_OASIS3-MCT_description_and_performance)_

### Internal Subsystem Contract: shared derived-type state + pointer-aliasing

Internal subsystems (`mod_atm_interface.F90`, `mod_pbl_interface.F90`, `mod_lm_interface.F90`, `mod_cu_interface.F90`, `mod_rad_interface.F90`, ...) do not pass data through subroutine arguments in the conventional sense — they share **module-level public singleton derived-type instances** (`mod_atm_interface.F90:35-45`: `type(slice), public :: atms`, `type(surfstate), public :: sfs`, `type(atmstate_tendency), public :: aten`), whose fields (in `Main/mpplib/mod_regcm_types.F90`) are `pointer, contiguous` arrays with no default target.

The actual data-flow mechanism is a pointer-remap call, `assignpnt` (~45 rank/type overloads, `Share/mod_memutil.F90:39-88`), invoked once at scheme initialization to alias each subsystem's small private exchange type onto the shared state. Concretely (`mod_pbl_interface.F90:94-186`, `init_pblscheme`):
```fortran
call assignpnt(sfs%tgbb, m2p%tg)
call assignpnt(atms%tb3d, m2p%tatm)
...
call assignpnt(aten%t, p2m%tten, pc_physic)   ! PBL output -> shared tendency array
call assignpnt(aten%u, p2m%uten, pc_physic)
```
`pblscheme` then calls the selected scheme (`holtbl`, `uwtcm`, ...) which writes into `p2m%tten`/`p2m%uten` — pointers that *are* `aten%t`/`aten%u`, later consumed directly by the dynamical core's tendency accumulation. There is no copy or message-passing step; this is compile-time-typed aliasing of shared mutable state, set up once and reused every timestep. This is precisely the "pointer-aliasing is the #1 GPU-porting risk" hazard the governing context flags: `assignpnt`'s aliasing is invisible to a compiler's automatic `do concurrent`/OpenACC data-region analysis, so any subsystem converted to run on-device must have its aliased fields' data residency reasoned about explicitly, not inferred.
_Source: repository `Main/mod_atm_interface.F90`, `mod_pbl_interface.F90`, `Main/mpplib/mod_regcm_types.F90`, `Share/mod_memutil.F90`_

### Configuration Format: namelists — validated values, unvalidated paths

RegCM has no single config file — configuration is ~40+ distinct `namelist /.../` blocks (roughly 60 declarations counted, several duplicated across sibling executables) spread across `Share/mod_dynparam.F90` (`dimparam, coreparam, molochparam, geoparam, terrainparam, debugparam, boundaryparam, globdatparam, cmip6param, pmip4param, perturbparam, clm_regcm, referenceatm, ncfilters, fnestparam, globwindow`) and `Main/mod_params.F90` (`restartparam, timeparam, outparam, physicsparam, dynparam, hydroparam, nonhydroparam, rrtmparam, cldparam, subexparam, microparam, grellparam, emanparam, tiedtkeparam, kfparam, chemparam, uwparam, holtslagparam, clmparam, cplparam, oasisparam, slabocparam, tweakparam`, ...), plus a few more in `mod_clm_params.F90`/`mod_bdycod.F90`/`mod_oasis_params.F90`.

Namelist *reads* are defensively handled: file open and every `read(ipunit, nml=...)` are `iostat`-checked, calling `fatal()` on failure. Scalar physics/numeric values are validated post-read, e.g. `mod_params.F90:987` `if (iocnflx < 0 .or. iocnflx > 3) call fatal(...)`, `:995` similarly for `ibltyp`, `:1162` `if (dt < mindt) call fatal(...)`, with some silent auto-clamping (`mod_dynparam.F90:544-546`: `if (nsg < 1) nsg = 1`). But **file-path namelist variables (`dirglob`, `inpglob`, `dirter`, `inpter`, `dirclm`, `cmip6_inp`, ...) are never existence-checked** — a repo-wide grep for `inquire(file=`/`exist=` in `Share/`/`Main/` finds only `Share/mod_nchelper.F90:1195-1220`'s `ncd_inqdim`, which checks a dimension *inside an already-open NetCDF file*, not a filesystem path. A placeholder or mistyped path surfaces only as a NetCDF/IO error deep inside `checkncerr`/`fatal` at first use — this confirms the governing context's "namelist inputs are not defensively parsed" claim specifically for path fields, while scalar option validation is in fact solid.
_Source: repository `Share/mod_dynparam.F90`, `Main/mod_params.F90`, `Share/mod_nchelper.F90`_

### Other External Surfaces

No installed/exported `libregcm`-style shared library and no Python/C bindings into the model itself exist (the only Python present, `Tools/Scripts/regcm_postproc-0.0.1/`, is an unrelated NetCDF post-processing helper). `bind(C)` usage in the tree is entirely inbound — RegCM calling C, not exposing Fortran to C callers: `Share/mod_posix.F90:25` (POSIX `opendir`/`readdir` interop), `Share/mod_nchelper.F90:1257,1307` (netCDF C API for string attributes), `Share/mod_spbarcoord.F90:36,174` (a C `qsort`-style comparator callback). `libbmi.a` (above) is the only attempt at a genuine external Fortran API, and it is inert.
_Source: repository `Share/mod_posix.F90`, `mod_nchelper.F90`, `mod_spbarcoord.F90`, `Tools/Scripts/regcm_postproc-0.0.1/`_

---

## Architectural Patterns and Design

_Note: generic web-architecture categories (microservices/monolith, GraphQL vs REST, cloud-native deployment) do not map onto a batch HPC Fortran model. Sections below cover the real analogues: SPMD/domain-decomposition architecture, module design conventions, data architecture, and the HPC job-submission deployment model._

### System Architecture: SPMD + 2D Domain Decomposition

RegCM5 is a single-program-multiple-data (SPMD) MPI model with genuinely **2D** domain decomposition, not 1D. `Share/mod_dynparam.F90:309-314` declares `nproc`/`myid` (populated from the real communicator via `mpi_comm_rank`/`mpi_comm_size` in `Main/mod_regcm_interface.F90:90-97`) and `njxcpus`/`niycpus`/`iyp`/`jxp` — the latter two optional and user-overridable through `namelist /dimparam/`.

The actual process-grid construction (`subroutine set_nproc`, `Main/mpplib/mod_mppparam.F90:1237-1609`) builds a genuine `mpi_cart_create(mycomm, 2, cpus_per_dim, ...)` Cartesian topology. If the user pins both `njxcpus`/`niycpus`, they must multiply exactly to `nproc` or the run aborts (`'CPU/RCPU mismatch'`); left unset, RegCM auto-factorizes `nproc` outward from `sqrt(nproc)`, biased toward the grid's aspect ratio, aborting with a suggested rank count if no even factorization exists. Tile sizing (`mod_mppparam.F90:1516-1539`) does **not** require the domain to divide evenly — remainder rows/columns are spread one-per-rank to the first `imiss` ranks (block-cyclic remainder handling), with a final `'DECOMPOSITION ERROR'` sanity abort. `nproc == 1` is a distinct code path that skips MPI decomposition entirely.

Directory layering matches the four build stages the governing context describes (`Main/`, `Share/`, `PreProc/`, `PostProc/`, `external/`), and the intended dependency direction actually holds under inspection: every `use mod_*` inside `Share/*.F90` (22 distinct modules) resolves to another `Share/` module — none reach into `Main/`'s 590 modules. `Main/` itself further splits into 12 physics-library subdirectories (`mpplib`, `pbllib`, `cumlib`, `radlib`, `chemlib`, `clmlib`, `batslib`, `ocnlib`, `microlib`, `cloudlib`, `oasislib`, `netlib`) alongside 37 top-level driver/interface files.
_Source: repository `Share/mod_dynparam.F90`, `Main/mod_regcm_interface.F90`, `Main/mpplib/mod_mppparam.F90`_

### Design Principles: module skeleton confirmed, lifecycle convention needs correction

The `private`-after-`use` + explicit `public ::` allowlist convention holds consistently across every module checked (`mod_pbl_interface.F90:35-48`, `mod_atm_interface.F90:28-61`, `mod_cu_tiedtke.F90:42-46`).

**Correction to the governing context**: the documented `init_mod_<name>`/`release_mod_<name>` lifecycle pair is not the pattern actually in use — a repository-wide search finds zero `subroutine release_mod_*` definitions anywhere, and only 3 files define any `init_mod_*` at all, none paired with a release counterpart. The pattern genuinely in force is `allocate_<name>`/`allocate_mod_<name>` routines calling the centralized `getmem`/`relmem` generic interfaces in `Share/mod_memutil.F90`. Explicit `relmem` deallocation is rare (3 call sites in all of `Main/`) — in practice, workspace allocated through `getmem` lives until process exit rather than being released by a per-module lifecycle call. This doesn't contradict the "don't allocate/deallocate inside a hot loop" performance rule (allocation is still front-loaded, once, via `allocate_*`), but it means a change described as "wire up the init/release lifecycle" would be introducing a pattern that doesn't exist yet, not restoring one that regressed.
_Source: repository `Main/mod_pbl_interface.F90`, `mod_atm_interface.F90`, `Main/cumlib/mod_cu_tiedtke.F90`, `Share/mod_memutil.F90`_

### Data Architecture: derived-type "state bags" as the shared data model

The central data-architecture pattern is the pointer-bearing derived type (`slice`, `surfstate`, `atmstate_tendency` in `Main/mpplib/mod_regcm_types.F90`) instantiated once as a module-level public singleton and pointer-aliased across subsystems via `assignpnt` (documented in the Integration Patterns section above). This is the same structure that makes the precision-kind system (`rkx`/`ik4`/`ik8`) load-bearing at the type-declaration level — every field in these state types is declared with the shared kind parameters, so a `do concurrent` loop's soundness depends on the compiler being able to see through the pointer aliasing to the underlying contiguous storage, which is exactly the governing context's "#1 GPU-porting risk."

One nuance worth recording: the governing context's specific example hazard — "an assumed-shape slice `a(:,2:18:2)` passed to a legacy F77 routine silently makes a contiguous copy" — was not found as an actual instance anywhere in the tree. There are no fixed-form (`.f`) F77 source files at all in `Main/`/`Share/`; F77-heritage code survives only as free-form `.F90` ports (EISPACK/LINPACK/LAPACK under `Main/netlib/`, KPP-generated chemistry integrators) using classic *sequence association* (e.g. `CALL DGETRF(N,N,WM(3),N,...)`, passing a scalar array element as the start of a contiguous block) rather than strided slicing. A repo-wide grep for strided array sections at call sites (`a(:,x:y:z)`) returned no matches. This specific hazard should be treated as a theoretical Fortran risk to watch for in new code, not a confirmed defect already present.
_Source: repository `Main/mpplib/mod_regcm_types.F90`, `Main/netlib/`, `Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90`_

### Scalability & Performance Patterns: `do concurrent` compiler-portability risk, and halo exchange's un-GPU-aware host-buffer design

Two architecture-level risks compound the pointer-aliasing hazard above for the GPU-porting effort:

1. **`do concurrent` support is uneven across the four required vendors.** Current sources confirm real fragmentation: GCC's `REDUCE` clause is "parsed but not yet lowered for actual parallelism"; Intel's `ifx` supports auto-parallelization and locality clauses but not yet `!$omp loop` composition with `do concurrent`; LLVM Flang's `do concurrent` support (OpenMP integration, locality clauses, `MASK`) is still partial. NVHPC is the most mature target (`-stdpar=gpu`/`multicore`), but a loop written to rely on `REDUCE`/`LOCAL` semantics that works under NVHPC may silently fail to parallelize — not fail to compile — under GCC or ifx, which is a correctness-adjacent risk (wrong performance, not wrong answer) that a build-matrix check across all four vendors needs to catch explicitly, since the governing context's "must build under GNU/Intel/NVHPC at minimum" rule does not by itself guarantee equivalent *parallelization*, only equivalent *compilation*.
2. **Halo exchange (`exchange_array_r8/r4` family, `Main/mpplib/mod_mppparam.F90`) is architected around host-memory MPI buffers**, as established in Technology Stack Analysis. Published practice for GPU-resident stencil codes (e.g. Meso-NH's OpenACC port, GROMACS's NVSHMEM-based halo redesign) converges on keeping halo data resident on-GPU and transferring directly GPU-to-GPU when the MPI library and interconnect support it, using asynchronous exchange to overlap communication with interior-point computation. RegCM's current halo-exchange call sites would need either explicit GPU-resident buffer passing or explicit host staging to benefit from HPC-X's GPU-aware collectives (noted in Technology Stack Analysis) — this is unallocated work, not a solved problem inherited "for free" from the `do concurrent`-only compute strategy.
_Source: [Portability of Fortran's 'do concurrent' on GPUs](https://arxiv.org/html/2408.07843); [Performance Portability of Do Concurrent in Fortran](https://jorgeg94.github.io/posts/2025.11.21-doconcurrent/); [Porting Meso-NH to GPU architectures](https://gmd.copernicus.org/articles/18/2679/2025/); [Redesigning GROMACS Halo Exchange with NVSHMEM](https://arxiv.org/html/2509.21527)_

### Security Architecture

Not a meaningful category here, consistent with the governing context: RegCM is a batch HPC scientific model with no network-facing surface. The closest analogue — Python tooling under `Tools/Scripts/` parsing external namelists/NetCDF/GRIB — is a robustness concern (malformed input files), not a security boundary, and is already covered under the Namelist Configuration finding in Integration Patterns Analysis (unvalidated file-path fields).

### Deployment & Operations Architecture

Deployment is Autotools-build-then-Slurm-submit, with no CI (no `.github/workflows`, no automated build-on-push gate) and no working automated regression-diff tool (`Tools/Scripts/BuildBot/testing.py` is dead Python 2). Validation is entirely fixture-driven integration runs against `Testing/test_001`–`016.in` and `Testing/CORDEX/*.namelist`, compared manually via NCO/CDO against a trusted baseline — there is no smaller trustworthy test unit than a full model run. On the target cluster (CINECA Leonardo), Intel-compiled runs go to `dcgp_usr_prod`/`dcgp_qos_dbg` (account `ICT26_MHPC_0`) and NVHPC-compiled runs go to `boost_usr_prod`/`boost_qos_dbg` (account `ICT26_MHPC`) — i.e. the accelerator build path and the CPU-vendor build path are validated on physically different partitions, which is a further reason the do-concurrent portability risk above (finding 1) needs an explicit cross-partition comparison step, not just "it built."

---

## Implementation Research: Performance Hotspots and GPU-Porting Risk

_Note: generic DevOps/CI/team-organization/cost-optimization categories from the template do not apply to a single-scientist-reviewed batch HPC codebase with no CI. This section instead delivers the research goal directly: concrete, evidence-based performance hotspots (compute and I/O) and refactoring/GPU risks._

### Performance Hotspots — Computation

Call-frequency design is already sound: RegCM decouples expensive physics from the main dynamical timestep via separate `/timeparam/` intervals (`Main/mod_params.F90`) — `dt` (dynamics) defaults to 100 s, while `dtrad` (radiation) = 1800 s (18×), `dtche` (chemistry) = 900 s (9×), `dtcum` (cumulus) = 300 s (3×), `dtsrf` (surface) = 600 s. So the *per-call* cost, not call frequency, is what determines each subsystem's hotspot ranking:

- **Radiation (RRTMG) is the leading compute-hotspot candidate and the least-measured one.** `Main/radlib/mod_rrtmg_driver.F90` (1,280 lines) plus the taumol kernels (`rrtmg_lw_taumol.F90` 3,166 lines, `rrtmg_sw_taumol.F90` 1,762 lines) and the largest genuine-logic file in the physics tree, `mod_rad_radiation.F90` (5,187 lines), are called only every 1800 s — but RRTMG's own core (`mod_rrtmg_driver.F90`, `rrtmg_lw_rad.F90`, `rrtmg_sw_rad.F90`) has **zero** `time_begin`/`time_end` instrumentation, so there is no existing production evidence of its actual share of wall time; only the outer driver (`mod_rad_colmod3.F90`) is instrumented.
- **Chemistry gas-phase integration is a distinct hotspot class: implicit, iterative, data-dependent.** The KPP-generated integrators (`Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90`, `GAS_CBMZ_NEW/mod_cbmz_integrator.F90`) call `DLSODE`, a stiff backward-differentiation-formula (BDF) solver with Newton-iteration counts that vary per grid cell depending on local chemical stiffness. These integrators also carry zero timing instrumentation.
- **Cumulus** (`Main/cumlib/mod_cu_tiedtke.F90`, 7,760 lines, the largest cumulus scheme) and **dynamics/advection** (`Main/mod_moloch.F90` 1,787 + `mod_tendency.F90` 2,069 + `mod_advection.F90` 984 lines) are, by contrast, well instrumented (`time_begin`/`time_end` present throughout) and dynamics is already the most heavily GPU-ported subsystem (112 `do concurrent` occurrences in `mod_moloch.F90` alone, active NVIDIA collaboration per git history).

**The instrumentation gap itself is the first finding**: the governing context's mandatory "required evidence for any optimization claim" rule (hotspot profile, wall time) cannot currently be satisfied for exactly the three subsystems most likely to be expensive — RRTMG core, KPP chemistry integrators, and I/O gather/write (next section) — because none of them have `time_begin` call sites today. Any GPU-porting or optimization work on these subsystems should start by adding `#ifdef DEBUG`-gated timing around them and profiling a real baseline run, not by assuming which one is the bottleneck.
_Source: repository line counts via `Main/radlib/`, `Main/chemlib/`, `Main/cumlib/`, `Main/mod_moloch.F90`; `Main/mod_params.F90` `/timeparam/` namelist; `Main/mpplib/mod_service.F90` (`time_begin`/`time_end` under `#ifdef DEBUG`)_

### Performance Hotspots — I/O

Output write cadence is alarm-driven at 3-6 simulated hours (`/outparam/`: `atmfrq`, `radfrq`, `srffrq`, `chemfrq`, `lakfrq`, `subfrq`, `optfrq`, `savfrq` for restarts in days) — **not** every dynamical timestep. This significantly de-risks the serial gather-then-write bottleneck identified in Technology Stack Analysis (`Main/mpplib/mod_ncout.F90`): it fires rarely relative to compute, so it is unlikely to dominate wall-clock time at typical simulation lengths, though it can still dominate at high rank counts specifically at each write event (a burst cost, not a sustained one). `mod_ncout.F90` itself has zero timing instrumentation, so this is a reasoned inference from call frequency, not a measured fact — it should be confirmed with the same profiling-gap fix noted above before being treated as settled.

Boundary-condition/ICBC input reads (driven by `globdatparam` in `Share/mod_dynparam.F90`) are a separate I/O path not covered by this pass of research — flagged as an open item for dedicated investigation rather than a resolved finding, since input-side I/O frequency and cost were not directly profiled here.
_Source: repository `Main/mod_params.F90` `/outparam/` namelist, `alarm_out_rad`/`alarm_out_che` (`mod_params.F90:2049,2057`); `Main/mpplib/mod_ncout.F90`_

### Refactoring / GPU-Porting Risk Enumeration

1. **`do concurrent` parallelization is compiler-uneven even where compilation succeeds.** A loop relying on `REDUCE`/`LOCAL` semantics that parallelizes correctly under NVHPC may silently run serial (not fail to build) under GCC or Intel — a real risk given "must build under 4 vendors" doesn't guarantee equivalent parallelization.
2. **Pointer aliasing via `assignpnt`** across shared derived-type state (`slice`, `surfstate`, `atmstate_tendency`) is invisible to automatic data-residency analysis — GPU offload of any subsystem touching this aliased state needs explicit reasoning about what's device-resident when.
3. **RRTMG carries a directly analogous, documented GPU-porting failure precedent.** ICON-A's first attempt to port its PSrad radiation scheme (RRTMG's own scheme family/lineage) to GPU via directives "did not reach any acceptable speedup," attributed to the scheme's data structures — specifically the extra spectral-band dimension — and was only resolved by replacing PSrad entirely with RTE+RRTMGP, a scheme designed for GPU from the start (including separate CPU/GPU code paths). This is not a generic "radiation is hard" caution — it is the same radiative-transfer code family RegCM uses, having already failed a directive-based port elsewhere. Combined with finding 1 above (RRTMG is currently the least-instrumented, most compute-suspicious subsystem), this is the single highest-uncertainty item in the whole GPU-porting effort.
4. **KPP chemistry integrators (stiff BDF/Newton, `DLSODE`) have data-dependent iteration counts per grid cell** — the classic irregular-control-flow antipattern for SIMT/`do concurrent` execution. A direct wrap is unlikely to parallelize well; a batched or fixed-iteration reformulation is probably needed, which is a numerics-review-level change (touches the governing context's "no algorithmic change without regression tests + scientific review" rule), not a mechanical port.
5. **Halo exchange targets host-memory MPI buffers only.** Realizing HPC-X 2.25's GPU-direct/GPUDirect-RDMA collective path requires either CUDA-aware buffer passing at `exchange_array_r8`/`exchange_array_r4` call sites or explicit host staging — unallocated engineering work, not a byproduct of the `do concurrent` compute strategy.
6. **BMI (external published contract) is dead code**, guarded by a never-defined `DEVELOPMENT` macro and internally inconsistent even if activated. Not a porting risk per se, but a landmine: a request to "extend the BMI interface" would be building a new implementation from a broken stub, not modifying a working seam — this should be flagged explicitly to whoever scopes such work, per the governing context's rule that external-contract changes need explicit flagging.
7. **The specific F77-contiguity-copy hazard named in the governing context (`a(:,2:18:2)` → silent copy) has no confirmed instance in the current tree** — worth downgrading from "known defect" to "pattern to watch for in new code," since no fixed-form F77 exists and no strided call-site slice was found.

### Recommended Validation Sequencing (per governing project rules)

Consistent with the "Testing Rules" and "Development Workflow Rules" in `_bmad-output/project-context.md` (no automated regression-diff tool exists; validation is manual NCO/CDO comparison against `Testing/` fixtures):

1. Add `#ifdef DEBUG`-gated `time_begin`/`time_end` around the three uninstrumented hotspot candidates (RRTMG core, KPP chemistry integrators, `mod_ncout.F90`) and profile a baseline run (e.g. `test_00N.in`) on both the `dcgp_usr_prod` (Intel) and `boost_usr_prod` (NVHPC) partitions before any optimization work — this produces the evidence the governing context already requires for any optimization claim.
2. Before porting any single subsystem, check whether it is reached through `assignpnt`-aliased shared state (Architectural Patterns Analysis) — if so, data residency needs to be designed explicitly, not inferred.
3. For any `do concurrent` loop added or changed, verify parallelization (not just compilation) under all required vendors — a loop that silently degrades to serial on GCC/Intel is a performance regression a build-only CI check would not catch.
4. Treat RRTMG GPU porting as its own scoped investigation given the ICON-A/PSrad precedent — evaluate whether a directive/`do concurrent` port is likely to succeed at all before investing in it, rather than assuming it will parallelize like the dynamical core did.
5. Any stencil/halo-boundary change (including GPU-residency changes to `exchange_array_r8/r4`) requires the governing context's mandatory multi-process-count regression comparison, not just a single-rank check.

---

## Research Synthesis

_Note on structure: the generic synthesis template includes categories (Competitive Technical Advantage, Regulatory Compliance, Business Impact) written for commercial/web products. RegCM5 is a scientific research code with a single technical decision-maker (the physics owner, per the governing context); those categories are omitted rather than padded with speculative content, consistent with this project's stated preference for concise, non-speculative writing._

### Table of Contents

1. Research Overview (above)
2. Technical Research Scope Confirmation
3. Technology Stack Analysis — build system, compiler assumptions, `do concurrent`/OpenACC, MPI, NetCDF/PnetCDF I/O
4. Integration Patterns Analysis — BMI, OASIS3-MCT, REGESM, internal subsystem contracts, namelist configuration
5. Architectural Patterns and Design — domain decomposition, module conventions, data architecture, deployment model
6. Implementation Research — performance hotspots and GPU-porting risk enumeration
7. Research Synthesis (this section) — executive summary, risk register, recommendations, methodology

### Executive Summary

RegCM5 is a mature, actively developed Fortran 90/2003/2008 regional climate model built on Autotools/libtool, targeting GNU, Intel, and NVHPC compilers with `do concurrent` as its sole loop-parallelism construct — a disciplined, standards-based choice that matches current NVIDIA guidance and avoids a fragmented OpenMP/OpenACC/CUDA-Fortran landscape. Two coupling standards exist side by side (OASIS3-MCT, live and field-rich; REGESM, a separate live path) alongside a third, BMI, that is present in name only — a dead, internally inconsistent stub guarded by a macro the build never defines. Internally, subsystems communicate through pointer-aliased shared derived-type state (`assignpnt`), a pattern efficient for CPU execution but opaque to compiler-driven GPU data-residency analysis, and already identified by the project's own governing rules as the leading GPU-porting hazard.

The most consequential finding for GPU-porting planning is an evidence gap, not a code defect: the two subsystems most likely to dominate wall-clock compute cost — RRTMG radiation and KPP-generated gas-phase chemistry integration — carry zero profiling instrumentation, while the already-GPU-ported dynamical core (MOLOCH) and cumulus schemes are well instrumented. This means the project's own mandatory evidence standard for optimization claims (baseline profile, wall time, hotspot data) cannot currently be met for the subsystems most worth investigating. Compounding this, RRTMG belongs to the same radiative-transfer scheme lineage (PSrad) whose GPU port in ICON-A failed to deliver acceptable speedup via directives and needed a full scheme replacement — a directly analogous precedent, not a generic caution about "radiation is hard."

I/O risk is lower than a first look suggests: although the default history-output path gathers all ranks' data to a single rank before a serial NetCDF write, it fires only every 3-6 simulated hours (alarm-driven), not every timestep, which likely bounds its share of total wall time — a conclusion that should be confirmed with real profiling rather than treated as settled, since `mod_ncout.F90` has no instrumentation either.

**Key Technical Findings:**

- `do concurrent`-only accelerator strategy is disciplined and matches current NVHPC guidance, but its actual parallelization (not just compilation) is unverified across GNU/Intel/LLVM-Flang, whose `do concurrent` support is measurably less mature than NVHPC's.
- Default diagnostic I/O is serial gather-then-write, mitigated by an infrequent write cadence rather than a parallel-I/O design; PnetCDF is opt-in and currently limited to restart files.
- The internal subsystem data contract (`assignpnt` pointer-aliasing over shared derived-type state) is the concrete mechanism behind the project's documented "#1 GPU-porting risk," now traced to specific modules and call sites.
- RRTMG radiation and KPP/DLSODE chemistry are the least-measured, most GPU-porting-uncertain subsystems; RRTMG in particular has a documented failed-port precedent in a closely related scheme.
- BMI is dead code, not a maintained external contract — a request to extend it would mean building a new implementation, not modifying a working one.
- One governing-context claim (`init_mod_*`/`release_mod_*` lifecycle) does not match the code as written; the actual pattern is `allocate_*` plus centralized `getmem`/`relmem`, worth correcting in the governing document.

**Technical Recommendations:**

1. Add `#ifdef DEBUG`-gated timing around RRTMG's core, the KPP chemistry integrators, and `mod_ncout.F90`, and profile a real baseline run on both target partitions before scoping any GPU-porting or optimization work on these subsystems.
2. Treat RRTMG GPU porting as a separate, higher-uncertainty investigation from the dynamical core's — evaluate feasibility against the ICON-A/PSrad precedent before committing effort.
3. Verify `do concurrent` parallelization (not just compilation) across all required compiler vendors for any new or changed loop, since silent serial fallback is a real, documented risk on non-NVHPC compilers.
4. Flag BMI's dormant/broken state explicitly to anyone scoping coupling work, rather than assuming it is a working seam.
5. Correct the governing context's module-lifecycle description (`init_mod_*`/`release_mod_*`) to reflect the actual `allocate_*`/`getmem`/`relmem` pattern.

### Consolidated Risk Register

| # | Risk | Area | Evidence | Severity driver |
|---|------|------|----------|------------------|
| 1 | `do concurrent` parallelizes unevenly across GNU/Intel/LLVM-Flang/NVHPC | Compute / portability | Vendor documentation and community reports (do concurrent GPU portability literature) | Silent performance regression, not a build failure |
| 2 | `assignpnt` pointer-aliasing over shared derived-type state | GPU data residency | `Main/mod_pbl_interface.F90:94-186`, `Share/mod_memutil.F90` | Compiler cannot infer aliasing; manual analysis required per subsystem |
| 3 | RRTMG shares lineage with a scheme that failed GPU porting elsewhere (ICON-A/PSrad) | Radiation / GPU porting | ICON-A GMD publication | Highest-uncertainty subsystem for the whole porting effort |
| 4 | KPP chemistry integrators use stiff BDF/Newton solvers with data-dependent iteration counts | Chemistry / GPU porting | `Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90` (`DLSODE`) | Classic irregular-control-flow SIMT antipattern |
| 5 | Halo exchange targets host-memory MPI buffers only | MPI / GPU-aware communication | `Main/mpplib/mod_mppparam.F90` exchange routines | HPC-X's GPU-direct path unexploited; extra engineering needed |
| 6 | BMI external contract is dead code behind an undefined macro | Integration / external contract | `Main/mod_bmiregcm.F90:16,979-987`; `DEVELOPMENT` undefined repo-wide | Landmine for anyone assuming it is a maintained seam |
| 7 | RRTMG core, KPP integrators, and `mod_ncout.F90` have zero timing instrumentation | Evidence / measurement | `grep` of `time_begin` call sites, `Main/mpplib/mod_service.F90` | No baseline evidence exists for the most compute-suspicious subsystems |
| 8 | Governing context's F77-contiguity-copy hazard example has no confirmed instance in the tree | Documentation accuracy | No `.f` files found; no strided call-site slice found | Low — theoretical risk, not a present defect; downgrade in future guidance |
| 9 | Governing context's `init_mod_*`/`release_mod_*` lifecycle claim does not match the code | Documentation accuracy | Zero `release_mod_*` definitions found repo-wide | Low — a documentation correction, not a code risk |

### Technical Research Methodology and Source Verification

**Technical scope**: build system and compiler assumptions, MPI usage, accelerator directives, NetCDF/I/O paths, physics/dynamics subsystems, internal and external integration contracts, domain decomposition and module design, and performance/GPU-porting risk — as scoped in the Technical Research Scope Confirmation section above.

**Data sources**: primary evidence is direct inspection of the RegCM5 repository (file paths and line numbers cited throughout each section); supplementary evidence is current web sources for external dependencies and comparable-model precedents, cited inline per finding. No claim rests on a single source where a second was available; several findings (e.g. the module-lifecycle correction, the BMI dead-code finding) are cross-checked against repo-wide greps rather than a single file read.

**Confidence levels**: findings grounded in direct code inspection (build system, MPI/I/O structure, integration contracts, decomposition mechanics) are high-confidence. The two performance-hotspot rankings (RRTMG, KPP chemistry) are reasoned from code size, call frequency, and known algorithmic properties (implicit solvers, spectral-dimension radiative transfer) rather than measured profiling data, since no such data exists in the codebase today — this is stated explicitly as the key limitation of the hotspot analysis, not papered over.

**Limitations**: boundary-condition/ICBC input I/O was not profiled in this pass and is flagged as an open item. No performance benchmarking was run as part of this research; all performance statements are architectural/structural inferences pending the instrumentation recommended above.

### Conclusion

RegCM5's GPU-porting strategy is coherent and standards-based where it has already been applied (the MOLOCH dynamical core), but the codebase's own governing risk model under-specifies two things this research surfaces concretely: which subsystems actually cost the most (an instrumentation gap, not a guess), and which external contract is safe to assume as a working seam (OASIS3-MCT and REGESM are; BMI is not). The single highest-leverage next step is not a GPU port at all — it is adding baseline timing to RRTMG, the KPP chemistry integrators, and the diagnostic-output path, so that subsequent porting or optimization decisions rest on the evidence the project's own rules already require.

---

**Technical Research Completion Date:** 2026-07-04
**Source Verification:** All codebase claims cited to file paths/line numbers; all external-technology claims cited to current web sources
**Confidence Level:** High for direct code-inspection findings; explicitly moderate for hotspot ranking pending real profiling (see Limitations above)

_This document is an internal technical research note for RegCM5 development planning, governed by `_bmad-output/project-context.md`._
