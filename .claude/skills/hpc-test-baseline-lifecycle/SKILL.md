---
name: hpc-test-baseline-lifecycle
description: Audit and promote RegCM5 regression baselines by wrapping manage_baseline.py. Use when the user wants to promote a new baseline, audit baseline freshness, or check PROMOTION_MANIFEST.jsonl integrity.
---

# hpc-test-baseline-lifecycle

Act as `hpc-test-agent-test-architect` (Matteo): audit and promote RegCM5 regression baselines by wrapping `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` directly — no generic-TEA analog exists, since web/API testing has no versioned golden-numerical-baseline archive concept.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-baseline-lifecycle` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present) — in particular `FAST_BASELINE_ROOT`.

## Audit and Promote

For a candidate run, decide whether it should supersede the current baseline — this requires a reviewed, intentional change (never a silent overwrite). Promote via `manage_baseline.py`'s `--force`/`--reason` flags, confirming the superseded generation is archived to `$WORK` (not discarded) unless `--no-archive` is explicitly and deliberately chosen. Confirm `PROMOTION_MANIFEST.jsonl` gained a well-formed entry (timestamp, user, RegCM commit, reason, files touched) after every promotion. Flag, rather than silently proceed past, any invocation missing `--nproc` against a process-count-organized baseline directory — that's a known false-negative trap ("no manifest" reported when the flat top-level directory was checked instead).
