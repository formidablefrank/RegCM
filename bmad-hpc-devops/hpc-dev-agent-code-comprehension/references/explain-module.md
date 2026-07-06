---
name: explain-module
description: Explain what a RegCM5 module or subroutine does and why
code: EM
added: 2026-07-05
type: prompt
---

# Explain a Module or Subroutine

The outcome is a developer understanding what a piece of code does, its place in the call graph, and its physical/numerical intent — grounded in the actual source, not general Fortran knowledge. The consumer will act on this understanding (extend it, fix it, port it), so every claim needs a `file:line` citation they can verify themselves.

Read the target file/subroutine directly rather than relying on its name or a doc description. State its purpose, its callers and callees (at least one level each way), the precision/unit conventions it uses (cross-reference `project-context.md`'s `rkx`/unit-comment rules), and — for physics/numerics code — what physical process or numerical scheme it implements, citing `Doc/ReferenceManual` where current. If `Doc/DeveloperGuide` or `project-context.md` itself makes a claim the source contradicts (the known pattern: stale precision/lifecycle claims), say so and route it to `flag-staleness`. For GPU-ported code, cross-reference the GPU-porting-hazard rules rather than treating it as a plain subroutine.

Never guess at physical/numerical intent from naming conventions alone — where the source and available docs don't make it clear, say what's uncertain rather than filling the gap with plausible domain knowledge.
