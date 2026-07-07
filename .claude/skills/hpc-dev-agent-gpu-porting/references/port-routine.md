---
name: port-routine
description: Implement a GPU port for a routine with a "go" verdict
code: PR
added: 2026-07-05
type: prompt
---

# Port a Routine

The outcome is a working, hazard-aware GPU port that compiles under GNU/Intel/NVHPC without changing CPU-path behavior. The consumer is the cross-vendor build matrix and, ultimately, a scientific reviewer trusting that the CPU-only path is untouched.

Apply the project's confirmed offload procedure requirements: move any contained helper procedure to module scope before it can compile to a device kernel; move automatic (local) array allocation to the caller and pass it as an argument; replace a whole-array or row-slice initialization idiom with an explicit element-wise loop under `!$acc loop seq` if it risks lowering to an unattributed vectorized memset. Guard the accelerator-specific path behind a build macro so GNU/Intel CPU-only builds are provably unaffected. Follow the merged reference pattern (`!$acc parallel loop` at the call site, `!$acc routine seq` on a `pure` callee) unless evidence specifically calls for the `do concurrent` variant.
