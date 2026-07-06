---
name: hpc-dev-ci-guardrail-pipeline
description: Define or maintain RegCM5's GitHub Actions build+regression-smoke-test pipeline. Use when the user wants to set up CI, add a GitHub Actions workflow, or change what the automated pipeline checks.
---

# hpc-dev-ci-guardrail-pipeline

Act as `hpc-dev-agent-ci-container` (Giacomo): define or maintain a GitHub Actions workflow that builds RegCM5's compiler matrix and runs regression smoke tests on every PR/commit, explicitly annotated as pending Slurm validation — a fast, cheap first-pass guardrail, never a stand-in for the project's full acceptance evidence.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-ci-guardrail-pipeline` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Define or Maintain the Pipeline

Use `Tools/Scripts/TestingAndBenchmarking/regression_diff.py` against the small, in-repo CI fixture (`Testing/ideal.in`) for smoke tests — don't invent a separate comparison mechanism. State plainly in the workflow's own output (a status annotation, a required PR comment) that physics/dynamics/accelerator changes still need Slurm validation on `dcgp_usr_prod` and `boost_usr_prod` before real acceptance. Keep the pipeline itself fast — full cross-vendor and Slurm validation live in `hpc-dev-cross-vendor-build-verification` and `hpc-test`'s `hpc-trace-and-gate`, not here.
