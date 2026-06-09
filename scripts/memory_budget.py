#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate embedded AI Flash/RAM budget.")
    parser.add_argument("--flash", required=True, help="Available Flash, e.g. 512K or 2M.")
    parser.add_argument("--ram", required=True, help="Available RAM, e.g. 256K.")
    parser.add_argument("--model", required=True, help="Model binary size.")
    parser.add_argument("--arena", required=True, help="Tensor arena or activation memory.")
    parser.add_argument("--stack", default="0", help="Total stack budget.")
    parser.add_argument("--heap", default="0", help="Heap/runtime budget.")
    parser.add_argument("--io", default="0", help="Input/output and feature buffers.")
    parser.add_argument("--flash-overhead", default="0", help="Firmware/runtime Flash overhead.")
    parser.add_argument("--ram-reserve", default="0", help="RAM reserve for safety margin.")
    args = parser.parse_args()

    flash = parse_size(args.flash)
    ram = parse_size(args.ram)
    flash_used = parse_size(args.model) + parse_size(args.flash_overhead)
    ram_used = (
        parse_size(args.arena)
        + parse_size(args.stack)
        + parse_size(args.heap)
        + parse_size(args.io)
        + parse_size(args.ram_reserve)
    )
    output = {
        "flash": budget("flash", flash, flash_used),
        "ram": budget("ram", ram, ram_used),
    }
    output["fits"] = output["flash"]["fits"] and output["ram"]["fits"]
    print(json.dumps(output, indent=2, sort_keys=True))


def budget(name: str, available: int, used: int) -> dict[str, object]:
    remaining = available - used
    return {
        "name": name,
        "available_bytes": available,
        "used_bytes": used,
        "remaining_bytes": remaining,
        "used_percent": round((used / available) * 100, 2) if available else None,
        "fits": remaining >= 0,
    }


def parse_size(text: str) -> int:
    normalized = text.strip().lower()
    multiplier = 1
    if normalized.endswith("kb"):
        multiplier = 1024
        normalized = normalized[:-2]
    elif normalized.endswith("k"):
        multiplier = 1024
        normalized = normalized[:-1]
    elif normalized.endswith("mb"):
        multiplier = 1024 * 1024
        normalized = normalized[:-2]
    elif normalized.endswith("m"):
        multiplier = 1024 * 1024
        normalized = normalized[:-1]
    try:
        return int(float(normalized) * multiplier)
    except ValueError as exc:
        raise SystemExit(f"Invalid size: {text}") from exc


if __name__ == "__main__":
    main()
