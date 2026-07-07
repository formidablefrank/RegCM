---
name: hpc-dev-containerization-release
description: Build devel/runtime multi-stage NVHPC container images for a verified RegCM5 build. Use when the user wants to containerize RegCM5, build a Docker/Apptainer image, or package a release for portable deployment.
---

# hpc-dev-containerization-release

Act as `hpc-dev-agent-ci-container` (Giacomo): build a devel-stage image (used to compile) and a separate, minimal runtime-stage image (used to ship and run) from an `hpc-dev-cross-vendor-build-verification`-verified build, with the pinned software stack — never a single image bundling NVIDIA's full devel HPC SDK, which isn't freely redistributable.

## Resolution rules

- Bare paths and `{skill-root}` (e.g. `references/guide.md`) resolve from this skill's installed directory.
- `{project-root}` → the project working directory.
- `hpc-dev-containerization-release` → the skill directory's basename.

## On Activation

1. Load config from `{project-root}/_bmad/config.yaml` (and `.user.yaml` if present).

## Build and Smoke-Test

Require a cross-vendor-verified build as the starting point — do not containerize an unverified tree. Compile against the devel image, then copy only the compiled binary and its runtime dependencies into the runtime-stage image. Pin NVHPC/HPC-X/CUDA/HDF5/netCDF-C/netCDF-Fortran/PnetCDF versions identically to the native build target. Smoke-test the runtime image against a small `Testing/` fixture before calling the build done, and note whether it's suitable for Apptainer conversion for direct execution on Leonardo.
