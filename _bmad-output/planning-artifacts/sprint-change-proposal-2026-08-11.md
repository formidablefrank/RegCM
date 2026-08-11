---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'moderate'
---

# Sprint Change Proposal: Contributor Onboarding, Unit Testing, and ADIOS2 I/O Backend

## 1. Issue Summary

franco requested three new capabilities be added to the RegCM5 HPC Modernization program's backlog:

1. A Docker container so developers can run RegCM5 or contribute to the source with minimal setup, with build/run documentation for both users and developers.
2. Automated unit and integration tests contributors can run to confirm a change has no unintended side effects, with developer documentation on running them.
3. An ADIOS2 I/O backend, opt-in alongside the existing netCDF output path.

This is a new-requirement scope addition, not a defect found in an existing story — no story is currently in flight against any of the three areas, so no rollback surface exists. Cross-checking against the existing PRD/epics/architecture found:

- **Containers** are already substantially planned (Epic 5, FR-28–FR-32: GNU/Intel/NVHPC-CUDA images, Apptainer, CI), but with no story for build/run documentation, and no explicit requirement that the production images also serve as a contributor development environment.
- **Testing** is already partially planned (Epic 2, FR-24–FR-27), but strictly as full-model integration/regression tooling. `project-context.md`'s Testing Rules section explicitly states no unit-test framework exists at the model level, and that isolated unit tests should not be invented for physics/dynamics routines — a real conflict with "unit tests," not just a gap.
- **ADIOS2** appears nowhere in the PRD, epics, or architecture. Epic 3 (I/O Scaling) is scoped to netCDF/PnetCDF/serial/async-netcdf only.

## 2. Impact Analysis

**Epic Impact:**
- Epic 4 (Documentation Modernization) — extended with Story 4.4 (container docs); Stories 4.1–4.3 gained a documentation-register acceptance criterion.
- Epic 5 (Multi-Vendor Containers and CI Gate) — Stories 5.1 and 5.3 extended with dev-machine-usability acceptance criteria; no new story (a separate lightweight container was considered and explicitly rejected — see §4.1 below).
- Epic 9 (new) — Contributor Testing Infrastructure: pFUnit adoption, an initial unit-test suite, and contributor testing documentation.
- Epic 10 (new) — ADIOS2 I/O Backend Integration: design, implementation across all three output paths (diagnostic/history, restart, CLM), and documentation.
- Epics 1, 2, 3, 6, 7, 8 — unaffected in scope; none become obsolete or need resequencing. Epics 9 and 10 have no technical dependency on any existing epic and are sequenced last by default.

**Story Impact:** 39 existing stories are unaffected in substance. Stories 4.1, 4.2, 4.3, 5.1, 5.3 each gained one additional acceptance criterion. Eight new stories were added (4.4, 9.1–9.3, 10.1–10.3).

**Artifact Conflicts:**
- **PRD**: Nine new FRs (FR-40–FR-47, skipping no numbers) across Features 4.6, 4.8 (extended) and two new Features (4.11, 4.12); three new Feature-specific NFRs (NFR-14, NFR-15, NFR-16); a new Phase 5 in the phased-scope plan; one Assumptions Index entry recording this proposal's origin. No MVP or existing-requirement conflict — purely additive.
- **Architecture**: Two new Architecture Decisions — AD-23 (ADIOS2 opt-in mechanism and version pinning) and AD-24 (unit-test scope: pure routines only, the explicit narrowing of the existing testing-boundary rule). Stack table gained ADIOS2 and pFUnit rows. Capability → Architecture Map gained three rows.
- **UX**: N/A — no UX contract exists for this program, confirmed unaffected.
- **Other**: `project-context.md`'s Testing Rules section will go stale once Epic 9 ships (same pattern the PRD already caught once with FR-21) — Story 9.1 owns that correction as part of its acceptance criteria, not done as part of this planning-only proposal.

**Technical Impact:** None yet — this proposal only touches planning artifacts (PRD, epics, architecture spine). No code, infrastructure, or deployment changes.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, via a hybrid of story additions to existing epics (4, 5) and two new epics (9, 10) — explicitly permitted under Direct Adjustment, not a rollback or MVP-scope review.

- Rollback (Option 2): not applicable — nothing has been implemented against these areas yet.
- MVP Review (Option 3): not warranted — this is additive scope, not a constraint-driven cut.
- Effort: **Medium** (this planning pass; implementation effort follows the normal per-story flow later).
- Risk: **Low** — every new capability is opt-in and additive (matching NFR-3's existing "zero behavior change for non-opted-in runs" pattern, already proven for FR-5/FR-6 and FR-13/FR-14); nothing touches validated existing code paths.

## 4. Detailed Change Proposals

All changes below were reviewed and approved incrementally with franco during this session, then applied directly to the planning artifacts.

### 4.1 Containers (Epic 5 / Epic 4 / PRD Features 4.8, 4.6)

Initial proposal included a separate lightweight development container (new Story 5.5). **franco rejected this** — the existing production images (GNU, Intel, NVHPC/CUDA) should serve both production validation and contributor development, with no second container track. Revised accordingly:

- **PRD FR-40** (Feature 4.8): production container images double as the contributor development environment — each must run under plain Docker on a non-HPC, non-GPU workstation; the NVHPC/CUDA image specifically must support its CPU-only `-stdpar=multicore` path without requiring a GPU.
- **PRD FR-41** (Feature 4.6): container build/run documentation for users and developers.
- **PRD NFR-14** (Feature 4.6): documentation register — scholarly/concise, matching `project-context.md`'s existing communication-style convention, now extended to authored documentation content itself. Applied to every documentation-authoring story (Epic 4's four stories, Epic 9's Story 9.3, Epic 10's Story 10.3).
- **Epic 5**: Stories 5.1 and 5.3 each gained an acceptance criterion confirming dev-machine usability (plain Docker, no HPC scheduler; GPU-less CPU path for the NVHPC/CUDA image). No new story.
- **Epic 4**: new **Story 4.4** — Container Build and Run Documentation for Users and Developers. Stories 4.1–4.3 each gained an NFR-14 acceptance criterion.

**Status:** ✅ Applied — `prd.md` §4.6, §4.8; `epics.md` Epic 4, Epic 5.

### 4.2 Testing (new Epic 9 / PRD Feature 4.11)

franco confirmed both a real unit-test framework and contributor documentation were wanted — not just Epic 2's integration tooling made contributor-friendly. This directly conflicts with `project-context.md`'s stated testing-boundary rule ("no meaningful unit vs. integration split... don't invent isolated unit tests for physics/dynamics routines"), so the resolution **narrows rather than reverses** that rule: pFUnit-based unit tests apply only to pure, side-effect-free routines (the three routines already confirmed `pure` for GPU porting — `getcape_new`, `interp1d_r8`, `heatindex`); stateful physics/dynamics/I/O code remains integration-only.

- **PRD FR-42/FR-43/FR-44** (new Feature 4.11): adopt pFUnit and establish the pattern; author the initial suite against the three pure routines; write contributor testing documentation covering both unit and integration workflows.
- **PRD NFR-15**: unit-test scope is limited to pure routines — the explicit narrowing statement.
- **Architecture AD-24**: the same narrowing, at architecture-decision level, requiring regcm5-dev's explicit sign-off (recorded in Story 9.1).
- **New Epic 9** (3 stories: 9.1 adopt pFUnit + correct `project-context.md`'s Testing Rules + sign-off; 9.2 initial suite; 9.3 contributor documentation, NFR-14 register).

**Status:** ✅ Applied — `prd.md` new §4.11; `epics.md` new Epic 9; `ARCHITECTURE-SPINE.md` new AD-24.

### 4.3 ADIOS2 (new Epic 10 / PRD Feature 4.12)

Initial proposal scoped ADIOS2 to diagnostic/history output only (v1), phased like FR-5/FR-33 was. **franco requested restart/CLM be in scope from the start** — revised to three independent namelist switches from day one, matching AD-6's per-path convention exactly rather than phasing it. ADIOS2 writes its own BP format (not NetCDF-compatible), so the design step (Story 10.1) must state explicitly how comparison against the NetCDF baseline is performed for each path — this is a first-class deliverable, not an assumed detail (NFR-16).

- **PRD FR-45/FR-46/FR-47** (new Feature 4.12): evaluate/design (build flag, three switches — `do_adios2_hist`/`do_adios2_rst`/`do_adios2_clm`, comparison plan); implement across all three paths, opt-in; documentation.
- **PRD NFR-16**: BP-vs-NetCDF comparison must be stated explicitly, never assumed.
- **Architecture AD-23**: the opt-in mechanism (build flag + three switches, default off) and version-pinning rule, extending AD-15's table.
- **New Epic 10** (3 stories: 10.1 design across all three paths; 10.2 implement across all three paths; 10.3 documentation, NFR-14 register).

**Status:** ✅ Applied — `prd.md` new §4.12; `epics.md` new Epic 10; `ARCHITECTURE-SPINE.md` new AD-23, Stack table, Capability Map.

## 5. Implementation Handoff

**Scope classification: Moderate** — backlog reorganization completed (two new epics, extensions to two existing epics, nine new/extended stories), no fundamental replan of vision, MVP, or existing epics' viability.

**Routed to:** Product Owner / Developer role (in this project, regcm5-dev / franco, per the project's sole-reviewer convention) for normal sprint planning and per-story development, following the existing `bmad-create-story` → `bmad-dev-story` → `bmad-code-review` cycle.

**Outstanding before implementation begins:**
- Epic 9's Story 9.1 requires regcm5-dev's explicit sign-off on the testing-boundary policy narrowing when it lands (not a blocker to drafting the story now, but to completing it).
- Epic 10's Story 10.1 must resolve the BP-vs-NetCDF comparison method before Story 10.2 can be implemented.
- `sprint-status.yaml` updated to reflect Epic 9 and Epic 10 (backlog) and Epic 4/Epic 5's added stories (see below).

**Success criteria:** Epic 9 and Epic 10 appear in `sprint-status.yaml`; a future `bmad-create-story` run against either epic produces a story consuming exactly the acceptance criteria recorded in `epics.md` above — no further disambiguation needed at that time.
