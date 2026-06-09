#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


RISE_TIME_LIMIT_NS = {
    "standard": 1000.0,
    "fast": 300.0,
    "fast-plus": 120.0,
}

DEFAULT_SINK_MA = {
    "standard": 3.0,
    "fast": 3.0,
    "fast-plus": 20.0,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check I2C pull-up value against rise time and sink current.")
    parser.add_argument("--pullup", required=True, help="Pull-up resistance, e.g. 4.7k.")
    parser.add_argument("--capacitance-pf", required=True, type=float, help="Estimated bus capacitance in pF.")
    parser.add_argument("--vdd", default=3.3, type=float, help="Bus voltage.")
    parser.add_argument("--vol-max", default=0.4, type=float, help="Low-level output voltage limit.")
    parser.add_argument(
        "--mode",
        choices=sorted(RISE_TIME_LIMIT_NS),
        default="fast",
        help="I2C speed mode.",
    )
    parser.add_argument(
        "--sink-ma",
        default=None,
        type=float,
        help="Device sink current capability in mA. Defaults by mode.",
    )
    args = parser.parse_args()

    pullup_ohms = parse_resistance(args.pullup)
    if args.capacitance_pf <= 0:
        raise SystemExit("--capacitance-pf must be positive")
    if args.vdd <= args.vol_max:
        raise SystemExit("--vdd must be greater than --vol-max")

    capacitance_f = args.capacitance_pf * 1e-12
    rise_time_ns = 0.8473 * pullup_ohms * capacitance_f * 1e9
    rise_limit_ns = RISE_TIME_LIMIT_NS[args.mode]
    sink_ma = args.sink_ma if args.sink_ma is not None else DEFAULT_SINK_MA[args.mode]
    r_min = (args.vdd - args.vol_max) / (sink_ma / 1000.0)
    r_max = (rise_limit_ns * 1e-9) / (0.8473 * capacitance_f)

    findings = []
    if rise_time_ns > rise_limit_ns:
        findings.append("Pull-up is too weak or bus capacitance too high for the selected I2C mode.")
    else:
        findings.append("Estimated rise time is within the selected I2C mode limit.")
    if pullup_ohms < r_min:
        findings.append("Pull-up may be too strong for the configured sink-current limit.")
    if pullup_ohms > r_max:
        findings.append("Pull-up exceeds the estimated maximum resistance for rise time.")
    if args.capacitance_pf > 400:
        findings.append("Bus capacitance is high; verify the selected mode and board/cable loading.")

    output = {
        "mode": args.mode,
        "pullup_ohms": pullup_ohms,
        "capacitance_pf": args.capacitance_pf,
        "vdd": args.vdd,
        "vol_max": args.vol_max,
        "sink_ma": sink_ma,
        "estimated_rise_time_ns": rise_time_ns,
        "rise_time_limit_ns": rise_limit_ns,
        "estimated_min_pullup_ohms": r_min,
        "estimated_max_pullup_ohms": r_max,
        "rise_time_ok": rise_time_ns <= rise_limit_ns,
        "sink_current_ok": pullup_ohms >= r_min,
        "findings": findings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_resistance(text: str) -> float:
    normalized = text.strip().lower().replace("ohm", "")
    multiplier = 1.0
    if normalized.endswith("k"):
        multiplier = 1000.0
        normalized = normalized[:-1]
    elif normalized.endswith("m"):
        multiplier = 1000.0 * 1000.0
        normalized = normalized[:-1]
    try:
        value = float(normalized) * multiplier
    except ValueError as exc:
        raise SystemExit(f"Invalid resistance: {text}") from exc
    if value <= 0:
        raise SystemExit("--pullup must be positive")
    return value


if __name__ == "__main__":
    main()
