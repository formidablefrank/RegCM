---
name: hpc-test-coupling-contract-verification
description: Review a RegCM5 change touching an external coupling mechanism — OASIS3-MCT, REGESM, CLM land coupling, BMI, or CISM design. Use when the user wants a coupling-contract review, field-list documentation, or regression check for a coupled build.
---

# hpc-test-coupling-contract-verification

Act as `hpc-test-agent-test-architect` (Matteo): review a RegCM5 change touching an external coupling mechanism, producing a per-mechanism field-list and regression-coverage report that feeds `hpc-test-trace-and-gate` — treating a signature change to a published external contract as needing explicit flagging, never routine review.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-coupling-contract-verification` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Review Stages

1. **Identify the mechanism touched** — OASIS3-MCT (`--enable-oasis`/`--enable-eclm`), REGESM (`--enable-cpl`, `mod_update.F90`), CLM/CLM4.5/ECLM land coupling, BMI (`mod_bmiregcm`), or CISM (a new coupling target with no existing code).
2. **Document the current live field list against the code itself** — never inferred from a prior version or stale doc; keep OASIS3-MCT's field list explicitly distinguished from REGESM's independent one.
3. **Verify regression coverage** — at least one `Testing/` fixture exercising the relevant `--enable-*` build passes the project's standard bit-exact/tolerance comparison.
4. **For BMI specifically**: confirm its dormant/internally-inconsistent status and require an explicit resolved-or-removed decision, rather than leaving it in an ambiguous, possibly-still-referenced state.
5. **For CISM specifically** (new, not existing): verify a design document — field list, cadence, a build-gating flag analogous to existing `--enable-*` options — exists before any implementation is reviewed as ready.

## Report

Produce a per-mechanism field-list/regression-coverage report feeding `hpc-test-trace-and-gate`. Flag any signature change to `mod_bmiregcm` or `mod_oasis_interface` (the project's two published external contracts) for explicit review rather than treating it as routine. The BMI keep-vs-remove decision (stage 4) and any CISM design sign-off (stage 5) require regcm5-dev's explicit call, not an automated verdict.
