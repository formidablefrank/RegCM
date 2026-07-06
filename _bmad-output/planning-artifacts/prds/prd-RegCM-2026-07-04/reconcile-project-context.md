# Input Reconciliation: project-context.md vs. PRD/Addendum

**Input checked:** `_bmad-output/project-context.md` (112 rules, `rule_count: 112`, status complete)
**Against:** `prd.md` + `addendum.md` (PRD: RegCM5 HPC Modernization, 2026-07-04)

## Method

Read all three documents in full. Enumerated every rule in project-context.md's six rule
sections (Language & Numerical, Architecture & Parallelism, Testing, Style, Workflow,
Critical Don't-Miss) and checked each against the PRD's Vision, Features 4.1-4.9, Cross-Cutting
NFRs, Constraints and Guardrails, Risk Register, and Open Questions, with particular attention
to the six items flagged in the task brief.

## Rules confirmed well-reflected (no gap)

- **Acceptance discipline (Build/Test/Numerical/Performance per change):** Explicitly restated
  in the PRD's Glossary ("Acceptance discipline"), Constraints and Guardrails, SM-1, and FR-10's/
  FR-13's/FR-14's consequences. "No time estimates" is honored structurally — §6 uses phase
  gates, not durations, with an explicit note ("solo-paced infrastructure work with no external
  launch deadline... phase gates, not a calendar, govern progression").
- **Bit-exact-by-default numerical rule:** Thoroughly reflected — Cross-Cutting NFRs, FR-25,
  FR-36, FR-37, SM-C1, and the Constraints section all restate the bit-exact default and require
  regcm5-dev's sign-off for any tolerance exception. FR-36 in particular correctly identifies the
  four already-merged GPU ports as a **live non-compliance** with this rule (statistical, not
  bit-exact, reproducibility), rather than accepting the thesis's measured divergence as a fait
  accompli — this is a faithful, even rigorous, application of the rule.
- **Four-vendor portability rule:** Reflected consistently (FR-8, Cross-Cutting NFRs, Portability
  guardrail, Non-Goals' AMD "where feasible" carve-out matches project-context.md's own wording).
- **"No CI exists" / "don't treat regression-tool work as a quick add-on":** Feature 4.7 is
  explicitly sized and flagged as the exception to Phase 1's "small and cheap" character (§4.7
  Notes: "should be resourced/estimated as such"; addendum "Notes on Phasing Rationale" quotes
  the governing rule almost verbatim: "this matches the governing project context's own explicit
  warning against treating regression-tool work as a quick add-on"). The PRD does not claim a
  working regression command already exists, and correctly distinguishes the general CPU-only
  regression-diff gap from the GPU-specific statistical-divergence workflow the thesis already
  built (FR-24 builds the former by hardening the latter's mechanism, not by conflating the two
  problems). This satisfies the rule.
- **"Scientific review means regcm5-dev's explicit sign-off":** Reflected repeatedly and correctly —
  Stakeholders and Approvals, Constraints and Guardrails, FR-27 (baseline updates), FR-36/FR-37
  (tolerance exceptions and threshold changes), all require regcm5-dev's explicit sign-off, matching
  project-context.md's "don't stall waiting for a review process that doesn't exist, and don't
  treat its absence as permission to skip the check."
- **Zero-overhead DEBUG instrumentation, mpi-serial compilability, published-contract flagging
  (OASIS/REGESM/CISM/BMI), namelist placeholder-path edge case:** all explicitly addressed
  (Cross-Cutting NFRs; FR-6; Risk Register's external-contract row; FR-18/FR-23).

## Gaps found

### 1. Addendum directly contradicts project-context.md's explicit correction on `getcape`'s `public` declaration

project-context.md is careful and specific here (lines 94-96): the **merged, reference** GPU-offload
pattern in this codebase is OpenACC (`!$acc parallel loop` / `!$acc routine seq`), and it states,
with an explicit parenthetical confirmation: *"A procedure offloaded this way must be `pure`; it
may remain `public` (confirmed: `getcape_new` is both `public` and offloaded successfully)."* It
then explicitly warns that a different constraint — an explicit `public` declaration blocking
kernel generation — is documented in the thesis only for a **`do concurrent`-based variant of the
same offload**, and *"does not apply to the OpenACC pattern actually merged here."* This is a
rule specifically written to prevent an agent from over-generalizing a thesis footnote to the
actual merged code.

`addendum.md`'s "Technical Lessons from the Source Thesis" section (line 20) states the opposite,
without that qualification:

> "Removing an explicit `public` declaration was necessary for `getcape` to offload successfully
> as a device kernel — an NVHPC-specific, non-obvious quirk with no equivalent documented
> behavior noted elsewhere. Any procedure marked `public` in its module and slated for offload
> should be checked against this."

This generalizes exactly the variant-specific constraint project-context.md pre-emptively
corrected, and turns it into a checklist item ("any procedure... should be checked against
this") that a future story (FR-8's cross-vendor verification, FR-9's RRTMG investigation, or
FR-35's verification pass) could act on — e.g., unnecessarily stripping `public` from an already-
working, already-offloaded procedure, or flagging a false positive against a currently-public,
currently-successful port. This is not a stylistic nit: it is a direct factual contradiction of a
rule project-context.md took care to state precisely, and it sits in the addendum section the PRD
tells implementers to treat as "hard-won constraints worth generalizing to any future porting FR
under this program (FR-9, FR-10, FR-11, FR-35)." Recommend correcting the addendum line to match
project-context.md's clarification (the `public`-blocks-kernel-generation constraint applies only
to the `do concurrent`-only variant, not the merged OpenACC pattern) before it propagates into
story-level guidance.

### 2. FR-10 (continuing MOLOCH GPU porting) omits the multi-process-count / stencil-halo regression rule

project-context.md (Architecture & Parallelism Rules, and again in Testing Rules) states: *"any
change to a stencil operation (advection, diffusion, anything with `i±1`/`j±1` neighbor access)
near a tile boundary must be regression-checked at more than one process count; a decomposition
bug can be invisible at `nproc=1`."* MOLOCH is RegCM5's dynamical core and, of every FR in this
program, the one most likely to touch exactly this kind of neighbor-access stencil code. FR-5
(diagnostic I/O) explicitly cites this rule in its own consequences ("verified at more than one
process count, per the project's stencil/parallel-code regression rule"), and FR-26 builds
general multi-process-count comparison capability into the regression-diff tool — but FR-10's
consequences ("ships with a commit/PR record stating Build, Test, Numerical, and Performance")
and SM-4 (which validates FR-8 and FR-10, but only in terms of cross-vendor parallelization) never
invoke this requirement for MOLOCH specifically. FR-8's cross-vendor check verifies a loop
*parallelizes*, which is a different property from *decomposition correctness at the tile
boundary*. As written, a MOLOCH GPU-porting change could satisfy every explicit FR-10/FR-8
consequence while never being checked at `nproc>1`, which is precisely the failure mode the rule
exists to prevent.

### 3. The "boundary-condition code is live experimental territory" rule is not carried into the PRD at all

project-context.md (Language & Numerical Rules) states: *"Boundary-condition code is currently
live experimental territory (active churn in recent history) — treat as higher-risk for
unsolicited changes; flag rather than silently 'fix' or 'optimize' it."* This rule does not
appear anywhere in the PRD's Risk Register, Constraints and Guardrails, or Non-Goals, even though
FR-34 explicitly brings boundary-condition/ICBC input I/O into this program's scope ("boundary-
condition/ICBC input reads (flagged as unprofiled in the technical research note)"), and this
repository's own recent commit history (visible at the top of this very session — "New attempt at
boundary condition," "Double filter," "Read pai from ICBC for moloch dynamical core") shows this
is not a hypothetical hazard but the actual, currently-active churn the rule warns about. FR-34 as
scoped is I/O profiling, not boundary-condition numerics, so it may not directly collide with the
rule — but the PRD gives no signal that a follow-on story growing out of FR-34 (or FR-9/FR-10,
which also sit near ICBC-adjacent code in the dynamical core) needs the explicit-flagging
treatment the rule requires rather than routine review. Recommend adding this as an explicit Risk
Register entry or Constraints caveat.

### 4. Dead regression-adjacent scripts are left in an unresolved, ambiguous state (minor)

project-context.md is explicit that `Tools/Scripts/BuildBot/testing.py` (dead Python 2) and
`Tools/Scripts/TestingAndBenchmarking/preproc-compare.py` (narrow, decade-old v3-vs-v4 ICBC tool)
are not usable and should be treated as "decorative." Feature 4.7 builds a new regression-diff
tool (FR-24-27) but never states what becomes of these two existing scripts — left in place,
deprecated, or removed. This is a smaller-scale version of the ambiguity the PRD itself refuses to
tolerate for BMI (FR-17 forces a resolved decision — implement to spec or remove — specifically
because "a broken, dormant 'contract' is worse than an honest absence of one, since it invites a
future contributor to assume it works"). The same reasoning applies to a dead regression script
that a future contributor might stumble on and assume is usable. Not a contradiction of any rule,
but a gap worth a one-line resolution (e.g., in FR-24's Out of Scope or Notes) for consistency
with the PRD's own logic elsewhere.

## Rules explicitly out of PRD's altitude (correctly not FR-level content, not gaps)

Module skeleton conventions, banned-legacy-Fortran enforcement, style/formatting rules (2-space
indent, license banner, array-constructor syntax), naming conventions, and the DEBUG-macro-guard
convention are all implementation-level rules appropriately left for story/implementation
guidance rather than PRD-level FRs. Their absence from the PRD is not a gap.
