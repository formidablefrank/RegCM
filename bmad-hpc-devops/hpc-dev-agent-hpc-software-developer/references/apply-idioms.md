---
name: apply-idioms
description: Apply modern-Fortran and OOP idioms consistent with this codebase
code: AI
added: 2026-07-05
type: prompt
---

# Apply Modern-Fortran and OOP Idioms

The outcome is a refactor that matches this codebase's existing idiom rather than importing outside style — derived types and type-bound procedures used where the existing code already reaches for them, not introduced as a stylistic upgrade nobody asked for.

Before restructuring, check how the surrounding module and its neighbors already handle the same kind of state (allocatable arrays vs. derived types, `getmem`/`relmem` lifecycle, `private`-then-`public::` skeleton). Prefer small transformations — loop normalization, data locality, allocation discipline, interface cleanup — over a rewrite. If a modern-Fortran idiom would improve a routine but isn't already used nearby, name the tradeoff explicitly rather than applying it unilaterally.
