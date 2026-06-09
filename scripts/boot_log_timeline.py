#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TS_RE = re.compile(r"^\[\s*(\d+(?:\.\d+)?)\]\s*(.*)$")


def main() -> None:
    parser = argparse.ArgumentParser(description="Find large timestamp gaps in Linux-style boot logs.")
    parser.add_argument("--log", required=True, help="Boot log file.")
    parser.add_argument("--gap-ms", default=500.0, type=float, help="Minimum gap to report.")
    parser.add_argument("--max-gaps", default=20, type=int, help="Maximum gaps to report.")
    args = parser.parse_args()

    entries = []
    for lineno, line in enumerate(Path(args.log).read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        match = TS_RE.match(line)
        if match:
            entries.append({"line": lineno, "time_s": float(match.group(1)), "text": match.group(2).strip()})

    gaps = []
    for prev, cur in zip(entries, entries[1:]):
        gap_ms = (cur["time_s"] - prev["time_s"]) * 1000.0
        if gap_ms >= args.gap_ms:
            gaps.append({"gap_ms": gap_ms, "from": prev, "to": cur})

    output = {
        "timestamped_lines": len(entries),
        "gap_threshold_ms": args.gap_ms,
        "reported_gaps": gaps[: args.max_gaps],
        "gap_count": len(gaps),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
