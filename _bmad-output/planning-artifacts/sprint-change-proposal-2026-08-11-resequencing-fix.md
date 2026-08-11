---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'minor'
---

# Sprint Change Proposal: Epic 11 Placement Correction

## 1. Issue Summary

franco asked whether the current epic/story dependencies and groupings still made sense, after five Sprint Change Proposals today, and authorized a rearrangement "to the best of your knowledge" if not. A fresh, systematic audit — grepping every dependency phrase in `epics.md` and checking it against the actual current position of its target — found the answer was **no, not fully**: Epic 11's placement (position 6, immediately after Epic 6) violated franco's own stated rule ("epics and stories with dependencies should be done later") for three of its own three stories, all depending on epics that sat later in the sequence (Epic 4's Story 4.5, Epic 13's Story 13.1).

This was a known, disclosed trade-off from the prior resequencing session — franco explicitly requested that placement despite the flagged conflict — not a new discovery. Given the fresh request to re-audit and fix, and given the original recommendation (Epic 11 positioned after Epic 13, where all four of its dependencies are satisfied) carried zero such violations, the fix is to move Epic 11 back.

## 2. Impact Analysis

**Epic Impact:** Only Epic 11 moves — from position 6 (right after Epic 6) to position 8 (right after Epic 13, right before Epic 12). No other epic's position changes.

**Story Impact:** All three of Epic 11's stories (11.1, 11.2, 11.3) had a "deferred until X lands" acceptance criterion each, added when the position-6 placement made that split necessary. With the epic moved so every dependency now precedes it, those three acceptance-criteria blocks are removed — not because the underlying requirement changed, but because the condition they existed to state no longer applies.

Two other dependency exceptions were checked and confirmed to remain genuinely inherent, not fixable by any reordering:
- Epic 9's Story 9.4 (needs Epic 4's Story 4.5) — Epic 9 sits early ("testing"), Epic 4 sits later ("documentation"); no placement of either epic satisfies both priorities and this dependency simultaneously.
- Epic 12's Story 12.3 (needs Epic 3 and Epic 10) — both are "remaining epics," correctly sequenced late; moving Epic 12 later just for Story 12.3 would misplace Stories 12.1/12.2, which have no dependency issue at all, out of the "refactoring" priority slot for no benefit.

Both remain flagged in place, as before.

**Artifact Conflicts:**
- `epics.md`: Epic 11's full detailed section (blurb + 3 stories) relocated from between Epic 6 and Epic 4 to between Epic 13 and Epic 12; the three deferred-until acceptance criteria removed; Epic 11's blurb rewritten (no longer needs to justify sitting ahead of its dependencies); the "Epic List" overview section reordered and its Epic 6/Epic 11 deviation note rewritten to describe the correction; Epic 13's blurb updated to note both its dependents are now satisfied.
- `sprint-status.yaml`: `epic-11` block moved to match; its three stories' inline dependency comments removed; a new comment explains the move.
- No changes needed to `prd.md` or `ARCHITECTURE-SPINE.md` — neither references Epic 11's *position*, only its content, which is unchanged.

**Technical Impact:** None — planning artifacts only.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, a single-epic relocation plus removal of three now-unnecessary acceptance-criteria blocks, executed as targeted edits rather than a full-file rewrite (unlike the five-epic-plus-extraction rewrite in the prior session, this is small enough for precise in-place moves).

- Rollback: not applicable.
- MVP Review: not warranted.
- Effort: **Low** — one epic moved, three ACs removed, four blurbs touched.
- Risk: **Low** — every dependency was individually re-verified against the corrected order before finalizing; the fix strictly reduces the number of flagged exceptions (from five to two) without introducing any new one.

## 4. Detailed Change Proposal

### Epic 11 Relocation

**Before:** `Epic 2, Epic 9, Epic 5, Epic 1, Epic 6, Epic 11, Epic 4, Epic 13, Epic 12, Epic 7, Epic 3, Epic 10, Epic 8` — 3 dependency violations (all of Epic 11's stories).

**After:** `Epic 2, Epic 9, Epic 5, Epic 1, Epic 6, Epic 4, Epic 13, Epic 11, Epic 12, Epic 7, Epic 3, Epic 10, Epic 8` — 0 dependency violations for Epic 11; the 2 inherent exceptions (Story 9.4, Story 12.3) unchanged and still individually flagged.

**Rationale:** This is exactly the position originally recommended before franco's explicit override in the prior session; moving it back was authorized by this turn's explicit "rearrange again to the best of your knowledge" request, once the fresh audit confirmed the override's flagged trade-off was real and avoidable.

**Status:** ✅ Applied — `epics.md`, `sprint-status.yaml`.

## 5. Implementation Handoff

**Scope classification: Minor** — single-epic relocation, no new scope, no epic restructuring beyond position.

**Routed to:** Developer agent (regcm5-dev / franco) for direct implementation; already executed as part of this proposal.

**Success criteria:** `epics.md` and `sprint-status.yaml` list all 13 epics in identical order; grepping every dependency phrase in `epics.md` against the final position of its target shows exactly two exceptions (Story 9.4, Story 12.3), both individually annotated, and zero unannotated violations.
