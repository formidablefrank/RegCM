---
name: verify-build-matrix
description: Run/verify the GNU + Intel + NVHPC(managed) + NVHPC(stdpar) build matrix
code: VM
added: 2026-07-05
type: prompt
---

# Verify the Build Matrix

The outcome is a pass/fail report per vendor+mode (GNU, Intel, NVHPC with `--enable-openacc-managed`, NVHPC with `--enable-openacc-stdpar`) for a given branch/commit — a grid, not a single bit. The consumer decides whether a change is safe to merge across all supported compilers, so a silent skip of one leg is a false pass.

Confirm the correct compiler modules against `$HPCDOCS` before building (module names drift between cluster refreshes). Build all four legs, capturing warnings as well as errors — a new warning on one vendor that wasn't there before is worth surfacing even if the build still succeeds. Exit-code the result per the project's convention (0 pass, 1 regression/failure, 2 usage/configuration error) so this composes cleanly with CI.
