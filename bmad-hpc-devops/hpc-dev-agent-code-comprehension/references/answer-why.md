---
name: answer-why
description: Answer a design-choice "why" question grounded in project history and rules
code: AW
added: 2026-07-05
type: prompt
---

# Answer a "Why" Question

The outcome is an answer grounded in something checkable — `project-context.md`, `Doc/`, git/commit history, or (once they exist) the architecture spine and PRD's own recorded findings — not a plausible-sounding rationalization. The consumer is a developer deciding whether to change something, so an ungrounded "why" is worse than admitting the reasoning isn't recorded anywhere.

Check `project-context.md` and the relevant `Doc/` manual first, then git log/commit messages for the area in question — this codebase's history carries real design rationale (e.g. the NVIDIA GPU-porting collaboration's commits). If a finding exists in the architecture spine or PRD (e.g. why RRTMG isn't GPU-ported yet, why parallel I/O isn't the default), cite it directly rather than re-deriving the reasoning. If none of these sources answers it, say plainly that the rationale isn't recorded anywhere you can find, rather than constructing a plausible-sounding one.
