---
name: hpc-dev-documentation-modernization
description: Correct stale RegCM5 documentation, write GPU-porting guidance, update user-facing namelist docs, and adopt FORD for auto-generated API docs. Use when the user wants to fix outdated docs, document a subsystem, or generate API documentation.
---

# hpc-dev-documentation-modernization

Act as `hpc-dev-agent-hpc-software-developer` (Jacopo) for the writing, consulting `hpc-dev-agent-code-comprehension` (Gaspare) for staleness detection: bring RegCM5's documentation into agreement with the codebase as it actually exists today, incrementally, rather than as a one-time full retrofit.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-documentation-modernization` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Correct Stale Claims

Fix the known pattern first: `Doc/DeveloperGuide/MainDeveloperGuide.tex` and `project-context.md`'s own Module Skeleton section both currently describe a hardcoded-precision, `init_mod_*`/`release_mod_*` pattern the codebase doesn't actually use — correct both to describe `rkx` and the real `allocate_*`/`getmem`/`relmem` pattern. For any other discrepancy `code-comprehension` flags, name the exact document, the exact claim, and the exact contradicting source location before fixing it.

## Write Guidance and User-Facing Docs

Produce the GPU-porting/performance guidance document consolidating the project's risk-tiering and validation-sequencing findings, placed where a future contributor would find it (alongside `Doc/DeveloperGuide/`). Update namelist documentation to state the CLM3.5 deprecation and warn that several `Testing/*.in` fixtures ship with literal placeholder paths requiring edits before use.

## Adopt FORD Incrementally

Add a FORD project configuration (repository root or under `Doc/`) covering at minimum `Main/`, `Share/`, and `PreProc/`. Add FORD-compatible doc-comments (`!!`/`!>`) only to modules this program's own stories actually touch — this is not a retrofit sprint across the whole codebase. Build the generated HTML on demand rather than committing it.
