# Epic 1 Context: Automated Regression Infrastructure

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

RegCM5 has no working automated regression-diff tool today: the legacy `testing.py` is dead Python 2, and `preproc-compare.py` only ever compared ICBC initial conditions between two old model versions. `regression_diff.py` and `manage_baseline.py` already exist and work; both were already committed to version control before this epic started (commit `238393c72` — corrected during Story 1.1, which found the epic's original "currently untracked" premise stale). This epic verifies and hardens both tools so that a single command replaces manual NCO/CDO comparison as the default way to check whether a change preserved RegCM5's numerical behavior. It is standalone and foundational: every later epic's Numerical and Test acceptance criteria become mechanically checkable only once this epic lands, rather than resting on ad hoc manual comparison.

## Stories

- Story 1.1: Verify and Commit the Regression-Diff Tool
- Story 1.2: Verify Multi-Process-Count Comparison
- Story 1.3: Retire the Legacy Regression Scripts
- Story 1.4: Establish Trusted Baselines for Testing/Fixtures

## Requirements & Constraints

- The tool must report field-by-field differences (MAD, RMSE, and their baseline-relative forms rMAD/rRMSE) against a trusted baseline — never a single pass/fail bit.
- Numerical policy is two-tier, not a sliding scale: CPU-only changes default to bit-exact (zero tolerance); CPU-to-GPU porting is accepted at measured statistical bounds (`tas`/`ps` rMAD and rRMSE under 0.1%, `huss` under 5%, over a 7-model-day run). A field not named in the tolerance table or an override defaults to bit-exact — this is the policy working as designed, not a gap.
- A per-field tolerance override file must be honored per field, without loosening any field left unspecified.
- Multi-process-count comparison must support at least `nproc=1` and `nproc=4` as the fixed minimum pair (RegCM5's auto-decomposition only performs a genuine 2D split at `nproc>=4`; below that, one direction's halo exchange is never exercised). This epic verifies that pair plus additional coverage at `nproc=16,64,196` — the higher counts are added coverage, not a replacement for the minimum pair, and a divergence appearing only at higher counts is still a real regression.
- The identical tolerance table applies across all process counts — no looser tier at higher rank counts.
- Baseline promotion must never silently overwrite: an existing baseline blocks a second promotion attempt unless an explicit override with a recorded reason is given.
- A trusted baseline must exist for at least the fixtures this program's own requirements exercise: I/O paths, MOLOCH GPU work, and coupling builds (OASIS3-MCT/REGESM).
- Success criterion for this epic (program-level): the regression-diff tool becomes the default regression-evidence method for every subsequent story in the program, replacing manual comparison — described in planning as the heaviest single item in the program's first phase.

## Technical Decisions

- Both tools live under `Tools/Scripts/TestingAndBenchmarking/`: `regression_diff.py` (flags: `--run-dir`, `--baseline-dir`, `--nprocs`, `--tolerance-file`, `--only-fields`, `--json`, `--report-file`) and `manage_baseline.py` (`promote`/`log` subcommands; `--nproc`, `--force` plus required `--reason`, `--archive-dir`/`--no-archive`). Both are already committed (`238393c72`); Story 1.1's scope narrowed to runtime verification and correcting a stale top-of-file comment that documented a `compare` subcommand the actual parser doesn't have.
- A `nproc-<N>/` subdirectory convention organizes any run/baseline/archive directory spanning multiple process counts; passing `--nproc` inconsistently between `promote` and `log` is a known footgun (`log` without it silently reports "no manifest" against the wrong directory instead of erroring).
- Shared exit-code convention: 0 = pass, 1 = genuine regression or policy failure (including a file that fails to open), 2 = usage/configuration error where nothing was actually compared.
- Trusted baselines live at `$FAST` (`/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/baseline`) — permanent for the project's life plus six months' grace, 1 TB quota, no backup. Superseded generations archive to `$WORK`, not `$SCRATCH` (which auto-purges after 40 days of inactivity). Every promotion is appended to `PROMOTION_MANIFEST.jsonl` (timestamp, user, action, run/baseline dir, RegCM git commit, reason, files, archive location).
- The canonical baseline fixture is the EUR12 domain (275x275x36, EURR-12, ROTLLR projection) at `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data/EURR12/EUR12_namelist.in`, run at 2 nodes on `dcgp_usr_prod`. `Testing/EUR12_namelist.in` is meant as a version-controlled reference copy of the same fixture but does not yet exist in the repository — Story 1.4 either adds it or explicitly flags the gap as a blocker for later I/O-scaling work, rather than assuming it present.
- Legacy scripts are archived, not deleted: `Tools/Scripts/BuildBot/testing.py` and `Tools/Scripts/TestingAndBenchmarking/preproc-compare.py` move to `Tools/Scripts/archive/`, with the commit message recording prior location and reason.
- This CI-scale fixture (`Testing/ideal.in`, with its own small in-repo, plain-git baseline) is a separate concern from the `$FAST` canonical baseline above and belongs to later container/CI work, not this epic.

## Cross-Story Dependencies

- Story 1.2 depends on Story 1.1: multi-process-count verification runs against the tool only after it is verified and committed.
- Story 1.3 depends on Stories 1.1–1.2: the legacy scripts are archived only once `regression_diff.py` is confirmed to supersede them.
- Story 1.4 depends on the tool existing: it uses `manage_baseline.py promote` to populate the first trusted baseline.
- This epic is a prerequisite for every later epic's Numerical/Test acceptance criteria: containerized CI (Epic 3) invokes this tool, GPU statistical-reproducibility testing (Epic 10) builds directly on the tolerance mechanism, and coupling regression coverage (Epic 13) builds on the baseline established here.
