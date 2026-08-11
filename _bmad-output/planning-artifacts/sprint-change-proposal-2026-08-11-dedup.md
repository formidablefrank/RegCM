---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'moderate'
---

# Sprint Change Proposal: Code Duplication Audit and Generic-Interface Consolidation

## 1. Issue Summary

franco requested an inspection of the source code to minimize duplication, with similar functions rewritten into single functions accepting multiple data types — naming communication, pointer assignments, computation, and I/O as candidate areas. This is the fourth same-day Sprint Change Proposal.

Unlike the prior three (each a reasonably well-bounded new capability), this request was genuinely open-ended ("inspect... if possible"). Before drafting, a quick grounding check against the actual codebase was run, since this program's own stated discipline is evidence over guesswork:

- `Main/mpplib/mod_mppparam.F90` (20,683 lines) has **42 duplicate-named subroutines** across a real4/real8 type axis and a 2D/3D/4D rank axis (`exchange_array_r4`/`_r8`, `real8_2d/3d/4d_distribute`/`real4_...`), already wrapped in generic interfaces at the call site (e.g. `interface exchange_array` → `module procedure exchange_array_r8, exchange_array_r4`).
- `mod_ncout.F90`/`mod_ncstream.F90` carry a parallel pattern, but by **array rank only** (`setup_var_2d`/`_3d`/`_4d`), not by type — correcting an initial assumption that I/O duplication mirrored the communication layer's type axis.
- `assignpnt` (`Share/mod_memutil.F90`) is already a single generic interface, and is this project's own documented "#1 GPU-porting risk" — not a fresh candidate.

Two real architectural tensions were surfaced and resolved with franco directly:
- **GPU-safety**: "a single function accepting multiple data types" could mean Fortran runtime polymorphism (`class(*)`/`select type`), which is incompatible with this project's `do concurrent`/OpenACC GPU-porting strategy (AD-3). **Resolved**: consolidation is scoped to compile-time mechanisms only (generic interfaces — already the codebase's own idiom — or preprocessor-generated bodies), never runtime dispatch near an offloaded code path.
- **File-collision risk**: the I/O-layer consolidation target is the same file Epic 3 (PnetCDF) and Epic 10 (ADIOS2) are already changing. **Resolved (franco's choice)**: sequence the I/O-layer story after both epics land.

## 2. Impact Analysis

**Epic Impact:**
- **New Epic 12: Code Duplication Audit and Generic-Interface Consolidation** (3 stories), audit-first per this program's own established pattern (FR-9's go/no-go checkpoint, Story 1.5's investigate-then-scope-only-if-confirmed discipline).
- Story 12.3 carries a hard, explicit dependency on Epic 3's Story 3.3/3.4 and Epic 10's Story 10.2 completing first.
- Epics 1–11 unaffected in their own content.

**Story Impact:** No existing story changed. Three new stories added; Story 12.1's own findings are expected to refine or extend Stories 12.2/12.3's exact candidate lists, and may justify further follow-up stories not pre-committed here.

**Artifact Conflicts:**
- **PRD**: New Feature 4.14 (FR-56–FR-58), one new Feature-specific NFR (NFR-19). Phase 5 updated with an explicit note that FR-58 overrides normal phase sequencing with its own hard dependency. Assumptions Index records both the corrected I/O-duplication framing and the file-collision resolution.
- **Architecture**: New AD-26 (generic-interface consolidation policy), extending AD-3 with the specific GPU-safety constraint for body consolidation. Capability → Architecture Map gained a row.
- **UX**: N/A.
- **Other**: None beyond the above. No change to `project-context.md` itself is required by this proposal (unlike the unit-test-framework change in an earlier session) — this work doesn't reverse any stated project convention, it extends an already-established one (generic interfaces).

**Technical Impact:** None yet — planning artifacts only.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, via one new epic, audit-first.

- Rollback: not applicable.
- MVP Review: not warranted — additive, and explicitly scoped down from "refactor everything" to an evidence-gated subset.
- Effort: **Medium** — the audit alone is nontrivial (multiple large files); implementation stories are deliberately scoped to confirmed candidates only, not the full codebase.
- Risk: **Low as structured** (audit-gated, bit-exactness required, existing stencil/halo regression discipline applies, GPU-safety constraint locked in) — would have been **High** had implementation been committed blind against a 20,683-line file without an audit step first, which is exactly why Story 12.1 exists as a separate prerequisite rather than folded into 12.2/12.3.

## 4. Detailed Change Proposals

All three were reviewed and approved incrementally with franco, after two scoping questions resolved the architectural tensions above.

### 4.1 Duplication Audit

- **PRD FR-56**, **Epic 12 Story 12.1**: repository-wide audit across communication, pointer-assignment, computation, and I/O code, producing a scored go/no-go inventory per candidate family — not a blanket refactor recommendation. `assignpnt` explicitly included and marked no-go. "Computation" candidates left to the audit's own findings rather than pre-assumed.

**Status:** ✅ Applied — `prd.md` §4.14; `epics.md` Epic 12.

### 4.2 Communication-Layer Consolidation

- **PRD FR-57**, **Architecture AD-26**, **Epic 12 Story 12.2**: the confirmed subset of `mod_mppparam.F90`'s 42 duplicate-named subroutines, consolidated via compile-time mechanisms only, bit-exact per AD-1, full stencil/halo `nproc=1`/`nproc=4` regression discipline (AD-12/AD-13), public interfaces unchanged.

**Status:** ✅ Applied — `prd.md` §4.14; `ARCHITECTURE-SPINE.md` AD-26; `epics.md` Epic 12.

### 4.3 I/O-Layer Consolidation, Sequenced After Epic 3 and Epic 10

- **PRD FR-58**, **Epic 12 Story 12.3**: the confirmed subset of `mod_ncout.F90`/`mod_ncstream.F90`'s rank-duplicated routines, same constraints as Story 12.2, with a hard dependency on Epic 3's Story 3.3/3.4 and Epic 10's Story 10.2 completing first — recorded in the story's own acceptance criteria, not only this document.

**Status:** ✅ Applied — `prd.md` §4.14; `epics.md` Epic 12.

## 5. Implementation Handoff

**Scope classification: Moderate** — one new epic with a genuine, hard cross-epic dependency (Story 12.3 on Epics 3 and 10) that sprint planning must respect, not a self-contained minor addition.

**Routed to:** Product Owner / Developer role (regcm5-dev / franco). Story 12.1 can start immediately with no dependency; Story 12.2 depends only on Story 12.1's findings; Story 12.3 additionally waits on Epics 3 and 10.

**Outstanding before implementation begins:**
- `sprint-status.yaml` updated with Epic 12 (backlog).
- Story 12.1 should run before any consolidation implementation is attempted — its findings determine Story 12.2/12.3's exact scope, and may surface additional candidates (e.g. in "computation" code) that justify further stories not created here.

**Success criteria:** Epic 12 appears in `sprint-status.yaml` with three stories; a future `bmad-create-story` run against Story 12.1 produces a story consuming exactly the acceptance criteria recorded in `epics.md`; Stories 12.2/12.3 are not pulled into a sprint before their recorded dependencies (Story 12.1's go decision; for 12.3, also Epics 3 and 10) are satisfied.
