#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate average current from repeated power states.")
    parser.add_argument(
        "--state",
        action="append",
        required=True,
        help="State as NAME:CURRENT:TIME, e.g. sleep:12uA:9.9s or tx:120mA:80ms.",
    )
    parser.add_argument("--battery-mah", default=None, type=float, help="Optional battery capacity in mAh.")
    args = parser.parse_args()

    states = [parse_state(item) for item in args.state]
    total_time_h = sum(item["duration_h"] for item in states)
    if total_time_h <= 0:
        raise SystemExit("Total time must be positive")
    charge_mah = sum(item["current_ma"] * item["duration_h"] for item in states)
    avg_current_ma = charge_mah / total_time_h
    life_h = None if args.battery_mah is None else args.battery_mah / avg_current_ma

    output = {
        "states": states,
        "cycle_time_s": total_time_h * 3600.0,
        "cycle_charge_mah": charge_mah,
        "average_current_ma": avg_current_ma,
        "battery_mah": args.battery_mah,
        "estimated_life_hours": life_h,
        "estimated_life_days": None if life_h is None else life_h / 24.0,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_state(text: str) -> dict[str, object]:
    parts = text.split(":")
    if len(parts) != 3:
        raise SystemExit(f"Invalid state {text!r}; expected NAME:CURRENT:TIME")
    name, current_text, duration_text = parts
    current_ma = parse_current_ma(current_text)
    duration_h = parse_time_h(duration_text)
    return {
        "name": name,
        "current_ma": current_ma,
        "duration_s": duration_h * 3600.0,
        "duration_h": duration_h,
        "charge_mah": current_ma * duration_h,
    }


def parse_current_ma(text: str) -> float:
    normalized = text.strip().lower()
    multiplier = 1.0
    if normalized.endswith("ua"):
        multiplier = 0.001
        normalized = normalized[:-2]
    elif normalized.endswith("ma"):
        normalized = normalized[:-2]
    elif normalized.endswith("a"):
        multiplier = 1000.0
        normalized = normalized[:-1]
    try:
        value = float(normalized) * multiplier
    except ValueError as exc:
        raise SystemExit(f"Invalid current: {text}") from exc
    if value < 0:
        raise SystemExit(f"Current must be non-negative: {text}")
    return value


def parse_time_h(text: str) -> float:
    normalized = text.strip().lower()
    multiplier = 1.0 / 3600.0
    if normalized.endswith("ms"):
        multiplier = 1.0 / 3_600_000.0
        normalized = normalized[:-2]
    elif normalized.endswith("s"):
        multiplier = 1.0 / 3600.0
        normalized = normalized[:-1]
    elif normalized.endswith("min"):
        multiplier = 1.0 / 60.0
        normalized = normalized[:-3]
    elif normalized.endswith("h"):
        multiplier = 1.0
        normalized = normalized[:-1]
    try:
        value = float(normalized) * multiplier
    except ValueError as exc:
        raise SystemExit(f"Invalid duration: {text}") from exc
    if value < 0:
        raise SystemExit(f"Duration must be non-negative: {text}")
    return value


if __name__ == "__main__":
    main()
