---
name: produce-hotspot-report
description: Turn captured profiling artifacts into a ranked, attributable hotspot report
code: HR
added: 2026-07-05
type: prompt
---

# Produce a Hotspot Report

The outcome is a ranked wall-clock breakdown by routine/phase that separates compute from I/O-wait, attributable to real source locations — not a flat percentage with no call-stack context. The consumer uses this to decide where to invest optimization or porting effort, so an unattributed hotspot (a compiler-runtime symbol with no call stack) is a finding to flag, not to drop silently.

Read the captured `perf`/Nsight artifacts and render a FlameGraph where useful. Where `perf` shows a symbol with no attributable call stack (a compiler-generated routine like a vectorized memset), say so explicitly and note that Nsight Systems may be needed to resolve it — this project has a known precedent for exactly this pattern. Cross-reference `-Minfo=accel` output to state what actually offloaded to GPU versus what only compiled without offloading.
