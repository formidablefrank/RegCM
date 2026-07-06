# Rubric Walker Review: ARCHITECTURE-SPINE.md

(Background subagent for this lens failed on a session-limit API error before
producing output; done inline instead, per the reviewer-gate fallback.)

## Verdict

Strong spine overall -- every checklist item passes except the boundary-condition
guardrail gap already surfaced by both reconciliation passes; no new findings
beyond what those two turned up, plus two small mechanical observations below.

## Checklist walk

- **Fixes the real divergence points, misses none that matter**: PASS. All
  nine coaching-session topics (CPU baseline, MPI/threading, I/O scaling,
  GPU-candidate selection, test strategy, reproducibility, profiling,
  build matrix, phased plan) have a corresponding AD or an explicit,
  reasoned Deferred entry.
- **Every AD's Rule is enforceable**: PASS. Each Rule is checkable against
  either code (AD-6, AD-12 cite exact file:line evidence), a script's actual
  behavior (AD-9, AD-10, AD-16 -- all tested this session), or a documented
  external source (AD-15, AD-18). AD-5's rule ("no fixed formula") is a
  policy rule rather than a mechanism, but it's still falsifiable (a future
  proposal citing an undocumented scoring formula would violate it).
- **Nothing in Deferred is secretly load-bearing right now**: PASS, given
  regcm5-dev's stated priority ordering (I/O/performance first). Halo-exchange
  GPU-direct and the FR-3/FR-33 instrumentation implementation are both
  genuinely inert until later-phase work resumes; the $FAST retention risk
  is real but has no available "rule" beyond flagging it (see note below).
- **Named tech verified-current**: PASS for everything newly asserted this
  session (GCC 16.1, Intel oneAPI 2026.0/ifx, NVHPC Container Guide 26.3 --
  see review-web-verification.md). Inherited stack versions (HPC-X 2.25,
  CUDA 12.9, HDF5/netCDF/PnetCDF versions) were pre-existing project-context
  facts, not re-verified this session -- reasonable, they weren't this
  session's claim to make.
- **Ratifies brownfield, doesn't contradict it**: PASS (see
  review-reconcile-project-context.md).
- **Covers the PRD's capabilities**: MOSTLY PASS -- see the boundary-condition
  guardrail gap and the missing Feature 4.9 Capability Map row
  (review-reconcile-prd.md findings #1 and #3).
- **Operational/environmental envelope not silently skipped**: PASS. Structural
  Seed covers HPC storage topology ($FAST/$WORK) and Slurm partitions --
  the actual "infra/deployment" envelope for a batch HPC scientific model.
  No cloud/deployment-environment concept applies here, so there's nothing
  further to add.
- **Diagrams valid mermaid, non-empty**: PASS. The one dependency-direction
  graph has 9 declared nodes and 11 edges, all node IDs consistent, valid
  `graph TD` syntax.
- **No placeholder text / leftover template comments**: PASS, confirmed by
  `lint_spine.py` (0 findings) and a manual read-through.

## Findings (beyond what reconciliation already surfaced)

1. **(Low) AD-16's `Binds` line reads "manage_baseline.py, regression_diff.py,
   FR-31's CI integration"** -- fine as written, but since FR-31 doesn't
   itself mandate an exit-code scheme, it's worth being clear in the Rule
   that this convention is *this program's own* choice for its tooling, not
   an FR-31 requirement being satisfied. Cosmetic; not worth a structural
   change, just noting for awareness.
2. **(Low) The Capability Map's row order roughly follows PRD feature
   numbering (4.1, 4.2, 4.3, 4.7, 4.8) with a gap at 4.4-4.6** -- once 4.9 is
   added (per the PRD reconciliation), consider whether to note explicitly
   that 4.4/4.5/4.6 are intentionally absent (one line) so a reader doesn't
   wonder whether they were missed. Optional polish, not a correctness issue.
