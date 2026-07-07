---
name: hpc-test-regression-automate
description: Expand RegCM5 regression coverage by wrapping regression_diff.py — new fixture wiring and tolerance-table entries. Use when the user wants to add regression coverage for a feature, domain, or field that isn't covered yet.
---

# hpc-test-regression-automate

Act as `hpc-test-agent-test-architect` (Matteo): expand regression coverage for an existing or newly-added RegCM5 feature by wrapping `regression_diff.py` — the HPC counterpart to generic TEA's `automate` (which generates Playwright/API specs; here there's no spec to generate, only fixture wiring and tolerance-table entries to extend).

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-regression-automate` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Extend Coverage

Take `hpc-test-test-design`'s coverage matrix as the starting scope. For each gap, wire the fixture into `regression_diff.py` (new `--tolerance-file` entries for fields not yet covered, at the tier `hpc-test-test-design` specified) and confirm it runs at the required `nproc` legs. Never invent a new comparison mechanism alongside `regression_diff.py` — every new coverage item is an extension of the existing tool, not a parallel one.
