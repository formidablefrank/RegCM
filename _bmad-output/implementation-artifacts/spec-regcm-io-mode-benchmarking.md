---
title: 'RegCM5 I/O Mode Benchmarking Sweep'
type: 'chore'
created: '2026-07-07'
status: 'in-progress'
review_loop_iteration: 0
context: []
baseline_commit: '9ee0370b5'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** RegCM5 has three swept I/O switches (`--enable-async-netcdf` build flag, `do_parallel_netcdf_in`, `do_parallel_netcdf_out`) but no data on how each affects runtime or scales with process count. `lsync` is held fixed at `.false.` (its existing default in the base namelist) and is not swept, to keep the combo count down.

**Approach:** Instrument `Main/regcm.F90` to time the data-prep phase (`RCM_initialize`) separately from the simulation phase (`RCM_run`); build two binaries (async-netcdf on/off); run all 8 runtime-level I/O-mode combinations (async × parallel_in × parallel_out, `lsync=.false.` fixed) scaled by **node count** (1, 2, 4, 8, 16 nodes, `--ntasks-per-node` fixed at 112 — one full `dcgp` node — so `mpirun -n ${SLURM_NTASKS}` always packs whole nodes) on the `dcgp` partition; collect timings into a CSV; and produce a grouped bar chart of the results. Writing the markdown report is deferred (see `deferred-work.md`). *(Scaling variable changed from raw process count to node count per human redesign — see Spec Change Log.)*

## Boundaries & Constraints

**Always:**
- Reuse `EUR12_task3.in` and `bin/slurm-task3-profile.sh` as the starting template; never edit those committed files in place — copy into the benchmarking output dir per combo.
- `lsync` stays fixed at `.false.` in every generated namelist — it is not a swept dimension.
- All node counts (1,2,4,8,16) submit under `dcgp_usr_prod` (the partition's own default QOS: no node/wall-time override, `MaxSubmitPU=1000`) — not `dcgp_qos_dbg` (2-node cap, `MaxSubmitPU=1`, periodically starved by an unreachable rogue driver on another login node), `dcgp_qos_lprod` (3-node cap), or `dcgp_qos_bprod` (`MinTRES node=17` — too big, rejects every size in this sweep with `QOSMinCpuNotSatisfied`). See Spec Change Log and deferred-work.md.
- Submit combos strictly one at a time regardless of QOS, polling each SLURM job to completion before submitting the next.
- Only ever run one `submit_sweep.sh` driver instance at a time, and always launch/monitor it from the same login node/session — this cluster has multiple independent login nodes with no shared process visibility and no passwordless SSH between them, so a driver started elsewhere is untraceable and uncontrollable from a different session.
- No profiling in this task (no perf/nsys/flamegraph) — timing only, via `MPI_Wtime()` around the init/run phases plus SLURM job wall-clock.
- All artifacts (build scripts, per-combo namelists, SLURM scripts, raw logs, `results.csv`, plot) live under `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/benchmarking/parallel-io-initial`.
- `plot_runtime.py` runs under the `rl-gpu` conda env.
- If a combo's job fails or times out, record it as failed in `results.csv` (not silently dropped) and continue the sweep.

**Ask First:**
- Whether to retry a failed/timed-out combo under a longer QOS, vs. leaving it recorded as failed.

**Never:**
- No changes to physics/numerics or the I/O implementation itself — measurement only, not optimization, in this task.
- No code changes to `Main/regcm.F90` beyond the two `MPI_Wtime()` timer wraps.
- No `report.md` in this spec — deferred (see `deferred-work.md`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Normal combo | Valid I/O-mode namelist + nproc | Job completes; init/run/total times recorded | N/A |
| Build failure | `--enable-async-netcdf` build or base build fails | Sweep for that binary's 4 combos halts; failure surfaced to human before continuing | Log build output, HALT |
| Job timeout/OOM | Debug QOS 30-min cap hit, or node OOM | Combo marked `status=failed` in `results.csv` with reason; sweep continues to next combo | N/A |
| Missing/partial stdout timers | Job completes but init/run timer lines absent from log | Combo marked `status=parse_error`; sweep continues | N/A |

</frozen-after-approval>

## Code Map

- `Main/regcm.F90` -- top-level driver calling `RCM_initialize()` then `RCM_run()`; add `MPI_Wtime()` wrap around each, print both to stdout in a greppable format
- `Main/mpplib/mod_runparams.F90:211,213` -- declares `do_parallel_netcdf_in`, `do_parallel_netcdf_out`, `lsync` (`&outparam` namelist group); only the first two are swept, `lsync` stays `.false.`
- `Main/mod_ncio.F90` -- `ASYNC_NETCDF`-gated ICBC prefetch (input-side async read via `mod_async_netcdf`); `do_parallel_netcdf_in` branches throughout (input path)
- `Main/mpplib/mod_ncout.F90:724` -- `lsync` wired to `outstream%opar%l_sync`; `do_parallel_netcdf_out` branches (output path)
- `configure.ac:334-347` -- `--enable-async-netcdf` build flag, sets `-DASYNC_NETCDF`
- `bin/slurm-task3-profile.sh`, `bin/task3-rank0-perf-wrap.sh`, `bin/task3-rank0-nsys-wrap.sh` -- reference build+run scripts to adapt (strip profiling wrappers, parametrize I/O flags/nproc/QOS)
- `RegCM-data/EURR12/EUR12_task3.in` -- base namelist template to copy per combo

## Tasks & Acceptance

**Execution:**
- [ ] `Main/regcm.F90` -- add `MPI_Wtime()` around `RCM_initialize`/`RCM_run` calls, print `INIT_WALLTIME=<s>` / `RUN_WALLTIME=<s>` to stdout -- gives the data-prep vs. simulation I/O split the intent requires
- [ ] `benchmarking/parallel-io-initial/build_async_on.sh`, `build_async_off.sh` -- two build scripts producing distinctly-named `Main/regcm` binaries -- async-netcdf is compile-time, needs two binaries
- [ ] `benchmarking/parallel-io-initial/gen_namelists.sh` -- generate the 8 namelist variants (2×2 runtime params × 2 binaries, `lsync=.false.` fixed) from `EUR12_task3.in`
- [ ] `benchmarking/parallel-io-initial/submit_sweep.sh` -- SLURM job template + serial driver loop: submit one combo (nodes=1,2,4,8,16; `--ntasks-per-node=112` fixed; `mpirun -n ${SLURM_NTASKS}`), poll via `squeue`/`sacct` to completion, pick QOS (dbg for nodes≤2, bprod otherwise), then submit the next
- [ ] `benchmarking/parallel-io-initial/parse_results.py` -- parse per-combo SLURM stdout for init/run/total wall-clock, write `results.csv` (columns: async_netcdf, parallel_in, parallel_out, lsync, nodes, nproc, init_time, run_time, total_time, status)
- [ ] `benchmarking/parallel-io-initial/plot_runtime.py` -- `rl-gpu` env; grouped bar chart, x=node count, y=runtime(s), legend=I/O mode, no axis annotation needed

**Acceptance Criteria:**
- Given the async-off, `parallel_in=true`-only, nodes∈{1,2,4,8,16} combo matrix (async-on and `parallel_in=false` excluded, see Spec Change Log), when the sweep completes, then `results.csv` has a row per attempted combo (10 new attempts, expected `ok`) with `init_time`/`run_time`/`total_time` for successes and `status=failed`/`parse_error` with reason for failures, and every row's `lsync` column reads `false`
- Given `results.csv`, when `plot_runtime.py` runs under `rl-gpu`, then one PNG/SVG bar chart is produced with node count on x, runtime(s) on y, and I/O-mode legend

## Spec Change Log

- 2026-07-07: Split from the original combined spec (instrumentation+build+sweep+parse+plot+report) — token overage (~1870 tokens). `report.md` deferred to a follow-up spec once `results.csv` and the chart exist (see `deferred-work.md`). Everything else in the original spec is preserved unchanged.
- 2026-07-07: `lsync` removed from the swept dimensions per human edit request — held fixed at `.false.` in every namelist instead of toggled. Combo count drops from 16→8 runtime combos (96→48 total SLURM jobs); nproc=1 lprod-QOS combos drop from 16→8 accordingly.
- 2026-07-07: `--enable-async-netcdf` build (job 48843799) fails on this branch with a pre-existing compile bug unrelated to this spec: `Main/mod_ncio.F90:873,992` reference `icbc_prefetch%pai_flat`, but the `icbc_prefetch_slot` type (mod_ncio.F90:98-129) never declares a `pai_flat` component (every other prefetched field has a matching `_flat` pointer; `pai` is missing one). Per human decision, async-on is dropped from this run rather than patched (patching `mod_ncio.F90` is out of this spec's boundaries). Sweep narrows to the 4 async-off combos (`parallel_in × parallel_out`) × 6 nproc = 24 runs. `build_async_on.sh` and the async-on entry in `submit_sweep.sh`'s `BINARIES` array are kept in place, unused, so a future spec can pick this back up once `mod_ncio.F90` is fixed.
- 2026-07-07: the async-off build itself needed a toolchain fix first: dropping `--enable-profile` (not needed once profiling was cut from scope) put `configure.ac` on its `-flto` branch for the Intel LLVM compiler, and plain GNU `ar`/`ranlib` cannot index an archive of LTO bitcode objects ("archive has no index; run ranlib to add one" at final link, reproduced across 3 build attempts including an explicit `ranlib` pass and a serialized final link). Fixed by pointing `AR`/`RANLIB` at the compiler's own `llvm-ar`/`llvm-ranlib` (`build_async_off.sh`, `build_async_on.sh`).
- 2026-07-07: `do_parallel_netcdf_in=.false.` (the `pin_F_pout_F`, `pin_F_pout_T` templates) confirmed broken on this branch — 7/7 attempted runs failed before the sweep driver was paused for a decision (see `deferred-work.md` for full evidence: `Invalid communicator` MPI_Allreduce abort at nproc=1, SIGSEGV across ranks at nproc=224). Per human decision, `parallel_in=false` is dropped from the remaining sweep; the 7 already-recorded failures stay in `results.csv` as documented failures, the other 5 `pin_F_pout_T` nproc combos are left unattempted rather than burning more cluster time on a known-broken path. Sweep narrows further to the 2 `parallel_in=true` combos (`parallel_out: on/off`) × 6 nproc = 12 runs.
- 2026-07-07: the sweep driver process died mid-run after the 7th job (likely a session/shell reset between conversation turns, not a script bug) — resumed cleanly since `submit_sweep.sh` is idempotent on `logs/*.done` markers.
- 2026-07-07: nproc=1 confirmed broken independent of I/O mode — all 4 namelist combos tested (`pin_F_pout_F`, `pin_F_pout_T`, `pin_T_pout_F`, `pin_T_pout_T`) crash identically at nproc=1 (`Invalid communicator` MPI_Allreduce abort ~786-788s in, see `deferred-work.md`). Per human decision, nproc=1 is dropped from the scale sweep going forward (`NPROCS=(4 16 64 144 224)` in `submit_sweep.sh`); the 2 already-recorded `parallel_in=true` nproc=1 failures stay in `results.csv` as documented failures rather than being re-attempted. Combined with the `parallel_in=false` exclusion, the remaining sweep is 2 templates × 5 nproc = 10 new runs.
- 2026-07-07: editing `submit_sweep.sh` while a driver instance had it open mid-loop corrupted one in-flight submission (`pin_T_pout_T__n4`, job 48856004: ran 40 min, hit debug-QOS TIMEOUT, but no `.sbatch`/`.out`/`.err` files were ever written, so the result is unverifiable and discarded — no `.done` marker was created, so `submit_sweep.sh` will retry it cleanly on next run). Operational rule going forward: always confirm the driver process is dead (`ps -ef | grep submit_sweep.sh`, `lsof` the file) before editing it, then relaunch — see `deferred-work.md`.
- 2026-07-07: discovered the "editing mishap" above was actually misdiagnosed — the real cause was a *second, independent* driver instance running on a different login node (`login01`) since early in the session, invisible to `ps`/`pkill`/`lsof` from the login node this conversation was actually running on (`login05`), and unreachable via `ssh` (no passwordless inter-login-node auth). At one point two drivers were alive simultaneously, racing for the single `dcgp_qos_dbg` submission slot. All jobs were cancelled (`scancel -u $USER`, cluster-wide so it also reaches jobs submitted from `login01`) and the campaign was rebuilt from scratch with a design change (see next entry) rather than resumed. See `deferred-work.md` for full evidence and the operational rule this establishes.
- 2026-07-07: **redesigned per human request**: scaling variable changed from raw MPI process count (nproc, unevenly packed across 1-2 nodes) to node count (`nodes=1,2,4,8,16`, `--ntasks-per-node=112` fixed at one full `dcgp` node, `mpirun -n ${SLURM_NTASKS}`). All prior nproc-based sweep artifacts (namelists/logs/output under the old `__n<nproc>` naming) are kept as-is — they're the evidence base for the `parallel_in=false` and nproc=1 bugs in `deferred-work.md` — but are no longer part of `results.csv`; `submit_sweep.sh`, `parse_results.py`, and `plot_runtime.py` were rewritten for the new `__nodes<N>` naming. async-netcdf and `parallel_in=false` stay excluded (both independently confirmed broken, unrelated to the scaling-variable change). New sweep: 2 templates × 5 node counts = 10 runs.
- 2026-07-07: switched all node counts to `dcgp_qos_bprod` (initially only nodes=4/8/16, with nodes=1/2 on `dcgp_qos_dbg`) after the rogue `login01` driver's periodic `dcgp_qos_dbg` submissions started starving this driver's own `dcgp_qos_dbg` requests (repeated `sbatch` rejections on the retry loop). `dcgp_qos_bprod` has no `MaxSubmitPU`, sidestepping the contention entirely.
- 2026-07-07: `dcgp_qos_bprod` turned out to have `MinTRES node=17` — a minimum-size floor above every node count in this sweep (max 16) — so every submission was rejected with `QOSMinCpuNotSatisfied`. Switched to `dcgp_usr_prod`, the `dcgp_usr_prod` partition's own default QOS (`sacctmgr show qos dcgp_usr_prod`: no node/wall-time limits, `MaxSubmitPU=1000`), which has neither the size floor nor the submit-count contention problem.

## Design Notes

Combos are the 2-way cross of `{parallel_out: on/off}` at `parallel_in=true` only, nodes ∈ {1,2,4,8,16} (async-netcdf and `parallel_in=false` excluded, see Spec Change Log) = 10 SLURM jobs. `--ntasks-per-node=112` is fixed (one full `dcgp` node); `mpirun -n ${SLURM_NTASKS}` so total ranks = nodes × 112. `lsync` is fixed `.false.` in every generated namelist, not swept. Each job does one clean (unprofiled) timing run only — no perf/nsys, per the current scope decision. All submissions use `dcgp_usr_prod` QOS (no `MaxSubmitPU` contention); `submit_sweep.sh` still submits and polls one job at a time for simplicity/predictability, never calling `sbatch` again until the prior job's terminal state is observed via `sacct`. Only one driver instance runs at a time, launched and monitored from a single, consistent login-node session.

## Verification

**Commands:**
- `wc -l benchmarking/parallel-io-initial/results.csv` -- expect 11 lines (header + 10 combos), fewer only if documented failures
- `conda run -n rl-gpu python benchmarking/parallel-io-initial/plot_runtime.py` -- expect a chart file written, no traceback
