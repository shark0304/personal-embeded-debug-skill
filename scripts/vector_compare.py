#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


NUMBER_RE = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare numeric golden-vector files.")
    parser.add_argument("--expected", required=True, help="Expected/golden vector file.")
    parser.add_argument("--actual", required=True, help="Actual firmware vector dump file.")
    parser.add_argument("--abs-tol", default=0.0, type=float, help="Absolute tolerance.")
    parser.add_argument("--rel-tol", default=0.0, type=float, help="Relative tolerance.")
    parser.add_argument("--max-mismatches", default=10, type=int, help="Number of mismatches to include.")
    args = parser.parse_args()
    if args.abs_tol < 0 or args.rel_tol < 0:
        raise SystemExit("Tolerances must be non-negative")
    if args.max_mismatches < 0:
        raise SystemExit("--max-mismatches must be non-negative")

    expected = load_numbers(Path(args.expected))
    actual = load_numbers(Path(args.actual))
    count = min(len(expected), len(actual))
    mismatches = []
    mismatch_count = 0
    max_abs_error = 0.0
    max_rel_error = 0.0
    max_abs_index = None

    for index in range(count):
        exp = expected[index]
        act = actual[index]
        abs_error = abs(act - exp)
        rel_error = abs_error / max(abs(exp), 1e-12)
        if abs_error > max_abs_error:
            max_abs_error = abs_error
            max_abs_index = index
        max_rel_error = max(max_rel_error, rel_error)
        tolerance = args.abs_tol + args.rel_tol * abs(exp)
        if abs_error > tolerance:
            mismatch_count += 1
            if len(mismatches) < args.max_mismatches:
                mismatches.append(
                    {
                        "index": index,
                        "expected": exp,
                        "actual": act,
                        "abs_error": abs_error,
                        "rel_error": rel_error,
                        "tolerance": tolerance,
                    }
                )

    length_mismatch = len(expected) != len(actual)
    output = {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "compared_count": count,
        "length_mismatch": length_mismatch,
        "abs_tol": args.abs_tol,
        "rel_tol": args.rel_tol,
        "max_abs_error": max_abs_error,
        "max_abs_error_index": max_abs_index,
        "max_rel_error": max_rel_error,
        "mismatch_count": mismatch_count,
        "mismatch_count_reported": len(mismatches),
        "first_mismatches": mismatches,
        "pass": (not length_mismatch) and mismatch_count == 0,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def load_numbers(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8")
    values = [float(match.group(0)) for match in NUMBER_RE.finditer(text)]
    if not values:
        raise SystemExit(f"No numeric values found in {path}")
    return values


if __name__ == "__main__":
    main()
