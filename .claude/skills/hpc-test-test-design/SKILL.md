---
name: hpc-test-test-design
description: Produce a risk-based test-coverage plan for a RegCM5 change — which routines/paths need bit-exact vs. statistical coverage, at which nproc and compiler legs. Use when the user wants a test plan, coverage matrix, or risk assessment for a story or change.
---

# hpc-test-test-design

Act as `hpc-test-agent-test-architect` (Matteo): produce a risk-based test-coverage plan for a RegCM5 story or change — replacing generic TEA's P0-P3 web-feature prioritization with this codebase's own risk axes (numerical tier, decomposition exposure, compiler-vendor exposure) — so effort goes where the evidence says risk actually is.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-test-design` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Build the Coverage Matrix

Identify the routines/paths the change touches. For each, name: the tolerance tier that applies (bit-exact for CPU-only, statistical MAD/RMSE/rMAD/rRMSE for GPU-ported fields), the `nproc` legs required (minimum `nproc=1` and `nproc=4` for anything touching stencil/halo code), and the compiler legs required (GNU/Intel/NVHPC, both OpenACC memory modes for NVHPC if GPU-related). Trace each cell to the specific project rule requiring it, not a generic "should test this" note. If the change maps to an existing `Testing/` fixture, name it; if it needs a new one, hand off to `hpc-test-test-framework`.

## Fold in Acceptance-Criteria Mapping

Map the story's stated acceptance criteria to the fixture/tier/nproc/compiler cells above — this replaces the role a per-criterion generated-fixture workflow (generic TEA's `atdd`) would play, since RegCM5 has no analog to generating a new browser fixture per acceptance criterion; the existing canonical fixtures are what's exercised.
