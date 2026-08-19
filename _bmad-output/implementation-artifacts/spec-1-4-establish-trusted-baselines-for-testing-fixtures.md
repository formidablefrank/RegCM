---
title: 'Establish Trusted Baselines for Testing/ Fixtures'
type: 'chore'
created: '2026-08-19'
status: 'done'
review_loop_iteration: 1
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: '5f4ea46b3952e1414384dfb1951db59ac136aa7f'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `manage_baseline.py promote` (verified in Story 1.1) works, but `$FAST`'s trusted-baseline directory is still empty, so FR-27 isn't satisfied by an actual populated baseline yet — only tooling capable of one.

**Approach:** Promote Story 1.2's already-completed EUR12 (idynamic=3 MOLOCH, 2-node/nproc=196, `dcgp_usr_prod`) twin run into the `$FAST` baseline; add the missing `Testing/EUR12_namelist.in` version-controlled reference copy (AD-8); prove the promotion tool's overwrite refusal with a real second attempt (AD-9); and record the still-nonexistent coupling-build fixture (FR-13/FR-14) as deferred rather than fabricating one.

## Boundaries & Constraints

**Always:** Reuse Story 1.2's completed `story1-2/RUN/nproc-196` EUR12 run as the promotion candidate — `git diff 647a9a3e7..HEAD -- Main Share PreProc` is empty (only file relocations/doc updates landed since), so it remains bit-exact-equivalent evidence for current HEAD. `Testing/EUR12_namelist.in` copies the `$FAST` canonical file's domain/physics parameters but replaces every path with the `/set/this/to/where/...` placeholder convention already used by `Testing/test_001.in`. Pass `--archive-dir $WORK/franco/RegCM-archive/baseline` on the promote call per AD-10.

**Ask First:** If franco wants a fresh Slurm run instead of reusing Story 1.2's output, confirm before submitting one. Before writing the coupling-fixture gap to `deferred-work.md`, confirm no OASIS3-MCT/REGESM-enabled namelist already exists somewhere unindexed.

**Never:** Fabricate an OASIS3-MCT/REGESM coupled namelist — Epic 13 (not yet started) owns creating that fixture. Pass `--force` on the initial promotion. Modify `regression_diff.py` or `manage_baseline.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initial promote | Empty `$FAST` baseline dir; `--run-dir` = Story 1.2's EUR12 nproc-196 output | Files copied; `PROMOTION_MANIFEST.jsonl` gets one `"initial"` entry with the current RegCM git commit | N/A |
| Second promote, no `--force` | Baseline now populated from above | Tool refuses (exit 2); no files or manifest changed | Confirms AD-9's refusal is real, not just documented |

</frozen-after-approval>

## Code Map

- `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` -- existing, verified tool (`promote`/`log`); used unmodified.
- `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/story1-2/RUN/nproc-196/` -- Story 1.2's completed EUR12 twin run (5 NetCDF files + `.txt`); confirmed bit-exact vs its `BASELINE/nproc-196` twin in `report_nprocs_1-4-16-64-196.json`; promotion source.
- `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/baseline/` (`$FAST/franco/RegCM-data/baseline`) -- currently empty; promotion target (AD-9).
- `/leonardo_work/ICT26_MHPC_0/franco/RegCM-archive/baseline/` (`$WORK/franco/RegCM-archive/baseline`) -- AD-10 archive target; exists, empty; unused this run (no conflicts).
- `Testing/test_001.in:27-70` -- placeholder-path convention (`dirter`/`inpter`/`dirglob`/`inpglob`/`dirout`) to replicate in the new file.
- `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/EUR12_namelist.in` -- source of domain/physics parameters for the new reference copy (AD-8).
- `_bmad-output/implementation-artifacts/deferred-work.md` -- append the coupling-fixture gap here.

## Tasks & Acceptance

**Execution:**
- [x] Run `manage_baseline.py promote --run-dir .../story1-2/RUN --baseline-dir $FAST/franco/RegCM-data/baseline --nproc 196 --archive-dir $WORK/franco/RegCM-archive/baseline` -- populates the first trusted baseline (note: `--run-dir` ends in `RUN`, not `RUN/nproc-196` — `manage_baseline.py` appends the `nproc-<N>` subdirectory itself when `--nproc` is given; passing both double-appends and fails with "run directory not found")
- [x] `Testing/EUR12_namelist.in` -- add: domain/physics params from the `$FAST` canonical copy, paths replaced with the placeholder convention, plus a short header comment identifying the fixture and distinguishing it from `Testing/CORDEX/EUR-12_RegCM5_ERA5.namelist` (different grid)
- [x] Re-run the identical `promote` command without `--force` -- capture the refusal (exit 2) as evidence
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- append an entry naming the missing OASIS3-MCT/REGESM coupled-build fixture (FR-13/FR-14), owned by Epic 13 -- state accurately that REGESM's code path (`Main/mod_update.F90`, gated by `icopcpl`) already exists but is unexercised by any fixture; the gap is the missing fixture/field-list/regression run, not an absent code path

**Acceptance Criteria:**
- Given `Testing/EUR12_namelist.in` is absent, when this story completes, then it exists in the repo with the same domain/physics parameters as the `$FAST` canonical copy and placeholder (not personal) paths.
- Given FR-27 also names coupling builds (FR-13/FR-14) as a baseline target, when no coupled namelist exists anywhere in the project, then the gap is recorded in `deferred-work.md` accurately (not overstating REGESM's code path as absent), not silently dropped or fabricated.
- Given AD-9's overwrite-refusal is the safety property protecting the newly-populated baseline, when a second `promote` call runs without `--force`, then it exits 2 and leaves `PROMOTION_MANIFEST.jsonl` and the baseline files unchanged, and this is captured by a repeatable command in `## Verification`, not only a one-time manual run.

## Spec Change Log

- 2026-08-19, review loop 1: `verification-gap` reviewer found AD-9's overwrite-refusal (frozen I/O matrix row) had no Acceptance Criterion or Verification command backing it — added both. `blind-hunter` reviewer found: (1) the documented `promote` command's `--run-dir` redundantly included `nproc-196` alongside `--nproc 196`, which `manage_baseline.py` would reject (`run directory not found`) — the command actually executed omitted the suffix and was correct, so this was a documentation-only bug, now fixed in Code Map/Tasks; (2) the implementation's `deferred-work.md` entry overstated the REGESM gap, claiming no trace of REGESM exists in `Main/`/`Share/`/`PreProc/`, when `Main/mod_update.F90`/`icopcpl` is REGESM's code path per the PRD itself (FR-14) — corrected to state the code path exists but is unexercised by any fixture; (3) `Testing/EUR12_namelist.in` had no header comment and could be confused with the similarly-named `Testing/CORDEX/EUR-12_RegCM5_ERA5.namelist` (different grid) — added a header comment. Also independently found and fixed: the Tasks list had the implementer flip `sprint-status.yaml`'s `1-4-...` entry straight to `done`, but step-05 of this workflow owns that transition (to `review`, not `done`) after review passes — removed that task and Code Map line; `sprint-status.yaml` was reverted to `in-progress`.
  KEEP: the actual `manage_baseline.py promote` invocation used (`--run-dir .../story1-2/RUN`, `--nproc 196`, `--archive-dir $WORK/franco/RegCM-archive/baseline`, no `--force`) is correct and already executed — do not re-run or alter the promoted `$FAST` baseline. `Testing/EUR12_namelist.in`'s domain/physics parameter values (everything except the new header comment) are correct and verified against the `$FAST` canonical copy — keep as is. The reuse-over-rerun rationale (`git diff 647a9a3e7..HEAD -- Main Share PreProc` empty) remains valid and unchanged.
  A pre-existing property of the AD-8 canonical fixture (surfaced incidentally, not caused by this story) was deferred rather than fixed here: `ichem`/`lakemod`/`nsg` are never set, so `ifchem`/`iflak`/`ifsub` are silently forced `.false.` at runtime despite reading `.true.` in the namelist — see `deferred-work.md`.

- 2026-08-19, review loop 1 (patch pass, no further loopback — all findings were patch/defer): `blind-hunter` found several documentation-consistency gaps, applied directly: `project-context.md`'s Testing Rules list didn't mention the new `Testing/EUR12_namelist.in`, now added; `deferred-work.md`'s new section heading read "implementation of 1-4-..." instead of the file's established "code review of 1-4-..." convention, renamed; the header comment was one dense run-on sentence and didn't note CLM4.5/ECLM is a compile-time macro choice the namelist can't guarantee, reworded into shorter sentences with that caveat; no repeatable command verified `Testing/EUR12_namelist.in` against the `$FAST` canonical copy it mirrors, added to Verification. `edge-case-hunter` found the `ichem`/`lakemod`/`nsg` deferred-work entry mischaracterized the root cause: `ifcordex = .true.` (also set in this fixture) unconditionally forces `ifshf`/`iflak`/`ifsub`/`ifopt`/`ifchem` to `.false.` at `Main/mod_params.F90:1182-1192`, before the `ichem`/`lakemod`/`nsg` mechanism even applies, and `ifshf` was missing from the original list — corrected the deferred-work.md entry to lead with `ifcordex` as the primary, unconditional cause and include `ifshf`. Both reviewers independently noted the promoted baseline's `do_parallel_netcdf_out = .false.` means it exercises FR-6's serial-write path, not FR-5's parallel-write path, despite epics.md's AC1 naming FR-5/FR-6 jointly — recorded as a new deferred-work.md entry (pre-existing property of the canonical fixture, out of scope to change here). Rejected as noise or out of scope: reformatting the file's inherited-from-canonical indentation/trailing-comma style or adding namelist groups absent from the canonical source (both would reduce fidelity to the fixture actually promoted); adding a `--force` overwrite scenario (would violate this spec's own frozen "Never: pass `--force` on the initial promotion").

## Design Notes

Reuse over re-run: `git diff 647a9a3e7..HEAD` (Story 1.2's `baseline_commit`) touches only `Tools/Scripts/{TestingAndBenchmarking,BuildBot}` file relocations and docs — no `Main/`, `Share/`, or `PreProc/` change — so Story 1.2's already-completed, already-verified-bit-exact EUR12 nproc=196 output is valid evidence for a baseline promoted at current HEAD; no new Slurm submission is needed.

Coupling gap: AD-8 pins EUR12 as the sole canonical baseline (Intel/GNU partition, no coupling). No OASIS3-MCT/REGESM namelist exists in `Testing/` or `RegCM-data`, and Epic 13 (which owns FR-13/FR-14) hasn't started. Recording this as deferred work — not inventing a coupled fixture — matches AC2's own precedent of explicit flagging over silent assumption.

## Verification

**Commands:**
- `python3 Tools/Scripts/TestingAndBenchmarking/manage_baseline.py log --baseline-dir $FAST/franco/RegCM-data/baseline --nproc 196` -- expected: one `initial` entry after promotion
- `git diff 647a9a3e7..HEAD -- Main Share PreProc` -- expected: empty (re-confirms reuse validity at implementation time)
- `python3 Tools/Scripts/TestingAndBenchmarking/manage_baseline.py promote --run-dir .../story1-2/RUN --baseline-dir $FAST/franco/RegCM-data/baseline --nproc 196 --archive-dir $WORK/franco/RegCM-archive/baseline` (no `--force`) -- expected: exit 2, refusal listing the 6 conflicting files, `PROMOTION_MANIFEST.jsonl` still one line (AD-9)
- `diff <(sed -n '/^&dimparam/,$p' Testing/EUR12_namelist.in) $FAST/franco/RegCM-data/EURR12/EUR12_namelist.in` -- expected: differs only in the 6 placeholder-path lines (`dirter`/`inpter`/`dirglob`/`inpglob`/`dirout`/`radclimpath`); every other line identical

## Suggested Review Order

**Reference fixture (AD-8)**

- The version-controlled reference copy this story adds — header identifies the fixture and its provenance, body is a byte-for-byte match to the `$FAST` canonical namelist except for placeholder paths.
  [`EUR12_namelist.in:1`](../../Testing/EUR12_namelist.in#L1)

- Where the actual domain/physics parameters begin — compare against the `$FAST` canonical copy via the Verification section's `diff` command.
  [`EUR12_namelist.in:12`](../../Testing/EUR12_namelist.in#L12)

**Gaps recorded, not silently dropped**

- Corrected entry: REGESM's code path exists (`Main/mod_update.F90`/`icopcpl`) but is unexercised by any fixture — the real FR-13/FR-14 gap.
  [`deferred-work.md:54`](./deferred-work.md#L54)

- `ifcordex=.true.` unconditionally disables `ifshf`/`iflak`/`ifsub`/`ifopt`/`ifchem` in the canonical fixture, inherited here as-is.
  [`deferred-work.md:57`](./deferred-work.md#L57)

- The promoted baseline exercises FR-6's serial-write path, not FR-5's parallel-write path (`do_parallel_netcdf_out = .false.`).
  [`deferred-work.md:60`](./deferred-work.md#L60)

**Peripherals**

- Sprint tracker synced to `in-progress` (this workflow moves it to `review` on completion, not `done` — see Spec Change Log).
  [`sprint-status.yaml:59`](./sprint-status.yaml#L59)

- Always-loaded project context updated so agents know `EUR12_namelist.in` exists and what it is.
  [`project-context.md:132`](../project-context.md#L132)
