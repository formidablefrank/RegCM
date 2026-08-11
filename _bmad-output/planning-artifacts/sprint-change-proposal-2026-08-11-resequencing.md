---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'moderate'
---

# Sprint Change Proposal: Epic and Story Resequencing

## 1. Issue Summary

franco requested a full reorganization of the backlog's epic order: group related stories in an epic, and prioritize testing, then containerization, then CI, then instrumentation, then documentation, then contribution guidelines, then refactoring, then GPU offloading, then remaining epics — with the explicit rule that epics/stories carrying dependencies should be scheduled later. This is qualitatively different from the four earlier Sprint Change Proposals today: it reorganizes the existing 12-epic backlog rather than adding new scope.

**Mechanics decision**: epic, story, and FR numbers were kept stable; `epics.md`'s epic *sections* were physically reordered to reflect the recommended execution sequence. This mirrors the PRD's own stated rule that FR IDs "remain stable references... even if features are reorganized — the ID is the stable reference, not its position" (PRD §0), applied the same way to epics. Renumbering every epic and rewriting the ~30+ cross-references that already exist across `prd.md`, `epics.md`, and `ARCHITECTURE-SPINE.md` (e.g. "Epic 3's Story 3.4," "builds on Epic 2's regression tool") would have carried materially higher risk of breaking a reference for no benefit the stable-ID approach doesn't already provide.

## 2. Impact Analysis

**Epic Impact:** All 13 epics affected by position; two structural changes:
- **Epic 4's Story 4.6 extracted into a new Epic 13** (Community Contribution Process), splitting franco's "documentation" and "contribution guidelines" priorities into two epics matching two priority tiers, rather than one epic covering both.
- **Epic 6 elevated** ahead of its literal "remaining epics" grouping — not named in franco's explicit list, but the original PRD itself states FR-20 (NVHPC compiler identity) is placed early "precisely because it unblocks any future NVHPC-specific work," i.e., Epic 7. Both of Epic 6's stories are low-risk and foundational.
- **Epic 11 (Quality Gates) placed immediately after Epic 6**, at franco's explicit request, ahead of both epics it depends on for two of its three stories (see Story Impact below).
- Epic 2 and Epic 9 (both "testing") were deliberately **kept as separate epics, sequenced adjacent** rather than merged — preserving the deliberate unit-vs-integration methodology distinction (AD-24/NFR-15) that a structural merge would have blurred.
- Epic 8 stays last, reaffirming the original planning session's own already-confirmed-with-franco decision — unaffected by this resequencing.

**Story Impact:** No acceptance criteria changed in substance. Five stories gained explicit deferred-until annotations reflecting dependencies that now fall later in the sequence than the story's own epic:
- Epic 9's Story 9.4 (unchanged from earlier today) — waits on Epic 4's Story 4.5.
- Epic 12's Story 12.3 (unchanged from earlier today) — waits on Epic 3 and Epic 10.
- Epic 11's Story 11.1 and Story 11.2 — their merge-blocking/Slurm-evidence-requirement halves wait on Epic 13's Story 13.1 (the pull-request template), which now sits after Epic 11 in the sequence.
- Epic 11's Story 11.3 — its dependency-scanning half waits on Epic 4's Story 4.5, which now sits after Epic 11.

These four Epic 11/13-related annotations are a direct, disclosed consequence of franco's explicit placement instruction — every dependency was checked against the final order, and these were the only violations found; both were flagged before executing, not discovered after.

**Artifact Conflicts:**
- `epics.md`: full reorder of the "Epic List" overview and all detailed epic sections; FR Coverage Map's FR-51/FR-52 entries updated from "Epic 4" to "Epic 13"; Epic 4's and Epic 9's blurbs updated for the story-count change and cross-epic dependency notes.
- `sprint-status.yaml`: reordered to match, `epic-13`/`13-1-...` added, `4-6-...` removed from `epic-4`'s list, deferred-until comments added.
- `ARCHITECTURE-SPINE.md`: one reference ("Story 4.6") updated to "Epic 13's Story 13.1" in the Capability → Architecture Map.
- `prd.md`: no FR/Feature content changed (Features are not epic-indexed); one new Assumptions Index entry recording this proposal's origin.

**Technical Impact:** None — planning artifacts only. `Epic 1`'s existing progress (`Story 1.1: done`, `Story 1.2: ready-for-dev`) was preserved exactly through the reorder, not reset.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, executed as a full-file rewrite of `epics.md` (given the number of independent section moves involved) rather than incremental edits, verified by re-deriving every recorded epic/story dependency against the final order before writing.

- Rollback: not applicable — nothing has been implemented against any epic yet, so nothing to unwind.
- MVP Review: not warranted — this changes sequencing, not scope.
- Effort: **Medium** — one large, carefully-verified rewrite plus matching updates to two smaller files.
- Risk: **Low as executed** (every original section's exact text was preserved; every dependency was individually checked against the new order; violations were disclosed and annotated rather than silently left broken) — would have been **high** had this been done as many small in-place edits given the number of interdependent cross-references, which is why a verified full-file reconstruction was used instead.

## 4. Detailed Change Proposals

Presented and approved as one consolidated proposal (franco's chosen review mode for this session), with one live adjustment during execution (Epic 11's placement, below).

### 4.1 Final Epic Order

| Position | Epic | Priority slot |
|---|---|---|
| 1 | Epic 2 — Automated Regression Infrastructure | Testing |
| 2 | Epic 9 — Contributor Testing Infrastructure | Testing |
| 3 | Epic 5 — Multi-Vendor Containers and CI Gate | Containerization + CI |
| 4 | Epic 1 — Profiling and Memory Evidence Baseline | Instrumentation |
| 5 | Epic 6 — Namelist and Build Hardening | *(elevated)* |
| 6 | Epic 11 — Performance, Memory-Safety, and Dependency Security Regression Gates | *(inserted at franco's request)* |
| 7 | Epic 4 — Documentation Modernization (minus Story 4.6) | Documentation |
| 8 | Epic 13 (new) — Community Contribution Process | Contribution guidelines |
| 9 | Epic 12 — Code Duplication Audit and Generic-Interface Consolidation | Refactoring |
| 10 | Epic 7 — Selective GPU Acceleration and Verification | GPU offloading |
| 11 | Epic 3 — Diagnostic, Restart, and Land-Model I/O Scaling | Remaining |
| 12 | Epic 10 — ADIOS2 I/O Backend Integration | Remaining |
| 13 | Epic 8 — External Coupling Modernization | Remaining, last |

**Status:** ✅ Applied — `epics.md` (full rewrite), `sprint-status.yaml` (reordered to match).

### 4.2 Epic 11 Placement — Live Adjustment During Review

Initial proposal placed Epic 11 after Epic 13 (once its real dependencies — Epic 4's Story 4.5, Epic 5, Epic 1's Story 1.6, and the future Epic 13's Story 13.1 — were all satisfied). franco requested it moved to immediately after Epic 6 instead. This creates two real dependency conflicts (Story 11.3 needs Epic 4's Story 4.5; Stories 11.1/11.2 need Epic 13's Story 13.1, both now later in the sequence) — flagged explicitly rather than silently resolved, and implemented as franco requested with all three of Epic 11's stories carrying disclosed deferred-until annotations for the halves that cannot start until their prerequisites land.

**Status:** ✅ Applied as franco's explicit final instruction, with disclosure annotations in both `epics.md` and `sprint-status.yaml`.

### 4.3 Story 4.6 Extraction into Epic 13

Split at franco's request to match "documentation" and "contribution guidelines" as two separate priority tiers rather than one epic covering both. Story renumbered 4.6 → 13.1 (content unchanged). Epic 4's blurb updated (six stories → five; FR-51/FR-52 removed from its FR list). All references to "Story 4.6" across `epics.md` and `ARCHITECTURE-SPINE.md` updated to "Epic 13's Story 13.1."

**Status:** ✅ Applied — `epics.md`, `ARCHITECTURE-SPINE.md`.

### 4.4 Epic 6 Elevation

Not named in franco's explicit priority list (which covers testing/containers/CI/instrumentation/documentation/contribution/refactoring/GPU, then "other epics"). Elevated on my own judgment, disclosed before executing: both stories are low-risk and foundational, and the original PRD's own Notes for Story 6.2 (FR-20) state it is placed early "precisely because it unblocks any future NVHPC-specific work" — i.e., Epic 7, which follows later in this sequence.

**Status:** ✅ Applied, flagged as a judgment call in the proposal presented for approval; franco did not object.

## 5. Implementation Handoff

**Scope classification: Moderate** — a full backlog reorganization touching every epic's document position and one epic's internal structure, but no new scope and no fundamental replan of vision or MVP.

**Routed to:** Product Owner / Developer role (regcm5-dev / franco). Epic 1 remains the active epic (`in-progress`, Story 1.2 `ready-for-dev`) exactly as before this resequencing — nothing about current in-flight work changed.

**Outstanding before implementation begins:**
- Anyone picking up Epic 11's Stories 11.1–11.3 should read their deferred-until annotations before starting — parts of each are genuinely blocked despite the epic's early position in the document.
- Epic 9's Story 9.4 and Epic 12's Story 12.3 carry the same kind of annotation, unchanged from earlier today.

**Success criteria:** `epics.md` reads top-to-bottom in the order above; `sprint-status.yaml` lists epics in the same order with Epic 1's existing progress intact; every cross-reference to an epic or story number elsewhere in `epics.md`, `prd.md`, and `ARCHITECTURE-SPINE.md` still resolves to the same content it did before this proposal — only its position moved, never its identity.
