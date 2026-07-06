#!/usr/bin/env python3

#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#
#    This file is part of ICTP RegCM.
#
#    Use of this source code is governed by an MIT-style license that can
#    be found in the LICENSE file or at
#
#         https://opensource.org/licenses/MIT.
#
#    ICTP RegCM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

# Promotes a run's output into a trusted, tracked directory -- a
# regression baseline (PRD FR-27) or a profiling-artifact archive, same
# mechanism either way. Refuses to overwrite an existing file unless
# --force is given, and records every promotion -- who, when, why,
# which files -- in a manifest alongside the target directory, so an
# update is always an explicit, reviewable decision, never a silent
# overwrite. A superseded generation is archived (--archive-dir) rather
# than discarded, unless --no-archive explicitly accepts the loss.

import argparse
import getpass
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = "PROMOTION_MANIFEST.jsonl"

# Exit-code convention (shared with regression_diff.py): 0 = pass, 1 =
# regression/policy failure, 2 = usage/configuration error. This tool never
# itself judges a regression -- every refusal here is a usage/configuration
# problem (a missing directory, a missing --reason, an undecided overwrite),
# so every error path exits 2.
EXIT_USAGE_ERROR = 2


def die(msg):
    print("error: {0}".format(msg), file=sys.stderr)
    sys.exit(EXIT_USAGE_ERROR)


def git_commit(repo_dir):
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def iter_files(run_dir):
    for path in sorted(run_dir.rglob("*")):
        if path.is_file():
            yield path.relative_to(run_dir)


def cmd_promote(args):
    run_dir = Path(args.run_dir).resolve()
    baseline_dir = Path(args.baseline_dir).resolve()
    archive_dir = Path(args.archive_dir).resolve() if args.archive_dir else None
    if args.nproc is not None:
        # FR-26 multi-process-count convention: each process count's output
        # lives in its own nproc-<N>/ subdirectory, consistently between
        # this tool and regression_diff.py's --nprocs.
        sub = "nproc-{0}".format(args.nproc)
        run_dir = run_dir / sub
        baseline_dir = baseline_dir / sub
        if archive_dir is not None:
            archive_dir = archive_dir / sub
    if not run_dir.is_dir():
        die("run directory not found: {0}".format(run_dir))
    baseline_dir.mkdir(parents=True, exist_ok=True)

    files = list(iter_files(run_dir))
    if not files:
        die("no files found under {0}".format(run_dir))

    conflicts = [f for f in files if (baseline_dir / f).exists()]
    if conflicts and not args.force:
        die(
            "{0} baseline file(s) already exist and would be overwritten:\n  {1}\n"
            "Re-run with --force and --reason to confirm the overwrite.".format(
                len(conflicts),
                "\n  ".join(str(f) for f in conflicts),
            )
        )
    if args.force and not args.reason:
        die(
            "--force requires --reason \"...\" recording why this "
            "baseline is being overwritten"
        )
    if conflicts and archive_dir is None and not args.no_archive:
        die(
            "overwriting {0} existing baseline file(s) requires either "
            "--archive-dir (superseded files preserved there) or --no-archive "
            "(explicitly accept permanent loss)".format(len(conflicts))
        )

    repo_root = Path(__file__).resolve().parents[3]

    archived_to = None
    if conflicts and archive_dir is not None:
        generation = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        commit = git_commit(repo_root)[:12]
        archived_to = archive_dir / "{0}-{1}".format(generation, commit)
        for rel in conflicts:
            dest = archived_to / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(baseline_dir / rel, dest)

    for rel in files:
        dest = baseline_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_dir / rel, dest)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user": getpass.getuser(),
        "action": "overwrite" if conflicts else "initial",
        "run_dir": str(run_dir),
        "baseline_dir": str(baseline_dir),
        "regcm_commit": git_commit(repo_root),
        "reason": args.reason or "initial baseline, no prior files conflicted",
        "files": [str(f) for f in files],
        "archived_to": str(archived_to) if archived_to else None,
    }
    with (baseline_dir / MANIFEST_NAME).open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    print("promoted {0} file(s) to {1}".format(len(files), baseline_dir))
    if conflicts:
        print(
            "  ({0} existing file(s) overwritten, recorded in {1})".format(
                len(conflicts), MANIFEST_NAME
            )
        )
        if archived_to:
            print("  (superseded generation archived to {0})".format(archived_to))
        else:
            print("  (--no-archive given: superseded files were NOT preserved)")


def cmd_log(args):
    baseline_dir = Path(args.baseline_dir).resolve()
    if args.nproc is not None:
        baseline_dir = baseline_dir / "nproc-{0}".format(args.nproc)
    manifest = baseline_dir / MANIFEST_NAME
    if not manifest.exists():
        print(
            "no manifest at {0} -- baseline has never been promoted "
            "through this tool".format(manifest)
        )
        return
    for line in manifest.read_text().splitlines():
        entry = json.loads(line)
        print(
            "{0}  {1}  {2:9s}  {3}".format(
                entry["timestamp"], entry["user"], entry["action"], entry["reason"]
            )
        )
        if entry.get("archived_to"):
            print("    archived: {0}".format(entry["archived_to"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    p_promote = sub.add_parser(
        "promote", help="copy a run's output into the trusted baseline directory"
    )
    p_promote.add_argument(
        "--run-dir", required=True, help="directory holding the candidate run's output"
    )
    p_promote.add_argument(
        "--baseline-dir", required=True, help="trusted baseline directory to promote into"
    )
    p_promote.add_argument(
        "--force", action="store_true", help="allow overwriting existing baseline files"
    )
    p_promote.add_argument(
        "--reason", help="justification for this promotion (required with --force)"
    )
    p_promote.add_argument(
        "--archive-dir",
        help="directory to copy superseded baseline files into, under a "
        "timestamped generation subdirectory, before they are overwritten",
    )
    p_promote.add_argument(
        "--no-archive",
        action="store_true",
        help="explicitly accept permanent loss of superseded baseline files "
        "instead of archiving them",
    )
    p_promote.add_argument(
        "--nproc",
        type=int,
        help="FR-26 multi-process-count convention: operate on the nproc-<N>/ "
        "subdirectory of --run-dir/--baseline-dir/--archive-dir instead of the "
        "directory itself",
    )
    p_promote.set_defaults(func=cmd_promote)

    p_log = sub.add_parser("log", help="show the promotion history for a baseline directory")
    p_log.add_argument("--baseline-dir", required=True)
    p_log.add_argument(
        "--nproc", type=int, help="show history for the nproc-<N>/ subdirectory instead"
    )
    p_log.set_defaults(func=cmd_log)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
