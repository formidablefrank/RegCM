# Reconciliation: ARCHITECTURE-SPINE.md vs. project-context.md

(Background subagent for this lens failed on a session-limit API error before
producing output; done inline instead, per the reviewer-gate fallback.)

## Verdict

The spine's Design Paradigm and seed facts ratify project-context.md correctly
-- no contradictions found. One confirmed gap (shared with the PRD
reconciliation), one informational note.

## Findings

1. **(Medium, confirms PRD-reconciliation finding #1) Boundary-condition
   guardrail.** project-context.md states directly: "Boundary-condition code
   is currently live experimental territory (active churn in recent
   history)... treat as higher-risk for unsolicited changes; flag rather than
   silently 'fix' or 'optimize' it." This is a standing brownfield rule, not
   just a PRD-derived one, and it bears directly on the spine's own I/O-scaling
   scope (AD-6, Capability Map row 4.2), since FR-34 explicitly profiles
   boundary-condition/ICBC input reads. Two independent sources (PRD
   Constraints, project-context.md) now confirm this is a real gap worth
   fixing, not just noting.

2. **(Medium, confirms PRD-reconciliation finding #4) DEBUG-macro-gating /
   zero-overhead constraint.** project-context.md's Debug facility rules:
   "Guarded by the DEBUG compile-time macro... Default behavior is DEBUG
   disabled, debug_level = 0 -- don't change these defaults as a side effect
   of unrelated work" and the Performance gotchas section's general
   instrumentation-placement rules. AD-17 (I/O timer naming convention) binds
   FR-3/FR-33 -- exactly the DEBUG-gated instrumentation this rule governs --
   but doesn't restate that the instrumentation must add zero overhead when
   DEBUG is undefined. Worth folding into AD-17's Rule text directly, since
   it's the single most relevant existing rule to that AD's scope.

3. **(Informational, no fix)** The GPU-porting hazard rules (pointer-aliasing,
   automatic-array-allocation-in-device-kernels, helper-procedure module-scope
   requirements, macro-guarding accelerator paths) are all pre-existing
   project-context.md rules that AD-3 (accelerator escalation policy)
   correctly defers to rather than re-stating -- appropriate, since the spine's
   job is new invariants, not duplicating the entire fact base.

4. **(Informational, no fix)** manage_baseline.py and regression_diff.py
   themselves (not the spine text, the actual files) already carry the
   project's standard MIT license banner and were verified this session to
   run correctly under both the default login-shell python3 (3.6.8) and
   `module load python/3.11.7`, consistent with the project's Python-module
   convention. No spine-level fix needed; noted for completeness.

## Not a gap

- Style rules (2-space indent, vim modeline, `[...]` array constructors) are
  Fortran-specific and don't apply to the new Python tooling; not a spine
  concern.
- The Testing Rules section's "no working automated regression-diff tool
  exists" gap is exactly what this session's regression_diff.py addresses --
  positive confirmation, not a finding.
