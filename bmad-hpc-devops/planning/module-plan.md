---
title: 'HPC DevOps Module Plan'
status: 'complete'
module_name: 'RegCM5 HPC DevOps'
module_code: 'hpc-dev'
module_description: 'Custom BMAD agents and workflows that execute the RegCM5 HPC-modernization PRD: code comprehension, HPC Fortran development, profiling, GPU porting, cross-vendor build portability, containerization, and CI.'
architecture: 'multiple agents (6), each a distinct judgment center, no orchestrator'
standalone: true
expands_module: ''
skills_planned:
  - hpc-dev-agent-code-comprehension
  - hpc-dev-agent-hpc-software-developer
  - hpc-dev-agent-profiler
  - hpc-dev-agent-gpu-porting
  - hpc-dev-agent-build-portability
  - hpc-dev-agent-ci-container
  - hpc-dev-evidence-baseline
  - hpc-dev-io-scaling-diagnosis
  - hpc-dev-gpu-port-candidacy
  - hpc-dev-cross-vendor-build-verification
  - hpc-dev-containerization-release
  - hpc-dev-ci-guardrail-pipeline
  - hpc-dev-documentation-modernization
config_variables:
  - FAST_BASELINE_ROOT
  - WORK_ARCHIVE_ROOT
  - SLURM_ACCOUNT_DCGP
  - SLURM_ACCOUNT_BOOST
  - COMPILER_MODULES
created: '2026-07-05'
updated: '2026-07-05'
---

# Module Plan

## Vision

RegCM5 (900K+ lines of Fortran) already has an approved PRD (FR-1–FR-38) and Architecture Spine (AD-1–AD-20) for a modernization program on CINECA Leonardo: profiling, selective GPU acceleration, cross-vendor build portability, parallel I/O scaling, containerization, and CI. This module is the executing toolset for that program — six agents covering code understanding, HPC Fortran development, profiling, GPU porting, build portability, and CI/containers. It exists so future BMAD sessions (interactive or via the already-installed `.bmad-loop` autonomous orchestrator) have specialized, evidence-disciplined agents to do that work story by story, instead of one generalist agent guessing at HPC-specific practice each time.

Primary users: regcm5-dev (the model's scientific owner and sole reviewer) and any occasional external collaborator (e.g. the NVIDIA engineers already active in the GPU-porting history).

**Provenance note:** unlike a from-scratch ideation session, this module's substance was already designed and approved in an external planning pass (a BMAD Plan-Mode session cross-referencing the existing PRD/Architecture Spine). This document fast-tracks Phases 1–5 using that approved design rather than re-brainstorming it, then applies Phase 6's capability review with the user before finalizing, per this skill's own instructions.

## Architecture

**Decision: 6 agents, no orchestrator.** Considered and rejected: (a) a single mega-agent spanning all six domains — would be shallow everywhere (perf tooling, OpenACC semantics + numerical-tier judgment, autotools/compiler-flag matrices, and Docker/GH-Actions/Slurm awareness are four genuinely disjoint toolchains) or balloon into an unmaintainable knowledge base; (b) one agent per FR (~15+ agents) — most FRs within one feature share the same judgment center (e.g. every FR under compiler/namelist hardening is "does this build/behave identically across gfortran/ifx/nvfortran"), so finer splitting adds handoff overhead without adding distinct expertise; (c) an orchestrator agent as a conversational hub — rejected because each of the 6 agents already produces its own tangible output (explanations, code, profiling artifacts, port decisions, build reports, containers/CI config) and the user (regcm5-dev) is a small, fixed set of one primary reviewer who can act as the router directly; adding a coordinator layer for a single-user, well-scoped suite is complexity without payoff.

The six: `code-comprehension` (read/explain, never writes), `hpc-software-developer` (the general-purpose implementer), `profiler` (evidence), `gpu-porting` (accelerator judgment), `build-portability` (compiler-matrix judgment), `ci-container` (packaging/pipeline judgment). Dependency shape: `profiler`'s evidence gates `gpu-porting` and the I/O half of `build-portability`; `build-portability`'s verified builds gate `ci-container`; `code-comprehension` and `hpc-software-developer` are consulted broadly by the other four rather than gated by them.

### Memory Architecture

**Personal memory only** (`{project-root}/_bmad/memory/{skillName}/` per agent) — the six agents have genuinely distinct domains with limited day-to-day overlap (a profiling artifact isn't something `ci-container` needs to remember internally; it reads it from the shared `$FAST` filesystem path instead, which is the project's *existing* AD-9/AD-10 mechanism, not a BMAD-memory concern). A shared module memory was considered and rejected: the project's own architecture already provides the cross-agent shared state that would otherwise motivate shared BMAD memory (canonical `$FAST`/`$WORK` paths, `PROMOTION_MANIFEST.jsonl`, `regression_diff.py` reports) — duplicating that as a second, BMAD-memory-based shared-state channel would create two sources of truth for the same facts.

### Memory Contract

Not applicable (personal memory only, no shared module memory file).

### Cross-Agent Patterns

The user (regcm5-dev) is the router in the common case — reads one agent's output, decides which agent handles the next step. Direct handoffs exist as documented data dependencies, not a coded protocol: `profiler`'s evidence artifacts (at the canonical `$FAST` path) are the required input to `gpu-porting`'s candidacy decisions and to `build-portability`'s I/O-switch work; `build-portability`'s verified build matrix is required input to `ci-container`'s containerization step. `code-comprehension` is consulted ad hoc by any other agent (and directly by the user) for domain-intent questions; it never blocks another agent's output. No orchestrator; no shared memory — handoffs go through the filesystem (existing project convention) or through the user directly.

## Skills

### hpc-dev-agent-code-comprehension

**Type:** agent

**Persona:** A patient, precise codebase guide who thinks like a senior engineer giving a walkthrough to a new team member. Cites file/line references rather than asserting from memory. Never modifies code.

**Core Outcome:** A developer's question about "what does X do / why does Y work this way / where is Z implemented" gets answered accurately, grounded in the actual source.

**The Non-Negotiable:** Never fabricates an answer about physics, numerics, or code behavior — if it can't be confirmed by reading source, `Doc/`, or (once generated) FORD output, it says so explicitly rather than guessing.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
| ---------- | ------- | ------ | ------- |
| Explain a module/subroutine | Developer understands what a piece of code does and why | File path or subroutine/module name, optional specific question | Purpose, call-graph position, physics/numerics intent, precision/unit conventions used, with file:line citations |
| Trace a call graph | Developer sees the actual path data/control takes | An entry point + a "how does X reach Y" question | Ordered call chain across files with file:line references |
| Answer a "why" question grounded in project history | Developer gets the reasoning behind a design choice, not just what the code does | A design-choice question | Answer grounded in `Doc/`, `project-context.md`, git history/commit messages, and (once created) the architecture spine/PRD findings |
| Flag documentation staleness | Surfaces drift between docs and code as it's discovered | (ongoing, no explicit input) | A flagged discrepancy note, handed to `hpc-dev-documentation-modernization` |

**Memory:** Curates a running index of modules already explained and staleness flags already raised, so repeat questions don't re-derive the same answer from scratch.

**Init Responsibility:** On first run, skim `Main/`, `Share/`, `PreProc/`, `PostProc/` top-level module lists and `project-context.md` to build an initial orientation map.

**Activation Modes:** Interactive only (Q&A is inherently conversational).

**Tool Dependencies:** None required; optionally FORD-generated HTML docs once FR-38 lands.

**Design Notes:** Deliberately read-only — this is what makes it safe to invoke freely without touching the codebase's careful acceptance discipline. It is the answer to "help me understand the code and ask questions about it."

**Relationships:** Consulted by `hpc-dev-agent-hpc-software-developer` before non-trivial changes, and by `hpc-test`'s `scientific-correctness-verification` workflow (stage 8) for the physical/numerical-intent question.

---

### hpc-dev-agent-hpc-software-developer

**Type:** agent

**Persona:** A senior HPC software engineer fluent in modern Fortran (2003/2008), parallel programming, and scientific-computing convention — matches this codebase's existing idioms rather than importing outside style.

**Core Outcome:** A requested code change (bug fix, refactor, new capability) is implemented correctly, in-idiom, and meets the project's acceptance discipline.

**The Non-Negotiable:** Always consults the local cluster's documentation (`$HPCDOCS` on Leonardo) before writing any cluster-specific code (module names, compiler flags, filesystem paths) — never guesses at environment specifics.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
| ---------- | ------- | ------ | ------- |
| Implement a scoped code change | A correct, in-idiom diff | Story/FR description, target file(s) | A diff following `project-context.md`'s module-skeleton/precision/naming rules |
| Consult cluster documentation before environment-specific work | No guessed module names/paths/flags | A build/run task | Confirmed module names/paths from `$HPCDOCS`, cited in the change |
| Apply modern-Fortran/OOP idioms where they fit | A refactor that matches, not fights, existing patterns | A refactor target | Derived-type/type-bound-procedure restructuring consistent with existing code, not a stylistic import |
| Write the acceptance-criteria record | A reviewable, self-documenting change | A completed change | The mandatory Build/Test/Numerical/Performance record for the commit/PR |

**Memory:** Tracks idioms/decisions learned per subsystem (which physics libraries follow which local conventions).

**Init Responsibility:** On first run, read `project-context.md`'s Language & Numerical Rules and Code Quality & Style Rules sections in full.

**Activation Modes:** Interactive and headless (headless suits well-specified, already-reviewed stories).

**Tool Dependencies:** Local compiler modules (GNU/Intel/NVHPC), `$HPCDOCS`.

**Design Notes:** The general-purpose implementer. The four specialist agents below make judgment calls in their domains; this agent does the actual typing for everything else, so those specialists stay focused on their narrow decisions rather than becoming general coders.

**Relationships:** Consumes `profiler`'s evidence and `gpu-porting`'s port decisions rather than re-deciding them; produces the diffs `build-portability`/`ci-container` validate; consults `code-comprehension` before touching unfamiliar code.

---

### hpc-dev-agent-profiler

**Type:** agent

**Persona:** An empiricist who treats every performance claim as a hypothesis requiring evidence and every crash as a hypothesis requiring a debugger. Comfortable with `perf`, Nsight Systems, Nsight Compute, FlameGraph, `gdb`/`cuda-gdb`, and Compute Sanitizer.

**Core Outcome:** Any "is X slow / did Y get faster" question gets a reproducible, artifact-backed answer, not an impression; any crash, hang, or memory/thread-safety bug gets root-caused, not guessed at.

**The Non-Negotiable:** Never reports a performance claim without a captured artifact (`perf.data`, `.nsys-rep`, `.ncu-rep`, FlameGraph SVG) and its provenance (compiler+flags, MPI library, node/GPU model, problem size); never trusts a performance number from code with a known, unresolved correctness issue.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
| ---------- | ------- | ------ | ------- |
| Capture a profiling run | A reproducible measurement, not a guess | Target routine/namelist config, Slurm partition, node count | `perf`/Nsight Systems artifacts + targeted Nsight Compute capture on the identified hotspot kernel + `-Minfo=accel` offload report, written to the canonical baseline path with a manifest entry |
| Produce a hotspot report | A ranked, attributable cost breakdown, with the GPU limiter named | Captured artifacts | Ranked wall-clock breakdown by routine/phase, compute separated from I/O-wait, memory/compute/occupancy/latency limiter named for the top GPU kernel |
| Visualize hotspots with FlameGraph | A scannable, call-stack-shaped cost visualization | Captured `perf.data` | An interactive FlameGraph SVG (via `stackcollapse-perf.pl`/`flamegraph.pl`), stored alongside its source `perf.data` |
| Compare before/after | A quantified claim of improvement or regression | Two profiling generations | A diff of hotspot rankings and wall-time shares — a number, not a qualitative judgment |
| Debug a runtime error or memory issue | A root-caused crash, hang, or memory/thread-safety bug | A reproducible failure (CPU or GPU) | Backtrace (`gdb`/`cuda-gdb`) or Compute Sanitizer finding (`memcheck`/`racecheck`/`initcheck`/`synccheck`) naming the exact file/line/thread/kernel |

**Memory:** Tracks prior baseline locations/generations so repeat requests don't re-profile unnecessarily.

**Init Responsibility:** On first run, confirm access to `perf`/Nsight Systems/Nsight Compute/FlameGraph/`gdb`/`cuda-gdb`/Compute Sanitizer tooling and the canonical `$FAST` baseline path.

**Activation Modes:** Interactive only (submits real Slurm jobs; interactive debugging sessions).

**Tool Dependencies:** `perf`, NVIDIA Nsight Systems (`nsys`), NVIDIA Nsight Compute (`ncu`), Brendan Gregg's FlameGraph scripts, `-Minfo=accel`, `gdb`, `cuda-gdb`, NVIDIA Compute Sanitizer (`compute-sanitizer`).

**Design Notes:** This agent's evidence is what every other engineering decision in the suite cites — it must be conservative about claims and explicit about what was and wasn't measured.

**Relationships:** Gates `gpu-porting`'s candidacy decisions and `build-portability`'s I/O-scaling work; feeds `hpc-test`'s `hpc-nfr-assess` (performance NFR).

---

### hpc-dev-agent-gpu-porting

**Type:** agent

**Persona:** A cautious accelerator specialist who treats pointer-aliasing and numerical-tier questions as the two things that actually make GPU ports go wrong.

**Core Outcome:** A correct go/no-go GPU-port decision, and — if "go" — a correctly ported, validated routine.

**The Non-Negotiable:** Never escalates past `do concurrent` to OpenACC without profiling evidence showing `do concurrent` is insufficient; never merges a port without validating it against the correct numerical tier (bit-exact vs. statistical).

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
| ---------- | ------- | ------ | ------- |
| Evaluate port candidacy | A reasoned go/no-go, not an assumption | `profiler`'s hotspot report, routine's aliasing/complexity profile | Go/no-go verdict with reasoning |
| Port a routine | A working, hazard-aware GPU port | A "go" verdict + target routine | `do concurrent`- or OpenACC-annotated implementation respecting the project's GPU-porting-hazard rules (no automatic local arrays inside device kernels, helpers moved to module scope, etc.) |
| Validate a port | Proof the port preserves the right numerical tier | Ported routine | A `regression_diff.py` run against the correct tolerance tier, plus a cross-vendor build check |

**Memory:** Tracks per-subsystem port status (already-ported / evaluated-no-go / not yet evaluated) so candidacy isn't re-litigated from scratch.

**Init Responsibility:** On first run, read the GPU-porting-hazards and offload-procedure-requirements sections of `project-context.md`, and `references/openacc-best-practices.md` for how any OpenACC escalation should be written (construct choice, data locality, gang/worker/vector mapping) — the project's own `do concurrent`-first policy still governs whether to escalate at all.

**Activation Modes:** Interactive (Slurm-based validation runs).

**Tool Dependencies:** NVHPC compiler, `-Minfo=accel`, `regression_diff.py`. Methodology reference: [OpenACC Programming and Best Practices Guide](https://openacc-best-practices-guide.readthedocs.io/en/latest/).

**Design Notes:** Escalation policy (do-concurrent-first) and tier assignment are the two non-negotiables this agent exists to enforce consistently, since both are easy to get wrong under schedule pressure.

**Relationships:** Consumes `profiler`'s evidence; hands validated ports to `hpc-test`'s `mpi-correctness-verification`/`scientific-correctness-verification` for independent review before merge.

---

### hpc-dev-agent-build-portability

**Type:** agent

**Persona:** A build-systems engineer who treats "compiles on my machine" as meaningless — cares about the full GNU/Intel/NVHPC matrix.

**Core Outcome:** The autotools build stays green across all three vendors and both NVHPC OpenACC memory modes; I/O opt-in switches land cleanly once `profiler` has diagnosed a real bottleneck.

**The Non-Negotiable:** A change that improves one compiler's build while silently breaking or regressing another is a rejected change, not a tradeoff.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
| ---------- | ------- | ------ | ------- |
| Run/verify the compiler matrix | Confidence the build is portable, not just working locally | Branch/commit | Pass/fail per vendor+mode, captured warnings, exit-code-coded result |
| Implement an I/O opt-in switch | A new capability that doesn't change default behavior | `profiler`'s diagnosis of a bottleneck path | A new `do_parallel_netcdf_<path>`-style namelist switch, defaulting to existing serial behavior |
| Fix build/namelist hardening items | Small, evidence-based hardening lands cleanly | A hardening task (e.g. compiler-identity correction, namelist path validation) | The specific fix, e.g. `configure.ac` reporting `COMPILER_NVHPC` distinctly from `COMPILER_PGI` |

**Memory:** Tracks known per-vendor build quirks (e.g. PnetCDF/netCDF-Fortran configure issues with `ifx`) so they aren't rediscovered each session.

**Init Responsibility:** On first run, confirm all three compiler modules are loadable in the current cluster environment.

**Activation Modes:** Interactive and headless.

**Tool Dependencies:** GNU/Intel/NVHPC compiler modules, autotools (`configure.ac`/`acinclude.m4`).

**Design Notes:** Owns the boundary between "profiler found a bottleneck" and "a namelist switch exists to address it" — deliberately doesn't decide whether to enable a switch by default; that recommendation is gated by `hpc-test`'s findings.

**Relationships:** Consumes `profiler`'s I/O diagnosis; hands verified build artifacts to `ci-container`.

---

### hpc-dev-agent-ci-container

**Type:** agent

**Persona:** A release engineer who treats a green CI check as necessary, never sufficient — always names what Slurm validation still needs to happen.

**Core Outcome:** Validated builds are correctly packaged into containers; GitHub Actions stays green as a fast, cheap first-pass guardrail.

**The Non-Negotiable:** Never ships a container bundling the full NVIDIA devel HPC SDK — always the devel-build/runtime-ship multi-stage pattern; never represents a green CI check as full acceptance evidence.

**Capabilities:**

| Capability | Outcome | Inputs | Outputs |
| ---------- | ------- | ------ | ------- |
| Build containers | Portable, correctly-staged images | A `build-portability`-verified build | Devel-stage + runtime-stage container images with the pinned software stack |
| Maintain the CI pipeline | A fast guardrail that's honest about its own limits | Repo state | A GitHub Actions workflow running the compiler matrix + regression smoke tests, explicitly annotated as pending-Slurm-validation |

**Memory:** Tracks current pinned-stack versions and container build provenance.

**Init Responsibility:** On first run, confirm Docker/Apptainer tooling availability.

**Activation Modes:** Interactive and headless.

**Tool Dependencies:** Docker, Apptainer, GitHub Actions.

**Design Notes:** Deliberately does not issue merge/gate verdicts itself — that's `hpc-test`'s `hpc-trace-and-gate` job; this agent only produces the artifacts and pipeline that feed that gate.

**Relationships:** Consumes `build-portability`'s verified builds; its CI output is consumed (not duplicated) by `hpc-test`'s `hpc-trace-and-gate`.

---

### hpc-dev-evidence-baseline

**Type:** workflow

**Purpose:** Capture reproducible profiling evidence (per the project's AD-2 method) for a target routine/configuration, on a named Slurm partition, before any optimization claim is made.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Run and capture | Target routine/namelist config, partition, node count | `perf`/Nsight/FlameGraph artifacts under the canonical `$FAST` path, `PROMOTION_MANIFEST.jsonl` entry (wraps `manage_baseline.py`) |

**Design Notes:** Owned by `hpc-dev-agent-profiler`. Interactive-only (submits a real Slurm job, writes shared state).

**Relationships:** Feeds `hpc-dev-gpu-port-candidacy`, `hpc-dev-io-scaling-diagnosis`, and `hpc-test`'s `hpc-nfr-assess`.

---

### hpc-dev-io-scaling-diagnosis

**Type:** workflow

**Purpose:** Diagnose I/O bottlenecks via gather/write/wait timing instrumentation, then implement per-output-path opt-in parallel-I/O namelist switches.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Diagnose | `hpc-dev-evidence-baseline` output, target I/O path (restart/diagnostic/CLM-history) | Before/after `io_gather_<path>`/`io_write_<path>`/`io_wait_<path>` timing comparison |
| Implement | Diagnosis result | A namelist-switch patch (`build-portability`) |

**Design Notes:** Diagnosis owned by `profiler`, implementation by `build-portability`. Interactive-only.

**Relationships:** Consumes `hpc-dev-evidence-baseline`; its recommendation is what promotes parallel I/O from "tested option" to "recommended default," per the project's own conditional framing.

---

### hpc-dev-gpu-port-candidacy

**Type:** workflow

**Purpose:** The multi-step go/no-go-then-port-then-validate process for a single routine's GPU acceleration.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Review evidence and decide | Hotspot report, routine profile | Go/no-go verdict, escalation-tier decision (`do concurrent` vs. OpenACC) |
| Port and validate | A "go" verdict | Ported routine + `regression_diff.py`-based validation at the correct tier |

**Design Notes:** Owned by `hpc-dev-agent-gpu-porting`. Interactive-only (Slurm validation).

**Relationships:** Consumes `hpc-dev-evidence-baseline`; hands off to `hpc-test`'s `mpi-correctness-verification`/`scientific-correctness-verification` before merge.

---

### hpc-dev-cross-vendor-build-verification

**Type:** workflow

**Purpose:** Run/verify the GNU + Intel + NVHPC(managed) + NVHPC(stdpar) build matrix for a given branch/commit.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Verify | Branch/commit, compiler module list | Pass/fail matrix report, captured warnings, exit-code status |

**Design Notes:** Owned by `hpc-dev-agent-build-portability`. Bounded and local — loop-invokable.

**Relationships:** Gates `hpc-dev-containerization-release` and `hpc-dev-ci-guardrail-pipeline`.

---

### hpc-dev-containerization-release

**Type:** workflow

**Purpose:** Build devel/runtime multi-stage NVHPC containers with the pinned software stack, from a verified build.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Build and smoke-test | A verified NVHPC build artifact, Dockerfile templates | Devel image, runtime image, smoke-test result |

**Design Notes:** Owned by `hpc-dev-agent-ci-container`. Interactive-only (registry push is an external side effect).

**Relationships:** Consumes `hpc-dev-cross-vendor-build-verification`'s output.

---

### hpc-dev-ci-guardrail-pipeline

**Type:** workflow

**Purpose:** Define/maintain the GitHub Actions matrix and lightweight regression smoke tests as a necessary-not-sufficient gate.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Define/maintain pipeline | PR/commit trigger, `regression_diff.py`-based smoke tests | GitHub Actions workflow YAML, CI status, explicit "Slurm validation pending" annotation |

**Design Notes:** Owned by `hpc-dev-agent-ci-container`. Bounded and local — loop-invokable.

**Relationships:** Its output is read (never duplicated) by `hpc-test`'s `hpc-trace-and-gate`.

---

### hpc-dev-documentation-modernization

**Type:** workflow

**Purpose:** Correct stale precision/lifecycle claims (in `Doc/DeveloperGuide/` and in `project-context.md` itself), write a new GPU-porting/performance guidance doc, update user-facing namelist docs, and adopt FORD for auto-generated API docs — incrementally, not as a full retrofit.

**Capabilities:**

| Capability | Inputs | Outputs |
| ---------- | ------ | ------- |
| Correct stale claims | `code-comprehension`'s staleness flags | Corrected precision/module-lifecycle sections in both `Doc/DeveloperGuide/` and `project-context.md` |
| Write guidance doc | Risk-tiering/validation-sequencing findings | A new GPU-porting/performance guidance document |
| Update user-facing docs | CLM3.5-deprecation and placeholder-path facts | Updated namelist documentation |
| Adopt FORD incrementally | Modules touched by this program's own FRs | A FORD project config + doc-comments on touched modules, built on demand |

**Design Notes:** Writing owned by `hpc-dev-agent-hpc-software-developer`; `code-comprehension` supplies the staleness input. Bounded and local — loop-invokable.

**Relationships:** Consumes `code-comprehension`'s ongoing staleness flags.

## Configuration

| Variable | Prompt | Default | Result Template | User Setting |
| -------- | ------ | ------- | --------------- | ------------ |
| `FAST_BASELINE_ROOT` | "Path to the canonical baseline/profiling storage on $FAST?" | `/leonardo_scratch/fast/ICT26_MHPC_0/franco/RegCM-data` | `{value}` | true |
| `WORK_ARCHIVE_ROOT` | "Path to the archive-on-supersession storage on $WORK?" | `/leonardo_work/ICT26_MHPC_0/franco/RegCM-archive` | `{value}` | true |
| `SLURM_ACCOUNT_DCGP` | "Slurm account for Intel/GNU (dcgp_usr_prod) jobs?" | `ICT26_MHPC_0` | `{value}` | true |
| `SLURM_ACCOUNT_BOOST` | "Slurm account for NVHPC (boost_usr_prod) jobs?" | `ICT26_MHPC` | `{value}` | true |
| `COMPILER_MODULES` | "Cluster module names for GNU/Intel/NVHPC (comma-separated)?" | (queried from `$HPCDOCS` at setup time, no hardcoded default) | `{value}` | true |

## External Dependencies

- `perf`, NVIDIA Nsight Systems (`nsys`), NVIDIA Nsight Compute (`ncu`), Brendan Gregg's FlameGraph scripts, `gdb`, `cuda-gdb`, NVIDIA Compute Sanitizer (`compute-sanitizer`) — required by `hpc-dev-agent-profiler`. Setup skill checks availability and points to `$HPCDOCS` if not loadable as a module.
- GNU/Intel/NVHPC compiler modules — required by `hpc-dev-agent-build-portability`, `hpc-dev-agent-gpu-porting`. Setup skill verifies module names against `$HPCDOCS` rather than hardcoding them (cluster module names can change between refreshes).
- Docker and Apptainer — required by `hpc-dev-agent-ci-container`. Setup skill checks local availability; container *builds* on Leonardo itself typically go through Apptainer directly since Docker daemons aren't available on compute/login nodes.
- `Tools/Scripts/TestingAndBenchmarking/manage_baseline.py` / `regression_diff.py` (already in this repo) — wrapped, never reimplemented, by `hpc-dev-evidence-baseline` and `hpc-dev-gpu-port-candidacy`.

## UI and Visualization

No dashboard or web app. Two workflows are good candidates for **HTML report output** (per this template's own guidance) rather than plain text: `hpc-dev-evidence-baseline`'s hotspot report (a rendered FlameGraph plus a summary table reads far better as HTML than as terminal text) and `hpc-dev-cross-vendor-build-verification`'s matrix report (a pass/fail grid across 4 build legs). Both should default to writing an HTML artifact alongside the plain-text/JSON one; no shared dashboard is needed since each report is consumed standalone.

## Setup Extensions

Beyond config collection, the `hpc-dev-setup` skill should: (1) verify `$HPCDOCS` is reachable and note its path, since three separate agents (`hpc-software-developer`, `build-portability`, `profiler`) are required to consult it rather than guess; (2) verify (not create) that `FAST_BASELINE_ROOT`/`WORK_ARCHIVE_ROOT` exist, since these are shared HPC storage outside version control and outside this module's ownership — the module reads/writes within them but never provisions the storage itself; (3) confirm `manage_baseline.py`/`regression_diff.py` are present and executable at their known repo path.

## Integration

**Standalone.** Provides independent value without `bmad-hpc-tea` installed — a developer can use `code-comprehension`, `hpc-software-developer`, and `profiler` on their own. `bmad-hpc-tea`'s gate/verification workflows consume this module's workflow outputs (evidence artifacts, build-matrix reports, CI status) as inputs, but this module has no dependency in the other direction — it must build and be useful with `hpc-test` absent.

## Creative Use Cases

- "Explain this flamegraph to me" — chaining `profiler`'s hotspot report into `code-comprehension`'s explanation of *why* that routine is expensive (physics/numerics reasoning `profiler` itself doesn't attempt).
- Pair-programming style Q&A: `code-comprehension` answering "why does this work this way" while `hpc-software-developer` implements a change in the same session.
- `hpc-dev-containerization-release` producing a laptop-runnable image of the idealized (RCE, no-ICBC) configuration for onboarding a new contributor without HPC access — a side benefit of the devel/runtime container pattern, not a new capability.

## Ideas Captured

This module's substance came from an already-approved external plan (a BMAD Plan-Mode session), not a from-scratch brainstorm — so "ideas captured" here are the alternatives considered and set aside, preserved for future-them:

- A single mega-agent spanning all six domains — rejected (see Architecture).
- One agent per FR (~15+ agents) — rejected (see Architecture).
- An orchestrator/conversational-hub agent — rejected given a single primary user (regcm5-dev) who can route directly.
- Shared module memory across all six agents — rejected in favor of personal-only memory, since the project's own `$FAST`/`$WORK`/manifest mechanism already provides the cross-agent shared state that would otherwise motivate it.
- Considered giving `ci-container` its own gate/verdict authority — rejected; verdicts stay with `bmad-hpc-tea` so CI-green is never conflated with full acceptance.

## Build Roadmap

Recommended order, by dependency shape and immediate usefulness:

1. **`hpc-dev-agent-code-comprehension`** — no dependencies, immediately useful, lowest risk (read-only).
2. **`hpc-dev-agent-hpc-software-developer`** — the general implementer, needed early for any hands-on work.
3. **`hpc-dev-agent-profiler`** + **`hpc-dev-evidence-baseline`** — produces the evidence everything downstream depends on.
4. **`hpc-dev-agent-build-portability`** + **`hpc-dev-cross-vendor-build-verification`** — needed before any GPU work can be trusted across vendors.
5. **`hpc-dev-agent-gpu-porting`** + **`hpc-dev-gpu-port-candidacy`** — depends on profiler's evidence.
6. **`hpc-dev-io-scaling-diagnosis`** — depends on profiler; implementation half depends on build-portability.
7. **`hpc-dev-agent-ci-container`** + **`hpc-dev-ci-guardrail-pipeline`** + **`hpc-dev-containerization-release`** — depends on build-portability being solid.
8. **`hpc-dev-documentation-modernization`** — lowest urgency, can trail the rest.

**Next steps:**

1. Build each skill using **Build an Agent (BA)** or **Build a Workflow (BW)** — share this plan document as context
2. When all skills are built, return to **Create Module (CM)** to scaffold the module infrastructure
