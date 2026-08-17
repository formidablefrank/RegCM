---
title: 'Verify and Commit the Regression-Diff Tool'
type: 'chore'
created: '2026-08-11'
status: 'done'
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: 'd64e912e93d34c6565df4145ce2265bc13c74dbc'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `regression_diff.py`/`manage_baseline.py` already exist and are already committed under `Tools/Scripts/TestingAndBenchmarking/` (commit `238393c72`) — Epic 1's premise that they sit "currently untracked" is stale and no longer holds. What is still genuinely open: the tools have never been run against a real fixture to confirm bit-exact same-run comparison and correct `--tolerance-file` override behavior, and `regression_diff.py`'s top-of-file docstring still documents a nonexistent `compare` subcommand.

**Approach:** Run `regression_diff.py` against two identical Slurm runs of `Testing/test_001.in` to verify bit-exact reporting and exit code 0; verify `--tolerance-file` per-field override behavior with a deliberately narrowed tolerance file; correct the stale docstring line to match the tool's real flat-flag invocation; record Build/Test/Numerical/Performance evidence in the commit description per project convention.

## Boundaries & Constraints

**Always:** Run fixture comparisons via Slurm, never the login node. Use the existing tolerance mechanism as-is (`DEFAULT_GPU_TOLERANCES`, full-replace — not merge — semantics on `--tolerance-file`); don't redesign it. Record Build/Test/Numerical/Performance evidence in the commit/PR description.

**Ask First:** If a real bit-exact run surfaces an actual tool defect (output doesn't match documented behavior), confirm before changing tool logic beyond this story's verify-and-document scope.

**Never:** Don't touch `manage_baseline.py`'s `promote`/`log` logic or its overwrite-refusal behavior — that verification is Story 1.4's scope. Don't archive `testing.py`/`preproc-compare.py` — Story 1.3's scope. Don't change `DEFAULT_GPU_TOLERANCES`' default values — this story verifies existing policy, it doesn't revise it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Same-run bit-exact | Two identical Slurm runs of `test_001.in` as `--run-dir`/`--baseline-dir` | Reports bit-exact agreement across all shared NetCDF fields, exits 0 | N/A |
| Tolerance override | `--tolerance-file` narrows a subset of fields (e.g. tightens `tas`) | Override honored per-field; every field not named in the override defaults to bit-exact | N/A |
| Malformed tolerance file | `--tolerance-file` points to unreadable/invalid JSON | `die_usage()` fires | Exits 2 (`EXIT_USAGE_ERROR`) |

</frozen-after-approval>

## Code Map

- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:33` -- stale docstring line reads `# Run via: uv run regression_diff.py compare --run-dir X --baseline-dir Y`; no `compare` subcommand exists — fix to the real flat-flag form
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:284-303` -- `main()`: flat `argparse` parser, no `add_subparsers()`; `--run-dir`/`--baseline-dir` required top-level flags, `--nprocs`/`--tolerance-file`/`--only-fields`/`--json`/`--report-file` optional; calls `cmd_compare(args)` directly
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:44-48` -- `DEFAULT_GPU_TOLERANCES`: `tas`/`ps` rMAD/rRMSE ≤0.1%, `huss` ≤5.0%
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:62-69` -- `load_tolerances()`: `--tolerance-file` fully replaces the default table (not a merge) via `json.load`
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:101-120` -- `judge()`: implements the tolerance-override AC directly -- looks up each field's tolerance (or bit-exact default) from the loaded table and decides pass/fail per field; this is the function the tolerance-override task actually verifies
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:50-59,281` -- exit code scheme: 0 pass, 1 regression (`cmd_compare`'s final `sys.exit`), 2 usage error (`EXIT_USAGE_ERROR`, `die_usage()`)
- `Testing/test_001.in` -- existing fixture (confirmed present, 1888 bytes) to run twice for the bit-exact verification
- `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` -- already tracked alongside `regression_diff.py` in the same commit; no changes needed here, confirms the "committed" half of this story's AC is already satisfied
- Verification artifacts (reproducibility): namelists `RegCM-data/test_001_verify/test_001_verify_run{1,2}.in`; preprocessed input `RegCM-data/test_001_verify/input/test_001_{DOMAIN000.nc,LANDUSE,TEXTURE}` and `RegCM-data/EURR12/RCMDATA/test_001_ICBC.2018102600.nc`; outputs `RegCM-data/test_001_verify/output_run{1,2}` (bit-exact scenario) and `output_run2_tol_test` (`output_run2` with ATM `ps` perturbed +0.05%, tolerance scenario); tolerance files `RegCM-data/test_001_verify/tolerance_{narrowed,malformed}.json`; full-field tolerance report `RegCM-data/test_001_verify/report_tol_narrowed_fullfields.json`; gitignored job scripts `bin/slurm-1-1-test001verify-{preproc,run,diff,diff-fullfields}.sh` (job IDs 51872925/51873081/51873953/51876659)

## Tasks & Acceptance

**Execution:**
- [x] `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:33` -- correct the stale docstring to the real flat-flag invocation (no `compare` token) -- prevents a future contributor from copy-pasting a command that fails
- [x] Slurm job: run `Testing/test_001.in` twice (identical config, same compiler/build), then `regression_diff.py --run-dir RUN1 --baseline-dir RUN2` -- confirms bit-exact reporting and exit 0 against real output, not just code inspection -- **see Verification/Caveat: 3 of 4 streams passed vacuously (zero records), only ATM is a genuine comparison**
- [x] Construct a `--tolerance-file` JSON narrowing one field's tolerance, rerun the comparison -- confirms the override-honored-per-field / rest-default-to-bit-exact behavior actually works at runtime -- **see Verification/Caveat: same vacuous-stream caveat applies to most of the "148 of 149 fields" figure**
- [x] Pass a deliberately malformed `--tolerance-file` -- confirms the `die_usage()`/exit-2 path fires as documented
- [x] Record Build/Test/Numerical/Performance evidence in the commit/PR description per project convention

**Acceptance Criteria:**
- Given `regression_diff.py` run against two identical runs of `test_001.in`, when invoked via `--run-dir`/`--baseline-dir`, then it reports bit-exact agreement across all shared NetCDF fields and exits 0 (see Verification/Caveat: genuinely demonstrated for the ATM stream; RAD/SRF/STS passed vacuously, zero records)
- Given a `--tolerance-file` narrowing a subset of fields, when passed to the tool, then the override is honored per-field and every field not named in it defaults to bit-exact (see Verification/Caveat: same vacuous-stream qualifier applies)
- Given the stale `compare`-subcommand docstring line, when this story completes, then it matches the tool's real flat-flag invocation
- Given both scripts are already committed (`238393c72`), when this story completes, then no further commit action is needed — this half of the original AC is already satisfied going in

### Review Findings

**`/bmad-code-review` pass (2026-08-11), reviewing the full branch diff (`61c8aa4ee`, `b475cb42a`, `8af0e7d8f`):**

- [x] [Review][Patch] `epic-1-context.md`'s Cross-Story Dependencies section misattributes "GPU statistical-reproducibility testing and coupling regression coverage" to "Epic 4 and beyond" — per `epics.md`, GPU statistical-reproducibility is Story 10.7 (Epic 10) and coupling regression coverage is Epic 13, not Epic 4 (which is instrumentation/profiling only, no GPU or coupling content). [_bmad-output/implementation-artifacts/epic-1-context.md:42] — **Fixed:** now cites Epic 10 and Epic 13 by name.
- [x] [Review][Patch] Spec's Code Map never lists `judge()` (`regression_diff.py:101-120`), the function that actually implements the tolerance-honored-per-field acceptance criterion the Tasks section verifies. [_bmad-output/implementation-artifacts/spec-1-1-verify-and-commit-the-regression-diff-tool.md:43] — **Fixed:** added a Code Map line for `judge()`.
- [x] [Review][Patch] `deferred-work.md`'s new heading ("Deferred from: verification of 1-1-...") breaks the file's established "Deferred from: code review of `<story>`" convention used by every other section, hurting grep-ability. [_bmad-output/implementation-artifacts/deferred-work.md:3] — **Fixed:** renamed to "Deferred from: code review of 1-1-verify-and-commit-the-regression-diff-tool", and this review's own new defer items were folded into the same section rather than creating a second, confusingly-similar heading.
- [x] [Review][Patch] Suggested Review Order's "vacuous bit-exact on zero-record streams" stop points only at `deferred-work.md:6`, skipping the adjacent, also-new item 3 (the docstring-isn't-a-real-docstring finding) at `deferred-work.md:7` — a reviewer following the order top-to-bottom is never directed to it. [_bmad-output/implementation-artifacts/spec-1-1-verify-and-commit-the-regression-diff-tool.md:97] — **Fixed:** stop now covers both lines.
- [x] [Review][Patch] Deferred item 1 (`mod_lm_interface.F90:930`) recommends prioritizing a fix but names no owner or tracking hook, and doesn't connect the risk forward to Story 1.2 — the next story queued to run real Slurm/DEBUG-build verification and the one most likely to hit this exact crash next. [_bmad-output/implementation-artifacts/deferred-work.md:5] — **Fixed:** added an explicit Story 1.2 forward-pointer to that entry.
- [x] [Review][Patch] The Tasks/Acceptance checklist and AC bullets for the bit-exact and tolerance-override scenarios are checked off with no inline pointer to the Verification section's Caveat — a reader skimming only the checklist would not know 3 of 4 streams passed vacuously (zero records, nothing actually compared) rather than via a genuine comparison. [_bmad-output/implementation-artifacts/spec-1-1-verify-and-commit-the-regression-diff-tool.md:58] — **Fixed:** added inline pointers to all 4 checklist/AC lines.
- [x] [Review][Defer] `epics.md`'s own Story 1.1 acceptance-criteria text still reads "Given both scripts are currently untracked... Then... committed" — the exact premise this story found stale, corrected only in the derived spec and `epic-1-context.md`, not at the planning-artifact source; a future `epic-1-context.md` regeneration risks silently reintroducing it. [_bmad-output/planning-artifacts/epics.md] — deferred, pre-existing (planning-artifact correction is outside an implementation story's normal scope)
- [x] [Review][Defer] `regression_diff.py`'s other documented error paths — `shape-mismatch`, `missing-in-candidate`, `missing-in-baseline` (`regression_diff.py:159-162,79-80`), and the "file fails to open" `unreadable` path (`regression_diff.py:50-53`) — were never runtime-exercised by this story's verification, only the three scenarios in the approved I/O Matrix. [Tools/Scripts/TestingAndBenchmarking/regression_diff.py] — deferred, pre-existing tool surface, good candidate for Story 1.2's own verification pass
- [x] [Review][Defer] The GPU tolerance policy's "7-model-day run" validity precondition (`epic-1-context.md:19`) is asserted as policy but never checked, recorded, or referenced anywhere `regression_diff.py` actually runs — the tool judges purely field-by-field with no run-duration awareness. [_bmad-output/implementation-artifacts/epic-1-context.md:19] — deferred, pre-existing policy/tooling gap
- [x] [Review][Defer] A non-DEBUG (production) build was never tried as a way to sidestep the DEBUG-only `mod_lm_interface.F90:930` crash and obtain genuine (non-vacuous) evidence across all 4 output streams instead of just ATM. [_bmad-output/implementation-artifacts/spec-1-1-verify-and-commit-the-regression-diff-tool.md:77] — deferred, cheap follow-up worth trying before/alongside a real fix to the crash itself

## Spec Change Log

## Design Notes

`epics.md`'s Story 1.1 text assumes both scripts are "currently untracked." That is stale: `git ls-files` and `git status` confirm `regression_diff.py`/`manage_baseline.py` were already added in commit `238393c72`. This spec narrows the story to what is actually still open — runtime verification and the docstring fix — rather than a from-scratch commit. Flag this correction in the commit/PR description so the record doesn't imply a commit action that didn't happen.

## Verification

**Commands:**
- `python3 -c "import ast; ast.parse(open('Tools/Scripts/TestingAndBenchmarking/regression_diff.py').read())"` -- expected: no syntax error after the docstring edit
- Slurm-submitted `regression_diff.py --run-dir RUN1 --baseline-dir RUN2` (twin `test_001.in` runs) -- expected: exit 0, all shared fields reported bit-exact
- Slurm-submitted rerun with a narrowed `--tolerance-file` -- expected: override applied per-field, exit 0 (or 1 only if a genuine, expected divergence was intentionally introduced for the test)
- `regression_diff.py --tolerance-file <malformed-path>` -- expected: exit 2

**Outcome (2026-08-11):** All three scenarios exercised against real Slurm output (`test_001.in`'s placeholder ERA5 paths substituted with a working copy using real, already-local terrain/IFSXX data, per `1-2-instrument-kpp-chemistry-integration.md`'s precedent — see Caveat below for why, and for provenance of the substitute paths). Bit-exact same-run: PASS, exit 0. Of the 4 output streams (ATM/RAD/SRF/STS), only ATM carried real, non-empty t=0 data; RAD/SRF/STS compared as bit-exact vacuously (zero time records on both sides — see Caveat). Tolerance override: a synthetic +0.05% perturbation of the real ATM `ps` field passed at the default 0.1% tolerance and failed (exit 1) against a `--tolerance-file` narrowing `ps` to 0.01% — confirmed genuinely at runtime with a full-field (no `--only-fields`) invocation: 148 of 149 shared fields across all 4 streams reported `"status": "exact"`, the sole exception being `ps` (`rmad_pct`/`rrmse_pct` 0.04997%, `passed: false`), confirming both halves of the AC in one run — the override is honored for the named field, and every unlisted field defaults to bit-exact (and passed, since untouched). Malformed tolerance file: exit 2 via `die_usage()`, as documented. Commit: `61c8aa4ee`.

**Caveat:** both twin runs crashed immediately after their t=0 initialization dump on a pre-existing DEBUG-build Intel runtime check (`Main/mod_lm_interface.F90:930`, `collect_output`, CONTIGUOUS-pointer violation) — the same crash site already logged as deferred-work item 5 from `1-2-instrument-kpp-chemistry-integration.md` (a second, independent DEBUG build hitting the identical guard). RAD/SRF/STS streams never reached their first flush and carry zero time records in this run; the bit-exact evidence for those 3 streams is a vacuous pass (nothing to compare), not confirmation of matching data — only the ATM stream's real t=0 record constitutes a genuine bit-exact comparison. Not fixed here (out of this story's scope); see `deferred-work.md`'s two new entries under this story's heading (the crash itself, and the separate finding that `regression_diff.py`'s comparison doesn't distinguish a vacuous zero-record pass from a real one).

## Suggested Review Order

**Tool fix**

- The whole code change: one corrected usage line, no logic touched.
  [`regression_diff.py:33`](../../Tools/Scripts/TestingAndBenchmarking/regression_diff.py#L33)

**Verification evidence & tracking**

- Runtime verification outcome, the crash caveat, and reproducibility paths — the actual substance of this story.
  [`spec-1-1-verify-and-commit-the-regression-diff-tool.md:93`](spec-1-1-verify-and-commit-the-regression-diff-tool.md#L93)

- The pre-existing crash that blocked full-stream verification, now recurring for a second story (see the added Story 1.2 forward-pointer).
  [`deferred-work.md:5`](deferred-work.md#L5)

- Two real tool-hardening gaps this story's own evidence surfaced: vacuous bit-exact on zero-record streams, and the usage comment that still isn't a real docstring.
  [`deferred-work.md:6-7`](deferred-work.md#L6-L7)

- Sprint tracker lift: `epic-1` moves to `in-progress`, this story moves to `review`.
  [`sprint-status.yaml:55`](sprint-status.yaml#L55)

- Epic context corrected to match reality: both tools were already committed before this epic began.
  [`epic-1-context.md:7`](epic-1-context.md#L7)
