#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Check embedded AI latency, period, and watchdog budget.")
    parser.add_argument("--period", required=True, help="Required cycle period, e.g. 100ms.")
    parser.add_argument(
        "--component",
        action="append",
        required=True,
        help="Pipeline component as NAME:TIME, e.g. inference:18ms. Repeat for each stage.",
    )
    parser.add_argument("--jitter", default="0ms", help="Worst-case scheduler/ISR/jitter allowance.")
    parser.add_argument("--watchdog", default=None, help="Watchdog timeout, e.g. 250ms.")
    parser.add_argument(
        "--duty-limit-percent",
        default=None,
        type=float,
        help="Optional duty-cycle ceiling for power/thermal budget.",
    )
    args = parser.parse_args()

    period_ms = parse_time_ms(args.period)
    jitter_ms = parse_time_ms(args.jitter)
    components = [parse_component(item) for item in args.component]
    component_total_ms = sum(item["time_ms"] for item in components)
    total_ms = component_total_ms + jitter_ms
    watchdog_ms = parse_time_ms(args.watchdog) if args.watchdog is not None else None
    duty_percent = (total_ms / period_ms) * 100.0

    findings = []
    if total_ms <= period_ms:
        findings.append("Pipeline fits the requested period with the supplied jitter allowance.")
    else:
        findings.append("Pipeline exceeds the requested period.")
    if watchdog_ms is not None:
        if total_ms <= watchdog_ms:
            findings.append("Pipeline fits within the watchdog timeout.")
        else:
            findings.append("Pipeline can exceed the watchdog timeout; feed point or workload must change.")
    if args.duty_limit_percent is not None:
        if duty_percent <= args.duty_limit_percent:
            findings.append("Duty cycle is within the selected limit.")
        else:
            findings.append("Duty cycle exceeds the selected power/thermal limit.")

    slowest = max(components, key=lambda item: item["time_ms"])
    output = {
        "period_ms": period_ms,
        "components": components,
        "component_total_ms": component_total_ms,
        "jitter_ms": jitter_ms,
        "total_ms": total_ms,
        "period_margin_ms": period_ms - total_ms,
        "fits_period": total_ms <= period_ms,
        "watchdog_ms": watchdog_ms,
        "watchdog_margin_ms": None if watchdog_ms is None else watchdog_ms - total_ms,
        "fits_watchdog": None if watchdog_ms is None else total_ms <= watchdog_ms,
        "duty_percent": duty_percent,
        "duty_limit_percent": args.duty_limit_percent,
        "fits_duty_limit": None
        if args.duty_limit_percent is None
        else duty_percent <= args.duty_limit_percent,
        "slowest_component": slowest,
        "findings": findings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_component(text: str) -> dict[str, object]:
    if ":" not in text:
        raise SystemExit(f"Invalid component {text!r}; expected NAME:TIME")
    name, time_text = text.split(":", 1)
    name = name.strip()
    if not name:
        raise SystemExit(f"Invalid component {text!r}; empty name")
    return {"name": name, "time_ms": parse_time_ms(time_text)}


def parse_time_ms(text: str) -> float:
    normalized = text.strip().lower()
    multiplier = 1.0
    if normalized.endswith("us"):
        multiplier = 0.001
        normalized = normalized[:-2]
    elif normalized.endswith("ms"):
        normalized = normalized[:-2]
    elif normalized.endswith("s"):
        multiplier = 1000.0
        normalized = normalized[:-1]
    try:
        value = float(normalized) * multiplier
    except ValueError as exc:
        raise SystemExit(f"Invalid time: {text}") from exc
    if value < 0:
        raise SystemExit(f"Time must be non-negative: {text}")
    return value


if __name__ == "__main__":
    main()
