#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review a register write against reserved, preserve, and W1C masks."
    )
    parser.add_argument("--value", required=True, help="Proposed register write value.")
    parser.add_argument("--current", default=None, help="Current/reset register value for preserve checks.")
    parser.add_argument("--width", default=32, type=int, help="Register width in bits.")
    parser.add_argument("--reserved-zero-mask", default="0", help="Bits that must be written as 0.")
    parser.add_argument("--reserved-one-mask", default="0", help="Bits that must be written as 1.")
    parser.add_argument("--preserve-mask", default="0", help="Bits that should preserve the current value.")
    parser.add_argument("--w1c-mask", default="0", help="Write-one-to-clear status flag bits.")
    parser.add_argument("--rmw", action="store_true", help="Set if the value comes from read-modify-write.")
    args = parser.parse_args()

    if args.width <= 0 or args.width > 128:
        raise SystemExit("--width must be in 1..128")
    all_bits = (1 << args.width) - 1
    value = parse_int(args.value) & all_bits
    current = parse_int(args.current) & all_bits if args.current is not None else None
    reserved_zero = parse_int(args.reserved_zero_mask) & all_bits
    reserved_one = parse_int(args.reserved_one_mask) & all_bits
    preserve = parse_int(args.preserve_mask) & all_bits
    w1c = parse_int(args.w1c_mask) & all_bits

    violations = []
    rz_violation = value & reserved_zero
    if rz_violation:
        violations.append(
            {
                "type": "reserved_zero_written_1",
                "mask": hex(rz_violation),
                "message": "Proposed write sets bits that the manual says must be written as 0.",
            }
        )
    ro_violation = (~value) & reserved_one & all_bits
    if ro_violation:
        violations.append(
            {
                "type": "reserved_one_written_0",
                "mask": hex(ro_violation),
                "message": "Proposed write clears bits that the manual says must be written as 1.",
            }
        )
    if current is not None:
        preserve_violation = (value ^ current) & preserve
        if preserve_violation:
            violations.append(
                {
                    "type": "preserve_bits_changed",
                    "mask": hex(preserve_violation),
                    "message": "Proposed write changes bits marked as preserve.",
                }
            )
    elif preserve:
        violations.append(
            {
                "type": "preserve_without_current",
                "mask": hex(preserve),
                "message": "Preserve mask was supplied but --current was not, so preserve cannot be checked.",
            }
        )
    w1c_written = value & w1c
    if w1c_written:
        message = "Proposed write writes 1 to W1C bits; this clears those flags."
        if args.rmw:
            message = "RMW write may clear W1C flags that were read as 1."
        violations.append({"type": "w1c_bits_written_1", "mask": hex(w1c_written), "message": message})

    output = {
        "width": args.width,
        "value": hex(value),
        "current": None if current is None else hex(current),
        "changed_bits": None if current is None else hex((value ^ current) & all_bits),
        "masks": {
            "reserved_zero": hex(reserved_zero),
            "reserved_one": hex(reserved_one),
            "preserve": hex(preserve),
            "w1c": hex(w1c),
        },
        "rmw": args.rmw,
        "violations": violations,
        "ok": not violations,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_int(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise SystemExit(f"Invalid integer: {text}") from exc


if __name__ == "__main__":
    main()
