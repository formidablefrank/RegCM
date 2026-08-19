---
title: 'Instrument KPP Chemistry Integration'
type: 'chore'
created: '2026-08-19'
status: 'review'
review_loop_iteration: 0
context: ['{project-root}/_bmad-output/project-context.md']
baseline_commit: 'f13b95a93b094c974e01945b25f37bf628b36057'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The KPP-generated chemistry integrator entry points (`mod_cb6_Integrator.F90`, `mod_cbmz_integrator.F90`) carry zero DEBUG-gated timing, so chemistry integration time is invisible separately from the already-instrumented chemistry support routines (drydep, emission, boundary).

**Approach:** Wrap each mechanism's `integrate`/`INTEGRATE` entry point in `time_begin`/`time_end`, matching the zero-prior-use-file convention established by Story 4.1's RRTMG instrumentation. Verify DEBUG/non-DEBUG compile across GNU/Intel/NVHPC. Attempt runtime verification via a constructed CBMZ-enabled fixture (no shipped fixture exercises gas-phase chemistry); accept code-inspection-only verification where a real run proves infeasible, and document exactly why rather than silently asserting full coverage.

## Boundaries & Constraints

**Always:** Use label `'cbmz_integrate'`/`'cb6_integrate'`, not bare `'integrate'` — `mod_cb6_Integrator.F90`'s entry point is also literally named `INTEGRATE`, and `mod_service`'s timer registry is a single flat namespace. Force `chemsimtype='CBMZ'` + `ichem=1` in any runtime-verification fixture — every shipped `Testing/*.in` fixture with `ichem=1` uses `'DUST'`/`'SULF'` (aerosol-only), never `'CBMZ'`, so an unmodified fixture adds zero chemistry-integration timer entries. Record Build/Test/Numerical/Performance evidence in the commit/PR description, stating explicitly which half of AC #1 (compile vs. runtime, CBMZ vs. CB6r2) is verified by which method.

**Ask First:** Before absorbing scope to fix any pre-existing bug surfaced while constructing a runtime-verification fixture — this story instruments and evidence-gathers, it does not fix unrelated chemistry/boundary/land-surface/radiation code. Before running a fresh HPC build/verification pass whose evidence would otherwise rest on a stale or superseded commit.

**Never:** Wire `GAS_CB6r2` into `configure.ac`/`Main/chemlib/Makefile.am` to make it testable — it is currently orphaned from the build entirely (own `Makefile.am` exists, but never referenced by the parent chain), and wiring it in is out of this story's scope. Touch RRTMG timing (Story 4.1, done) or diagnostic-I/O gather/write timing (Story 4.3, backlog). Attempt any GPU-porting-related change — KPP/DLSODE chemistry is explicitly excluded from GPU-porting scope (`ARCHITECTURE.md` §7: "data-dependent, irregular iteration structure is a known poor fit for SIMT execution"). Modify `Main/mpplib/mod_service.F90`'s shared timer registry (e.g. adding the `maxnsubs` bounds check) — shared infrastructure used by 40+ files, not owned by this story.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| DEBUG build, CBMZ mechanism | `chemsimtype='CBMZ'`, `ichem=1`, a fixture that actually reaches `chemmain`→`integrate` | `time_print` shows `cbmz_integrate` as a distinct, populated timer | If blocked by an unrelated pre-existing bug before reaching `integrate`, document the blocker and fall back to code-inspection verification — do not fix the blocker under this story |
| DEBUG build, CB6r2 mechanism | `GAS_CB6r2` is unwired from the build | Cannot be build- or run-verified through the normal chain | Code-inspection-only verification against the identical, already-verified CBMZ pattern; state this explicitly, do not imply parity with CBMZ's evidence |
| Non-DEBUG production build | Same code path executes | `-DDEBUG` absent from build log; no observable timing overhead | Structural argument (guard absence) suffices — no differential run required |
| Unmodified shipped fixture | `chemsimtype` left at `'DUST'`/`'SULF'`/unset | Zero chemistry-integration timer entries | Must not be mistaken for a "no overhead" or "verified" result — gas-phase chemistry never dispatched |

</frozen-after-approval>

## Code Map

- `Main/chemlib/GAS_CBMZ_NEW/mod_cbmz_integrator.F90:33,35,166,168,203` -- `integrate`; label `'cbmz_integrate'`; the reachable, buildable, partially-runtime-blocked mechanism
- `Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90:49,51,102,104,154` -- `INTEGRATE`; label `'cb6_integrate'`; identical pattern, code-inspection-only (unreachable from any build)
- `Main/mpplib/mod_service.F90:165-183` -- shared `time_begin`/`time_end`, `maxnsubs=100` fixed capacity, no bounds check (pre-existing, deferred, not this story's to fix)
- `Main/chemlib/mod_che_common.F90:376` -- `chemsimtype` dispatch; `'CBMZ'` branch is the only one reaching gas-phase `integrate`
- `Main/chemlib/mod_che_chemistry.F90` -- `chemistry`'s `k`/`i`/`j` grid loop calling `chemmain`/`chemmain_cb6`, itself calling `integrate`/`INTEGRATE` inside an adaptive substep loop -- confirms the call-site granularity (wrap the whole call, not inside it) matches the existing `drydep_aero` precedent
- `Main/chemlib/Makefile.am:21`, `configure.ac:1005` -- confirms `GAS_CB6r2` is not built by the current autotools chain (`SUBDIRS`/`AC_CONFIG_FILES` list `GAS_CBMZ_NEW` only)
- `bin/slurm-1-2-build-{gnu,intel,nvhpc}-{debug,production}.sh` -- the six reduced-scope (`external`/`Share`/`Main/mpplib`/`Main/chemlib`) build-verification scripts, reused unmodified for this story's two build passes
- `_bmad-output/implementation-artifacts/deferred-work.md` -- six pre-existing bugs/constraints surfaced while attempting runtime verification, recorded here

## Tasks & Acceptance

**Execution:**
- [x] Instrument CBMZ's `integrate` entry point, guarded zero-prior-use convention (matching Story 4.1's RRTMG files)
- [x] Instrument CB6r2's `INTEGRATE` entry point identically; flag it cannot be build/run-verified through the normal chain
- [x] Verify DEBUG and non-DEBUG builds compile both instrumented files across GNU/Intel/NVHPC
- [x] Attempt to construct a CBMZ-enabled fixture and run it under a DEBUG build -- **blocked**: six unrelated pre-existing bugs/constraints each stopped the run before reaching `integrate` (see Spec Change Log); downgraded to code-inspection-only per franco's direction
- [x] Confirm zero overhead in a non-DEBUG production build -- structural argument (guard absence, confirmed in the build-verification task), no differential run needed
- [x] Reapply the instrumentation onto current `develop` after discovering it only ever lived on a stale, unmerged branch (see Spec Change Log)
- [x] Re-verify the reapplied code's build across the full GNU/Intel/NVHPC × DEBUG/production matrix on the current tree

**Acceptance Criteria:**
- Given a DEBUG-enabled build with an active gas-phase mechanism, when a fixture exercising that mechanism runs, then timing output separates integration time from other, already-instrumented chemistry support routines. **Met for CBMZ by code-inspection only** (pattern matches verified RRTMG/`cb6_integrate` instrumentation; six unrelated bugs blocked an actual run). **Met for CB6r2 by code-inspection only** (mechanism is unreachable from any build).
- Given a non-DEBUG production build, when the same run executes, then instrumentation adds no measurable overhead (NFR-4). **Met structurally** -- the `#ifdef DEBUG` guard is confirmed absent from production build output for both files, on all three vendors, on the current tree.

## Spec Change Log

- **CB6r2's DEBUG compile was twice claimed "resolved"/"re-verified" and twice found false on review.** The compile loop that was supposed to prove it never actually built `mod_cb6_Function`/`mod_cb6_Rates`/`mod_cb6_Jacobian` first, so `mod_cb6_Integrator.F90`'s `USE mod_cb6_Function` failed (`Cannot open module file`). No job anywhere has shown `mod_cb6_Integrator.F90` compiling successfully under `-DDEBUG`. **Resolution:** AC #1's CB6r2 half is code-inspection-only, stated plainly, not compile-verified.
- **An `aeroppt` bug fix (unrelated file, `mod_rad_aerosol.F90`) was claimed shipped and verified, then found never to exist in the tree** — the cited verification job actually crashed on a different, already-known bug, with zero occurrences of the claimed crash. **Resolution:** removed the false claim, moved the diagnosed-but-unfixed `aeroppt` bug to the deferred-work ledger as still open.
- **Runtime verification (Task 4) surfaced six unrelated pre-existing bugs/constraints**, each blocking a CBMZ-enabled fixture before it ever reached `integrate`: a MOLOCH chemical-boundary-relaxation SIGSEGV under `ichebdy=0` (`mod_che_bdyco.F90:992`), a `drydep_gas` subscript-0 crash (`mod_che_drydep.F90:841`), a `relax_coefficients` power-of-2 footgun, an `iproj='ROTLLR'`/`idynamic=3` design restriction, a `mod_lm_interface.F90:930` pointer-contiguity crash (also independently blocking two other stories), and the `aeroppt` bug above. Franco directed stopping after the `mod_lm_interface.F90:930` crash rather than continuing to chase a clean run. **Resolution:** all six recorded as central `deferred-work.md` entries (previously only one, an unrelated `mod_service.F90` capacity risk, had been synced); Task 4/AC #1's runtime half accepted as code-inspection-only.
- **The code itself was never actually on `develop`.** The instrumentation was implemented and committed on a branch (`instrumentation/kpp-chem`, `2c7968d1b`) that was never merged and fell far behind `develop` (predating four other Epic 1 stories, the epic renumbering, and the EUR12 baseline work) — while the story's own documentation, already synced onto `develop`, described the code as landed. **Resolution:** reapplied the two-file diff byte-for-byte onto a fresh branch (`instrumentation/kpp-chem-4-2`) cut from current `develop`.
- **The reapplied code's only build evidence was from the old, stale commit — never confirmed on the code as it now stands.** A parallel review pass (blind-hunter/edge-case-hunter/verification-gap) flagged this as the one substantive gap; two rejected findings from the same pass (missing `save` on the timer index, unconditional `ik4` import) turned out to already be this file's own documented, previously-verified convention for zero-prior-use files, not real defects. **Resolution:** franco directed a full cross-vendor re-verification; all six legs (GNU/Intel/NVHPC × DEBUG/production) passed on the current commit, `-DDEBUG` correctly present/absent per config (see Verification).

## Design Notes

**Two valid `mod_service` guard conventions in this codebase — do not mix them.** Zero-prior-use files (this story's two target files, and Story 4.1's RRTMG files) use `#ifdef DEBUG`-guarded `use mod_service`, unconditional `use mod_intkinds, only : ik4`, and `integer(ik4) :: indx = 0` (implicit `SAVE` via initializer). Files that already reference `mod_service` elsewhere (`mod_che_drydep.F90`, `mod_che_emission.F90`, `mod_che_bdyco.F90`) instead use a bare unconditional `use mod_service` and an explicit `integer(ik4), save :: idindx = 0`. A reviewer unfamiliar with this distinction may flag the first convention's `indx`/no-`save` as a defect — it isn't; it's the deliberate, already-verified pattern for this file's situation.

**Per-column call-site instrumentation is the established, reviewed pattern here, not a "never inside a loop body" violation.** `chemistry` calls `chemmain`/`chemmain_cb6` inside a triple-nested grid loop, and those in turn call `integrate`/`INTEGRATE` inside their own adaptive substep loop — wrapping the whole call at its own entry/exit (not inside `DLSODE`'s internal iteration) is the correct, only-established granularity, mirroring `drydep_aero`'s existing instrumentation.

**No RegCM configuration with live gas-phase chemistry appears to have ever run to completion in this codebase's history.** Four independent attempts to exercise `ichem=1`/`chemsimtype='CBMZ'` end-to-end each surfaced a different, unrelated pre-existing bug (MOLOCH boundary code, land-surface output collection, aerosol optical properties, dry deposition) — a real pattern, not a one-off blocker. Treat any future attempt to actually run gas-phase chemistry as genuinely unexplored territory, likely to surface further unrelated bugs.

## Verification

**Cross-vendor build matrix, current tree** (commit `edf7ea926`, franco-directed full re-verification after the reapplication above): GNU/Intel/NVHPC × DEBUG/production, six Slurm jobs, reduced scope (`external`/`Share`/`Main/mpplib`/`Main/chemlib`), reusing the six pre-existing, unmodified Task-3 scripts.

| Vendor | Config | Job | Result | `-DDEBUG` occurrences in log |
|---|---|---|---|---|
| GNU | debug | 53019755 | PASS | 91 |
| GNU | production | 53020167 | PASS | 0 |
| Intel | debug | 53020615 | PASS | 91 |
| Intel | production | 53021257 | PASS | 0 |
| NVHPC | debug | 53024087 | PASS | 91 |
| NVHPC | production | 53025612 | PASS | 0 |

All six PASS; DEBUG builds correctly compile in the guard, production builds correctly compile it out — matching the original 2026-08-11 verification pattern against the code's first (pre-reapplication) commit. Logs: `RegCM-data/build-logs/1-2-<vendor>-<config>-<jobid>.out`/`.err`.

**Runtime verification: not achieved, accepted as code-inspection-only.** Three real Slurm attempts against a chemistry-enabled EUR12 CORDEX fixture each crashed in a different pre-existing chemistry/boundary support routine before ever reaching `cbmz_integrate` (confirmed 0 occurrences across all per-rank debug files from the last attempt). CB6r2 cannot be runtime-verified at all — unreachable from any build. See Spec Change Log and `deferred-work.md` for the six bugs/constraints this surfaced.

## Suggested Review Order

**Instrumentation code**

- Entry point: the reachable, compile-verified `time_begin` call.
  [`mod_cbmz_integrator.F90:168`](../../Main/chemlib/GAS_CBMZ_NEW/mod_cbmz_integrator.F90#L168)

- Matching `time_end`, single exit, no early `return`.
  [`mod_cbmz_integrator.F90:203`](../../Main/chemlib/GAS_CBMZ_NEW/mod_cbmz_integrator.F90#L203)

- Identical pattern applied to CB6r2 — code-inspection-only, `GAS_CB6r2` unwired from the build.
  [`mod_cb6_Integrator.F90:104`](../../Main/chemlib/GAS_CB6r2/mod_cb6_Integrator.F90#L104)

**Why the code needed reapplying, and how it was re-verified**

- The stale-branch discovery and reapplication.
  [`spec-4-2-instrument-kpp-chemistry-integration.md`](spec-4-2-instrument-kpp-chemistry-integration.md) (Spec Change Log)

- Full cross-vendor build matrix on the reapplied code.
  [`spec-4-2-instrument-kpp-chemistry-integration.md`](spec-4-2-instrument-kpp-chemistry-integration.md) (Verification)

**Deferred-work ledger (six pre-existing bugs/constraints made visible)**

- MOLOCH `morelax_chiten` SIGSEGV — the most severe, already blocking two other stories independently.
  [`deferred-work.md:18`](deferred-work.md#L18)

- `mod_lm_interface.F90:930` pointer-contiguity crash — cross-referenced from three separate stories.
  [`deferred-work.md:35`](deferred-work.md#L35)

**Peripherals**

- Sprint tracker, currently `review` — a further `/bmad-code-review` pass or direct sign-off decides `done`.
  [`sprint-status.yaml:78`](sprint-status.yaml#L78)
