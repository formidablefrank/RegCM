---
name: validate-port
description: Validate a GPU port against the correct numerical tier
code: VP
added: 2026-07-05
type: prompt
---

# Validate a Port

The outcome is proof — not an assertion — that a GPU port preserves the numerical behavior the project actually requires for that field: bit-exact by default, or the established statistical bounds (`tas`/`ps` rMAD/rRMSE under ~0.1%, `huss` under ~5%, over a 7-model-day run) if the field is already accepted under the GPU-porting statistical-tolerance precedent. A port that "compiles and runs" is not validated.

Run `Tools/Scripts/TestingAndBenchmarking/regression_diff.py` against a trusted baseline for the affected field(s), at more than one process count if the routine touches stencil/halo code. State which tier applies and why — never leave a reviewer guessing which bar a result was checked against. If the NVHPC `autocompare` build option is available, try it as a first-pass host-versus-device check before the full regression run.
