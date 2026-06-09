#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode integer register bitfields.")
    parser.add_argument("--value", required=True, help="Register value, decimal or 0x-prefixed hex.")
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help="Field definition as NAME:MSB:LSB. Repeat for multiple fields.",
    )
    args = parser.parse_args()

    value = parse_int(args.value)
    fields = [decode_field(value, item) for item in args.field]
    print(
        json.dumps(
            {
                "value": value,
                "value_hex": hex(value),
                "fields": fields,
            },
            indent=2,
            sort_keys=True,
        )
    )


def decode_field(value: int, spec: str) -> dict[str, object]:
    parts = spec.split(":")
    if len(parts) != 3:
        raise SystemExit(f"Invalid field spec {spec!r}; expected NAME:MSB:LSB")
    name, msb_text, lsb_text = parts
    msb = int(msb_text, 0)
    lsb = int(lsb_text, 0)
    if msb < lsb or lsb < 0:
        raise SystemExit(f"Invalid bit range in {spec!r}")
    width = msb - lsb + 1
    mask = (1 << width) - 1
    field_value = (value >> lsb) & mask
    return {
        "name": name,
        "msb": msb,
        "lsb": lsb,
        "width": width,
        "value": field_value,
        "value_hex": hex(field_value),
    }


def parse_int(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise SystemExit(f"Invalid integer: {text}") from exc


if __name__ == "__main__":
    main()
