#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a Renode Robot text/XML report.")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    text = Path(args.report).read_text(encoding="utf-8", errors="replace")
    failed = bool(re.search(r"\b(FAIL|failed|AssertionError|Timeout)\b", text, re.I))
    output = {
        "test_name": extract(r"<test name=\"([^\"]+)\"", text, "renode_robot_test"),
        "status": "failed" if failed else "passed",
        "duration": extract(r"elapsedtime=\"([0-9.]+)\"", text, None),
        "failed_reason": first_match(r"(FAIL.*|.*Timeout.*|.*AssertionError.*)", text),
        "logs": text.splitlines()[-20:],
        "artifacts": [],
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def extract(pattern: str, text: str, default: object) -> object:
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else default


def first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else None


if __name__ == "__main__":
    main()
