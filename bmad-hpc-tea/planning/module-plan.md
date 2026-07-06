---
title: 'HPC Test Architect Module Plan'
status: 'complete'
module_name: 'RegCM5 HPC Test Architect'
module_code: 'hpc-test'
module_description: 'A custom Test Architect module adapting BMAD TEA conventions for RegCM5: numerical-reproducibility tiers, MPI/scientific/coupling correctness review, and evidence-gated PASS/CONCERNS/FAIL decisions for a Fortran HPC climate model instead of a web app.'
architecture: 'single agent (Matteo), 10 workflows, no orchestrator'
standalone: true
expands_module: ''
skills_planned:
  - hpc-test-agent-test-architect
  - hpc-test-test-framework
  - hpc-test-test-design
  - hpc-test-regression-automate
  - hpc-test-test-review
  - hpc-test-nfr-assess
  - hpc-test-trace-and-gate
  - hpc-test-baseline-lifecycle
  - hpc-test-mpi-correctness-verification
  - hpc-test-scientific-correctness-verification
  - hpc-test-coupling-contract-verification
config_variables:
  - FAST_BASELINE_ROOT
  - CI_FIXTURE
created: '2026-07-05'
updated: '2026-07-05'
---

# Module Plan

## Vision

The generic `tea` module already installed in this repo (`bmad-tea` + `bmad-testarch-*`) is built for web/API testing: Playwright fixtures, network-first patterns, browser specs. None of that maps to RegCM5 — a Fortran HPC batch SPMD model whose "tests" are full-model integration runs against canonical namelists, whose correctness concerns are MPI rank/halo behavior, numerical-reproducibility tiers, and physical-scheme preservation, not UI flows. This module is the domain adaptation the generic TEA module's own documentation explicitly anticipates: same shape (one architect persona, risk-based design, evidence-gated verdicts), entirely different knowledge base and workflow set.

This module's job, relative to its sibling `bmad-hpc-devops`: `hpc-dev` produces artifacts and executes changes; `hpc-test` designs coverage, audits evidence quality, and adjudicates gate decisions. `hpc-test` never re-implements a `hpc-dev` workflow (e.g. it never builds its own CI pipeline — it consumes `hpc-dev-ci-guardrail-pipeline`'s output).

## Architecture

**Decision: one agent (Matteo), not a Murat variant, not multiple agents.** The generic module's persona "Murat" carries a CREED built for web/API judgment (fixtures, network-first, browser quality) — reusing that name for numerical-tolerance/Slurm-gate judgment would mean two differently-behaving agents sharing a name across `bmad-help` and `module-help.csv`, and the domains genuinely don't overlap. A separately-named custom persona is also immune to future upgrades/reinstalls of the generic `tea` module. Kept as a single agent, mirroring the generic module's own shape (one persona, many workflow skills) — this is one judgment center (adjudicate evidence/gate quality) expressed across several workflow shapes, not several judgment centers needing separate personas.

### Memory Architecture

**Stateless**, matching the sibling `hpc-dev` module's decision and for the same reason: this is a functional engineering-support role, not an evolving personal companion, and the project's own tracking (PRD, architecture spine, `PROMOTION_MANIFEST.jsonl`, git history) is the durable record a BMAD sanctum would otherwise duplicate.

### Memory Contract

Not applicable (stateless, no sanctum).

### Cross-Agent Patterns

The user (regcm5-dev) routes between `hpc-test` and `hpc-dev` directly. `hpc-test`'s workflows consume `hpc-dev`'s workflow outputs (evidence artifacts, build-matrix reports, CI status) as inputs but never duplicate how those are produced. `hpc-test-trace-and-gate` is the single place a PASS/CONCERNS/FAIL verdict is rendered — no other workflow in either module issues a merge verdict.

## Skills

### hpc-test-agent-test-architect

**Type:** agent

**Persona:** Matteo — a rigorous evidence auditor, at home with both statistics (MAD/RMSE/rMAD/rRMSE) and Fortran/MPI code, who treats "it compiled and ran" as unrelated to "it's correct." Adjudicates, never implements.

**Core Outcome:** Every RegCM5 change gets an evidence-backed test plan, a quality audit of its regression coverage, and — when asked — a PASS/CONCERNS/FAIL verdict that never confuses CI-green with full acceptance.

**The Non-Negotiable:** Never issues PASS without both a green CI check and real Slurm validation on the required partition(s); CI-green alone is CONCERNS at best, per the project's own CI-guardrail rule.

**Capabilities:** (routes to the 10 workflow skills below; the agent itself is the persona/voice those workflows act through, not a separate capability set)

**Memory:** none (stateless).

**Init Responsibility:** on first run, read `project-context.md`'s Testing Rules and the Architecture Spine's AD-1/AD-4/AD-12/AD-13/AD-16 in full.

**Activation Modes:** interactive and headless.

**Tool Dependencies:** `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py`, `regression_diff.py`.

**Design Notes:** Deliberately holds no independent judgment on *how* to fix anything — that's `hpc-dev`'s job. Matteo designs, audits, and gates; she does not write code or run profiling herself.

---

### hpc-test-test-framework

**Type:** workflow

**Purpose:** Bootstrap the regression-harness layout (Slurm submission templates, wiring to `manage_baseline.py`/`regression_diff.py`) for a new fixture or subsystem — the HPC counterpart to generic TEA's Playwright/fixture bootstrap.

**Capabilities:** Inputs: target fixture/subsystem (e.g. a new `Testing/*.in` namelist). Outputs: a Slurm submission template and a wired-in `regression_diff.py` invocation for that fixture.

**Design Notes:** Loop-invokable (bounded, local, no Slurm submission itself — it only templates one).

---

### hpc-test-test-design

**Type:** workflow

**Purpose:** Risk-based test plan for a story/change: which routines/paths need bit-exact vs. statistical coverage, at which `nproc`/compiler legs, replacing generic TEA's P0-P3 web-feature prioritization with this codebase's own risk axes (numerical tier, decomposition exposure, compiler-vendor exposure).

**Capabilities:** Inputs: story/FR description, affected routines/paths. Outputs: a coverage matrix (routine × tolerance tier × nproc legs × compiler legs), each cell traced to the specific rule (AD-1, AD-12/13, FR-8) that requires it.

**Design Notes:** Loop-invokable. Absorbs the one step generic TEA's `atdd` would have covered here (mapping acceptance criteria to existing fixtures) — see `atdd` below.

---

### hpc-test-regression-automate

**Type:** workflow

**Purpose:** Expand regression coverage for existing features by wrapping `regression_diff.py` — the HPC counterpart to generic TEA's `automate` (which generates Playwright/API specs; here there's no spec to generate, only fixture/tolerance-table coverage to extend).

**Capabilities:** Inputs: `hpc-test-test-design`'s coverage matrix, existing fixture set. Outputs: new/extended `Testing/` fixture wiring and tolerance-table entries in `regression_diff.py`'s `--tolerance-file`.

**Design Notes:** Loop-invokable.

---

### hpc-test-test-review

**Type:** workflow

**Purpose:** Quality audit of the regression-testing setup itself — are thresholds too loose, is `nproc=4` really 4 MPI ranks, are baselines stale — the HPC counterpart to generic TEA's test-quality audit (fixture/selector/wait-pattern review there; fixture/threshold/Slurm-script review here).

**Capabilities:** Inputs: a fixture set or tolerance-file. Outputs: an issue list (e.g. "threshold X was set once and never revisited," "baseline Y predates the last decomposition change").

**Design Notes:** Loop-invokable.

---

### hpc-test-nfr-assess

**Type:** workflow

**Purpose:** Audit non-functional-requirement evidence, adapted to this domain's own NFR categories: numerical-reproducibility, performance (wraps `hpc-dev-agent-profiler`'s evidence), I/O-scalability, cross-compiler portability — not the generic module's security/accessibility/reliability set.

**Capabilities:** Inputs: a change plus its `hpc-dev`-produced evidence (profiling artifacts, build-matrix report). Outputs: a per-category compliance report, explicit about missing evidence rather than assuming compliance.

**Design Notes:** Loop-invokable.

---

### hpc-test-trace-and-gate

**Type:** workflow

**Purpose:** The PASS/CONCERNS/FAIL gate decision. **PASS** requires CI green *and* Slurm validation on both required partitions *and* the correct tolerance tier respected *and* `nproc=1`/`nproc=4` both passing *and* the baseline properly promoted. **CONCERNS**: CI green + Slurm green but with a caveat (a statistical metric near threshold, only one partition validated, a perf claim lacking profiling evidence) — CI-green-but-Slurm-not-yet-run always lands here, never PASS, which is the direct encoding of the project's CI-guardrail rule. **FAIL**: CI red, or Slurm validation skipped entirely, or a tolerance/decomposition violation.

**Capabilities:** Inputs: CI status (from `hpc-dev-ci-guardrail-pipeline`), Slurm validation record, `hpc-test-mpi-correctness-verification`/`hpc-test-scientific-correctness-verification`/`hpc-test-coupling-contract-verification` findings. Outputs: the verdict plus its rationale, citing which specific requirement is unmet for anything short of PASS.

**Design Notes:** Interactive-only — a loop must never self-issue a merge-greenlighting PASS.

---

### hpc-test-baseline-lifecycle

**Type:** workflow

**Purpose:** Audit and promote regression baselines by wrapping `manage_baseline.py` directly — no generic-TEA analog exists, since web/API testing has no versioned golden-numerical-baseline archive concept.

**Capabilities:** Inputs: a candidate run directory. Outputs: a promotion decision (via `manage_baseline.py`'s `--force`/`--reason`), confirming `PROMOTION_MANIFEST.jsonl` integrity and archive-to-`$WORK` on supersession.

**Design Notes:** Interactive-only (touches shared, hard-to-reverse `$FAST`/`$WORK` state).

---

### hpc-test-mpi-correctness-verification

**Type:** workflow

**Purpose:** Review a RegCM5 change for MPI correctness. User-specified stages, one step file each:

1. Identify ranks, communicators, decomposed arrays, and halo regions touched by the change.
2. Inspect collective calls and rank participation — every rank must reach a given collective symmetrically.
3. Inspect send/receive ordering and synchronization.
4. Inspect reductions and numerical order sensitivity.
5. Define rank-layout tests (the `nproc=1`-and-`4` minimum).
6. Define decomposition-comparison tests (concrete `regression_diff.py` invocations across process counts).

**Capabilities:** Inputs: a diff/story touching parallel code. Outputs: an MPI-correctness review report plus a test-plan slice consumable by `hpc-test-test-design`/`hpc-test-regression-automate`.

**Design Notes:** Loop-invokable (mechanical, rule-driven, no subjective sign-off required).

---

### hpc-test-scientific-correctness-verification

**Type:** workflow

**Purpose:** Evaluate whether a RegCM5 change preserves scientific behavior. User-specified stages, one step file each:

1. Identify changed outputs and affected fields.
2. Classify fields by sensitivity.
3. Choose bitwise or tolerance-based comparison.
4. Inspect NetCDF variables and metadata.
5. Inspect restart reproducibility.
6. Inspect domain decomposition consistency (reuses stage 6 of `hpc-test-mpi-correctness-verification`).
7. Summarize unexplained differences.
8. Check whether the computation is consistent with the numerical scheme and governing physical process — consulting `hpc-dev-agent-code-comprehension` (Gaspare) for domain intent, terminating in the project's rule that scientific review means regcm5-dev's explicit sign-off, not an automated verdict.

**Capabilities:** Inputs: a diff/story touching physics/numerics. Outputs: a scientific-correctness review report; a FAIL at stage 3/4/7 or an unresolved stage 8 concern blocks `hpc-test-trace-and-gate` from PASS.

**Design Notes:** Interactive-only (stage 8 explicitly requires human sign-off, not an automated verdict).

---

### hpc-test-coupling-contract-verification

**Type:** workflow

**Purpose:** Review a RegCM5 change touching an external coupling mechanism (OASIS3-MCT, REGESM, CLM land coupling, BMI, or CISM design).

**Capabilities:** Stages: (1) identify which mechanism is touched; (2) document the current live field list against the code itself; (3) verify regression coverage for the relevant `--enable-*` build; (4) for BMI, confirm dormant status and require an explicit resolved-or-removed decision; (5) for CISM, verify a design document (field list, cadence, build-gating flag) exists before implementation is reviewed as ready. Inputs: a diff/story touching a coupling module. Outputs: a per-mechanism field-list/regression-coverage report feeding `hpc-test-trace-and-gate`.

**Design Notes:** Stages 1-3 are loop-invokable (documentation/coverage checks); the BMI keep-vs-remove decision (stage 4) and CISM design sign-off (stage 5) are interactive-only, requiring regcm5-dev's explicit call.

## Configuration

| Variable | Prompt | Default | Result Template | User Setting |
| -------- | ------ | ------- | --------------- | ------------ |
| `FAST_BASELINE_ROOT` | "Path to the canonical baseline/profiling storage on $FAST?" | `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data` | `{value}` | false |
| `CI_FIXTURE` | "In-repo CI fixture namelist (AD-11)?" | `Testing/ideal.in` | `{value}` | false |

## External Dependencies

`Tools/Scripts/TestingAndBenchmarking/manage_baseline.py`/`regression_diff.py` (already in this repo) — wrapped, never reimplemented. No new CLI tools or MCP servers required.

## UI and Visualization

`hpc-test-trace-and-gate`'s verdict and `hpc-test-nfr-assess`'s compliance report are strong HTML-report candidates (a PASS/CONCERNS/FAIL banner plus per-requirement detail reads far better than terminal text). No shared dashboard needed.

## Setup Extensions

Beyond config collection: confirm `manage_baseline.py`/`regression_diff.py` are present and executable at their known repo path (same check `hpc-dev-setup` performs — harmless if duplicated).

## Integration

**Standalone.** Provides independent value without `bmad-hpc-devops` installed (e.g. `hpc-test-test-review`/`hpc-test-nfr-assess` can audit existing manual regression practice even before `hpc-dev`'s automation exists) — but `hpc-test-trace-and-gate` and `hpc-test-nfr-assess` are most useful once `hpc-dev`'s workflows are producing the evidence they consume.

## Creative Use Cases

- Running `hpc-test-mpi-correctness-verification`/`hpc-test-scientific-correctness-verification` against a historical, already-merged commit as a dogfood/calibration check that the workflows produce concrete, codebase-grounded findings rather than generic review boilerplate.
- `hpc-test-nfr-assess`'s performance category doubling as a lightweight second opinion on `hpc-dev-agent-profiler`'s own hotspot report, catching cases where an optimization claim outruns its evidence.

## Ideas Captured

Alternatives considered and set aside: reusing the generic `tea` module's `bmad-tea` persona directly (rejected — different judgment domain, risk of behavior drift across reinstalls); a separate agent for MPI vs. scientific vs. coupling review (rejected — one judgment center, adjudication, expressed across workflow shapes, matching the `hpc-dev` module's own "few well-scoped skills" discipline); porting generic TEA's `atdd` workflow as-is (rejected — no analog to per-acceptance-criterion generated fixtures for multi-hour full-model Slurm runs; folded into a `hpc-test-test-design` step instead); giving `hpc-test` its own CI-pipeline-authoring workflow (rejected — stays owned by `hpc-dev-ci-guardrail-pipeline`; `hpc-test` only consumes its output).

## Build Roadmap

1. **`hpc-test-agent-test-architect`** (Matteo) — the persona every workflow acts through.
2. **`hpc-test-test-design`** — the risk-based plan other workflows consume.
3. **`hpc-test-mpi-correctness-verification`**, **`hpc-test-scientific-correctness-verification`**, **`hpc-test-coupling-contract-verification`** — the three correctness-review workflows, independent of each other.
4. **`hpc-test-regression-automate`**, **`hpc-test-test-review`** — coverage expansion and audit, once a design/review target exists.
5. **`hpc-test-nfr-assess`** — depends on `hpc-dev`'s evidence existing to audit.
6. **`hpc-test-baseline-lifecycle`** — wraps `manage_baseline.py`, usable once fixtures exist.
7. **`hpc-test-trace-and-gate`** — the gate, last, since it consumes every other workflow's output.
8. **`hpc-test-test-framework`** — lowest urgency, one-time/rare bootstrap.

**Next steps:**

1. Build each skill using **Build an Agent (BA)** or **Build a Workflow (BW)** — share this plan document as context
2. When all skills are built, return to **Create Module (CM)** to scaffold the module infrastructure
