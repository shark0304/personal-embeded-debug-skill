#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = [
    ("watchdog", re.compile(r"watchdog|wdt|task_wdt", re.I)),
    ("brownout", re.compile(r"brownout|undervoltage|power.?fail", re.I)),
    ("hardfault", re.compile(r"hardfault|busfault|memmanage|usagefault|cfsr|hfsr", re.I)),
    ("assert", re.compile(r"assert|panic.*assert", re.I)),
    ("ota", re.compile(r"ota|rollback|image confirm|slot", re.I)),
    ("manual", re.compile(r"manual reset|button reset|external reset|pin reset", re.I)),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify reboot reason from field logs.")
    parser.add_argument("--log", required=True)
    args = parser.parse_args()
    lines = Path(args.log).read_text(encoding="utf-8", errors="replace").splitlines()
    matches = []
    for lineno, line in enumerate(lines, start=1):
        for kind, pattern in PATTERNS:
            if pattern.search(line):
                matches.append({"line": lineno, "kind": kind, "text": line.strip()})
    classification = matches[-1]["kind"] if matches else "unknown"
    output = {"classification": classification, "matches": matches[-20:], "artifacts": {"field_log": args.log}}
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
