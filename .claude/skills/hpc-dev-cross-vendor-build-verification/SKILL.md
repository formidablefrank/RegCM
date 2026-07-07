---
name: hpc-dev-cross-vendor-build-verification
description: Run and report the GNU + Intel + NVHPC(managed) + NVHPC(stdpar) build matrix for a RegCM5 branch or commit. Use when the user wants to verify a change builds across compilers, or check compiler-matrix status before merging.
---

# hpc-dev-cross-vendor-build-verification

Act as `hpc-dev-agent-build-portability` (Franco): build a given RegCM5 branch/commit under all four required legs — GNU, Intel, NVHPC with `--enable-openacc-managed`, NVHPC with `--enable-openacc-stdpar` — and report pass/fail per leg as a grid, so a change that helps one vendor while silently regressing another is caught before merge, not after.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-cross-vendor-build-verification` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present) — in particular `COMPILER_MODULES`.

## Verify the Matrix

Confirm the correct compiler modules against `$HPCDOCS` before building — module names drift between cluster refreshes, and a stale name is a silent-skip risk, not a cosmetic one. Build all four legs, capturing warnings as well as hard failures; a new warning on one vendor that wasn't there before is worth surfacing even when the build still succeeds. Report the result as a per-vendor+mode grid, and exit-code it per the project's convention (0 pass, 1 regression/failure, 2 usage/configuration error) so it composes cleanly with `hpc-dev-ci-guardrail-pipeline`.
