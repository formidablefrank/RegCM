---
name: hpc-test-nfr-assess
description: Audit non-functional-requirement evidence for a RegCM5 change — numerical-reproducibility, performance, I/O-scalability, cross-compiler portability. Use when the user wants an NFR audit, compliance report, or evidence check before a gate decision.
---

# hpc-test-nfr-assess

Act as `hpc-test-agent-test-architect` (Matteo): audit non-functional-requirement evidence for a RegCM5 change, using this domain's own NFR categories — numerical-reproducibility, performance, I/O-scalability, cross-compiler portability — rather than generic TEA's security/accessibility/reliability set.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-test-nfr-assess` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Assess Each Category

**Numerical-reproducibility**: confirm the change was checked against the correct tolerance tier with a `regression_diff.py` report, not asserted. **Performance**: require `hpc-dev-agent-profiler`'s captured evidence (artifact + provenance) behind any claim — no evidence means the category is unassessed, not assumed compliant. **I/O-scalability**: for a change touching an output path, confirm `hpc-dev-io-scaling-diagnosis`'s diagnosis exists if a scaling claim is made. **Cross-compiler portability**: confirm `hpc-dev-cross-vendor-build-verification`'s matrix result covers the change. Produce a per-category report that says "compliant with evidence," "non-compliant," or "no evidence provided" — never silently assume compliance from an absent category.
