---
name: consult-cluster-docs
description: Confirm cluster-specific facts before writing environment-specific code
code: CD
added: 2026-07-05
type: prompt
---

# Consult Cluster Documentation Before Environment-Specific Work

The outcome is a code or build change whose environment-specific facts (module names, compiler flags, filesystem paths, partition/account names) are confirmed against `$HPCDOCS`, not guessed or remembered from a prior cluster generation. The consumer will run this on Leonardo directly, so a wrong module name or stale path fails at submission time, not review time.

Before writing anything that names a compiler module, a filesystem path (`$FAST`/`$WORK`/`$SCRATCH`), a Slurm partition/account, or a library version, check `$HPCDOCS` for the current value and cite what was found. If `$HPCDOCS` doesn't cover the specific question, say so plainly rather than falling back on a remembered or plausible-sounding value — an outdated module name is a silent failure mode, not a cosmetic one.
