---
title: 'RegCM5 I/O Subsystem Report and do_parallel_netcdf_out Hang Root-Cause'
type: 'chore'
created: '2026-07-07'
status: 'done'
route: 'one-shot'
review_loop_iteration: 0
context: []
---

# RegCM5 I/O Subsystem Report and do_parallel_netcdf_out Hang Root-Cause

## Intent

**Problem:** `spec-regcm-io-mode-benchmarking` produced `results.csv`/`runtime_by_io_mode.png` but explicitly deferred writing the analysis report (see `deferred-work.md`); separately, `do_parallel_netcdf_out=.true.` never produced a single successful run in that sweep, and the reason was unknown.

**Approach:** Read RegCM5's I/O source (`Share/mod_ncstream.F90`, `Main/mpplib/mod_ncout.F90`, `configure.ac`, `acinclude.m4`, and this tree's own regenerated `config.log`/`Main/Makefile`) to document every configure flag, namelist parameter, and I/O mechanism (gather-to-rank-0, PnetCDF, native NetCDF4/HDF5-parallel, async pthread offload); cross-referenced the sweep's `sacct` job history against `sweep_status.txt`/`logs/*.out` to root-cause the `do_parallel_netcdf_out` hang as a missing-MPI-IO-hints / missing-Lustre-ADIO-enablement problem rather than a "wrong code path" bug; wrote `report.md` plus three explanatory SVG diagrams; proposed a staged (aggregator subcomm &rarr; tuned hints &rarr; PnetCDF &rarr; staged/async I/O) optimization path.

## Suggested Review Order

**The hang finding (start here)**

- Corrected job timeline (job 48868355 TIMEOUT after the full 1h, not a 16s cancel) and why the collective-HDF5 path — not a fallback footgun — is what actually hung.
  [`report.md` &sect;6.1-6.2](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/report.md#61-what-was-actually-observed)

- The two concrete missing pieces (`MPI_INFO_NULL`, no `I_MPI_EXTRA_FILESYSTEM`) and the seven-back-to-back-collective-opens compounding factor.
  [`report.md` &sect;6.3](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/report.md#63-what-is-missing-and-why-it-matches-a-collective-open-hang-on-lustre)

- Source of truth for the hardwired `MPI_INFO_NULL`.
  [`mod_mppparam.F90:72`](../../Main/mpplib/mod_mppparam.F90#L72)

- The four-way CPP-macro branch this flag actually dispatches to, and which one this build's `config.log`/`Makefile` prove was taken.
  [`mod_ncstream.F90:353-396`](../../Share/mod_ncstream.F90#L353-L396)

**Configure flags and namelist reference**

- Full flag table (`--enable-pnetcdf`, `--enable-parallel-nc`, `--enable-nc4-filters`, `--enable-cdf5`, `--enable-async-netcdf`, and the auto-detected `NETCDF4_HDF5`).
  [`report.md` &sect;3](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/report.md#3-configure-time-flags-controlling-io)

- Where `NETCDF4_HDF5` actually gets defined (not a flag — an auto-detected capability check).
  [`acinclude.m4:174-194`](../../acinclude.m4#L174-L194)

- `do_parallel_netcdf_in`/`do_parallel_netcdf_out`/`lsync` namelist semantics, including the `lsync` in-code-default-vs-documented-example discrepancy.
  [`report.md` &sect;4](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/report.md#4-namelist-parameters-outparam)

**Async NetCDF (orthogonal axis, currently unmeasured)**

- Why `--enable-async-netcdf` is a per-rank latency-hiding mechanism, not a cross-rank parallelism mechanism, and why it can't be benchmarked yet on this branch.
  [`report.md` &sect;5.3, &sect;7](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/report.md#53-async-netcdf---enable-async-netcdf-orthogonal-axis)
  [`mod_async_netcdf.F90:16-52`](../../Share/mod_async_netcdf.F90#L16-L52)

**Optimization proposals**

- Staged plan from immediate hint/Lustre fixes through aggregator subcommunicators, PnetCDF, and staged/async I/O (ADIOS2 / HDF5 async VOL).
  [`report.md` &sect;8](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/report.md#8-proposed-io-optimization-paths-staged-by-cost-and-risk)

**Diagrams**

- Gather-to-rank-0 vs. collective-parallel data paths, with the hang point annotated.
  [`fig1-io-architectures.svg`](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/figures/fig1-io-architectures.svg)

- Which of the four `outstream_setup` implementations a build gets, and which this benchmark took.
  [`fig2-macro-decision-tree.svg`](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/figures/fig2-macro-decision-tree.svg)

- Proposed aggregator-subcomm and staged/async target architectures.
  [`fig3-sota-target-architecture.svg`](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/figures/fig3-sota-target-architecture.svg)

**Peripheral / evidence trail**

- Raw sweep data this report's numbers were checked against.
  [`results.csv`](../../../RegCM-data/EURR12/benchmarking/parallel-io-initial/results.csv)

- Pre-existing, out-of-scope bugs this report cross-references (async-netcdf build failure, `parallel_in=false` crash, nproc=1 crash) rather than fixes.
  [`deferred-work.md`](deferred-work.md)
