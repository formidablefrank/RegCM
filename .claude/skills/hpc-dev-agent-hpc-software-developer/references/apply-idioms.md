---
name: apply-idioms
description: Apply object-oriented and performance-conscious modern-Fortran idioms consistent with this codebase
code: AI
added: 2026-07-05
type: prompt
---

# Apply Object-Oriented and Optimization Idioms in Scientific Fortran

The outcome is a refactor that matches this codebase's existing idiom rather than importing outside style — derived types and type-bound procedures used where the surrounding code already reaches for them, and any optimization (loop normalization, data locality, allocation discipline) applied where the existing pattern already supports it, never introduced as a stylistic upgrade nobody asked for. In scientific HPC Fortran, "modern" and "fast" are not the same axis, and this codebase's own idiom is the tiebreaker whenever they pull apart.

Before restructuring, check how the surrounding module and its neighbors already handle the same kind of state (allocatable arrays vs. derived types, `getmem`/`relmem` lifecycle, `private`-then-`public::` skeleton). Prefer small transformations — loop normalization, data locality, allocation discipline, interface cleanup — over a rewrite. If a modern-Fortran or OOP idiom would improve a routine but isn't already used nearby, name the tradeoff explicitly rather than applying it unilaterally.

Polymorphic dispatch (a `class`-based derived type calling a type-bound procedure through its vtable) costs a real, non-inlinable indirection every call — harmless outside hot paths, but inside a per-gridpoint or per-timestep inner loop it can silently block vectorization and auto-parallelization in exactly the code this program is trying to speed up. Never introduce `class`/type-bound dispatch inside a loop already targeted for `do concurrent`/OpenACC, or already identified as a hotspot by `hpc-dev-agent-profiler` — a `select type`/concrete-type call, or restructuring the dispatch to happen once outside the loop, preserves the abstraction without paying the cost on every iteration.
