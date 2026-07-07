---
name: trace-call-graph
description: Trace how control or data flows between an entry point and a target
code: TC
added: 2026-07-05
type: prompt
---

# Trace a Call Graph

The outcome is an ordered, `file:line`-cited call chain answering "how does X reach Y" — a developer should be able to open each cited location and confirm the chain themselves, not just trust the summary.

Start from the named entry point and follow real call sites (not assumed ones) forward or backward as the question requires, through interface modules (`mod_*_interface.F90`) where the path crosses a subsystem boundary — name the boundary crossing explicitly, since those are deliberate seams, not incidental. Where the path runs through a halo-exchange or MPI collective, note that explicitly (`mod_mppparam`), since it's a common point where developers lose the thread. Stop at the first point where the chain becomes ambiguous (a pointer-aliased or dynamically-dispatched call) rather than guessing which branch is taken, and say plainly that it's ambiguous.
