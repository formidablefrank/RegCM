# Technical Fact-Check Review: PRD "RegCM5 HPC Modernization" + Addendum

Reviewed against:
1. `_bmad-output/project-context.md` (authoritative/ground truth)
2. `_bmad-output/planning-artifacts/research/technical-regcm5-hpc-architecture-and-gpu-porting-risk-analysis-research-2026-07-04.md`
3. `_bmad-source/implementation/regcm5-optimization.pdf` (Tica thesis; extracted to text/rendered figures for verification)

Files reviewed: `prd.md`, `addendum.md` (same directory).

Total findings: **7** (2 high, 2 medium, 3 low/moderate).

---

## Finding 1 — HIGH — GPU-porting reproducibility threshold (~0.2%) contradicts the authoritative source's own stated bound (0.1%)

**Location(s):**
- `prd.md` FR-25 (line 379): "...with the source thesis's measured bounds (`tas`/`ps` rMAD/rRMSE **~0.2%**, `huss` ~5%) as the accepted reference..."
- `prd.md` FR-37 (line 227): "`tas` and `ps` rMAD/rRMSE under **~0.2%**, `huss` under ~5%... pinned to the source thesis's measured bounds"
- `prd.md` FR-37 consequence (line 230): "...fails if `tas`/`ps` rMAD/rRMSE exceeds **~0.2%**..."
- `prd.md` SM-12 (line 522): "(`tas`/`ps` rMAD/rRMSE **<0.2%**, `huss` <5%)"
- `prd.md` Open Question 9 resolution (line 627): "...accepted at the source thesis's measured statistical bounds (`tas`/`ps` rMAD/rRMSE **~0.2%**, `huss` ~5%)"

**What it should say:** `project-context.md` (line 144, authoritative) states: "the thesis measured relative divergence **below 0.1%** for near-surface air temperature and surface pressure, and below 5% for near-surface specific humidity." The thesis's own Conclusions chapter (Ch. 6) states the identical figure verbatim: "After 7 model days, the numerical divergence remained **below 0.1%** for the near-surface air temperature and surface pressure while for the near-surface specific humidity remained within 5%." The addendum's own more granular citation of Ch. 5 (line 30) is consistent with this: tas rMAD/rRMSE 0.06%/0.17%, ps rMAD/rRMSE 0.008%/0.019% — the *worst* of these four numbers (tas rRMSE, 0.17%) is still under 0.2%, but calling the combined bound "~0.2%" doubles the headline figure (0.1%) that both the authoritative project-context.md and the thesis's own conclusion use, and is roughly 10x looser than ps's own individually measured bound (~0.02%).

**Why it matters:** This is a regression-test acceptance threshold (FR-37, enforced by SM-12) — every one of its five occurrences is internally self-consistent (no flip-flopping), but all five consistently misstate the bound relative to both cited sources. As written, FR-37's regression test would accept up to 2x more numerical drift in `tas`/`ps` than the project's own documented precedent permits, silently loosening the scientific-correctness bar the whole two-tier policy exists to enforce.

**Sources cited:** `project-context.md` line 144; thesis PDF Chapter 6 (Conclusions), and Chapter 5 (§5.2, §5.4) for the granular tas/ps numbers the addendum itself cites correctly.

---

## Finding 2 — HIGH — Feature 4.1 overgeneralizes the three-offload-strategy comparison from `getcape` alone to all four hotspots

**Location:** `prd.md`, Feature 4.1 description (line 79): "All four were already GPU-ported and benchmarked by the thesis (OpenACC, `do concurrent`, and a hybrid `do concurrent`+OpenACC-data-region strategy were **each tried and found comparably effective**), yielding a cumulative 7.10× speedup from these four fixes alone..."

**What it should say:** The thesis restricts the three-strategy comparison (pure OpenACC vs. pure `do concurrent` vs. hybrid `do concurrent`+OpenACC-data-region) to the `getcape` call site only: "We employ three different strategies to distribute the two outer most loops [of `getcape`] among GPU threads: i.) Using OpenACC directives, ii.) Using `do concurrent` construct, and iii.) using `do concurrent` construct with an OpenACC data directive" (thesis, ~p.27, §3.1–3.3; Fig. 3.5 caption: "Three GPU implementations are compared... [for] the coupled RegCM5–CLM4.5 simulations"). `interp1d_r8` and `heatindex` were offloaded via **OpenACC only**: "In this section, we give the details for **offloading using OpenACC** the call sites for `interp1d_r8` and `heatindex`" (thesis §3.5). The `mod_clm_hydrology2` memset fix was a compiler-codegen workaround (explicit loop under `!$acc loop seq`), not a three-strategy comparison at all.

The addendum's own "Technical Lessons" section (line 22) correctly scopes this claim: "All three strategies tried... delivered comparable speedups **for `getcape`**... The pattern actually merged into the codebase is pure OpenACC (per `project-context.md`), not `do concurrent` or the hybrid." This directly contradicts the PRD body's "all four... each tried."

**Why it matters:** This is a factual claim about what the source thesis actually tested, used to justify treating all four hotspots as equally well-validated across offload strategies. Only `getcape` received that validation; the PRD overstates the evidence base for the other three.

**Sources cited:** thesis PDF §3.1–3.5, Fig. 3.5; `addendum.md` line 22 (self-contradicts `prd.md` line 79).

---

## Finding 3 — MEDIUM — Stale references to retired FR-36

**Location(s):**
- `prd.md` FR-8 scope note (line 180): "the four hotspots already ported under **FR-35/FR-36** use OpenACC directly..."
- `prd.md` FR-35 body (line 215): "...record their location for FR-8's cross-vendor check and **FR-36's reproducibility work**."
- `prd.md` (line 221): "#### ~~FR-36: Restore bit-exact reproducibility for the four already-ported GPU hotspots~~ — **Retired**"

**What it should say:** FR-36 is explicitly retired (its own heading is struck through two lines after FR-35, and Phase 3's list at line 495 also shows it struck through). FR-36 never described porting work in the first place (its retired scope was "restore bit-exact reproducibility," an action the resolution of Open Question 9 rendered moot) — it should not be cited as a co-source of "already ported" work (FR-8, line 180) or as the FR that will do "reproducibility work" going forward (FR-35, line 215). Per the doc's own resolution, **FR-37** is the FR that now owns the reproducibility regression test.

**Why it matters:** Both references are dangling pointers to a retired requirement, left over from before FR-36 was struck. A reader following FR-8 or FR-35's cross-references would look for GPU-porting or reproducibility work in a requirement the document itself says does not exist.

**Sources cited:** internal to `prd.md` (self-contradiction between lines 180/215 and line 221).

---

## Finding 4 — MEDIUM — SM-10 and SM-11 are absent from §7 with no explanation

**Location:** `prd.md` §7 Success Metrics (lines 512–533). The Primary list runs SM-1, SM-2, SM-3, SM-9, SM-4, SM-7, SM-8, SM-12; Secondary runs SM-5, SM-6, SM-13; Counter-metrics run SM-C1, SM-C2. **SM-10 and SM-11 do not appear anywhere in `prd.md` or `addendum.md`.**

**What it should say:** Unlike FR-36, which is explicitly kept in the document with a strikethrough heading and a "Retired" note explaining why (line 221) and cross-referenced from Open Question 9's resolution, SM-10 and SM-11 are simply missing — no strikethrough, no retirement note, no renumbering statement. §0's stated convention that FR numbering is stable "even if features are reorganized" (line 12) has no equivalent statement for SM numbering, so this reads as an unexplained gap rather than a deliberate, documented one. This confirms the prior partial review's observation: the omission is real, not a false alarm, and as currently written it is unexplained.

**Recommendation:** Either restore SM-10/SM-11 (if they were meant to validate something — e.g., a metric for FR-19 memory-growth or FR-11 halo-exchange investigations currently has no SM at all), or add an explicit "retired"/"renumbered" note matching the FR-36 treatment.

**Sources cited:** internal to `prd.md` (completeness gap, not a source mismatch).

---

## Finding 5 — LOW/MEDIUM — Addendum's "three HPC platforms beyond Leonardo" is self-contradictory

**Location:** `addendum.md`, "Multi-Platform Performance Portability" section (line 71): "The source thesis also benchmarked the GPU-enabled CLM4.5-coupled configuration across **three HPC platforms beyond Leonardo** (MareNostrum 5 ACC, **Leonardo Booster**, ORFEO H100)..."

**What it should say:** Listing "Leonardo Booster" as one of the platforms "beyond Leonardo" is self-contradictory — Leonardo Booster is Leonardo. The thesis states: "We also studied the performance portability of the coupled configurations across **two other platforms** running on H100 GPUs" (Ch. 6, Conclusions) — i.e., Leonardo (the original A100 baseline) plus two additional platforms (MareNostrum 5 ACC, ORFEO H100), three platforms total, only two of which are "beyond Leonardo." `prd.md`'s Open Question 10 (line 628) phrases this correctly ("benchmarked performance portability across three HPC centers," without the contradictory "beyond Leonardo" qualifier).

**Sources cited:** thesis PDF Chapter 6 (Conclusions).

---

## Finding 6 — LOW — Four hotspot percentages presented as one simultaneous breakdown, but are from three sequential post-fix profiles

**Location:** `prd.md`, Feature 4.1 description (line 79): "The confirmed hotspots, **in order of wall-clock share**, are: (1) `getcape`... **54%**... (2) ... memset... **~20%**; (3) `interp1d_r8`... **~12%**; (4) `heatindex`... **~8%**."

**Context:** Each individual number is thesis-sourced and accurate (54% and 20% both appear verbatim in the thesis's own Conclusions chapter; 12% and 8% appear verbatim in §3.4–3.5), but they are not measurements from one single profile snapshot. Per the thesis: the *original* combined profile (Fig. 2.6) shows `getcape` at 37% and the memset at 19–20% (Hotspot 1) simultaneously. `getcape`'s **54%** figure is specifically measured *after* the memset hotspot had already been eliminated (Fig. 2.7 caption: "after removing the hotspot 1... the call site for the `getcape` subroutine... now takes up a significant 54%"). `interp1d_r8` (12%) and `heatindex` (8%) are from a still-later profile, taken after `getcape` itself was also offloaded (§3.4: "In the absence of the previous two major hotspots, we noticed new stack plateaus... Hotspot 3... 12%... Hotspot 4... 8%"). Presenting all four side by side "in order of wall-clock share" (54+20+12+8 ≈ 94%, suggestive of a single decomposition) risks implying a simultaneous breakdown that doesn't match the sequential elimination methodology the thesis actually used.

**Recommendation:** Not a numeric error per se — worth a one-clause qualifier noting these are successive "next-largest-hotspot-after-the-previous-fix" measurements, not one simultaneous profile.

**Sources cited:** thesis PDF Figs. 2.6, 2.7, §3.4; thesis Conclusions (Ch. 6).

---

## Finding 7 — LOW — PRD/addendum never use the actual merged procedure name (`getcape_new`)

**Location:** Throughout `prd.md` (Glossary line 60, FR-35 line 215, FR-8 line 180) and `addendum.md` (line 20), the ported CAPE/CIN procedure is referred to only as "`getcape`."

**What it should say:** `project-context.md` (lines 95–97, 210) explicitly and repeatedly names the merged, offloaded, `public`, `pure` procedure **`getcape_new`** — confirmed directly in the repository: `Share/mod_capecin.F90` declares both `public :: getcape` (the original, non-`pure` subroutine, line 394) and `public :: getcape_new` (the `pure` offloaded version, line 94), and the live call site in `Main/mod_output.F90` (lines 1082, 1099) calls `getcape_new`, not `getcape`. (The thesis's own prototype code uses a third name, `getcape_gpu`, for its listings — none of the three documents agree on the name of the offloaded procedure, but only `project-context.md`'s `getcape_new` matches what is actually in the tree today.)

**Why it matters (minor):** Low practical risk since a search for "getcape" also matches "getcape_new," but an implementer executing FR-35 ("confirm each of the four ports compiles... record their location") who searches strictly for a symbol named `getcape` rather than `getcape_new` could be misled about which subroutine is the actual offloaded one.

**Sources cited:** `project-context.md` lines 95–97, 210; repository `Share/mod_capecin.F90` (lines 27–28, 94, 394); `Main/mod_output.F90` (lines 1082, 1099).

---

## Items explicitly checked and found CLEAN (no residual defect)

- **`do concurrent` vs. OpenACC for the four ported hotspots (task item 1):** No remaining claim anywhere in `prd.md`/`addendum.md` that the four hotspots (`getcape`/`getcape_new`, `mod_clm_hydrology2`, `interp1d_r8`, `heatindex`) use `do concurrent` as their *merged* offload mechanism. FR-8's scope note and the addendum's "Correction" paragraph both correctly state the merged pattern is OpenACC (`!$acc parallel loop` + `!$acc routine seq`), consistent with `project-context.md`.
- **`public`-declaration-blocks-offload claim (task item 2):** Only one mention (`addendum.md` line 20), and it correctly attributes the `public`-removal constraint to the `do concurrent` variant only, explicitly stating `getcape_new` remains `public` and offloads successfully under the merged OpenACC pattern. No stale claim requiring `public` removal survives.
- **Two-tier reproducibility policy narrative (task item 3, apart from Finding 1's number):** FR-25, FR-36 (retired, struck through), FR-37, SM-12, SM-C1, the Risk Register row, and Open Question 9 are all narratively consistent with the final resolution (CPU-only bit-exact by default; CPU-to-GPU porting specifically statistical, per thesis-measured bounds). The only defect is the numeric one in Finding 1.
- **I/O slowdown figures:** "at 800 CPU cores: sequential 3.7 h vs. HDF5-parallel 7.7 h vs. PnetCDF-parallel 4.0 h" (FR-34, addendum) matches Fig. 2.4 of the thesis exactly (verified by rendering the page).
- **Speedup factors:** 7.10× (cumulative from the four fixes, relative to initial) and 14.17× (with further unpublished optimization) both match the thesis's Conclusions chapter and Fig. 3.4/4.1 verbatim.
- **Compiler support table claim** (GNU `gfortran` has no `do concurrent` GPU path; Intel `ifx` offloads via OpenMP backend to Intel GPUs): matches thesis Table 1.2 exactly.
- **Superlinear scaling claim** (>100% efficiency relative to 4-GPU baseline, MareNostrum 5 and Leonardo, 4–16 GPUs): matches thesis Ch. 4 text.
- **FR-9's reference to FR-4's data:** consistent — FR-4 is the aggregating baseline report that subsumes FR-1's RRTMG-specific measurement; no contradiction found.
