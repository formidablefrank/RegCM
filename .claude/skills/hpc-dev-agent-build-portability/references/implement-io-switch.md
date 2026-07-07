---
name: implement-io-switch
description: Implement a per-output-path opt-in parallel-I/O namelist switch
code: IS
added: 2026-07-05
type: prompt
---

# Implement an I/O Opt-In Switch

The outcome is a new namelist switch that lets a run opt into parallel I/O for one specific output path, without changing default behavior for anyone who doesn't opt in. The consumer is a modeler running at high rank count who needs this capability to exist, and every other user who must see zero observable change.

Require `hpc-dev-agent-profiler`'s diagnosis of the specific bottleneck path (diagnostic/history, restart/checkpoint, or CLM land-model history) before implementing — don't add a switch speculatively. Follow the existing `do_parallel_netcdf_in`/`do_parallel_netcdf_out` naming convention already used for ICBC input and restart, rather than inventing a different shape. Preserve existing output file format and variable naming for downstream consumers (PostProc, external analysis pipelines) unless the run explicitly opts into the new mode. Confirm a `mpi-serial` build still compiles and runs with the switch present but unused.
