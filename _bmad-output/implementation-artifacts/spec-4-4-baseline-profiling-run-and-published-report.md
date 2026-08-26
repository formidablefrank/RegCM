---
title: 'Baseline Profiling Run and Published Report'
type: 'chore'
created: '2026-08-23'
status: 'done'
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: '321539eb939098e8cf482754d97220a7f59a39c7'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Epics 10 and 11's hotspot decisions still rest on the source thesis's CLM4.5-coupled data and a structural-inference note. Only one partial measurement exists so far — Story 4.1's Intel/`dcgp_usr_prod` RRTMG pass (job 48812653, `≈6.0%`) — and it predates Stories 4.2/4.3's DEBUG timers and has no `boost_usr_prod` (NVHPC) counterpart.

**Approach:** Build a `--enable-debug` binary on each partition (a full-link Intel binary; refresh/reuse Story 4.3's NVHPC binary), run the AD-8 canonical fixture (`RegCM-data/EURR12/EUR12_namelist.in`, RRTMG forced active, default diagnostic-I/O path) under `perf`+FlameGraph on `dcgp_usr_prod` and both `perf`+FlameGraph and Nsight Systems on `boost_usr_prod` (the latter to resolve `nvfortran`-runtime symbols `perf` cannot attribute), read each run's `mod_service` `time_print` table for measured per-subsystem wall-time share, and attempt one NVHPC GPU-flavored build for `-Minfo=accel` evidence. Publish findings as a new report citing the thesis's four hotspots and job 48812653.

## Boundaries & Constraints

**Always:** Use `perf --call-graph dwarf` (`-g` build) + FlameGraph on both partitions, plus NVIDIA Nsight Systems (`--trace=osrt`, no `mpi`) on `boost_usr_prod`, wrapping the `regcm` process directly (rank-0 only) via `bin/task3-rank0-{perf,nsys}-wrap.sh`'s pattern — not `mpirun`/`srun` (AD-2, this cluster's per-rank job-step isolation). Report measured wall-time share per subsystem per partition straight from `mod_service`'s `time_print` table for every currently-registered Epic-4 timer (`rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw`, `io_gather_hist`/`io_write_hist`/`io_wait_hist`), cross-checked against perf/Nsight symbol-level Self%. Explicitly cite the thesis's CLM4.5-coupled hotspots (`getcape`/CAPE-CIN 54%, CLM-hydrology memset ~20%, `interp1d_r8` ~12%, `heatindex` ~8%) and job 48812653 as prior evidence extended here, not repeated. Base the working fixture on `RegCM-data/EURR12/EUR12_namelist.in` (the AD-8 canonical baseline, real paths, 7-day window), forcing `irrtm=1`; diagnostic I/O stays at its file default (serial, already NVHPC-runtime-verified by Story 4.3). Let the user review each Slurm script before submission. State in the commit description exactly which partition/subsystem is measured versus code-inspection/deferred.

**Ask First:** Before spending real effort chasing `--enable-openacc-managed`/`-debug`/`-stdpar` past `mod_bdycod.F90`'s ICE — Story 4.3 already conclusively characterized it as a systemic NVHPC 26.3 backend defect (`deferred-work.md`, 2026-08-22 entry); capture whatever `-Minfo=accel` output the build emits before that failure and stop. Before forcing `chemsimtype` on for KPP-chemistry timer coverage — Story 4.2 documented that no chemistry-enabled configuration has ever run to completion in this codebase (six distinct crashes across two stories); default to reporting `cbmz_integrate`/`cb6_integrate` as not measured this pass. Before fixing any pre-existing bug surfaced while building or running — this story measures and reports, it does not fix.

**Never:** Modify `mod_service.F90`'s shared timer registry or any Epic-4 instrumentation call site (Stories 4.1–4.3, done). Repeat Story 4.3's exhaustive HDF5-/PnetCDF-parallel path verification — this story reports wall-time share, not I/O-path correctness. Claim a wall-time-share number without a real job's captured `time_print`/perf/Nsight output backing it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| DEBUG build, both partitions, working fixture | `irrtm=1`, chemistry off, default diagnostic I/O | Report states measured per-subsystem wall-time share on each partition from `time_print` + perf/Nsight | N/A |
| NVHPC GPU-flavored build reaches `mod_bdycod.F90`'s known ICE | Build attempted for `-Minfo=accel` evidence | `-Minfo=accel` output captured for every file compiled before the failure; report states which offloaded routines got confirmed | Do not re-investigate the ICE |
| Chemistry-enabled fixture attempted | `chemsimtype` forced on | Likely crash before reaching `cbmz_integrate`/`cb6_integrate` (Story 4.2 precedent) | Report states chemistry share as not measured this pass, cites Story 4.2 |
| Non-DEBUG production build | Same binaries without `-DDEBUG` | Out of scope — no overhead already covered by Stories 4.1–4.3 | N/A |

</frozen-after-approval>

## Code Map

- `bin/slurm-task3-profile.sh`, `bin/task3-rank0-{perf,nsys}-wrap.sh` -- Story 4.1's `dcgp_usr_prod` perf+Nsight+FlameGraph pipeline; reuse directly for the Intel leg (`FLAMEGRAPH_DIR=/leonardo_scratch/fast/ICT26_MHPC_0/franco/FlameGraph`)
- `_bmad-output/implementation-artifacts/spec-4-1-instrument-rrtmgs-compute-core.md:91` -- job 48812653's measured RRTMG `≈6.0%` (Intel/`dcgp`, `--enable-profile` build, no DEBUG timers) -- prior evidence to extend
- `bin/slurm-4-3-build-intel-debug.sh` -- existing Intel DEBUG compile-check, reduced scope (`external`/`Share`/`Main/mpplib`), never links `Main/regcm` -- extend to a full link; no runnable Intel DEBUG binary exists yet
- `bin/regcm-4-3-debug-nvhpc` -- existing NVHPC DEBUG binary (Story 4.3), already carries all Epic-4 timers merged into `develop` -- reuse for `boost_usr_prod`, rebuild only if stale against current HEAD
- `Main/mpplib/mod_service.F90:165,185,259-271` -- `time_begin`/`time_end`/`time_print`, the unconditionally-emitted per-run table this report reads
- `RegCM-data/EURR12/EUR12_namelist.in` -- AD-8 canonical baseline fixture (real paths, `gdate1`/`mdate0`=2009090100, `gdate2`/`mdate2`=2009090800, `do_parallel_netcdf_out=.false.`) -- copy and force `irrtm=1`; this is the base fixture per this checkpoint's direction, not Story 4.1's truncated `EUR12_task3.in` copy
- `RegCM-data/story4-3/EUR12_story4-3_serial.in` -- Story 4.3's working serial diagnostic-I/O fixture, same `do_parallel_netcdf_out=.false.` default -- confirms the AD-8 fixture's default path is already runtime-verified
- `deferred-work.md` (`mod_bdycod.F90` ICE entries, 2026-08-21/22) -- do not re-open this investigation
- `_bmad-output/implementation-artifacts/spec-4-2-instrument-kpp-chemistry-integration.md` (Verification, Design Notes) -- chemistry-enabled runtime history behind the Ask-First chemistry decision
- `_bmad-source/implementation/regcm5-optimization-thesis.pdf` Appendix A -- profiling method source; four hotspot figures to cite

## Tasks & Acceptance

**Execution:**
- [x] `bin/slurm-4-3-build-intel-debug.sh` (copy) -- extend to a full `Main/regcm` link -- produce a runnable Intel DEBUG binary with current Epic-4 instrumentation -- **done** (`bin/slurm-4-4-build-intel-debug.sh`, job 53957457, PASS; an intermediate attempt at `-j112` hit a parallel-make race in `Main/microlib`, reverted to `-j32` matching this project's own precedent)
- [x] Confirm or rebuild `bin/regcm-4-3-debug-nvhpc` against current `develop` HEAD -- ensure the NVHPC leg reflects all Epic-4 timers -- **done, via a new sequential-build script, not the existing one**: `bin/slurm-4-3-fullbuild-nvhpc-debug.sh`'s own recursive `make -j16` hit the exact Automake SUBDIRS race documented in this project's build rules (job 53957181, `NVFORTRAN-F-0004-Unable to open MODULE file mod_date.mod`); `bin/slurm-4-4-refresh-nvhpc-debug.sh` (new, sequential per-directory, Story 4.3's own script left untouched) succeeded (job 53957727, PASS)
- [x] Copy `RegCM-data/EURR12/EUR12_namelist.in`, force `irrtm=1`, keep diagnostic I/O and chemistry at their file defaults -- one working fixture reused on both partitions -- **done**, with one correction: `RegCM-data/story4-4/EUR12_story4-4.in` (dcgp) and `EUR12_story4-4_boost.in` (boost) are two copies differing only in `dirout`, not one shared file -- `Main/mod_params.F90:749` enforces a hard 24-simulated-hour-multiple minimum run length (discovered via an actual crash, job 53957605), which is the AD-8 fixture's minimum window on both partitions regardless, so the two copies are identical in every namelist value that matters to this story
- [x] Submit `dcgp_usr_prod` run under `perf --call-graph dwarf` + FlameGraph -- capture `time_print` + perf output -- **done** (job 53958861, PASS, 48m32s; two earlier attempts failed on the 24h-minimum-runtime discovery and a missing output directory, both fixed)
- [x] Submit `boost_usr_prod` run under both `perf --call-graph dwarf` + FlameGraph and Nsight Systems (`--trace=osrt`) -- capture `time_print` + perf + Nsight output -- **done**, split into two separate jobs (Nsight: job 53958915, PASS, 5h11m; perf: job 54143865, PASS after a corrupted first attempt, job 54078622 -- perf's default ~4000Hz sampling rate produced a 574GB capture with lost/corrupted chunks over the leg's 5.5-hour duration; fixed to `-F 99` in `bin/task4-4-rank0-perf-wrap-nvhpc.sh`)
- [x] Attempt one GPU-flavored NVHPC build for `-Minfo=accel` evidence, stopping at `mod_bdycod.F90`'s known ICE without further investigation -- **done** (job 53958940); the build crashed earlier and differently than expected -- a new, fifth NVHPC 26.3 compiler defect (`fort2` segfault) in `Main/microlib/mod_micro_nogtom.F90`, `mod_bdycod.F90` never reached -- 234 `-Minfo=accel` lines captured before the crash, logged to `deferred-work.md` per this story's own Ask-First boundary (capture evidence, don't chase the fix)
- [x] Write `_bmad-output/implementation-artifacts/epic-4-baseline-profiling-report.md` -- per-subsystem, per-partition measured wall-time share, explicit citations to the thesis's four hotspots and job 48812653, chemistry-timer coverage stated as not measured (cites Story 4.2) -- **done**

**Acceptance Criteria:**
- Given Stories 4.1–4.3's instrumentation is in place, when the baseline run executes on `dcgp_usr_prod` and `boost_usr_prod`, then the report states, per subsystem and per configuration, measured wall-time share on each partition — not an estimate — explicitly citing the thesis's `getcape`/CAPE-CIN (54%), CLM-hydrology memset (~20%), `interp1d_r8` (~12%), `heatindex` (~8%) findings — **met, with one documented exception**: every figure is directly measured except the MOLOCH driver's absolute total on `boost_usr_prod`, which overflowed `mod_service.F90`'s fixed print format on all 16 ranks (a pre-existing infrastructure limitation, out of this story's scope to fix) and is reported as a bounded estimate (firm lower bound 5234.09s from its own known physics sub-timers, upper bound ~17,779s) rather than an exact figure — every other subsystem, on both partitions, is a direct measurement
- Given the report is published, when a later story cites hotspot data, then it cites this report and the source thesis, not the technical research note's structural inference — **met**
- Given AD-2's fixed profiling method, when the profiling pass runs, then it uses `perf --call-graph dwarf` with FlameGraph rendering, NVIDIA Nsight Systems, and `-Minfo=accel` to confirm offload behavior — **met**; the report also documents a genuine methodological finding not anticipated at spec time -- rank-0-only `perf` sampling reflects that one rank's own behavior (MPI-communication-bound at dcgp's 224-way decomposition, compute-bound at boost's 16-way decomposition), not a domain-average subsystem share, so `mod_service`'s DEBUG timers -- not `perf`'s Children%/Self% columns -- are the report's primary evidence source for wall-time share; `perf`/Nsight are used as AD-2 intends, for hot-routine identification and compiler-runtime attribution

## Spec Change Log

- **2026-08-24, implementation:** The frozen Boundaries text describes the fixture as having a "7-day window" — accurate of the AD-8 canonical file itself, but this story's actual runs use the file's minimum valid window instead. `Main/mod_params.F90:749` enforces `mod(mdate2-mdate1,24)==0` (discovered via an actual FATAL crash, job 53957605, when a since-abandoned checkpoint direction tried a 6-simulated-hour window before this constraint was known); `dcgp_qos_dbg`/`boost_qos_dbg`'s hard 30-minute `MaxWall` cannot fit even the 24h minimum at measured rates (36m41s/24h at 224 ranks, confirmed via job 48753781), so both run legs use `dcgp_qos_lprod`/`boost_qos_lprod` instead. Read the Tasks entries above, not the frozen text's "7-day window" parenthetical, as the accurate description of what actually ran.
- **2026-08-25/26, implementation:** `perf`'s rank-0-only Children%/Self% breakdown turned out not to be usable as a wall-time-share source (see the report's own "Why perf's rank-0 capture is not a percentage-share source" section) — dcgp's rank 0 is MPI-communication-bound at 224-way decomposition, and boost's `rrtmg_driver` shows 0.46% via `perf` against 2010s via the DEBUG timer, a 24x divergence attributed to imperfect DWARF unwinding through NVHPC's `-Mbounds` runtime-check helper. The frozen Boundaries text's "cross-checked against perf/Nsight symbol-level Self%" is satisfied in spirit (both tools ran, both are cited) but `mod_service`'s DEBUG timers, not `perf`'s own percentages, ended up as the report's primary wall-time-share evidence — a finding, not a shortcut.
- **2026-08-25/26, implementation:** `Main/mod_moloch.F90:321-444` wraps the entire `moloch()` driver — including its call to `physical_parametrizations` (line 363), which itself calls RRTMG, microphysics, PBL, and cumulus — in the single `'moloch'` DEBUG timer. The frozen Boundaries text's per-timer report expectation is met, but the report's percentages treat `moloch` as inclusive of `rrtmg_driver`/`microphys`/`holtbl`/`tiedtkedrv` (a breakdown within `moloch`, not four additional additive top-level costs) — confirmed independently via `perf`'s own call graph. Reading the timers as flat and additive, as an earlier draft of this story's own analysis initially did, double-counts every physics scheme's cost.
- **2026-08-26, bmad-build step-04 review:** Three parallel review layers (Blind Hunter, Edge-Case Hunter, Verification-Gap Reviewer) ran against the full diff since `baseline_commit` (two new markdown files plus a `deferred-work.md` append — no source code touched this story). All three independently flagged the same real bug: `sprint-status.yaml` was left at `in-progress` while every task/AC in this spec reads done/met — confirmed via `sprint_plan.py`'s `cmd_status` branching on that exact field (recommends resuming `bmad-build` instead of surfacing the "story in review" risk line) and via Story 4-3's own precedent (moved to `review`, not `in-progress`, at the same point). **Fixed**: `review` (this spec's own frontmatter uses `in-review`, a different vocabulary — `sprint-status.yaml`'s own status-definitions comment specifies `backlog`/`ready-for-dev`/`in-progress`/`review`/`done`). Five more real findings, all patched directly in the report/`deferred-work.md` (no code, no re-run needed): (1) `mod_micro_nogtom.F90` mislabeled "WSM7-family" in `deferred-work.md` — it is the Tompkins/Nogherotto scheme; WSM7 is a separate file — corrected. (2) That same entry's claimed crash location (`solver`/`ice_fallspeed`/`rain_fallspeed`) contradicted its own evidence (`solver` compiled cleanly); re-checked against source — the next `!$acc routine seq` procedure after `solver` is `nnls`, corrected to name it. (3) The `-Minfo=accel` section claimed `mod_clm_hydrology2.F90` as a confirmed offload routine; re-checked the source — it carries zero `!$acc` directives — removed the claim, and added `interp1d_r8` (confirmed via the build's stderr stream, missed on first pass because NVHPC's `-Minfo=accel` output for that file landed there rather than stdout) in its place. (4) The frozen Boundaries text names `rrtmg_lw`/`rrtmg_sw` alongside `rrtmg_driver` as timers to report; the report only showed the combined `rrtmg_driver` figure — added both as explicit rows in both platforms' tables. (5) Boost's MOLOCH point estimate mixed a `system_clock()`-based lower bound with a `cpu_time()`-based upper bound into one blended percentage not on the same footing as dcgp's cleanly-measured 91.2% — removed the blended estimate; both bounds are now stated separately with the scope difference explained, and a genuinely apples-to-apples cross-platform metric (each physics scheme's share of the combined physics total, unaffected by either run's overflow) is used instead. Also added, as direct improvements rather than defect fixes: an explicit reconciliation of dcgp's own DEBUG-timer sum against the job's real wall-clock and the model's `cpu_time()` figure (mirroring the transparency already given to boost), an itemized breakdown of what had been a lumped "everything else" bucket on both platforms, an explanation for the gap between this story's RRTMG figure and Story 4.1's independent ≈6.0% (different build type and measurement method, not a contradiction), an explicit caveat that DEBUG-build overhead could skew the DEBUG timers themselves not just `perf`'s, an explicit caveat naming the >10x rank-count difference between partitions as an uncontrolled variable in the Intel-vs-NVHPC comparison, and one concrete load-imbalance figure (`rrtmg_driver`'s ~40% max/min spread across dcgp's 224 ranks) substantiating the report's own rank-0-unrepresentativeness argument with data already on hand. One frozen-text finding (the Ask-First boundary's "six distinct crashes across two stories" — all six were in Story 4.2's own Task 4 alone, not two stories) was triaged as reject: a two-word miscount in a parenthetical aside, not affecting intent or any decision the spec drives, disproportionate to an intent_gap loopback that would revert this story's completed work. No `intent_gap` or `bad_spec` findings — nothing required reverting code or looping back to step-02.

## Design Notes

**Chemistry timer coverage is deliberately not attempted this pass.** Story 4.2 exhausted six distinct real attempts to run a chemistry-enabled configuration to completion, each hitting a different unrelated pre-existing bug, and stopped at franco's direction. Re-attempting it here would repeat that dead end rather than measure anything new; the report states `cbmz_integrate`/`cb6_integrate` coverage as unchanged from Story 4.2's code-inspection-only status.

**`-Minfo=accel` evidence comes from a build that is expected to eventually fail, not a working GPU binary.** `nvfortran` emits `-Minfo=accel` per file as it compiles, so a build that reaches `mod_bdycod.F90`'s already-closed ICE still yields real offload confirmation for every routine compiled before it (`getcape_new`, `mod_interp.F90`, `mod_clm_hydrology2.F90`, `mod_heatindex.F90`). This satisfies AD-2's `-Minfo=accel` requirement without a full working GPU binary or reopening Story 4.3's closed investigation.

## Verification

**Commands:**
- Manual review of each job's `time_print` table, `perf report`/FlameGraph SVG, and Nsight Systems report -- expected: nonzero, sane per-timer values for `rrtmg_driver`/`rrtmg_lw`/`rrtmg_sw` and `io_gather_hist`/`io_write_hist`/`io_wait_hist` on both partitions -- **done**: all four artifacts inspected on both partitions, values sane and, where two independent runs exist (boost's nsys and perf legs), mutually consistent within ~0.5%
- `grep -c "Minfo=accel\|Generating" <nvhpc-build.log>` -- expected: nonzero offload-confirmation lines for files compiled before any failure -- **done**: 234 lines (job 53958940)

**Manual checks (if no CLI):**
- Confirm the published report cites job IDs and measured percentages for every claim, not estimates, and explicitly names the thesis figures and job 48812653 as prior evidence being extended -- **done**, `_bmad-output/implementation-artifacts/epic-4-baseline-profiling-report.md`

## Suggested Review Order

**Methodology (read first — everything else depends on this)**

- Entry point: what this report replaces and why it's citable going forward.
  [`epic-4-baseline-profiling-report.md:12`](epic-4-baseline-profiling-report.md#L12)

- The 24-simulated-hour minimum is a hard model constraint, not a choice — discovered via an actual crash.
  [`epic-4-baseline-profiling-report.md:18`](epic-4-baseline-profiling-report.md#L18)

- The nesting fact that governs every percentage below: `moloch`'s DEBUG timer already includes RRTMG/microphysics/PBL/cumulus.
  [`epic-4-baseline-profiling-report.md:25`](epic-4-baseline-profiling-report.md#L25)

- Why `perf`'s rank-0 sampling can't be read as a wall-time-share source on this codebase's decomposition.
  [`epic-4-baseline-profiling-report.md:79`](epic-4-baseline-profiling-report.md#L79)

**dcgp_usr_prod (Intel) evidence**

- The full measured breakdown, including the `rrtmg_lw`/`rrtmg_sw` split and the physics-only cross-platform metric.
  [`epic-4-baseline-profiling-report.md:31`](epic-4-baseline-profiling-report.md#L31)

- Reconciling three different "total run time" numbers that don't match, and why that's expected.
  [`epic-4-baseline-profiling-report.md:50`](epic-4-baseline-profiling-report.md#L50)

**boost_usr_prod (NVHPC) evidence**

- The full measured breakdown; MOLOCH's own total is bounded, not read directly, due to a print-format overflow.
  [`epic-4-baseline-profiling-report.md:58`](epic-4-baseline-profiling-report.md#L58)

- Why the two MOLOCH bounds aren't collapsed into one percentage comparable to dcgp's 91.2%.
  [`epic-4-baseline-profiling-report.md:75`](epic-4-baseline-profiling-report.md#L75)

**Comparison to prior evidence and known gaps**

- The ~1.7x gap against Story 4.1's own RRTMG figure, explained rather than glossed over.
  [`epic-4-baseline-profiling-report.md:91`](epic-4-baseline-profiling-report.md#L91)

- What this report does and does not re-measure from the source thesis's four CLM4.5-coupled hotspots.
  [`epic-4-baseline-profiling-report.md:93`](epic-4-baseline-profiling-report.md#L93)

- A fifth, previously-undocumented NVHPC 26.3 compiler crash, and which `-Minfo=accel` evidence survives it.
  [`epic-4-baseline-profiling-report.md:99`](epic-4-baseline-profiling-report.md#L99)

**Tracking and known-issues ledger (peripheral)**

- The new `deferred-work.md` entry for the `mod_micro_nogtom.F90` compiler crash — corrected during review to name the right scheme and the right crash site (`nnls`, not `solver`).
  [`deferred-work.md:148`](deferred-work.md#L148)

- Sprint status moved to `review`, matching this story's own completed Tasks & Acceptance — corrected during review from a stale `in-progress`.
  [`sprint-status.yaml:80`](sprint-status.yaml#L80)
