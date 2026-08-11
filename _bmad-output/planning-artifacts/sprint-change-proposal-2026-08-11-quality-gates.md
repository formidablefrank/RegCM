---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'moderate'
---

# Sprint Change Proposal: Performance, Memory-Safety, and Dependency Security Regression Gates

## 1. Issue Summary

franco requested automated tests for performance and security regressions, with merge requests blocked if a code change introduces runtime slowness, security vulnerabilities, or memory leaks. This is the third same-day Sprint Change Proposal, following the ones that added Epics 9–10 and Epic 4/Epic 9's Tools/contribution stories.

Before drafting, two real tensions with the program's own existing architecture were surfaced and resolved with franco directly, not silently assumed:

- **Performance in CI**: AD-4/NFR-9 already state a green GitHub Actions check is necessary but not sufficient for anything performance-sensitive, since GitHub-hosted runners have no representative hardware and no dedicated allocation — final acceptance requires Slurm validation on the real partitions. A CI check blocking merge on wall-clock timing alone would have overridden that principle. **Resolved**: a two-tier design — a coarse, automatic CI smoke check (tripwire only) plus required Slurm-based evidence for hot-path changes, extending AD-4 rather than contradicting it.
- **"Security vulnerabilities"**: `project-context.md` already states this codebase is "not a meaningful attack surface in the usual sense," being a batch HPC scientific model, not a network-facing service. **Resolved**: scoped to what is concretely meaningful given this program's own recent additions — dependency scanning for the new `requirements.txt` files (Epic 4/Epic 9) and container vulnerability scanning for Epic 5's images — plus, at franco's request, Fortran sanitizer builds (`-fsanitize=address,undefined`) as the closest real analogue to a security-relevant bug class in the model core, overlapping deliberately with the memory-leak gate rather than inventing a separate, unfounded "security scan" of the physics code.

## 2. Impact Analysis

**Epic Impact:**
- **New Epic 11: Performance, Memory-Safety, and Dependency Security Regression Gates** (3 stories), with explicit cross-epic dependencies rather than standing alone: Story 11.1 builds on Epic 1's Story 1.6; Story 11.2 builds on Epic 1's FR-4/AD-8 baseline and Epic 4's Story 4.6; Story 11.3 builds on Epic 4's Story 4.5 and Epic 5's container/CI stories.
- Epics 1–10 unaffected in their own content — Epic 11 references them but does not modify their acceptance criteria.

**Story Impact:** No existing story changed. Three new stories added, each with an explicit forward dependency recorded in its own acceptance criteria (not just this document) so a future `bmad-create-story` run surfaces the ordering.

**Artifact Conflicts:**
- **PRD**: New Feature 4.13 (FR-53–FR-55), two new Feature-specific NFRs (NFR-17 CI-tier non-authoritative, NFR-18 new-findings-only). Phase 5 and Assumptions Index updated, explicitly recording that FR-54/FR-55's scoping decisions were resolved against AD-4/NFR-9 and `project-context.md`'s existing position, not in spite of them.
- **Architecture**: New AD-25 (two-tier performance regression gate), extending AD-4 with the specific tier-selection rule. Capability → Architecture Map gained a row.
- **UX**: N/A.
- **Other**: None beyond the above.

**Technical Impact:** None yet — planning artifacts only.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, via one new epic with three stories, each carrying explicit forward/cross-epic dependencies.

- Rollback: not applicable.
- MVP Review: not warranted — additive, and the two architectural tensions were resolved as extensions of existing principles (AD-4, `project-context.md`'s attack-surface position), not as scope cuts.
- Effort: **Medium** — three stories, each touching CI configuration, build variants, and the PR template.
- Risk: **Low** — every gate is either a coarse tripwire (CI smoke tier, generous tolerance) or scoped to genuinely new surface area (dependency/container files this program itself is adding); nothing retroactively blocks on pre-existing findings (NFR-18).

## 4. Detailed Change Proposals

All three were reviewed and approved incrementally with franco, after two scoping questions resolved the architectural tensions above.

### 4.1 Memory-Leak and Memory-Safety Regression Gate

- **PRD FR-53**, **Epic 11 Story 11.1**: Story 1.6's Valgrind pass becomes a repeatable CI check against `Testing/ideal.in`, failing only on new findings relative to Story 1.6's recorded baseline (NFR-18); a GNU `-fsanitize=address,undefined` build adds a distinct, complementary check.

**Status:** ✅ Applied — `prd.md` §4.13; `epics.md` Epic 11.

### 4.2 Performance Regression Gate — CI Smoke Tier + Required Slurm Evidence

- **PRD FR-54**, **NFR-17**, **Architecture AD-25**, **Epic 11 Story 11.2**: coarse automatic CI timing check on `Testing/ideal.in` (generous tolerance, tripwire only); required Slurm-based evidence against AD-8's canonical baseline for changes touching profiled hotspots or dynamics/I/O/GPU code, checked at review per NFR-10 — with an explicit waiver path for changes outside that scope, so the requirement doesn't block every unrelated PR.

**Status:** ✅ Applied — `prd.md` §4.13; `ARCHITECTURE-SPINE.md` AD-25; `epics.md` Epic 11.

### 4.3 Dependency and Container Vulnerability Scanning

- **PRD FR-55**, **Epic 11 Story 11.3**: `pip-audit` against every `requirements.txt` added under Epic 4/Epic 9; Trivy (or equivalent) against Epic 5's container images, gating the container-build pipeline. Scope statement explicit that this does not claim the Fortran core is "security-scanned" in a generic sense — Story 11.1 covers memory-safety in the core on its own terms.

**Status:** ✅ Applied — `prd.md` §4.13; `epics.md` Epic 11.

## 5. Implementation Handoff

**Scope classification: Moderate** — one new epic with genuine cross-epic dependencies requiring sequencing awareness (not a self-contained minor addition, but no fundamental replan either).

**Routed to:** Product Owner / Developer role (regcm5-dev / franco), for sprint planning that respects the recorded dependencies: Story 11.1 after Story 1.6, Story 11.2 after Story 4.6 (and informed by FR-4/AD-8), Story 11.3 after Story 4.5 and Epic 5's container stories.

**Outstanding before implementation begins:**
- `sprint-status.yaml` updated with Epic 11 (backlog).
- None of Epic 11's stories should be pulled before their respective dependencies land — this is recorded in each story's own acceptance criteria, not only here.

**Success criteria:** Epic 11 appears in `sprint-status.yaml` with three stories; a future `bmad-create-story` run against any of them produces a story consuming exactly the acceptance criteria recorded in `epics.md`, including the dependency-ordering criteria, with no further disambiguation needed.
