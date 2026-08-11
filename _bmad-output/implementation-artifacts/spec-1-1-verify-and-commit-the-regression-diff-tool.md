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
- `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:50-59,281` -- exit code scheme: 0 pass, 1 regression (`cmd_compare`'s final `sys.exit`), 2 usage error (`EXIT_USAGE_ERROR`, `die_usage()`)
- `Testing/test_001.in` -- existing fixture (confirmed present, 1888 bytes) to run twice for the bit-exact verification
- `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` -- already tracked alongside `regression_diff.py` in the same commit; no changes needed here, confirms the "committed" half of this story's AC is already satisfied
- Verification artifacts (reproducibility): namelists `RegCM-data/test_001_verify/test_001_verify_run{1,2}.in`; preprocessed input `RegCM-data/test_001_verify/input/test_001_{DOMAIN000.nc,LANDUSE,TEXTURE}` and `RegCM-data/EURR12/RCMDATA/test_001_ICBC.2018102600.nc`; outputs `RegCM-data/test_001_verify/output_run{1,2}` (bit-exact scenario) and `output_run2_tol_test` (`output_run2` with ATM `ps` perturbed +0.05%, tolerance scenario); tolerance files `RegCM-data/test_001_verify/tolerance_{narrowed,malformed}.json`; full-field tolerance report `RegCM-data/test_001_verify/report_tol_narrowed_fullfields.json`; gitignored job scripts `bin/slurm-1-1-test001verify-{preproc,run,diff,diff-fullfields}.sh` (job IDs 51872925/51873081/51873953/51876659)

## Tasks & Acceptance

**Execution:**
- [x] `Tools/Scripts/TestingAndBenchmarking/regression_diff.py:33` -- correct the stale docstring to the real flat-flag invocation (no `compare` token) -- prevents a future contributor from copy-pasting a command that fails
- [x] Slurm job: run `Testing/test_001.in` twice (identical config, same compiler/build), then `regression_diff.py --run-dir RUN1 --baseline-dir RUN2` -- confirms bit-exact reporting and exit 0 against real output, not just code inspection
- [x] Construct a `--tolerance-file` JSON narrowing one field's tolerance, rerun the comparison -- confirms the override-honored-per-field / rest-default-to-bit-exact behavior actually works at runtime
- [x] Pass a deliberately malformed `--tolerance-file` -- confirms the `die_usage()`/exit-2 path fires as documented
- [x] Record Build/Test/Numerical/Performance evidence in the commit/PR description per project convention

**Acceptance Criteria:**
- Given `regression_diff.py` run against two identical runs of `test_001.in`, when invoked via `--run-dir`/`--baseline-dir`, then it reports bit-exact agreement across all shared NetCDF fields and exits 0
- Given a `--tolerance-file` narrowing a subset of fields, when passed to the tool, then the override is honored per-field and every field not named in it defaults to bit-exact
- Given the stale `compare`-subcommand docstring line, when this story completes, then it matches the tool's real flat-flag invocation
- Given both scripts are already committed (`238393c72`), when this story completes, then no further commit action is needed — this half of the original AC is already satisfied going in

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
  [`spec-1-1-verify-and-commit-the-regression-diff-tool.md:77`](spec-1-1-verify-and-commit-the-regression-diff-tool.md#L77)

- The pre-existing crash that blocked full-stream verification, now recurring for a second story.
  [`deferred-work.md:5`](deferred-work.md#L5)

- A real tool-hardening gap this story's own evidence surfaced: vacuous bit-exact on zero-record streams.
  [`deferred-work.md:6`](deferred-work.md#L6)

- Sprint tracker lift: `epic-1` and this story move from `backlog` to `in-progress`.
  [`sprint-status.yaml:55`](sprint-status.yaml#L55)

- Epic context corrected to match reality: both tools were already committed before this epic began.
  [`epic-1-context.md:7`](epic-1-context.md#L7)
