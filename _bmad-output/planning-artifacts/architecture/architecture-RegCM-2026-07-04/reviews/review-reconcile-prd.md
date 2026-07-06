# Reconciliation: ARCHITECTURE-SPINE.md vs. prd-RegCM-2026-07-04/prd.md

Note: the 5 background subagents dispatched for the reviewer gate all failed on a
shared session-limit API error before producing any output. This review was done
inline by the orchestrating session instead, per the reviewer-gate fallback
("if subagents are unavailable, run sequentially").

## Verdict

The spine reconciles cleanly with the PRD's Features, FR numbers, and Phased Scope.
Three real gaps found, all fixable without contradicting anything already decided.

## Findings

1. **(Medium) Boundary-condition guardrail missing.** PRD Constraints and
   Guardrails states: "Boundary-condition code is currently live experimental
   territory... FR-34's boundary-condition/ICBC input-I/O profiling must flag
   findings for regcm5-dev's review rather than silently 'fixing' or 'optimizing'
   anything it touches there." FR-34 (I/O profiling across all paths, including
   boundary-condition/ICBC input) falls squarely under the spine's own
   Capability Map row "4.2 I/O Scaling and Optimization." Nothing in the spine
   carries this guardrail forward, so a future FR-34 implementer working only
   from the spine would not be warned. This is confirmed independently from
   project-context.md too (see the companion review).

2. **(Low) AD-7's `Binds` cites FR-12 incorrectly.** FR-12 is "configurable
   GPU target architecture" (making `PGI_GPU_ARCH` a configure-time option),
   not the `--enable-openacc-managed`/`--enable-openacc-stdpar` memory-mode
   choice AD-7 actually governs. Likely drifted in from a Structural Seed
   sweep touching the same `configure.ac` area. Should be removed or
   corrected.

3. **(Low) Capability → Architecture Map omits Feature 4.9** (GitHub CI/CD
   Pipeline, FR-31/FR-32) even though AD-4's own `Binds` line cites FR-31/32
   directly. Every other AD-bound feature has a Capability Map row; 4.9 should
   too, for internal consistency.

4. **(Informational, no fix needed)** Cross-Cutting NFR "DEBUG-only
   instrumentation overhead: FR-1-FR-3's timing instrumentation must add zero
   overhead to non-DEBUG production builds" is directly relevant to AD-17 (I/O
   timer naming) but isn't restated there. Cross-referenced with
   project-context.md's Debug facility rules in the companion review — treating
   as one confirmed finding there, not double-counting here.

5. **(Informational, no fix needed)** regcm5-dev's sole-scientific-sign-off
   authority and the login-node fair-use guardrail are organizational/process
   facts, not technical build-divergence risks — reasonable that the spine
   doesn't restate them as ADs.

## Not a gap

- Features 4.4 (External Coupling), 4.5 (Namelist/Build/Compiler hardening),
  4.6 (Documentation) are legitimately absent from the Capability Map: none of
  their FRs carry a "two independently-built units could diverge
  incompatibly" risk this spine's altitude needs to fix (FR-20's NVHPC
  compiler-identity fix is a quiet prerequisite for AD-14/AD-15's
  vendor-distinct build matrix, worth a one-line footnote but not a new AD).
- FR numbering, phase assignment, and tolerance values (0.1%/5%) in AD-1/AD-13
  match the PRD verbatim.
