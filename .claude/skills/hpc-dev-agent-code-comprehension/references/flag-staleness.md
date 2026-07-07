---
name: flag-staleness
description: Note a discrepancy between documentation and the actual source
code: FS
added: 2026-07-05
type: prompt
---

# Flag Documentation Staleness

The outcome is a specific, actionable discrepancy note — which doc, which claim, what the source actually shows — handed off for `hpc-dev-documentation-modernization` to fix, not fixed here. This agent never edits documentation or code itself.

When answering any other capability surfaces a place where `Doc/DeveloperGuide`, `Doc/UserGuide`, or `project-context.md` contradicts what the source actually does (the known pattern: precision/module-lifecycle claims are already confirmed stale), name the exact document, the exact claim, and the exact contradicting source location. Don't silently work around a stale doc by only telling the user the correct answer — the discrepancy itself is the deliverable here, since it's what lets someone actually fix the documentation.
