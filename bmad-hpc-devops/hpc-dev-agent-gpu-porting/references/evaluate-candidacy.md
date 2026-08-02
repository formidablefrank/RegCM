---
name: evaluate-candidacy
description: Decide go/no-go on porting a routine to GPU
code: EC
added: 2026-07-05
type: prompt
---

# Evaluate Port Candidacy

The outcome is a reasoned go/no-go verdict, not an assumption that a hotspot is automatically worth porting. The consumer acts on this to allocate real porting effort, so a "go" without evidence risks sinking work into a port that mirrors a known failure precedent (e.g. ICON-A's PSrad); a reflexive "no-go" on a genuine hotspot leaves real performance on the table.

Require `hpc-dev-agent-profiler`'s hotspot report as the starting evidence — a structural (code-size) argument alone is not sufficient. Check the routine's aliasing profile: any `pointer, contiguous` derived-type field reached via `assignpnt` is a blocker until proven otherwise. Check for automatic (local, entry-sized) array allocation, contained helper procedures, and other known device-kernel-generation blockers from `project-context.md`'s GPU-porting-hazards list. Decide the escalation tier: `do concurrent` first; escalate to OpenACC only when profiling evidence shows `do concurrent` is insufficient for this specific kernel — not by default. When OpenACC escalation is the answer, load `openacc-best-practices.md` before committing to an approach — it governs the `kernels`-vs-`parallel` choice and the data-locality/parallelism-mapping plan, not just the directive syntax. State the verdict and the reasoning, including what would change the answer.
