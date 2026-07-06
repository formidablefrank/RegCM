---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-07-06'
status: 'approved'
scope: 'minor'
---

# Sprint Change Proposal: Implementation Readiness Report Follow-Up

## 1. Issue Summary

The Implementation Readiness Check completed on 2026-07-06 (`implementation-readiness-report-2026-07-06.md`) rated the RegCM5 HPC Modernization program **READY** for Phase 1, with zero critical findings. Its Epic Quality Review pass, however, surfaced four polish-level issues plus one disclosure item, none blocking implementation:

- A systematic Given/When/**And** pattern instead of Given/When/**Then** across nearly all acceptance criteria in `epics.md` (39 stories).
- Story 5.2's third acceptance criterion asserted behavior about Story 5.3's not-yet-existing NVHPC/CUDA container — unverifiable at the time Story 5.2 itself is completed.
- Epic 5's epic-level summary was phrased system-centric rather than persona-first, inconsistent with Epics 1–4 and 6–8 (individual Epic 5 stories were already fine).
- FR-39 (Valgrind memory-leak/error check, Epic 1 / Story 1.6) exists in `epics.md` but is not recorded anywhere in the PRD — added directly during epic creation at franco's request, disclosed at the time but not reflected back into the PRD.

This is not a scope, requirement, or architectural change — it is a pre-implementation artifact-quality cleanup triggered by the readiness gate itself, discovered before Sprint Planning has run (no story is yet in flight, so no rollback surface exists).

## 2. Impact Analysis

**Epic Impact:** None of the 8 epics required scope changes, removal, redefinition, or resequencing. Only Epic 5's summary line and two of its stories (5.2, 5.3) needed edits.

**Story Impact:** All 39 stories' acceptance criteria were touched only mechanically (And → Then on the closing line of 32 blocks that lacked a Then); no acceptance criterion's substantive meaning changed. Stories 5.2 and 5.3 had one AC relocated between them.

**Artifact Conflicts:**
- PRD: needed one addendum entry (§9 Assumptions Index) to record FR-39's origin. No MVP or requirements-scope conflict.
- Architecture: no conflicts found.
- UX: not applicable — no UX contract exists for this program.

**Technical Impact:** None. No code, infrastructure, or deployment implications — this proposal only touches planning-artifact text.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment.**

Rollback (Option 2) does not apply — nothing has been implemented yet. MVP/scope review (Option 3) is not warranted — no finding touches requirements or scope achievability. All four issues are resolvable as direct text edits to existing artifacts, with no epic restructuring, no new stories, and no timeline impact.

- Effort: **Low**
- Risk: **Low**
- Rationale: the readiness report itself already concluded these were non-blocking; Direct Adjustment simply executes the fixes it already specified.

## 4. Detailed Change Proposals

### 4.1 PRD — Record FR-39's origin

**File:** `prds/prd-RegCM-2026-07-04/prd.md`, §9 Assumptions Index

```diff
  - §7 — No numeric performance targets are set pending Phase 1's baseline; this is a deliberate scoping choice, not an oversight.
+ - §4.1 (epics-level addition) — FR-39 (Valgrind memory-leak/error check, under Epic 1) does not originate in this PRD. It was added directly during epic creation at franco's explicit request. Recorded here for traceability, not because this PRD itself scopes it.
```

**Status:** ✅ Applied.

### 4.2 Epics — Reword Epic 5's summary to persona-first

**File:** `epics.md` (both occurrences: Epic List overview, line ~193; Epic 5's own section header, line ~586)

```diff
- RegCM5 builds and runs as GNU, Intel, and NVHPC/CUDA container images under Docker or Apptainer on any compatible system, and every pull request is automatically gated by a GNU+Intel build plus a regression-diff check before merge. Builds on Epic 2's regression-diff tool for its CI check; otherwise standalone — does not require Epic 7's GPU verification to package a container.
+ A developer or HPC operator gets RegCM5 built and running as GNU, Intel, and NVHPC/CUDA container images under Docker or Apptainer on any compatible system, with every pull request automatically gated by a GNU+Intel build plus a regression-diff check before merge. Builds on Epic 2's regression-diff tool for its CI check; otherwise standalone — does not require Epic 7's GPU verification to package a container.
```

**Status:** ✅ Applied (both occurrences).

### 4.3 Epics — Move Story 5.2's forward-looking AC into Story 5.3

**File:** `epics.md`, Story 5.2 (removed):

```diff
  **Given** a `Testing/` fixture run through the GNU and Intel Apptainer images on Leonardo
  **When** compared against the corresponding native-build baseline (Epic 2's `regression_diff.py`)
  **Then** output matches within the project's existing tolerance policy (AD-1)
-
- **Given** Story 5.3's NVHPC/CUDA variant, once it exists
- **When** it is also converted to Apptainer
- **Then** it runs the same way — this story's Apptainer mechanism is generic across all three variants, not GNU/Intel-specific
```

**File:** `epics.md`, Story 5.3 (appended):

```diff
  **Given** this container's GPU-side execution
  **When** compared to native validation on `boost_usr_prod`
  **Then** it's treated as additional validation/distribution surface, not a substitute for native HPC-partition validation (NFR-8)
+
+ **Given** Story 5.2's Apptainer conversion mechanism, established for the GNU and Intel images
+ **When** this NVHPC/CUDA image is also converted to Apptainer
+ **Then** it runs the same way, without modification to that mechanism — confirming it is generic across all three variants, not GNU/Intel-specific
```

**Status:** ✅ Applied.

### 4.4 Epics — Mechanical Given/When/Then normalization

**File:** `epics.md`, all 39 stories.

**Method:** Every acceptance-criteria block was parsed programmatically; 32 blocks were found lacking a `**Then**` line and closing instead with exactly one `**And**` line (zero blocks had ambiguous multi-**And** chains, so no block required manual disambiguation). The closing `**And**` was replaced with `**Then**` in each of those 32 blocks only — no other line was touched, and no acceptance criterion's substantive meaning changed.

**Verification:** Post-edit scan confirms 0 remaining acceptance-criteria blocks without a `**Then**` line.

**Status:** ✅ Applied (32 blocks across the document).

## 5. Implementation Handoff

**Change scope classification: Minor** — implemented directly, no backlog reorganization or replan required.

- **Executed by:** This session (Correct Course workflow), acting as the direct-implementation path for a Minor-scope change.
- **Responsibilities:** All four changes above are already applied to `prd.md` and `epics.md` as of this proposal's approval. No further handoff to a separate Developer/PO/Architect role is needed.
- **Success criteria:** (a) PRD's Assumptions Index includes the FR-39 note — met; (b) Epic 5's summary reads persona-first in both locations — met; (c) Story 5.2 contains only its two self-contained ACs, Story 5.3 contains the migrated AC — met; (d) zero acceptance-criteria blocks in `epics.md` lack a `**Then**` line — met (verified by script).

## 6. Approval

**Approved by:** franco, via explicit selection of "Option 1, Direct Adjustment" and "(b) Mechanical normalization pass" during this session, with final sign-off ("yes") on the complete proposal.
**Date:** 2026-07-06.
