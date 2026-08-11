---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'minor'
---

# Sprint Change Proposal: Tools/ Documentation and Contribution Process

## 1. Issue Summary

franco requested two further additions to the RegCM5 HPC Modernization program's backlog, following the same-day Sprint Change Proposal that added Epics 9 and 10 (`sprint-change-proposal-2026-08-11.md`):

1. User documentation for the scripts under `Tools/`, plus a Makefile or `requirements.txt` where that makes them easier to build and run.
2. A systematic contribution process for this open-source scientific codebase: instructions on how to contribute, and rules for raising issues and merge requests.

Neither area is currently in the PRD/epics. A repository check confirmed:

- `Tools/Programs/` has 11 Fortran utilities, each with its own Makefile, but no top-level build. `Tools/Scripts/` is a large, heterogeneous collection (ICBC/pre-processing, plotting, `pycordexer`, `pyplotter`, `pyrunner`) with no `requirements.txt` anywhere, aside from `TestingAndBenchmarking/` (already Epic 2's territory) and `regcm_postproc-0.0.1` (an explicit PRD Non-User, §2.2).
- No `CONTRIBUTING.md` and no `.github/` directory exist at all — consistent with `project-context.md`'s existing note that there is no CI pipeline either.

This is additive new-requirement scope, not a defect. No story is in flight against either area.

## 2. Impact Analysis

**Epic Impact:**
- Epic 4 (Documentation Modernization) — extended with two new stories (4.5, 4.6); no epic-level restructuring.
- Epic 9 (Contributor Testing Infrastructure, added by the prior proposal this session) — extended with one new story (9.4), which introduces a genuine cross-epic dependency: Story 9.4 cannot start meaningfully before Epic 4's Story 4.5 lands (dependency and build/requirements-file normalization).
- Epics 1, 2, 3, 5, 6, 7, 8, 10 — unaffected.

**Story Impact:** No existing story's acceptance criteria changed. Six new acceptance-criteria blocks were added across two new Epic 4 stories and one new Epic 9 story.

**Artifact Conflicts:**
- **PRD**: Five new FRs (FR-48–FR-52) — three extending Feature 4.6 (Documentation Modernization), one extending Feature 4.11 (Contributor Unit Testing Framework), plus an NFR-15 scope-statement update explicitly extending the "pure routines only" narrowing to `Tools/` code. Phase 5 and the Assumptions Index updated accordingly. No MVP conflict — additive.
- **Architecture**: No new Architecture Decision needed — this work follows AD-24's already-adopted pure-routine unit-test scoping rule directly, applied to a new code area rather than requiring a new rule.
- **UX**: N/A, unaffected.
- **Other**: None beyond the PRD/epics changes.

**Technical Impact:** None yet — planning artifacts only.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, entirely as new stories within existing epics (no new epic needed this time).

- Rollback: not applicable.
- MVP Review: not warranted — additive.
- Effort: **Low** (two focused documentation/tooling stories plus one testing story).
- Risk: **Low** — no existing code path is touched; `c++read`'s Makefile normalization preserves its existing `ncxx4-config`-based dependency detection rather than replacing it.

## 4. Detailed Change Proposals

Both proposals were reviewed and approved incrementally with franco, then applied directly to the planning artifacts.

### 4.1 Tools/ Documentation, Build Ergonomics, and Testing

franco's initial ask (documentation + Makefile/`requirements.txt`) was refined twice during review:
- **Scoping choice**: one `requirements.txt` per Python tool group (`Python/`, `pyplotter/`, `pyrunner/`), not one repo-wide file — these are unrelated utilities with different dependencies.
- **Addition 1**: normalize `c++read`'s hand-written Makefile to the `Makefile.am`/`Makefile.in` autotools pattern already used by `CheckSun`, `RegCM_read`, and `timeseries` (noticed while franco had the file open).
- **Addition 2**: also add unit and integration tests for the `Tools/` code, reusing Epic 9's pure-routine-vs-full-run testing pattern rather than inventing a separate one.

- **PRD FR-48**: Tools/ scripts and programs documentation (a single findable catalog).
- **PRD FR-49**: Tools/ build and run ergonomics (top-level `Tools/Programs/Makefile`, `c++read` autotools normalization, per-group `requirements.txt`).
- **PRD FR-50** (Feature 4.11): unit and integration tests for `Tools/` code, depending on FR-49.
- **Epic 4, Story 4.5** — Document and Streamline the Tools/ Scripts and Programs.
- **Epic 9, Story 9.4** — Unit and Integration Tests for Tools/ Scripts and Programs (explicitly depends on Story 4.5).

**Status:** ✅ Applied — `prd.md` §4.6/§4.11; `epics.md` Epic 4, Epic 9.

### 4.2 Contribution Guide, Issues, and Merge Requests

- **PRD FR-51**: `CONTRIBUTING.md` — acceptance discipline (NFR-10), sign-off model, pointers to (not a copy of) `project-context.md`/Dev Guide.
- **PRD FR-52**: `.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE.md` — reproduction/fixture/compiler info for issues; Build/Test/Numerical/Performance record and a CI-is-necessary-not-sufficient statement (AD-4) for pull requests.
- **Epic 4, Story 4.6** — Contribution Guide, Issue, and Merge-Request Rules.

**Status:** ✅ Applied — `prd.md` §4.6; `epics.md` Epic 4.

## 5. Implementation Handoff

**Scope classification: Minor** — two new stories in an existing epic plus one new story in another existing epic, no epic restructuring, no new epic.

**Routed to:** Developer agent (regcm5-dev / franco) for direct implementation via the normal `bmad-create-story` → `bmad-dev-story` → `bmad-code-review` cycle. No PM/Architect escalation needed.

**Outstanding before implementation begins:**
- `sprint-status.yaml` updated with Stories 4.5, 4.6, and 9.4 (backlog).
- Story 9.4 should not be picked up before Story 4.5 completes — the dependency is recorded in both stories' acceptance criteria, not just this document.

**Success criteria:** Epic 4 shows six stories and Epic 9 shows four in `sprint-status.yaml`; a `bmad-create-story` run against any of the three new stories produces a story consuming exactly the acceptance criteria recorded in `epics.md` above.
