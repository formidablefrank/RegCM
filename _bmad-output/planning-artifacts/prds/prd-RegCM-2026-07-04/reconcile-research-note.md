# Reconciliation: Technical Research Note → PRD + Addendum

**Source input:** `_bmad-output/planning-artifacts/research/technical-regcm5-hpc-architecture-and-gpu-porting-risk-analysis-research-2026-07-04.md`
**Checked against:** `prd.md`, `addendum.md` (prd-RegCM-2026-07-04)

## Method

Walked the research note section by section (Technology Stack, Integration Patterns, Architectural Patterns, Implementation/Hotspots, Research Synthesis incl. the 9-item Risk Register) and matched each distinct finding to its PRD/addendum destination. The known, intentional supersession (RRTMG hotspot ranking corrected by the Tica thesis) was excluded from gap consideration per instructions — it is explicitly and repeatedly acknowledged in PRD §4.1, §4.3, the Risk Register, and addendum's "Primary Technical References" and "Options Considered: GPU-Porting Strategy for RRTMG."

## Finding → PRD/Addendum Mapping (high-confidence matches, not repeated as gaps)

| Research note finding | PRD/Addendum destination |
|---|---|
| `do concurrent` sole loop construct; cross-vendor unevenness (GCC REDUCE, ifx, LLVM Flang, NVHPC maturity) | FR-8, Glossary, Risk Register row 1, Cross-Cutting NFRs |
| Serial gather-then-write I/O default, PnetCDF restart-only | FR-5/6/33/34, Glossary, Feature 4.2 description (with regcm5-dev's operational-experience correction, documented in addendum "I/O Correction Note") |
| RRTMG/KPP zero timing instrumentation | FR-1, FR-2, FR-3, Risk Register row 7, addendum "Why the Instrumentation Gap Matters" |
| ICON-A/PSrad precedent for RRTMG | FR-9, addendum "Options Considered: GPU-Porting Strategy for RRTMG," Risk Register row 3 (explicitly reframed as "unconfirmed rather than dismissed" post-thesis) |
| NVHPC misclassified as `COMPILER_PGI` | FR-20 |
| `PGI_GPU_ARCH="ccnative"` hardcoded, no override | FR-12 |
| AMD/AOCC has no configure-time hook | §5 Non-Goals ("AMD where feasible, not mandatory"), Open Question 4 |
| `assignpnt` pointer-aliasing as #1 GPU-residency hazard | Glossary, FR-9/10/11 scoping, addendum "assignpnt Pointer-Aliasing Mechanism," Risk Register row 2 |
| Halo exchange is host-buffer-only, HPC-X GPU-direct unexploited | FR-11, Glossary, Risk Register row 5 |
| BMI dormant/internally-inconsistent, guarded by undefined `DEVELOPMENT` macro, toy-model boilerplate | FR-17, addendum "Options Considered: BMI Resolution," Risk Register row 6, External Coupling Contracts table |
| OASIS3-MCT live/field-rich; REGESM live, independent field list, needs separate flagging | FR-13/FR-14, Glossary, addendum "Coupling Field Lists" |
| CLM3.5 vs CLM4.5/ECLM tiering | FR-15, Glossary, §5 Non-Goals |
| Namelist scalar validation solid, but path variables never existence-checked | FR-18 (near-verbatim: same variable names `dirglob`/`inpglob`/`dirter`/`inpter`/`dirclm`/`cmip6_inp`) |
| `init_mod_*`/`release_mod_*` lifecycle claim doesn't match code; actual pattern is `allocate_*`/`getmem`/`relmem` | FR-21 (applied to `MainDeveloperGuide.tex`), Risk Register row 8 — see Gap 2 below re: which document |
| `relmem` called at only 3 sites; workspace lives until process exit | FR-19 (memory-growth investigation, scoped as "confirm before fixing") |
| No CI, dead `BuildBot/testing.py`, manual NCO/CDO comparison only | Feature 4.7 (FR-24–27), Feature 4.9 (FR-31/32) |
| Intel→`dcgp_usr_prod`, NVHPC→`boost_usr_prod`, physically different partitions | Constraints and Guardrails ("HPC platform guardrail"), FR-4 |
| ICBC/boundary-condition input I/O not profiled, flagged as open item | FR-34, Glossary ("ICBC"), SM-9 (explicitly closes "the boundary-condition-I/O open item from the technical research note") |
| PnetCDF vs netCDF-4-parallel compression tradeoff | FR-5 "Out of Scope" note |
| Async pthread-backed NetCDF (`mod_async_netcdf.F90`) as alternative | FR-7 |
| `mpi-serial` must keep working unmodified | FR-6 |
| Confidence-level framing (high for code inspection, moderate for hotspot ranking, explicit not-papered-over limitation) | Mirrored structurally via `[ASSUMPTION]` tags + §9 Assumptions Index, and the FR-1 "Correction to the prior hotspot ranking" narrative |

## Gaps Found

**1. The F77 strided-slice contiguity-copy hazard downgrade is dropped entirely.**
Research note Risk Register row 8: the governing context's specific hazard example (`a(:,2:18:2)` passed to a legacy F77 routine silently making a contiguous copy) "has no confirmed instance in the current tree" and should be "downgraded from 'known defect' to 'pattern to watch for in new code'" — an explicit, named documentation-accuracy correction, parallel in kind to the `init_mod_*`/`release_mod_*` lifecycle correction (Risk Register row 9). The lifecycle correction was carried into the PRD (FR-21). The F77-hazard downgrade was not: it does not appear in FR-21's two named corrections (precision claims, module-lifecycle claims), anywhere else in Feature 4.6 (Documentation Modernization), in the Risk Register, or in the addendum. This is a low-severity item per the research note's own severity rating, but it is a distinct, explicitly-recommended correction that is silently absent rather than acknowledged as out of scope.

**2. Ambiguity about which document the lifecycle correction belongs to.**
The research note frames the `init_mod_*`/`release_mod_*` correction as a correction to **"the governing context"** (i.e., `_bmad-output/project-context.md`) — "worth correcting in the governing document" — not to `Doc/DeveloperGuide/MainDeveloperGuide.tex`. FR-21 applies the fix only to `MainDeveloperGuide.tex`. It's plausible both documents carry the same stale claim and fixing the Developer Guide is the intended, sufficient remediation, but nothing in the PRD confirms `project-context.md` itself was checked or corrected, and (per the same research-note framing) the F77-hazard correction from Gap 1 was *also* a "governing context" documentation item — reinforcing that this class of correction (fixing `project-context.md`, not just the Developer Guide) may be incompletely scoped by FR-21. Lower confidence than Gap 1 since `project-context.md`'s actual contents weren't available to verify directly.

## No other material gaps found

Every other distinct finding, risk-register row, and recommendation in the research note — including secondary/context-only items like the COSMO-CLM coupling-overhead comparison, the "no compiler-identity macros scattered in physics code" observation, and the `mpi_f08`-not-used note — either maps cleanly to an FR/section above, or was correctly treated as non-load-bearing background not requiring its own FR (verified these are absent from the research note's own Risk Register / Recommendation lists, so their omission is not a silent drop).

The RRTMG-hotspot correction, the I/O-burst-vs-sustained-cost correction, and the ICBC-input-I/O closure are all explicitly and traceably reconciled with sourcing and rationale — these are the intended model of "acknowledged supersession" the PRD/addendum use well throughout.
