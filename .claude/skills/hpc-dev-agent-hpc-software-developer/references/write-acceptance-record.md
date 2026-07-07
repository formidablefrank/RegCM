---
name: write-acceptance-record
description: Write the mandatory Build/Test/Numerical/Performance acceptance record for a change
code: AR
added: 2026-07-05
type: prompt
---

# Write the Acceptance-Criteria Record

The outcome is a commit/PR record a reviewer can act on without re-deriving what was tested — this project has no CI or PR template to enforce the structure, so the written record is the only evidence trail.

State four things concretely, every time, regardless of how small the change looks: **Build** (which compiler/vendor combination(s) it was built under), **Test** (which `Testing/` namelist(s) it was validated against, and at what process count(s) — nproc=1 and nproc=4 minimum for anything touching stencil/halo code), **Numerical** (bit-exact, or an explicit stated tolerance with justification), **Performance** (only claimed with evidence — compiler+flags, node/GPU type, problem size, a captured profiling artifact — never asserted from intuition). No time estimates.
