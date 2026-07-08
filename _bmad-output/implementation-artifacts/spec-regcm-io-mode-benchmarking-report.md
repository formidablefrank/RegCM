---
title: 'RegCM5 I/O Subsystem Report and do_parallel_netcdf_out Performance Analysis'
type: 'chore'
created: '2026-07-07'
status: 'done'
route: 'one-shot'
review_loop_iteration: 0
context: []
---

# RegCM5 I/O Subsystem Report and do_parallel_netcdf_out Performance Analysis

## Intent

**Problem:** `spec-regcm-io-mode-benchmarking` produced `results.csv`/`runtime_by_io_mode.png` but explicitly deferred writing the analysis report (see `deferred-work.md`); separately, `do_parallel_netcdf_out=.true.` was measurably slower than the default and the reason was unknown.

**Approach:** Read RegCM5's I/O source (`Share/mod_ncstream.F90`, `Main/mpplib/mod_ncout.F90`, `configure.ac`, `acinclude.m4`, this tree's own regenerated `config.log`/`Main/Makefile`, and `lfs getstripe` on the campaign's output directory) to document every configure flag, namelist parameter, and I/O mechanism (gather-to-rank-0, PnetCDF, native NetCDF4/HDF5-parallel, async pthread offload); confirmed this build takes the `PNETCDF` path (`--enable-pnetcdf`, mutually exclusive with the auto-detected `NETCDF4_HDF5` per `configure.ac:889-903`) with Intel MPI's Lustre ROMIO driver enabled (`I_MPI_EXTRA_FILESYSTEM=lustre`); root-caused `do_parallel_netcdf_out=.true.`'s slowdown (0% at 1 node &rarr; +82% at 16 nodes) to two compounding gaps — `ncout_mpi_info` still hardwired to `mpi_info_null` (no striping/aggregation hints) and this campaign's output files sitting inside Lustre's 1-OST Progressive-File-Layout tier — compounded by `write_record_output_stream` (`mod_ncout.F90:4334-4457`) issuing one full-communicator collective call per variable, not batched; wrote `report.md` plus four explanatory SVG diagrams; proposed a staged (aggregator subcomm &rarr; tuned hints &rarr; staged/async I/O) optimization path, plus XIOS as a higher-investment alternative.

## Suggested Review Order

**The core finding (start here)**

- The data: `do_parallel_netcdf_out=.true.` completes correctly at every scale but the gap grows from ~0% to +82% over 1-16 nodes — an Amdahl's-law-shaped result, not a cost that scales down with more ranks.
  [`report.md` &sect;6.1](../../../RegCM-data/benchmarking/parallel-io-initial/report.md#61-what-the-data-shows)

- Why: no MPI-IO striping hints (`ncout_mpi_info = mpi_info_null`), Lustre's Progressive File Layout capping this campaign's <10GB output files to 1 OST, and one full-communicator collective call per variable per output step.
  [`report.md` &sect;6.2-6.4](../../../RegCM-data/benchmarking/parallel-io-initial/report.md#62-missing-mpi-io-striping-hints)

- The per-variable collective-call loop that's the mechanism most likely to scale badly with rank count.
  [`mod_ncout.F90:4334-4457`](../../Main/mpplib/mod_ncout.F90#L4334-L4457)

- Source of truth for the hardwired `MPI_INFO_NULL`.
  [`mod_mppparam.F90:72`](../../Main/mpplib/mod_mppparam.F90#L72)

- Why `PNETCDF` (not `NETCDF4_HDF5`) is the branch this build actually takes, and why the two are mutually exclusive by construction.
  [`mod_ncstream.F90:353-396`](../../Share/mod_ncstream.F90#L353-L396)
  [`configure.ac:889-903`](../../configure.ac#L889-L903)

**Configure flags and namelist reference**

- Full flag table (`--enable-pnetcdf`, `--enable-parallel-nc`, `--enable-nc4-filters`, `--enable-cdf5`, `--enable-async-netcdf`, and the auto-detected `NETCDF4_HDF5`).
  [`report.md` &sect;3](../../../RegCM-data/benchmarking/parallel-io-initial/report.md#3-configure-time-flags-controlling-io)

- Where `NETCDF4_HDF5` actually gets defined (not a flag — an auto-detected capability check).
  [`acinclude.m4:174-194`](../../acinclude.m4#L174-L194)

- `do_parallel_netcdf_in`/`do_parallel_netcdf_out`/`lsync` namelist semantics, including the `lsync` in-code-default-vs-documented-example discrepancy.
  [`report.md` &sect;4](../../../RegCM-data/benchmarking/parallel-io-initial/report.md#4-namelist-parameters-outparam)

**Async NetCDF (orthogonal axis, currently unmeasured)**

- Why `--enable-async-netcdf` is a per-rank latency-hiding mechanism, not a cross-rank parallelism mechanism, and why it can't be benchmarked yet on this branch.
  [`report.md` &sect;5.3, &sect;7](../../../RegCM-data/benchmarking/parallel-io-initial/report.md#53-async-netcdf---enable-async-netcdf-orthogonal-axis)
  [`mod_async_netcdf.F90:16-52`](../../Share/mod_async_netcdf.F90#L16-L52)

**Optimization proposals**

- Staged plan from immediate hint/Lustre fixes through aggregator subcommunicators, PnetCDF, and staged/async I/O (ADIOS2 / HDF5 async VOL).
  [`report.md` &sect;8](../../../RegCM-data/benchmarking/parallel-io-initial/report.md#8-proposed-io-optimization-paths-staged-by-cost-and-risk)

**Diagrams**

- Gather-to-rank-0 vs. collective-parallel data paths, with the current bottleneck mechanisms annotated on panel B.
  [`fig1-io-architectures.svg`](../../../RegCM-data/benchmarking/parallel-io-initial/figures/fig1-io-architectures.svg)

- Which of the four `outstream_setup` implementations a build gets; `PNETCDF` and `NETCDF4_HDF5` are mutually exclusive, and this benchmark takes `PNETCDF`.
  [`fig2-macro-decision-tree.svg`](../../../RegCM-data/benchmarking/parallel-io-initial/figures/fig2-macro-decision-tree.svg)

- Proposed aggregator-subcomm and staged/async target architectures.
  [`fig3-sota-target-architecture.svg`](../../../RegCM-data/benchmarking/parallel-io-initial/figures/fig3-sota-target-architecture.svg)

- The two bottleneck mechanisms behind §6 and the resulting Amdahl's-law-shaped data.
  [`fig4-post-fix-bottleneck.svg`](../../../RegCM-data/benchmarking/parallel-io-initial/figures/fig4-post-fix-bottleneck.svg)

**Peripheral / evidence trail**

- Raw sweep data this report's numbers were checked against.
  [`results.csv`](../../../RegCM-data/benchmarking/parallel-io-initial/results.csv)

- Pre-existing, out-of-scope bugs this report cross-references (async-netcdf build failure, `parallel_in=false` crash, nproc=1 crash) rather than fixes.
  [`deferred-work.md`](deferred-work.md)
