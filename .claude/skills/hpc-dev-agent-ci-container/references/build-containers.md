---
name: build-containers
description: Build devel/runtime multi-stage NVHPC containers from a verified build
code: BC
added: 2026-07-05
type: prompt
---

# Build Containers

The outcome is a devel-stage image (used to compile) and a separate, smaller runtime-stage image (used to ship and run) with the pinned software stack — never a single image bundling NVIDIA's full devel HPC SDK, which isn't freely redistributable. The consumer runs the runtime image on Leonardo (via Apptainer) or elsewhere, so it must be self-contained and minimal.

Require `hpc-dev-agent-build-portability`'s cross-vendor-verified build as the starting point — don't build a container from an unverified tree. Compile against the devel image, then copy only the compiled binary and its runtime dependencies into the runtime-stage image. Pin NVHPC/HPC-X/CUDA/HDF5/netCDF-C/netCDF-Fortran/PnetCDF versions identically to the native build target. Smoke-test the runtime image (a small `Testing/` fixture) before calling the build done.
