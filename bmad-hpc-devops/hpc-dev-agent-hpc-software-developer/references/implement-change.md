---
name: implement-change
description: Implement a scoped RegCM5 code change
code: IC
added: 2026-07-05
type: prompt
---

# Implement a Scoped Code Change

The outcome is a diff that solves exactly the stated problem, in this codebase's own idiom, ready for review. The consumer is a reviewer (regcm5-dev) applying this project's acceptance discipline, so the change must be traceable to a specific FR/story and scoped to one subsystem (or one clearly-scoped seam between two).

Follow `project-context.md`'s module-skeleton, precision (`rkx`/`ik4`/`ik8`, never hardcoded `real(8)`/`dp`), and banned-legacy-Fortran rules exactly. Write minimal code that solves the stated problem — no speculative generality, no unrequested refactor riding along. If the change touches a stencil/halo operation or an external-contract module (`mod_bmiregcm`, `mod_oasis_interface`), flag that explicitly rather than treating it as routine. When in doubt about idiom, consult `hpc-dev-agent-code-comprehension` rather than guessing from general Fortran style.
