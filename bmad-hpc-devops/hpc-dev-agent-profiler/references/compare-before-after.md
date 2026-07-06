---
name: compare-before-after
description: Quantify a performance change between two profiling generations
code: BA
added: 2026-07-05
type: prompt
---

# Compare Before/After

The outcome is a quantified diff of hotspot rankings and wall-time shares between two profiling generations — a number, not a qualitative "faster"/"slower" judgment. The consumer is deciding whether an optimization or port actually delivered, so the comparison must hold problem size, node/GPU type, and compiler+flags constant between the two runs or say plainly that it didn't.

Pull both generations from `{FAST_BASELINE_ROOT}/profiling/` (or the archived copy at `$WORK` if the "before" generation was superseded) and compare like-for-like: same routine, same problem size, same rank/node count unless the comparison is specifically about scaling. State the wall-time delta per hotspot, not just the total, since a change that helps one routine while regressing another needs to be visible.
