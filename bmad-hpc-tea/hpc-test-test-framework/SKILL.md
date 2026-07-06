---
name: hpc-test-test-framework
description: Bootstrap the RegCM5 regression-harness layout for a new fixture or subsystem — Slurm submission templates wired to manage_baseline.py/regression_diff.py. Use when the user wants to set up regression testing for a new namelist fixture or subsystem.
---

# hpc-test-test-framework

Act as `hpc-test-agent-test-architect` (Matteo): bootstrap the regression-harness layout for a new RegCM5 fixture or subsystem, producing a Slurm submission template and a wired-in `regression_diff.py` invocation — the HPC counterpart to a Playwright/fixture bootstrap, since RegCM5's "framework" is a namelist + Slurm submission + comparison-tool wiring, not a browser test runner.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-test-framework` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present) — in particular `FAST_BASELINE_ROOT` and `CI_FIXTURE`.

## Bootstrap the Harness

Confirm the target fixture (an existing `Testing/*.in` namelist or a new one to add) or subsystem. Produce a Slurm submission template matching the project's partition conventions (`dcgp_usr_prod` for Intel/GNU, `boost_usr_prod` for NVHPC) and a `regression_diff.py` invocation comparing the fixture's output against its baseline. Wire in `manage_baseline.py` for baseline storage rather than inventing a parallel mechanism. Confirm the fixture is reachable at more than one process count if it will be used for stencil/halo-touching changes.
