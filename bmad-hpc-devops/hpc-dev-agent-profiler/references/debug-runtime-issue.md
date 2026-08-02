---
name: debug-runtime-issue
description: Debug a RegCM5 CPU/GPU runtime error, hang, or memory/thread-safety issue
code: DR
added: 2026-07-06
type: prompt
---

# Debug a Runtime Error or Memory Issue

The outcome is a root-caused runtime error or memory/thread-safety issue — reproduced under a debugger or sanitizer, with the exact failing call frame, thread, or kernel launch identified — not a guess read off a stack-trace string. The consumer is whoever fixes it (usually `hpc-dev-agent-hpc-software-developer`), so "crashes somewhere in the radiation scheme" is not done; naming the file, line, variable, and failure mode is.

This is correctness work, not performance work — establish it first. A bottleneck measurement on a kernel with a live correctness bug is not trustworthy evidence, so a debugging finding here can block a pending `hpc-dev-evidence-baseline`/`produce-hotspot-report.md` claim rather than the other way around.

**CPU-side crash or hang**: reproduce under `gdb` (batch mode `-batch -ex run -ex bt full` on the cluster, interactive for a live session) and capture a full backtrace at the point of failure, not just the top frame — an MPI rank crashing inside a halo exchange often has the real cause several frames up, in the caller that passed a bad array bound.

**GPU-side crash, hang, or wrong-answer bug** in `do concurrent`/OpenACC-offloaded code: reproduce under `cuda-gdb` the same way, and separately run the relevant **NVIDIA Compute Sanitizer** tool — this catches classes of GPU memory/thread-safety bugs a CPU debugger cannot see and that can silently corrupt results without ever crashing, so treat "wrong output, no crash" as at least as strong a reason to reach for it as a crash:
- `memcheck` — out-of-bounds or misaligned device-memory access
- `racecheck` — shared-memory data races between threads
- `initcheck` — reads of uninitialized device memory
- `synccheck` — invalid use of synchronization primitives (e.g. `__syncthreads()` reached non-uniformly across a block)

**Multi-rank/multi-GPU hang that's hard to reproduce under a single-process debugger**: an Nsight Systems trace across ranks can localize where the run stalls (which rank, which collective, which kernel never launched) even though its primary job elsewhere is performance timeline capture, not correctness.

Once fixed, hand off to `hpc-dev-evidence-baseline` if the fix touched a hot loop — a bounds or race fix sometimes changes generated code enough to shift performance, and re-measuring is this agent's other capability, not this one.
