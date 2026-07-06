---
title: RegCM5 HPC Modernization — Architecture Reference
status: final
created: '2026-07-05'
updated: '2026-07-05'
companion_to: ARCHITECTURE-SPINE.md
---

# RegCM5 HPC Modernization — Architecture Reference

## 0. Purpose and Audience

This document is the narrative companion to `ARCHITECTURE-SPINE.md`, the terse
decision record for RegCM5's HPC modernization program (`prd-RegCM-2026-07-04`,
9 features, FR-1 through FR-38, 4 phases). The spine is the build substrate —
each `AD-n` is a stable citation for future stories and reviews. This document
explains the same decisions in prose, for regcm5-dev as the model's scientific
owner and sole reviewer, and for external collaborators (for instance, the
NVIDIA engineers already active in `mod_moloch.F90`) who need the reasoning,
not just the rule.

Where the spine states a Rule, this document states the Rule and why it
exists. Rationale that lives only here is not binding — the spine's `AD-n` IDs
are the citable reference; this document may be revised more freely to keep
the explanation clear.

## 1. Design Paradigm

RegCM5 is a Fortran HPC batch scientific model, not a service: it runs to
completion as an SPMD MPI job, not as a long-lived process. Two structural
facts follow from the existing codebase, ratified rather than redesigned by
this program:

- **Parallelism** is a 2D domain decomposition over `(iy, jx)`, governed by
  `Share/mod_dynparam.F90`. Every new parallel code path goes through this
  decomposition — there is no second parallelism model to invent.
- **Loop-level parallelism and accelerator offload** are unified under a
  single Fortran 2008 construct, `do concurrent`. NVHPC compiles the same
  source to `-stdpar=multicore` for CPU threading or `-stdpar=gpu` for GPU
  offload, selected by a build flag, not by a second code path. OpenACC is
  available as an escalation when `do concurrent` proves insufficient for a
  specific kernel — the four subsystems already GPU-ported and merged
  (`getcape`/CAPE-CIN, the CLM-hydrology memset fix, `interp1d_r8`,
  `heatindex`) all took that escalation path. There is deliberately no
  OpenMP track and no CUDA Fortran track: `do concurrent` already covers
  the CPU-multicore case OpenMP would otherwise be reached for.

This paradigm is why the modernization program can afford to be selective
about GPU work (§7) rather than porting everything: the same source already
runs correctly on CPU-only builds regardless of how much of it is
GPU-accelerated.

## 2. CPU Baseline Strategy

Every I/O-scaling and performance claim this program makes needs a fixed
point of comparison, or two people's numbers are not comparable. That fixed
point is a single namelist:

```
/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/EUR12_namelist.in
```

a 275×275×36 `EURR-12` domain (`ROTLLR` projection), run at 2 nodes on the
`dcgp_usr_prod` (Intel) partition. The repository also carries
`Testing/EUR12_namelist.in`, the same domain and physics parameters in
version-controlled form — that copy exists for documentation and portability,
not as a second canonical reference. If a performance or I/O claim wasn't
measured against the deployment copy above, at this node count, on this
partition, it isn't evidence this program accepts.

A separate, much smaller fixture — `Testing/ideal.in`, a 100×500×60 idealized
MOLOCH domain with no ICBC or lateral forcing — exists purely for CI
correctness-gating on GitHub-hosted runners (§9). It is not a performance
baseline and should never be cited as one.

## 3. MPI and Threading Strategy

MPI is the sole inter-process parallelism model, via the 2D decomposition
described in §1. `external/mpi-serial` is a drop-in stub so the same code
compiles and runs correctly under a fully serial build — any new parallel
code must keep working under both.

One code-level fact governs how this program tests that decomposition:
RegCM5's automatic rank-to-grid mapping (`set_nproc`,
`Main/mpplib/mod_mppparam.F90:1366-1399`) only splits **both** the `iy` and
`jx` dimensions once `nproc >= 4`. Below that — including the seemingly
reasonable `nproc=2` — only one dimension is split; the other direction's
halo exchange is never exercised, and a decomposition bug there would be
exactly as invisible as running on a single rank. For that reason, this
program's fixed minimum regression pair is **`nproc=1` and `nproc=4`**, not
`nproc=2`. Every change touching stencil or halo code (advection, diffusion,
anything with `i±1`/`j±1` neighbor access) is checked at both.

A related, easy-to-get-wrong question is what tolerance applies when
comparing `nproc=1` against `nproc=4` output. The answer is: the same
two-tier tolerance policy as any other comparison (§4) — no separate,
looser tier for "differences caused by decomposition." RegCM5's halo
exchange exists precisely so a grid point sees the correct neighbor values
regardless of how many ranks are involved; there is no global reduction in
the core prognostic fields that would make results legitimately
rank-count-dependent. A bit-exact-tier field that diverges between `nproc=1`
and `nproc=4` means a real bug, not an artifact to wave off.

**Corrected** (an earlier draft of this document, and the PRD it followed,
understated this): GPU-direct halo exchange is not future or speculative
work — it is already implemented, regcm5-dev-confirmed as scientifically
validated, in `Main/mpplib/mod_mppparam.F90`'s `real8_2d_exchange`/
`real8_3d_exchange`/`real8_4d_exchange` routine family and their directional
variants (51 `host_data use_device` occurrences file-wide). Each routine
packs boundary data into contiguous scratch buffers via `do concurrent`
inside an `!$acc data copy(ml) create(...)` region, then wraps the actual
`mpi_isend`/`mpi_irecv` calls in `!$acc host_data use_device(...)` to pass
device pointers directly to HPC-X 2.25's GPUDirect RDMA path — entirely
internal to each routine body, with no caller-visible signature change.
This is exactly the "GPU-direct as a drop-in behind existing signatures"
pattern this document's own earlier draft asked about as a hypothetical;
it turned out to already be the answer. The simpler point-to-point
`exchange_array_r8`/`exchange_array_r4` primitives (same file) remain
plain host-memory MPI calls with no `!$acc` directives — GPU-direct is
scoped to the packed multi-dimensional exchange family, not universal.
FR-11 is accordingly a verification-and-documentation task confirming
this builds under current target versions, not a fresh feasibility
investigation.

## 4. Numerical Reproducibility Policy

RegCM5 has one reproducibility bar for CPU-only changes and a different,
explicitly narrower one for CPU-to-GPU porting:

- **CPU-only changes default to bit-exact.** Zero tolerance, no exceptions,
  unless regcm5-dev explicitly reviews and records one.
- **CPU-to-GPU porting is accepted at the source thesis's measured
  statistical bounds**: `tas` and `ps` rMAD/rRMSE under 0.1%, `huss` under
  5%, measured over a 7-model-day run. This is an established precedent
  (`project-context.md`), not a new concession — the four already-merged GPU
  ports were following this policy correctly, not violating a stricter one.

This is a two-tier policy, not a sliding scale, and the table that
implements it (in `regression_diff.py`, §8) only knows about `tas`, `ps`,
and `huss` today. Porting a new subsystem to GPU — a MOLOCH wind field, for
instance — does not automatically inherit statistical tolerance. Until that
field's own measured bound is added to the tolerance table, its regression
check holds it to bit-exact by default. That is the policy working as
designed, not a gap to route around silently.

## 5. Profiling Method

This program adopts the tooling the source thesis (`regcm5-optimization.pdf`)
already used, rather than inventing a new profiling facility:

- **`perf --call-graph dwarf`** (built with `-g` debug symbols), rendered as
  flame graphs via Brendan Gregg's FlameGraph scripts, for CPU call-stack
  attribution.
- **NVIDIA Nsight Systems**, specifically because `perf` alone cannot
  resolve some compiler-runtime symbols back to a source-level call stack —
  the thesis's own experience with an unattributed `__c_mset16_avx` memset
  is the concrete example of why this matters.
- **`-Minfo=accel`**, to confirm what a given code region actually offloaded
  and what data movement the compiler generated, rather than assuming a
  `do concurrent` or OpenACC region did what was intended.

Profiling artifacts — `perf.data`, FlameGraph SVGs, Nsight `.nsys-rep`
files, written hotspot reports — get the same storage discipline as
regression baselines (§8): they live on `$FAST` while active and are
archived to `$WORK` on supersession, through the same `manage_baseline.py`
tool.

## 6. I/O Scaling Strategy

RegCM5's diagnostic/history output today gathers every rank's subdomain onto
one I/O rank for a single serial NetCDF write. PnetCDF (true MPI-IO parallel
writes) already exists in the codebase, but only for restart files. This
program extends parallel-write capability to every output path — diagnostic
(FR-5/6), restart (already partially covered), and CLM land-model history
(FR-33) — while keeping serial gather-write as the default everywhere,
because the source thesis measured parallel write as consistently *slower*
than serial across every tested rank count, for reasons FR-34 has not yet
explained. Promoting parallel I/O to a default before that explanation
exists would repeat exactly the kind of unevidenced optimization this
program exists to eliminate.

The three output paths get **independent** opt-in switches, not one unified
toggle, because they resolve on different timelines and the code already
works this way: `do_parallel_netcdf_in`/`do_parallel_netcdf_out` already
exist as two separate switches — the former for ICBC/boundary input
(`mod_params.F90`/`mod_clm_params.F90`), the latter for restart output
(`mod_savefile.F90`).
`mod_ncout.F90` — the diagnostic/history writer FR-5 targets — currently has
no switch of its own and must add one following that same
`do_parallel_netcdf_<path>` naming pattern, not a different shape.

FR-34's investigation into *why* parallel write is slower touches
boundary-condition and ICBC input reads specifically — code the project
already treats as live experimental territory subject to active churn.
Findings there must be flagged for regcm5-dev's review, never silently "fixed"
or "optimized," even when a performance win looks obvious.

## 7. GPU Candidate Selection Criteria

There is deliberately no scoring formula for deciding which subsystem gets
GPU-ported next. Each candidate — RRTMG's radiative-transfer kernels, KPP
chemistry, or anything else — gets its own scoped investigation and an
explicit go/no-go checkpoint, the way FR-9 scopes RRTMG specifically. This
is a standing policy choice, not a placeholder for a formula not yet
written: regcm5-dev's priority right now is I/O scaling and profiling-driven
performance work (§6, §5), not formalizing GPU-porting selection, and
inventing a formula prematurely would risk optimizing for the wrong
signal before enough subsystems have gone through a real investigation to
generalize from.

What the investigation itself should weigh is already established from the
four subsystems already ported: a confirmed, *measured* wall-clock share
(not a structural/code-size guess — RRTMG's apparent size made it look like
the top candidate before real profiling showed it wasn't present at all in
the coupled-configuration flame graph); an absence of blocking
pointer-aliasing (`assignpnt`); and regular, non-data-dependent control
flow (the reason KPP/DLSODE chemistry is excluded from this program's
GPU-porting scope entirely — its data-dependent, irregular iteration
structure is a known poor fit for SIMT execution).

## 8. Test Strategy and Regression Tooling

RegCM5 had no working automated regression-diff tool before this program:
the existing `BuildBot/testing.py` is dead Python 2, and
`preproc-compare.py` only ever compared ICBC initial conditions between two
old model versions. Two tools now close that gap, both built and tested
this session, both living under `Tools/Scripts/TestingAndBenchmarking/`:

### `manage_baseline.py` — baseline and profiling-artifact promotion

Promotes a run's output into a trusted, tracked directory — either the
regression baseline or the profiling-artifact archive, same mechanism
either way:

```
manage_baseline.py promote --run-dir RUN --baseline-dir BASE \
    [--nproc N] [--force --reason "..."] [--archive-dir DIR | --no-archive]
manage_baseline.py log --baseline-dir BASE [--nproc N]
```

It refuses to overwrite an existing file without `--force`, refuses
`--force` without a recorded `--reason`, and refuses to resolve an
overwrite at all unless an `--archive-dir` is given (superseded files are
copied there first, under a timestamped generation folder) or `--no-archive`
explicitly accepts permanent loss. Every promotion — timestamp, user, RegCM
git commit, reason, files touched — is appended to
`PROMOTION_MANIFEST.jsonl` alongside the target directory. `--nproc N`
operates on a `nproc-N/` subdirectory of `--run-dir`/`--baseline-dir`/
`--archive-dir`, so baselines spanning multiple process counts (§3) stay
organized consistently; passing `--nproc` inconsistently between `promote`
and `log` calls is a known footgun (`log` without it silently reports "no
manifest" against the wrong, empty top-level directory rather than an
error).

The live regression baseline lives on `$FAST`
(`/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/baseline`), and
profiling artifacts live at `.../franco/RegCM-data/profiling` — the same `$FAST`
area, for the same reason: `$FAST` is permanent for the life of project
`ICT26_MHPC_0` (plus six months' grace after it ends), unlike the
similarly-named but distinct `$SCRATCH` area, which auto-purges anything
untouched for 40 days. Superseded generations of either are archived to
`$WORK` (`/leonardo_work/ICT26_MHPC_0/franco/RegCM-archive/{baseline,profiling}`)
rather than `$SCRATCH`, for the same reason — an "archive" that silently
expires after 40 days of inactivity isn't an archive. `$FAST` itself has no
backup and a fixed 1 TB quota shared across the whole project; nobody is
yet tracking the project's end date against that six-month grace window,
which remains a standing, unresolved risk.

### `regression_diff.py` — the FR-24/25/26 comparison tool

Compares every `.nc` file a candidate run produces against the matching
file in a trusted baseline, field by field:

```
regression_diff.py --run-dir RUN --baseline-dir BASE \
    [--nprocs 1,4] [--tolerance-file T.json] [--only-fields a,b] \
    [--json] [--report-file report.json]
```

For each shared variable it reports MAD, RMSE, and their baseline-relative
forms rMAD/rRMSE — never a single pass/fail bit — and judges each field
against the two-tier policy from §4 (bit-exact by default; statistical
bounds for the fields already in the tolerance table). `--nprocs 1,4` runs
FR-26's multi-process-count check in one invocation, reading `nproc-<N>/`
subdirectories of both `--run-dir` and `--baseline-dir` per §3's
convention, and applies the identical tolerance table to each — no separate
tier for cross-rank-count comparison. `--report-file` persists the full
JSON report to disk for citation in a commit or PR's acceptance record.

Both tools share an exit-code convention so a CI pipeline (§9) or a Slurm
wrapper script can tell "the check genuinely failed" apart from "the tool
was misconfigured": **0 = pass, 1 = a genuine regression or policy failure
(including a candidate or baseline file that fails to open — a bad output
file is a regression, not a misconfiguration), 2 = a usage or configuration
error** (a missing directory, a malformed argument) that means nothing was
actually compared. `manage_baseline.py` never itself judges a regression,
so every one of its error paths exits 2.

Once FR-3/FR-33 add timing instrumentation to the diagnostic, restart, and
CLM history I/O paths (not yet implemented — see §6), that instrumentation
should follow a fixed naming convention so FR-34's cross-path report can aggregate them
uniformly: `io_gather_<path>`, `io_write_<path>`, `io_wait_<path>`, where
`<path>` is `hist`, `rst`, or `clm`, passed as the free-form label RegCM5's
existing `time_begin`/`time_end` API already expects
(`Main/mpplib/mod_service.F90`). Like all `DEBUG`-gated instrumentation in
this codebase, it must add zero overhead to non-DEBUG production builds.

## 9. Build Matrix

**Native builds.** GNU and Intel are both required and both validate on the
`dcgp_usr_prod` partition (`dcgp_qos_dbg`, account `ICT26_MHPC_0`) — GNU
shares Intel's existing partition assignment rather than getting its own.
NVHPC validates on `boost_usr_prod` (`boost_qos_dbg`, account `ICT26_MHPC`).
AMD/AOCC remains "where feasible," with no assigned partition, unless an
AMD allocation becomes available. Every native NVHPC build tests both
`--enable-openacc-managed` and `--enable-openacc-stdpar` as required,
equally-supported configurations — not one default plus an occasional
check. For an actual GPU production or profiling *run* (as opposed to a
build-matrix *test*), the default is explicit device memory allocation —
plain `--enable-openacc` (`USE_OPENACC=1`, no `mem:managed`/`mem:unified`
flag), requiring explicit `!$acc data`/`copyin`/`copyout`/`create` clauses.
This isn't a departure from the codebase's validated pattern: the
halo-exchange routines (§3) and the `meanall_1D_real8`/`real4` reduction
routines both already manage device memory explicitly, not automatically.

**Version pinning is asymmetric by design.** NVHPC (26.3), HPC-X (2.25),
CUDA (12.9), and every I/O library (HDF5 1.14.3, netCDF-C 4.9.2,
netCDF-Fortran 4.6.1, PnetCDF 1.12.3) are hard-pinned identically across
native builds and all three container variants — bumping any of them needs
the same regression evidence as any other stack change. GNU and Intel
compiler versions are not pinned the same way: containers use whatever
release is currently verified compatible with the pinned I/O library
versions, re-checked at each rebuild. As of this writing, that's GCC 16.1
and Intel oneAPI 2026.0 (`ifx` 2026.0.0) — the latter needs
`FC=ifx F77=ifx CC=icx --disable-fortran-type-check` to build
netCDF-Fortran/PnetCDF cleanly, a known Intel-specific configure issue, not
a RegCM5 bug.

**Containers.** Three variants — GNU, Intel, NVHPC/CUDA — package RegCM5 as
OCI/Docker images, runnable via Apptainer on HPC systems without a Docker
daemon or root access. The NVHPC variant follows NVIDIA's own official
multi-stage pattern (HPC SDK Container Guide 26.3): build against the full
"devel" SDK image, then copy only the compiled binary and its runtime
dependencies into a "runtime"-stage image for distribution — the devel SDK
itself is not freely redistributable. All three variants build from an
Ubuntu 24.04 base image — web-verified compatible with the NVHPC devel
pattern above (NVIDIA publishes `nvcr.io/nvidia/nvhpc:26.3-devel-cuda_multi-ubuntu24.04`),
so the NVHPC variant's base doesn't diverge from GNU/Intel's, closing what
was a real risk to the bit-exact agreement FR-28 requires between them.

**CI.** A green GitHub Actions check (GNU+Intel container builds plus the
regression-diff tool against `Testing/ideal.in`) is necessary evidence but
not sufficient. Final acceptance for any physics, dynamics, or accelerator
change still requires Slurm validation on the actual HPC partitions above —
a passing CI run validates CPU-path builds and one small fixture, not the
four-vendor-plus-GPU discipline this project requires.

## 10. Phased Migration Plan

This program's four phases, unchanged from the PRD, are sequenced by
priority and technical dependency, not a calendar:

1. **Foundation** — profiling instrumentation and baseline (FR-1-4), the
   regression-diff infrastructure this document describes (FR-24-27),
   namelist validation, the NVHPC compiler-identity fix, and documentation
   corrections. Everything later depends on this phase's evidence existing.
2. **I/O and Memory Hardening** — diagnostic/restart/CLM parallel I/O
   (FR-5-7, FR-33), the investigation into why parallel write measures
   slower than serial (FR-34), and a memory-growth investigation (FR-19).
   regcm5-dev's stated near-term priority.
3. **Selective Acceleration and Containerization** — verifying the four
   already-merged GPU ports (FR-35), the statistical-reproducibility
   regression test (FR-37), further GPU-porting work evaluated case by case
   (§7), and all three container variants plus CI (FR-28-32). Highest
   uncertainty of the four phases.
4. **External Coupling Modernization** — OASIS3-MCT, REGESM, and CLM
   documentation/hardening, a CISM coupling design, and resolving BMI's
   dormant status. No technical dependency on Phases 1-3; sequenced last by
   priority choice, not necessity.

## 11. Open Items

The two build-matrix items from an earlier version of this document —
container base OS/distro and the default OpenACC production memory mode —
are now resolved (§9: Ubuntu 24.04; explicit device memory allocation).

The PRD's own remaining open questions (BMI resolution direction, CISM
coupling sponsor, AMD/AOCC commitment trigger, external-collaborator review
process, multi-platform performance portability beyond Leonardo) are
inherited as context, not re-litigated here — see
`prd-RegCM-2026-07-04/prd.md` §8.

## 12. References

- `ARCHITECTURE-SPINE.md` — the terse, citable decision record this document
  explains (20 `AD-n` entries).
- `_bmad-output/planning-artifacts/prds/prd-RegCM-2026-07-04/prd.md` — the
  driving PRD (FR-1 through FR-38, FR-36 retired, 4 phases).
- `_bmad-output/project-context.md` — the standing brownfield rule set (112
  rules) this program ratifies throughout.
- `_bmad-source/regcm5-optimization.pdf` — the ICTP/SISSA MHPC thesis (Tica,
  2024-2026) whose profiling data, GPU-porting work, and reproducibility
  precedent this program builds on directly.
