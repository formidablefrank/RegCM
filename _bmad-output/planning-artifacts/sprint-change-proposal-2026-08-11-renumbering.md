---
project_name: 'RegCM'
user_name: 'franco'
date: '2026-08-11'
status: 'approved'
scope: 'moderate'
---

# Sprint Change Proposal: Story 9.4 Relocation and Full Epic/Story Renumbering

## 1. Issue Summary

franco requested two changes: (1) move Story 9.4 (`Tools/` unit and integration tests) into Epic 4 (Documentation Modernization), and (2) renumber all epics and stories to match. This reverses the "stable ID, reordered position" convention adopted in the two prior resequencing sessions today — franco explicitly asked for real renumbering this time, not another reorder-in-place.

Moving Story 9.4 was independently valuable beyond franco's stated reason: its only dependency was Epic 4's Story 4.5 (the `Tools/` Makefile/`requirements.txt` work), which is exactly what Epic 9's own blurb had been carrying as a flagged, unavoidable cross-epic exception since the second resequencing pass. Relocating the story into Epic 4 turns that cross-epic dependency into a normal in-epic one (Story 4.6 now simply follows Story 4.5, both in the same epic) — eliminating one of the two dependency exceptions that had been flagged all day, not just documenting it more clearly.

## 2. Impact Analysis

**Epic Impact:** Every epic's number changed except none stayed the same — the full 13-epic set was renumbered 1–13 in execution-sequence order (previously: stable IDs in a reordered document; now: sequential IDs matching document order exactly). Epic content, dependencies, and relative sequence are otherwise unchanged from the prior (second) resequencing pass.

**Story Impact:**
- Story 9.4 relocated into Epic 4 as its new 6th story, with its acceptance criteria simplified (the "deferred until Story 4.5 lands, regardless of Epic 9's position" framing is no longer needed — it's now a plain in-epic dependency, Story 4.5 before Story 4.6).
- Every other story's number changed to match its epic's new number (e.g. the story formerly "5.1" is now "3.1", since old Epic 5 is new Epic 3) — content, acceptance criteria, and relative story order within each epic are unchanged.
- Epic 12's Story 12.3 (now Story 9.3) remains the one true, inherent cross-epic dependency exception (needs Epic 11 and Epic 12, formerly Epic 3 and Epic 10) — not fixable by relocation the way Story 9.4 was, since it's genuinely about I/O-layer code both those epics touch, not a documentation-artifact dependency.

**Mechanics:** Given the number of cross-references this creates (every "Epic N", "Story N.M", "Epics N and M", "Stories N.M–N.M", "Story N.M/N.M" mention across `epics.md`, `prd.md`, `ARCHITECTURE-SPINE.md`, and `sprint-status.yaml`), this was executed via a script rather than freehand edits, built and verified in three stages:

1. A first automated pass correctly handled every singular "Epic N" and "Story N.M" mention (including headers, YAML keys, and FR-cross-references) using a collision-safe two-phase placeholder substitution — the naive alternative (sequential find-and-replace) would have double-converted numbers that are both a valid old ID and a valid new ID (e.g. old Epic 1 → new Epic 4, and old Epic 4 → new Epic 6, so a naive pass converting "1"→"4" would then wrongly re-convert that same "4" again under the "4"→"6" rule).
2. A second, deliberately narrower pass targeted multi-number references sharing one "Story"/"Epic" word — `Story 5.1/5.3`, `Stories 12.1/12.2`, `Epics 3 and 7`, `Stories 7.1–7.7`, etc. — which the first pass's regex couldn't see, since there's no repeated "Story"/"Epic" word before the second number to anchor a match.
3. Running these as two separate sequential passes on already-mutated text reintroduced the exact double-conversion bug pass 1 was designed to avoid (verified by inspection, e.g. `Story 3.3/3.4` was mis-converted to `Story 8.3/11.4`). The fix was consolidating both pattern sets into one script, applied once to the pristine original text, all placeholders resolved together at the end.

A handful of patterns were deliberately left for manual, by-hand review rather than automated: dash-number-range mentions of old epics that become non-contiguous after remapping (`Epics 1–8`, rewritten as prose since the mapped set `{1,3,4,5,6,10,11,13}` isn't a range), and one 4-item list (`Epics 4, 9, 10, and 13` → `Epics 2, 6, 7, and 12`, re-sorted ascending).

**Artifact Conflicts:** `epics.md` (epic/story headers, Epic List overview, FR Coverage Map, all cross-reference prose), `prd.md` (Assumptions Index cross-references), `ARCHITECTURE-SPINE.md` (Capability → Architecture Map), `sprint-status.yaml` (epic/story keys and inline comments) — all four renumbered consistently. FR-N, AD-N, and NFR-N identifiers were never touched (verified byte-for-byte identical before/after) — only epic and story identifiers changed.

**Technical Impact:** None — planning artifacts only. Epic 4's (formerly Epic 1's) in-flight progress — `Story 4.1: done`, `Story 4.2: ready-for-dev` — was preserved exactly through the renumbering.

## 3. Recommended Approach

**Selected: Option 1 — Direct Adjustment**, executed as a verified, scripted transformation rather than manual edits, given the reference density involved.

- Rollback: not applicable.
- MVP Review: not warranted.
- Effort: **Medium-High** — building and debugging a collision-safe renumbering script, catching and fixing the sequential-pass bug, and exhaustively auditing every remaining match by hand.
- Risk: **Low as verified** — every FR/AD/NFR reference confirmed byte-identical before/after; every epic and story cross-reference individually re-checked after the fix; line counts and story counts (52, unchanged) confirmed stable; `epics.md` and `sprint-status.yaml` confirmed to list epics in identical order.

## 4. Detailed Change Proposal

### Story 9.4 → Epic 4's Story 4.6

**Rationale:** Its only dependency, Story 4.5, already lives in Epic 4. Relocating it (rather than continuing to flag the cross-epic wait) eliminates the dependency entirely rather than documenting around it.

**Status:** ✅ Applied — content moved, AC simplified, both epics' blurbs and the FR Coverage Map (`FR-50`) updated.

### Full Renumbering (old → new)

| Old | New | Old | New | Old | New |
|---|---|---|---|---|---|
| 2 | 1 | 6 | 5 | 12 | 9 |
| 9 | 2 | 4 | 6 | 7 | 10 |
| 5 | 3 | 13 | 7 | 3 | 11 |
| 1 | 4 | 11 | 8 | 10 | 12 |
| | | | | 8 | 13 |

Execution order (unchanged from the prior resequencing pass, now expressed as the epics' actual numbers): 1 (regression infra), 2 (unit testing), 3 (containers+CI), 4 (instrumentation), 5 (namelist/build), 6 (documentation), 7 (contribution process), 8 (quality gates), 9 (refactoring), 10 (GPU), 11 (I/O scaling), 12 (ADIOS2), 13 (external coupling, last).

**Status:** ✅ Applied — `epics.md`, `prd.md`, `ARCHITECTURE-SPINE.md`, `sprint-status.yaml`, all verified consistent.

## 5. Implementation Handoff

**Scope classification: Moderate** — a mechanical but pervasive identifier change across four documents; no scope, dependency structure, or content change beyond Story 9.4's relocation.

**Routed to:** Product Owner / Developer role (regcm5-dev / franco). Epic 4 (formerly Epic 1) remains the active epic with its progress intact.

**Outstanding before implementation begins:** Anyone with an external reference to the old numbering (notes, a browser tab, a half-written story file) should re-resolve it against the new numbers — the mapping table above is the authoritative old→new key.

**Success criteria:** `epics.md` and `sprint-status.yaml` both list epics 1–13 in identical order; every FR/AD/NFR reference is byte-identical to before this proposal; grepping both files for any remaining multi-number Epic/Story reference finds none that weren't individually verified correct.
