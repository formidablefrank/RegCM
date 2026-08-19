---
title: 'Verify Multi-Process-Count Comparison'
type: 'chore'
created: '2026-08-18'
status: 'done'
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: '647a9a3e77851d796745fc2932a498816c64349b'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `regression_diff.py --nprocs` has never been exercised at runtime. AD-12 requires `nproc=1`/`nproc=4` as a verified minimum pair before this tool becomes the project's default regression check. `test_001.in` (34×64, Story 1.1's fixture) geometrically can't decompose at `nproc=196` (`set_nproc`'s 3×3-points-per-tile floor, `mod_mppparam.F90:1605-1611`). The larger EUR12 fixture (275×275) clears that floor at every count, but empirical timing (see Design Notes) showed it needs on the order of a full day of wall-clock time per run at `nproc=1`/`4` — infeasible for this story's low-count legs.

**Approach:** Split by fixture. Run twin (identical, unchanged-code) executions of `test_001.in` at `nproc=1,4,16,64` (all pass the 3×3 floor, all fast per Story 1.1 precedent) and of the canonical EUR12 fixture (`/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/EUR12_namelist.in`) at `nproc=196` only, each pair's output placed under matching `nproc-<N>/` subdirectories of a common `--run-dir`/`--baseline-dir` pair, then invoke `regression_diff.py --run-dir RUN --baseline-dir BASE --nprocs 1,4,16,64,196` once to confirm bit-exact agreement and identical tolerance-table application at every count.

## Boundaries & Constraints

**Always:** Run every fixture execution via Slurm (`dcgp_usr_prod`/`dcgp_qos_dbg`/`ict26_mhpc` for the Intel build), never the login node. Use already-preprocessed input as-is for both fixtures — don't regenerate `test_001.in`'s inputs or EUR12's `DOMAIN000.nc`/`ICBC`/`CLM45_surface`. Apply the identical tolerance table across every `nproc` (AD-13) — no override that loosens higher counts. Keep `nproc=1`/`nproc=4` the required minimum pair (AD-12) even though this story also covers 16/64/196. Record Build/Test/Numerical/Performance evidence in the commit/PR description, including the fixture-split rationale.

**Ask First:** `test_001.in` has `ipptls=1` — the exact configuration that caused the `mod_lm_interface.F90:930` crash in Story 1.1; expect it to recur, and confirm before absorbing more crash-workaround scope beyond what Story 1.1 already spent. If the `nproc=196` (2-node, EUR12) run's resource needs threaten fair-use or exceed `dcgp_qos_dbg`'s ceiling, confirm before requesting a larger QOS. If even `test_001.in`'s legs prove impractically slow (unexpected given Story 1.1's precedent, but not yet re-confirmed under the mandatory 24-simulated-hour duration), confirm before further approach changes rather than defaulting to a longer QOS or a non-DEBUG build unilaterally.

**Never:** Don't touch `manage_baseline.py` — Story 1.4's scope. Don't change `DEFAULT_GPU_TOLERANCES` — this story verifies existing policy, doesn't revise it. Don't fix `regression_diff.py`'s vacuous zero-record bit-exact gap or its untested error paths (shape-mismatch, missing-in-candidate/baseline, unreadable) — both already deferred from Story 1.1, out of scope here too. Don't archive `testing.py`/`preproc-compare.py` — Story 1.3's scope.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Bit-exact at all 5 counts | Twin `test_001.in` runs at `nproc=1,4,16,64` plus twin EUR12 runs at `nproc=196`, each pair under matching `nproc-<N>/` subdirectories of one common `--run-dir`/`--baseline-dir` | Single `--nprocs 1,4,16,64,196` invocation reports bit-exact agreement at every count, exit 0 | N/A |
| Non-vacuous data | Each `nproc-<N>` pair's compared streams | Real, non-zero time records past t=0 confirmed before trusting any "exact" verdict | If a stream is empty, flag explicitly rather than accepting a silent pass |
| Geometric/wall-clock fixture fit | `nproc=196` needs EUR12 (`test_001.in` fails the 3×3 floor there); `nproc=1,4,16,64` need `test_001.in` (EUR12 is wall-clock infeasible there) | Each count runs on the fixture sized for it, no fatal abort, no multi-day job | If either fixture still fails/times out at its assigned count, HALT per Ask First |

</frozen-after-approval>

## Code Map

- `regression_diff.py:288-292,234-263` -- `--nprocs`: comma-separated list; `cmd_compare()` loops per `n`, reads `run_dir/nproc-{n}` and `baseline_dir/nproc-{n}` via `check_dir()` (225-227, exits 2 if missing) — caller pre-creates the subdirectories, tool never does
- `regression_diff.py:231,246,254-255,270-275,281` -- tolerances loaded once, applied unchanged per count (AD-13, no per-count branching); JSON nests per `nproc-<N>`; `overall_ok` fails the run if any count fails; aggregate `RESULT` line; shared exit-code convention
- `Main/mpplib/mod_mppparam.F90:1384-1401,1605-1611` (`set_nproc`) -- aspect-ratio-nudged `cpus_per_dim` search; hard `fatal('Too much processors')` below 3×3 points/tile — `test_001.in` (34×64) fails this at `nproc=196` (`jxp=2`) but passes at `nproc=1,4,16,64` (worst case `jxp=4,iyp=8` at 64); EUR12 (275×275) passes at 196
- `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/EUR12_namelist.in` -- `iy=275,jx=275,kz=36`, `dt=45`, `ipptls=2`, `icup_lnd=icup_ocn=5`, `gdate1=2009090100`→`gdate2=2009090800`; input already preprocessed at `RegCM-data/EURR12/input/`. **Empirical timing (job 52631324, `nproc=4`, killed by TIMEOUT at 1h09m):** log's last `ATM/SRF/RAD variables written at` line shows only `2009-09-01 01:00 UTC` reached -- 1 of the mandatory 24 simulated hours -- after over an hour of wall time; a second probe at `nproc=1` (job 52621984) didn't survive aerosol-climatology init in 40 minutes. This is why EUR12 is now scoped to `nproc=196` only.
- `Testing/test_001.in` -- `iy=34,jx=64,kz=18`, `ipptls=1` (Story 1.1's fixture); ran fast there (twin runs completed well inside 30 min per `spec-1-1`'s Verification section) but crashed on `mod_lm_interface.F90:930` after t=0
- `Main/mod_lm_interface.F90:349,930` -- `assignpnt(sptc,lm%csrate)` guard (`ipptls>1 .and. any(icup==5)`) is **true** for EUR12, **false** for `test_001.in` -- `test_001.in`'s `ipptls=1` is exactly why Story 1.1 hit the crash there; expect a recurrence on this story's `test_001.in` legs too
- `bin/slurm-task2b-build-and-run.sh` -- reference Slurm template (`dcgp_usr_prod`/`dcgp_qos_dbg`/`ict26_mhpc`, 2 nodes×112 tasks/node, 30 min for a 1-day EUR12-scale run at 224 ranks); confirms the `nproc=196` EUR12 leg should fit comfortably at 2 nodes/196 ranks, consistent with the empirical timing note above pointing to *low* rank counts, not EUR12 itself, as the cost driver
- `spec-1-1-verify-and-commit-the-regression-diff-tool.md` -- Story 1.1 precedent: twin-run methodology on `test_001.in`, Build/Test/Numerical/Performance evidence convention, the vacuous-zero-record caveat to guard against here, and the crash's full root-cause writeup
- `ARCHITECTURE-SPINE.md:98,104` -- AD-12 / AD-13 definitions

## Tasks & Acceptance

**Execution:**
- [x] Write Slurm job script(s) for twin `test_001.in` executions at `nproc=1,4,16,64` and twin EUR12 executions at `nproc=196` -- place each pair's output under a common `RUN-dir/nproc-<N>/` and `BASELINE-dir/nproc-<N>/` -- matches the directory convention `regression_diff.py --nprocs` expects regardless of which fixture produced it
- [x] Submit and confirm all 10 runs (5 counts × 2 twins) complete without a fatal abort; if `mod_lm_interface.F90:930` recurs on a `test_001.in` leg, apply Story 1.1's already-established documentation of it rather than re-deriving the root cause, per Ask First -- **recurred exactly as anticipated (no code change made or needed -- documented, not worked around)**, see Verification/Caveat
- [x] Run `regression_diff.py --run-dir RUN --baseline-dir BASE --nprocs 1,4,16,64,196` once -- confirms single-invocation multi-count reporting and identical tolerance-table application (AD-13)
- [x] Manually confirm each `nproc-<N>` pair's compared streams carry genuine non-zero time records (not the vacuous zero-record pass flagged in `deferred-work.md`) before treating the run as valid evidence -- **see Verification/Caveat: genuine only for ATM at nproc=1/4/16/64 and for all streams at nproc=196; RAD/SRF/STS at nproc=1/4/16/64 are vacuous**
- [x] Record Build/Test/Numerical/Performance evidence in the commit/PR description, including why the fixture differs by process count

**Acceptance Criteria:**
- Given twin runs (`test_001.in` at `nproc=1,4,16,64`, EUR12 at `nproc=196`) placed under matching `nproc-<N>/` subdirectories, when `regression_diff.py --run-dir RUN --baseline-dir BASE --nprocs 1,4,16,64,196` is invoked, then the single invocation reports pass/fail for all five counts using the identical tolerance table (AD-13), no looser tier at higher counts
- Given the same unchanged fixture (per count) run twice at every process count, when the comparison runs, then it reports bit-exact agreement at all five, confirming no existing decomposition bug at higher rank counts
- Given AD-12 fixes `nproc=1` and `nproc=4` as the required minimum pair, when `nproc=16/64/196` are added, then they are additional coverage beyond that minimum, not a replacement — a divergence appearing only at 16/64/196 is still a real regression

## Spec Change Log

- **2026-08-18, mid-implementation:** Original approach ran EUR12 at all 5 counts. Real Slurm evidence (job 52631324, `nproc=4`: only 1 of 24 mandatory simulated hours reached after 1h09m before TIMEOUT; job 52621984, `nproc=1`: didn't survive init in 40 min) showed EUR12 at low `nproc` is wall-clock infeasible (plausibly a day+ per run), not just tight on QOS. Human-confirmed resolution: split by fixture — `test_001.in` (fast, proven in Story 1.1) for `nproc=1,4,16,64`; EUR12 (only fixture clearing the 3×3 decomposition floor) for `nproc=196`. **KEEP:** the `--nprocs`-mechanism understanding (Code Map lines on `regression_diff.py`), AD-12/AD-13 citations, and the vacuous-zero-record caveat all still apply unchanged. Known-bad state avoided: burning further multi-hour Slurm allocations chasing a single-fixture approach that can't complete within any practical QOS.

## Design Notes

Two fixtures, chosen per count for different reasons. `test_001.in` (34×64, `ipptls=1`) fails the 3×3 decomposition floor at `nproc=196` (see Code Map) but is fast and already proven at `nproc≤64` from Story 1.1 — expect its known `mod_lm_interface.F90:930` crash (`ipptls=1` leaves `lm%csrate` disassociated) to recur there, per Ask First. EUR12 (275×275, `ipptls=2`) clears the decomposition floor at `nproc=196` and its `icup_lnd=icup_ocn=5` configuration makes the `assignpnt(sptc,lm%csrate)` guard true (genuinely associating `lm%csrate`, unlike `test_001.in`) — `EUR12_task2b.in` already completed under `--enable-debug` Intel without crashing, consistent with that. But EUR12 is the wrong choice at low `nproc`: the empirical timing note in Code Map shows it doesn't fit any practical wall-clock budget below roughly 196 ranks, so it is scoped to that one count only.

## Verification

**Commands:**
- Slurm-submitted `regression_diff.py --run-dir RUN --baseline-dir BASE --nprocs 1,4,16,64,196` (job 52838350, `bin/slurm-1-2-diff.sh`) -- expected: exit 0, all 5 `nproc-<N>` blocks report bit-exact -- **got exactly this: exit 0, `pass: true` at all 5 counts, 0 non-exact fields out of 149 (nproc=1/4/16/64) / 202 (nproc=196) compared fields -- but see Caveat below: this headline number is not equally strong evidence at every count**

**Build:** both fixtures ran the identical pre-existing binary, not rebuilt for this story (no source changes) -- `./Main/regcm` reports `GIT Revision: 39f20-dirty compiled at: data : Aug 11 2026 time: 04:57:04` in every run's own stdout header (confirmed identical on job 52647992 (`test_001.in`, nproc=1) and job 52648082 (EUR12, nproc=196)), an `--enable-debug` Intel oneAPI 2024.1.0 build (module set matches `bin/slurm-task2b-build-and-run.sh`'s reference toolchain).

**Outcome (2026-08-19):** All 10 twin runs (5 counts × RUN/BASELINE) completed. `nproc=196` (EUR12, `bin/slurm-1-2-twin-run.sh`, jobs 52648082/52648968, ~27 min each -- against `dcgp_qos_dbg`'s 30-min cap) produced genuinely complete data: ATM 25 / RAD 24 / SRF 24 / STS 1 real time records (ATM = t=0 init dump + 24 hourly steps; RAD/SRF hourly from t=1 only, no t=0 radiation/surface diagnostic; STS = one daily record at the 24h boundary -- consistent with `atmfrq=radfrq=srffrq=savfrq=1.0h` in the namelist), all fields bit-exact between RUN and BASELINE. `nproc=1,4,16,64` (`test_001.in`, jobs completing in 9-19s each) each hit `RESULT: CRASHED ... exit=152 -- expected mod_lm_interface.F90:930 if ipptls=1` immediately after the t=0 `ATM variables written` line. Confirmed directly in job 52647992's stderr, not just inferred from timing/precedent:
  ```
  forrtl: severe (408): fort: (32): A pointer with the CONTIGUOUS attributes is being made to a non-contiguous target.
  regcm   collect_output   930   mod_lm_interface.F90
  regcm   surface_model    570   mod_lm_interface.F90
  ```
  This is the exact recurrence this spec's Ask First clause anticipated (`test_001.in`'s `ipptls=1` leaves `lm%csrate` disassociated, same root cause as Story 1.1). `regression_diff.py --nprocs 1,4,16,64,196` in one invocation reported `pass: true` at every count with zero non-exact fields.

**Caveat:** manually confirmed via `netCDF4`'s `time` dimension length on every file in both trees (per this story's own Tasks item, prompted by the vacuous-pass gap `deferred-work.md` flagged after Story 1.1). At `nproc=1,4,16,64`: only the `ATM` stream carries a real record (`time_len=1`); `RAD`/`SRF`/`STS` are all `time_len=0` on both RUN and BASELINE, so their "exact" verdict is the same vacuous zero-record pass Story 1.1 already documented, not new evidence -- `regression_diff.py` still doesn't distinguish this case (pre-existing gap, out of this story's scope per Boundaries). The genuine evidence at those 4 counts is therefore ATM-only, bit-exact, real spatially-varying t=0 fields (`ps`, `ta`, `ua`, `va`, `hus`, `ts`, ...). **This means AD-12's mandated `nproc=1`/`nproc=4` minimum pair is verified for ATM only, not for RAD/SRF/STS** -- flagged explicitly here (deferred to `deferred-work.md`) rather than let the `pass: true` headline imply full multi-stream coverage at those counts. At `nproc=196`: every stream has real, multi-record data and the bit-exact verdict is fully genuine -- this is the one count in the sweep with complete, non-vacuous coverage across all output streams.

## Suggested Review Order

**Fixture-split decision and why**

- Why EUR12-everywhere was abandoned mid-implementation and replaced with a fixture split.
  [`spec-1-2-verify-multi-process-count-comparison.md:15`](./spec-1-2-verify-multi-process-count-comparison.md#L15)

- The human-confirmed pivot, with the real Slurm timing evidence that triggered it.
  [`spec-1-2-verify-multi-process-count-comparison.md:65`](./spec-1-2-verify-multi-process-count-comparison.md#L65)

- Why `test_001.in` handles 1/4/16/64 and EUR12 only 196 -- decomposition floor vs. wall-clock cost.
  [`spec-1-2-verify-multi-process-count-comparison.md:69`](./spec-1-2-verify-multi-process-count-comparison.md#L69)

**Verification evidence -- the actual substance**

- Full outcome: 10 runs, per-count record counts, and the confirmed crash recurrence.
  [`spec-1-2-verify-multi-process-count-comparison.md:78`](./spec-1-2-verify-multi-process-count-comparison.md#L78)

- The crash claim substantiated with real stderr, not just timing/precedent.
  [`spec-1-2-verify-multi-process-count-comparison.md:80`](./spec-1-2-verify-multi-process-count-comparison.md#L80)

- Which binary/build produced every run (same DEBUG Intel build, both fixtures).
  [`spec-1-2-verify-multi-process-count-comparison.md:76`](./spec-1-2-verify-multi-process-count-comparison.md#L76)

**Known gap -- AD-12's minimum pair only partly verified**

- The headline `pass: true` qualified: genuine only for ATM at low `nproc`, full at `nproc=196`.
  [`spec-1-2-verify-multi-process-count-comparison.md:86`](./spec-1-2-verify-multi-process-count-comparison.md#L86)

- Deferred: closing the RAD/SRF/STS gap needs a non-DEBUG build, a different low-`nproc` fixture, or a tool-level zero-record guard.
  [`deferred-work.md:25`](./deferred-work.md#L25)

**Tooling fixes from review**

- `regression_diff.py`'s own exit code now propagates as the Slurm job's exit status, not always 0.
  [`slurm-1-2-diff.sh:28`](../../bin/slurm-1-2-diff.sh#L28)

- EUR12 namelist substitution now asserted, matching the guard the `test_001.in` script already had.
  [`slurm-1-2-twin-run.sh:62`](../../bin/slurm-1-2-twin-run.sh#L62)

**Peripherals**

- Sprint tracker synced to `review`, matching this spec's own status.
  [`sprint-status.yaml:57`](./sprint-status.yaml#L57)

- Supporting driver and `test_001.in` twin-run scripts (unmodified by review; robustness gaps deferred above).
  [`slurm-1-2-submit-queue.sh`](../../bin/slurm-1-2-submit-queue.sh) · [`slurm-1-2-t001-twin-run.sh`](../../bin/slurm-1-2-t001-twin-run.sh)

