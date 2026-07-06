# RegCM5 HPC Test Architect (`hpc-test`)

A custom BMAD Test Architecture module adapting the generic `tea`/`bmad-testarch-*` conventions (built for web/API testing — Playwright, fixtures, network-first patterns) to RegCM5: a Fortran HPC batch model whose "fixtures" are canonical namelists and reference datasets, whose "tests" are full-model integration runs, and whose correctness concerns are numerical-reproducibility tiers, MPI/halo behavior, and physical-scheme preservation — not UI flows.

This module's job, relative to its sibling `bmad-hpc-devops`: `hpc-dev` produces artifacts and executes changes; `hpc-test` designs coverage, audits evidence quality, and adjudicates gate decisions. `hpc-test` never re-implements a `hpc-dev` workflow (e.g. it never builds its own CI pipeline — it consumes `hpc-dev-ci-guardrail-pipeline`'s output).

## Agent

**Matteo** (`hpc-test-agent-test-architect`) — a rigorous evidence auditor who treats "it compiled and ran" as unrelated to "it's correct." Own persona, not a variant of the generic module's "Murat": the judgment domain (numerical/Slurm evidence adjudication) doesn't overlap with Murat's web/API-fixture domain.

## Workflows

| Generic TEA | HPC counterpart |
| --- | --- |
| `framework` | `hpc-test-test-framework` |
| `test-design` | `hpc-test-test-design` |
| `atdd` | *(dropped — folded into a `hpc-test-test-design` step)* |
| `automate` | `hpc-test-regression-automate` |
| `test-review` | `hpc-test-test-review` |
| `ci` | *(dropped — stays owned by `hpc-dev-ci-guardrail-pipeline`)* |
| `trace` | `hpc-test-trace-and-gate` |
| `nfr-assess` | `hpc-test-nfr-assess` |
| *(none)* | `hpc-test-baseline-lifecycle` (new) |
| *(none)* | `hpc-test-mpi-correctness-verification` (new) |
| *(none)* | `hpc-test-scientific-correctness-verification` (new) |
| *(none)* | `hpc-test-coupling-contract-verification` (new) |

## The gate: `hpc-test-trace-and-gate`

**PASS** requires CI green *and* Slurm validation run and green on both required partitions *and* the correct tolerance tier respected *and* `nproc=1`/`nproc=4` both passing where required *and* the baseline properly promoted. **CI-green-but-Slurm-not-yet-run always lands at CONCERNS, never PASS.**

## Getting started

1. Run `hpc-test-setup` once per fresh clone to register this module's config into `_bmad/config.yaml`/`_bmad/module-help.csv`.
2. Start with **Matteo** (`hpc-test-agent-test-architect`) for a new story: `hpc-test-test-design` produces the coverage matrix that `hpc-test-mpi-correctness-verification`, `hpc-test-scientific-correctness-verification`, and `hpc-test-coupling-contract-verification` then apply per-change.
3. See `planning/module-plan.md` for the full build roadmap and design rationale.

## Loop invocability

`hpc-test-test-design`, `hpc-test-test-review`, `hpc-test-nfr-assess`, `hpc-test-regression-automate`, `hpc-test-test-framework`, and `hpc-test-mpi-correctness-verification` are loop-invokable. `hpc-test-trace-and-gate` (a loop must never self-issue a merge-greenlighting PASS), `hpc-test-baseline-lifecycle` (touches shared, hard-to-reverse `$FAST`/`$WORK` state), and `hpc-test-scientific-correctness-verification` (its stage 8 explicitly requires regcm5-dev's sign-off, not an automated verdict) are interactive-only. `hpc-test-coupling-contract-verification` is loop-invokable for its documentation/coverage stages; its BMI/CISM decisions are interactive-only.

## Distribution

Installable independently via `.claude-plugin/marketplace.json` — e.g. `npx bmad-method install --custom-source <path-or-git-url> --tools claude-code --yes`. Fill in `license`/`homepage`/`repository` before distributing externally.
