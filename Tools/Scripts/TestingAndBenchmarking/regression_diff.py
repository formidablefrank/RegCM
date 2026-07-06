#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["netCDF4", "numpy"]
# ///

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

# First-cut automated NetCDF regression-diff tool (PRD FR-24/FR-25),
# replacing manual NCO/CDO comparison. Compares every .nc file a
# candidate run produces against the matching file in a trusted
# baseline directory (see manage_baseline.py), field by field, and
# reports MAD/RMSE and their baseline-relative forms rMAD/rRMSE --
# never a single pass/fail bit. The project's two-tier numerical
# policy applies by default: every field must be bit-exact unless it
# is named in the tolerance table (CPU-to-GPU porting's established
# statistical bounds, FR-25/FR-37), in which case rMAD/rRMSE must fall
# within that field's accepted percentage.
#
# Run via: uv run regression_diff.py compare --run-dir X --baseline-dir Y
# (uv resolves netCDF4/numpy automatically from the header above).

import argparse
import json
import sys
from pathlib import Path

import netCDF4
import numpy as np

DEFAULT_GPU_TOLERANCES = {
    "tas": {"rmad_pct": 0.1, "rrmse_pct": 0.1},
    "ps": {"rmad_pct": 0.1, "rrmse_pct": 0.1},
    "huss": {"rmad_pct": 5.0, "rrmse_pct": 5.0},
}

# Exit-code convention (shared with manage_baseline.py): 0 = pass, 1 =
# regression/policy failure (a field genuinely diverged, or a file couldn't
# be read/compared), 2 = usage/configuration error (bad arguments, a
# directory that doesn't exist -- nothing was actually compared).
EXIT_USAGE_ERROR = 2


def die_usage(msg):
    print("error: {0}".format(msg), file=sys.stderr)
    sys.exit(EXIT_USAGE_ERROR)


def load_tolerances(path):
    if path is None:
        return DEFAULT_GPU_TOLERANCES
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        die_usage("could not read --tolerance-file {0}: {1}".format(path, exc))


def iter_nc_files(root):
    return {p.relative_to(root) for p in Path(root).rglob("*.nc")}


def compare_variable(cand_var, base_var):
    c = np.asarray(cand_var[:])
    b = np.asarray(base_var[:])
    if c.shape != b.shape:
        return {"status": "shape-mismatch", "candidate_shape": c.shape, "baseline_shape": b.shape}
    if not (np.issubdtype(c.dtype, np.number) and np.issubdtype(b.dtype, np.number)):
        return None
    c = c.astype(np.float64)
    b = b.astype(np.float64)
    if np.array_equal(c, b):
        return {"status": "exact", "mad": 0.0, "rmse": 0.0, "rmad_pct": 0.0, "rrmse_pct": 0.0}
    diff = c - b
    mad = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    base_mean_abs = float(np.mean(np.abs(b)))
    base_rms = float(np.sqrt(np.mean(b ** 2)))
    return {
        "status": "differs",
        "mad": mad,
        "rmse": rmse,
        "rmad_pct": (mad / base_mean_abs * 100.0) if base_mean_abs > 0 else None,
        "rrmse_pct": (rmse / base_rms * 100.0) if base_rms > 0 else None,
    }


def judge(name, result, tolerances):
    if result is None:
        return None
    if result["status"] == "shape-mismatch":
        return {"field": name, "tier": "n/a", "passed": False, **result}
    if result["status"] == "exact":
        return {"field": name, "tier": "bit-exact", "passed": True, **result}
    tol = tolerances.get(name)
    if tol is None:
        return {"field": name, "tier": "bit-exact", "passed": False, **result}
    rmad_ok = result["rmad_pct"] is not None and result["rmad_pct"] <= tol["rmad_pct"]
    rrmse_ok = result["rrmse_pct"] is not None and result["rrmse_pct"] <= tol["rrmse_pct"]
    return {
        "field": name,
        "tier": "statistical (GPU-port, rmad<={0}% rrmse<={1}%)".format(
            tol["rmad_pct"], tol["rrmse_pct"]
        ),
        "passed": bool(rmad_ok and rrmse_ok),
        **result,
    }


def compare_file(cand_path, base_path, tolerances, only_fields):
    # A file that can't be opened/read is treated as a comparison FAILURE
    # (exit 1: something is wrong with the actual output), not a tool crash
    # (exit 2 is reserved for bad arguments/paths, not bad run output).
    try:
        cand_ds = netCDF4.Dataset(str(cand_path))
    except Exception as exc:
        return [
            {
                "field": "(file)",
                "tier": "n/a",
                "passed": False,
                "status": "unreadable",
                "detail": "candidate: {0}".format(exc),
            }
        ]
    try:
        base_ds = netCDF4.Dataset(str(base_path))
    except Exception as exc:
        cand_ds.close()
        return [
            {
                "field": "(file)",
                "tier": "n/a",
                "passed": False,
                "status": "unreadable",
                "detail": "baseline: {0}".format(exc),
            }
        ]

    results = []
    try:
        cand_ds.set_auto_mask(False)
        base_ds.set_auto_mask(False)
        cand_names = set(cand_ds.variables)
        base_names = set(base_ds.variables)
        for name in sorted(base_names - cand_names):
            results.append({"field": name, "tier": "n/a", "passed": False, "status": "missing-in-candidate"})
        for name in sorted(cand_names - base_names):
            results.append({"field": name, "tier": "n/a", "passed": False, "status": "missing-in-baseline"})
        for name in sorted(cand_names & base_names):
            if only_fields and name not in only_fields:
                continue
            raw = compare_variable(cand_ds.variables[name], base_ds.variables[name])
            j = judge(name, raw, tolerances)
            if j is not None:
                results.append(j)
    finally:
        cand_ds.close()
        base_ds.close()
    return results


def run_comparison(run_dir, baseline_dir, tolerances, only_fields):
    cand_files = iter_nc_files(run_dir)
    base_files = iter_nc_files(baseline_dir)

    all_results = {}
    ok = True

    for rel in sorted(base_files - cand_files):
        all_results[str(rel)] = [
            {"field": "(file)", "tier": "n/a", "passed": False, "status": "missing-in-candidate"}
        ]
        ok = False
    for rel in sorted(cand_files - base_files):
        all_results[str(rel)] = [
            {"field": "(file)", "tier": "n/a", "passed": False, "status": "missing-in-baseline"}
        ]
        ok = False

    for rel in sorted(cand_files & base_files):
        results = compare_file(run_dir / rel, baseline_dir / rel, tolerances, only_fields)
        all_results[str(rel)] = results
        if any(not r["passed"] for r in results):
            ok = False

    return ok, all_results


def print_report(all_results, indent=""):
    for fname, results in all_results.items():
        print(indent + fname)
        for r in results:
            mark = "PASS" if r["passed"] else "FAIL"
            if r["status"] == "unreadable":
                print(indent + "  [{0}] {1}: unreadable ({2})".format(mark, r["field"], r["detail"]))
            elif r["status"] in ("missing-in-candidate", "missing-in-baseline", "shape-mismatch"):
                print(indent + "  [{0}] {1}: {2}".format(mark, r["field"], r["status"]))
            elif r["status"] == "exact":
                print(indent + "  [{0}] {1}: bit-exact".format(mark, r["field"]))
            else:
                rmad = "{0:.4g}%".format(r["rmad_pct"]) if r["rmad_pct"] is not None else "n/a"
                rrmse = "{0:.4g}%".format(r["rrmse_pct"]) if r["rrmse_pct"] is not None else "n/a"
                print(
                    indent
                    + "  [{0}] {1}: MAD={2:.6g} RMSE={3:.6g} rMAD={4} rRMSE={5} tier={6}".format(
                        mark, r["field"], r["mad"], r["rmse"], rmad, rrmse, r["tier"]
                    )
                )


def check_dir(path, label):
    if not Path(path).is_dir():
        die_usage("{0} not found or not a directory: {1}".format(label, path))


def cmd_compare(args):
    tolerances = load_tolerances(args.tolerance_file)
    only_fields = set(args.only_fields.split(",")) if args.only_fields else None

    if args.nprocs:
        # FR-26: a single invocation compares the same fixture at more than one
        # process count -- RegCM5's decomposition is local-stencil-based (halo
        # exchange exists so a grid point sees correct neighbor values
        # regardless of rank count), so a divergence here is a decomposition
        # bug, not an accepted artifact: the same two-tier tolerance table
        # applies unchanged, no separate nproc-specific tier.
        try:
            nprocs = [int(n) for n in args.nprocs.split(",")]
        except ValueError:
            die_usage("--nprocs must be a comma-separated list of integers, got: {0}".format(args.nprocs))
        overall_ok = True
        report = {}
        for n in nprocs:
            sub = "nproc-{0}".format(n)
            run_dir = Path(args.run_dir).resolve() / sub
            baseline_dir = Path(args.baseline_dir).resolve() / sub
            check_dir(run_dir, "--run-dir/{0}".format(sub))
            check_dir(baseline_dir, "--baseline-dir/{0}".format(sub))
            ok, results = run_comparison(run_dir, baseline_dir, tolerances, only_fields)
            report[sub] = {"pass": ok, "files": results}
            overall_ok = overall_ok and ok
    else:
        run_dir = Path(args.run_dir).resolve()
        baseline_dir = Path(args.baseline_dir).resolve()
        check_dir(run_dir, "--run-dir")
        check_dir(baseline_dir, "--baseline-dir")
        ok, results = run_comparison(run_dir, baseline_dir, tolerances, only_fields)
        overall_ok = ok
        report = {"pass": ok, "files": results}

    if args.report_file:
        Path(args.report_file).write_text(json.dumps(report, indent=2))

    if args.json:
        print(json.dumps(report, indent=2))
    elif args.nprocs:
        for sub, sub_report in report.items():
            print(sub)
            print_report(sub_report["files"], indent="  ")
        print()
        print("RESULT: {0}".format("PASS" if overall_ok else "FAIL"))
    else:
        print_report(report["files"])
        print()
        print("RESULT: {0}".format("PASS" if overall_ok else "FAIL"))

    sys.exit(0 if overall_ok else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="candidate run's NetCDF output directory")
    parser.add_argument("--baseline-dir", required=True, help="trusted baseline NetCDF output directory")
    parser.add_argument(
        "--nprocs",
        help="comma-separated process counts to compare in one invocation (FR-26), e.g. 1,4 -- "
        "each count read from a nproc-<N>/ subdirectory of --run-dir/--baseline-dir",
    )
    parser.add_argument(
        "--tolerance-file",
        help="JSON file {field: {rmad_pct, rrmse_pct}} overriding the default two-tier tolerance table",
    )
    parser.add_argument(
        "--only-fields", help="comma-separated list of variable names to restrict comparison to"
    )
    parser.add_argument("--json", action="store_true", help="machine-readable JSON output")
    parser.add_argument("--report-file", help="write the JSON report to this path for the acceptance record")
    args = parser.parse_args()
    cmd_compare(args)


if __name__ == "__main__":
    main()
