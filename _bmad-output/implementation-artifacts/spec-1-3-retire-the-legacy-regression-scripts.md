---
title: 'Retire the Legacy Regression Scripts'
type: 'chore'
created: '2026-08-19'
status: 'done'
route: 'one-shot'
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: '9c21f70ba893afb82fa8be984403ccdcf0ba04bb'
---

# Retire the Legacy Regression Scripts

## Intent

**Problem:** `Tools/Scripts/BuildBot/testing.py` (dead Python 2) and `Tools/Scripts/TestingAndBenchmarking/preproc-compare.py` (narrow ICBC v3/v4-only tool) still sit in their original working directories, where a contributor could mistake either for the project's real regression tool now that `regression_diff.py`/`manage_baseline.py` are verified (Stories 1.1-1.2) and supersede them.

**Approach:** `git mv` both files into a new `Tools/Scripts/archive/` directory, preserving history rather than deleting; record each file's prior location and archival reason in the commit message; sync the two stale path references in `project-context.md`; defer the follow-up items surfaced by review (archive index, orphaned `BuildBot/` support files) to `deferred-work.md` rather than expanding this story's scope.

## Suggested Review Order

**Archival move**

- `testing.py` relocated from `Tools/Scripts/BuildBot/` — dead Python 2, non-runnable on any modern interpreter.
  [`testing.py:1`](../../Tools/Scripts/archive/testing.py#L1)

- `preproc-compare.py` relocated from `Tools/Scripts/TestingAndBenchmarking/` — narrow decade-old ICBC v3/v4 comparison, not a general tool.
  [`preproc-compare.py:1`](../../Tools/Scripts/archive/preproc-compare.py#L1)

**Documentation sync**

- Path references updated so the always-loaded project context doesn't point agents at the old locations.
  [`project-context.md:135`](../project-context.md#L135)

- Second stale reference, under Critical Don't-Miss Rules, updated the same way.
  [`project-context.md:215`](../project-context.md#L215)

**Follow-up scope notes (deferred, not implemented here)**

- Archive lacks a README/index explaining the "why" to someone just browsing the tree.
  [`deferred-work.md:34`](./deferred-work.md#L34)

- `BuildBot/` still holds `testing.py`'s orphaned support files and the same-vintage `configure-auto`, none named in this story's scope.
  [`deferred-work.md:37`](./deferred-work.md#L37)

**Peripherals**

- Sprint tracker synced to `in-progress` during implementation (this workflow moves it to `done` on completion).
  [`sprint-status.yaml:58`](./sprint-status.yaml#L58)
