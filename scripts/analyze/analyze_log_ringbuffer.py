#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract last logs, uptime, and firmware version from a ringbuffer log.")
    parser.add_argument("--log", required=True)
    parser.add_argument("--last", default=50, type=int)
    args = parser.parse_args()
    lines = Path(args.log).read_text(encoding="utf-8", errors="replace").splitlines()
    text = "\n".join(lines)
    output = {
        "firmware_version": extract(r"(?:fw|firmware|version)[:= ]+([A-Za-z0-9_.+-]+)", text),
        "uptime": extract(r"uptime[:= ]+([0-9.]+\s*(?:ms|s|sec|h)?)", text),
        "last_logs": lines[-args.last :],
        "artifacts": {"ringbuffer_log": args.log},
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(1) if match else None


if __name__ == "__main__":
    main()
