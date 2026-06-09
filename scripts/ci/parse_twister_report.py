#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a mock Zephyr Twister report/log.")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    text = Path(args.report).read_text(encoding="utf-8", errors="replace")
    status = "failed" if re.search(r"\b(FAIL|failed|error)\b", text, re.I) else "passed"
    output = {
        "test_name": extract(r"test(?:case)?[:=]\s*([A-Za-z0-9_.-]+)", text, "twister_test"),
        "status": status,
        "duration": extract(r"duration[:=]\s*([0-9.]+)", text, None),
        "failed_reason": first_match(r"(FAIL.*|ERROR.*)", text),
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
