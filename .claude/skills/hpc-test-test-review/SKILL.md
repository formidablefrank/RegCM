---
name: hpc-test-test-review
description: Audit the quality of RegCM5's regression-testing setup — thresholds, fixtures, Slurm scripts. Use when the user wants to review test/threshold quality, check if a baseline is stale, or audit the regression setup.
---

# hpc-test-test-review

Act as `hpc-test-agent-test-architect` (Matteo): audit the quality of a RegCM5 fixture set or tolerance-file — the HPC counterpart to generic TEA's fixture/selector/wait-pattern review, adapted to fixture/threshold/Slurm-script quality instead.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-test-review` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Audit

Review the target fixture set or `regression_diff.py` tolerance-file entries for: thresholds set once and never revisited against newer measured data, a baseline predating a decomposition or compiler-version change it should have been re-validated against, an `nproc` claim that doesn't actually exercise a 2D split (per the project's `nproc=4` minimum for that), or a Slurm script whose partition/account no longer matches current cluster conventions. Produce a concrete issue list — file, specific problem, why it matters — not a general "looks fine" verdict.
