#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a pytest/pytest-embedded text report.")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    text = Path(args.report).read_text(encoding="utf-8", errors="replace")
    failed = "failed" in text.lower() or "error" in text.lower()
    output = {
        "test_name": extract(r"::([A-Za-z0-9_]+)", text, "pytest_embedded_test"),
        "status": "failed" if failed else "passed",
        "duration": extract(r"in\s+([0-9.]+)s", text, None),
        "failed_reason": first_match(r"(E\s+.*|FAILED.*|ERROR.*)", text),
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
