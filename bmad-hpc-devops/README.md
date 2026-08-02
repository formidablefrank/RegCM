# RegCM5 HPC DevOps (`hpc-dev`)

A custom BMAD module that executes RegCM5's HPC-modernization program — the PRD and Architecture Spine already approved for this project (`_bmad-output/planning-artifacts/`). This module produces artifacts and executes changes; its sibling module, `bmad-hpc-tea`, designs test coverage, audits evidence quality, and adjudicates gate decisions. Neither re-implements the other's workflows.

## Agents

| Agent | Skill | Mandate |
| --- | --- | --- |
| Gaspare | `hpc-dev-agent-code-comprehension` | Reads and explains RegCM5 source; answers developer questions; never modifies code. |
| Jacopo | `hpc-dev-agent-hpc-software-developer` | Writes/modifies modern Fortran for RegCM5 on HPC infrastructure; consults `$HPCDOCS` before environment-specific code. |
| Lorenzo | `hpc-dev-agent-profiler` | Captures reproducible perf/Nsight profiling evidence; visualizes CPU hotspots with FlameGraph; debugs CPU/GPU runtime errors and memory/thread-safety issues with gdb/cuda-gdb/Compute Sanitizer. |
| Dario | `hpc-dev-agent-gpu-porting` | Decides GPU-port candidacy, ports via `do concurrent`/OpenACC, validates against the tolerance policy. |
| Franco | `hpc-dev-agent-build-portability` | Keeps the GNU/Intel/NVHPC build matrix green; implements I/O opt-in switches. |
| Giacomo | `hpc-dev-agent-ci-container` | Packages builds into containers; maintains the GitHub Actions pipeline. |

## Workflows

`hpc-dev-evidence-baseline`, `hpc-dev-io-scaling-diagnosis`, `hpc-dev-gpu-port-candidacy`, `hpc-dev-cross-vendor-build-verification`, `hpc-dev-containerization-release`, `hpc-dev-ci-guardrail-pipeline`, `hpc-dev-documentation-modernization`.

## Getting started

1. Run `hpc-dev-setup` once per fresh clone to register this module's config into `_bmad/config.yaml`/`_bmad/module-help.csv` (gitignored local state — this module's source is committed, but its install registration is not).
2. Talk to **Gaspare** (`hpc-dev-agent-code-comprehension`) first if you need to understand the codebase before changing it.
3. Follow the build roadmap in `planning/module-plan.md` for a recommended sequencing: code comprehension → HPC developer → profiler/evidence-baseline → build-portability/cross-vendor-verification → GPU porting → I/O scaling → CI/containers → documentation.

## Loop invocability

`hpc-dev-cross-vendor-build-verification`, `hpc-dev-ci-guardrail-pipeline`, and `hpc-dev-documentation-modernization` are bounded/local and may be invoked by the `.bmad-loop` autonomous orchestrator. `hpc-dev-evidence-baseline`, `hpc-dev-io-scaling-diagnosis`, `hpc-dev-gpu-port-candidacy`, and `hpc-dev-containerization-release` submit real Slurm jobs or touch shared `$FAST`/`$WORK` state and are interactive-only.

## Distribution

This module is installable independently of the RegCM5 repo via `.claude-plugin/marketplace.json` — e.g. `npx bmad-method install --custom-source <path-or-git-url> --tools claude-code --yes`. Fill in `license`/`homepage`/`repository` in that file before distributing externally.
