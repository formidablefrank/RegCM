# Adversarial Incompatibility Review: ARCHITECTURE-SPINE.md

(Background subagent for this lens failed on a session-limit API error before
producing output; done inline instead, per the reviewer-gate fallback.)

## Verdict

Found one high-value, previously-invisible gap (the tolerance table's silent
default for un-listed GPU-ported fields) plus three smaller ones. Checked one
suspected symmetry bug in the actual code and found it already handled
correctly.

## Findings

1. **(High) AD-1's tolerance table has no growth rule.** AD-1's Rule text
   reads as if the *policy* covers all CPU-to-GPU-ported fields ("CPU-to-GPU
   porting specifically is accepted at the source thesis's measured
   statistical bounds"), but the actual *mechanism*
   (`regression_diff.py`'s `DEFAULT_GPU_TOLERANCES`) only implements
   statistical tolerance for `tas`, `ps`, `huss`. Two people extending
   GPU-porting to a new subsystem -- say, MOLOCH's advection producing a new
   GPU-ported wind field `ua` -- could each read AD-1 and reasonably conclude
   opposite things: one assumes any GPU-ported field automatically gets
   statistical treatment (matching the stated policy), the other discovers
   the tool actually holds `ua` to bit-exact by default (since it isn't in
   the table) and their port now "fails" the regression check even though
   it's working as designed under the CPU-only default. This is exactly a
   case of two units each following the letter of an AD yet building
   incompatible expectations. **Fix**: add an explicit rule that any newly
   GPU-ported output field must have its own measured tolerance added to the
   tool's tolerance table (or a `--tolerance-file`) before its check will
   pass at anything looser than bit-exact -- omission is a deliberate
   bit-exact default, not an oversight to route around.

2. **(Medium) No designated default OpenACC memory mode for GPU
   production/profiling runs.** AD-7 fixes both `--enable-openacc-managed`
   and `--enable-openacc-stdpar` as required *build-matrix test* cells, but
   says nothing about which mode is the default for an actual production or
   profiling run on `boost_usr_prod`. Two people could diverge: one assumes
   `managed` (matches the source thesis's original benchmarks), another
   assumes `stdpar` (unified memory, and FR-11's own notes flag
   `mem:unified` as a promising future direction). This doesn't collide with
   AD-8's canonical baseline (which runs on the Intel/GNU partition, not
   NVHPC), but it would matter the moment anyone runs a GPU-side baseline or
   profiling pass. Not fixed in this pass -- recommend either a quick
   decision or an explicit Deferred entry so it isn't silently assumed
   later.

3. **(Medium) Container base OS/distro is undecided across all three
   variants.** AD-18 fixes the NVHPC-specific devel/runtime redistribution
   pattern but says nothing about the common base Linux distribution for the
   GNU, Intel, and NVHPC/CUDA container images. Three independent builders
   (FR-28 GNU, FR-28 Intel, FR-30 NVHPC) could each pick a different base
   image (e.g. Ubuntu vs. Rocky Linux vs. NVIDIA's own NGC base), producing
   inconsistent libc versions and filesystem layouts across variants that
   are supposed to agree bit-exactly per FR-28's own acceptance criterion.
   Not researched or decided in this pass (out of scope for tonight's
   priority); added to Deferred rather than invented.

4. **(Low) `manage_baseline.py log` silently "succeeds" if `--nproc` is
   forgotten on a per-process-count-organized baseline.** If a baseline was
   promoted with `--nproc 4` (living under `baseline-dir/nproc-4/`), running
   `log --baseline-dir baseline-dir` (without `--nproc 4`) reports "no
   manifest -- baseline has never been promoted through this tool" -- a
   misleading false negative, not an error. Two people could diverge simply
   by one of them forgetting the flag. Low severity (a documentation/UX
   footgun, not a build-divergence risk), worth a one-line caveat in
   Consistency Conventions rather than a code fix right now.

5. **(Low, not fixed -- below spine altitude)** AD-6 fixes the *pattern*
   (`do_parallel_netcdf_<path>`) but not the *literal* name FR-5's diagnostic
   switch should use. Two implementers could pick `do_parallel_netcdf_hist`
   vs. `do_parallel_netcdf_diag`. Judged low severity: this is a single new
   symbol scoped to one story, reviewed by regcm5-dev (sole reviewer) before
   merge -- easy to catch and rename, unlike the tolerance-table gap above,
   which fails silently in exactly the way this AD is supposed to prevent.
   Not changing the spine for this.

## Checked and found correct (no finding)

- **`--nproc` symmetry across `--run-dir`/`--baseline-dir`/`--archive-dir`**:
  verified against the actual `manage_baseline.py` source -- when `--nproc N`
  is given, all three paths get the `nproc-N/` subdirectory appended
  identically (`cmd_promote`, lines computing `run_dir`/`baseline_dir`/
  `archive_dir` together before any usage). No asymmetry exists; my initial
  suspicion here was wrong.
- **AD-13's same-tolerance-across-nproc rule already covers the "GPU kernel
  behaves differently at different per-rank domain sizes" concern** -- since
  GPU-ported fields keep their statistical (not bit-exact) tolerance even in
  the nproc=1-vs-4 comparison, a legitimate small kernel-launch-configuration
  difference wouldn't false-positive as a "decomposition bug." Well-designed;
  not a gap.
