---
name: fix-hardening-item
description: Fix a small, evidence-based build/namelist hardening item
code: FH
added: 2026-07-05
type: prompt
---

# Fix a Build/Namelist Hardening Item

The outcome is a small, concrete, low-risk hardening fix (e.g. giving `nvfortran` its own `COMPILER_NVHPC` identity distinct from `COMPILER_PGI`, or namelist file-path existence validation) landed without changing any currently-applied flag selection or runtime behavior. The consumer needs proof the change is identity/validation-only, not a behavior change riding along.

Confirm before and after that existing OpenACC/`do concurrent`/stdpar flag selection applies identically — an unchanged build output for at least one `Testing/` fixture is the evidence this is a naming/identity correction, not a behavior change. For namelist path validation, fail fast with a diagnostic naming the specific offending variable and path, immediately after the namelist read — not deep inside a later NetCDF/IO error path.
