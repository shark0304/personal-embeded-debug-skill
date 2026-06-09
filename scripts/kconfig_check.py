#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Kconfig .config or autoconf.h symbols.")
    parser.add_argument("--config", required=True, help=".config, autoconf.h, or config fragment.")
    parser.add_argument("--require", action="append", required=True, help="Symbol requirement, e.g. CONFIG_I2C=y.")
    args = parser.parse_args()

    symbols = parse_config(Path(args.config).read_text(encoding="utf-8", errors="replace"))
    checks = []
    for spec in args.require:
        name, expected = parse_requirement(spec)
        actual = symbols.get(name, "n")
        checks.append({"symbol": name, "expected": expected, "actual": actual, "ok": actual == expected})

    output = {"checks": checks, "ok": all(item["ok"] for item in checks)}
    print(json.dumps(output, indent=2, sort_keys=True))
    if not output["ok"]:
        raise SystemExit(1)


def parse_config(text: str) -> dict[str, str]:
    symbols: dict[str, str] = {}
    for line in text.splitlines():
        if match := re.match(r"^(CONFIG_[A-Za-z0-9_]+)=(.*)$", line):
            symbols[match.group(1)] = match.group(2).strip().strip('"')
        elif match := re.match(r"^# (CONFIG_[A-Za-z0-9_]+) is not set$", line):
            symbols[match.group(1)] = "n"
        elif match := re.match(r"^#define (CONFIG_[A-Za-z0-9_]+)\s+(.+)$", line):
            value = match.group(2).strip()
            symbols[match.group(1)] = "y" if value == "1" else value.strip('"')
    return symbols


def parse_requirement(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        return spec, "y"
    name, expected = spec.split("=", 1)
    return name, expected


if __name__ == "__main__":
    main()
