---
name: maintain-ci-pipeline
description: Define/maintain the GitHub Actions matrix and regression smoke tests
code: MP
added: 2026-07-05
type: prompt
---

# Maintain the CI Pipeline

The outcome is a GitHub Actions workflow that builds the compiler matrix and runs regression smoke tests on every PR/commit, explicitly annotated as pending Slurm validation — never presented as full acceptance evidence on its own. The consumer is a reviewer who must not mistake a green check for "fully validated."

Use `Tools/Scripts/TestingAndBenchmarking/regression_diff.py` against the small, in-repo CI fixture for smoke tests — don't invent a separate comparison mechanism. State plainly in the workflow's own output (a status annotation, a required PR comment) that physics/dynamics/accelerator changes still need Slurm validation on `dcgp_usr_prod` and `boost_usr_prod` before real acceptance, per the project's CI guardrail policy.
