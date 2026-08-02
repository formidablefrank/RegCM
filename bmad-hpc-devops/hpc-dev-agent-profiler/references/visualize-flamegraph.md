---
name: visualize-flamegraph
description: Render a FlameGraph visualization from captured CPU profiling data
code: FG
added: 2026-08-03
type: prompt
---

# Visualize Hotspots with FlameGraph

The outcome is an interactive SVG that makes a call-stack-shaped cost distribution visually scannable — wide frames are where the time goes — handed to whoever is deciding where to invest optimization effort, not a wall of `perf report` percentages they have to reconstruct the shape of by hand.

FlameGraph is the CPU-side visualization, built from `perf`'s sampled call stacks: run `perf script` against the captured `perf.data` to get raw samples, fold them into collapsed-stack format with Brendan Gregg's `stackcollapse-perf.pl`, then render with `flamegraph.pl` to produce the SVG. Write it alongside the `perf.data` it was rendered from under `{FAST_BASELINE_ROOT}/profiling/`, so the two travel together through `manage_baseline.py`'s promotion rather than the SVG going stale relative to its source data.

Read the rendered graph the way it's meant to be read: frame width is proportion of samples (cost), not call order — a wide, flat frame near the top is a self-cost hotspot worth naming directly in the hotspot report; a tall, narrow stack is a deep call chain that's cheap per-frame even if it looks alarming. Cross-reference any frame that resolves to a compiler-runtime symbol with no attributable source location (the known `__c_mset16_avx`-style pattern) back to `produce-hotspot-report.md`'s guidance on that case, rather than treating an unattributed wide frame as a dead end.

GPU kernel time doesn't flame-graph the same way — Nsight Systems' own timeline view and Nsight Compute's per-kernel report are the visualization for device-side work; don't force a `perf`-based FlameGraph over CUDA kernel execution it never sampled.
