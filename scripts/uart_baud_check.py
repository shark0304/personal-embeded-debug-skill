#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate UART divisor and baud-rate error.")
    parser.add_argument("--clock", required=True, help="UART peripheral clock, e.g. 80M or 16000000.")
    parser.add_argument("--baud", required=True, type=float, help="Requested baud rate.")
    parser.add_argument("--oversampling", default=16, type=int, help="Oversampling ratio, commonly 16 or 8.")
    parser.add_argument(
        "--fractional-bits",
        default=4,
        type=int,
        help="Generic fractional divisor bits. Use 0 for integer-only UARTs.",
    )
    parser.add_argument(
        "--peer-error-percent",
        default=0.0,
        type=float,
        help="Absolute baud error of the other endpoint, percent.",
    )
    parser.add_argument(
        "--tolerance-percent",
        default=2.0,
        type=float,
        help="Combined absolute error budget to treat as suspicious.",
    )
    args = parser.parse_args()

    clock = parse_size(args.clock)
    if args.baud <= 0:
        raise SystemExit("--baud must be positive")
    if args.oversampling <= 0:
        raise SystemExit("--oversampling must be positive")
    if args.fractional_bits < 0 or args.fractional_bits > 16:
        raise SystemExit("--fractional-bits must be in 0..16")

    ideal_divisor = clock / (args.baud * args.oversampling)
    scale = 1 << args.fractional_bits
    quantized_divisor = round(ideal_divisor * scale) / scale
    if quantized_divisor <= 0:
        raise SystemExit("Computed divisor is zero; clock is too low for this baud/oversampling.")

    actual_baud = clock / (args.oversampling * quantized_divisor)
    local_error_percent = ((actual_baud - args.baud) / args.baud) * 100.0
    combined_abs_error = abs(local_error_percent) + abs(args.peer_error_percent)
    suspicious = combined_abs_error > args.tolerance_percent

    notes = [
        "This is a generic divisor estimate; verify exact BRR/divider encoding in the MCU reference manual.",
        "Measure a 0x55 pattern at the pins to confirm the actual bit time.",
    ]
    if suspicious:
        notes.append("Combined baud error exceeds the selected tolerance.")
    if abs(local_error_percent) < 0.01 and args.peer_error_percent == 0:
        notes.append("Divider quantization looks clean; next check clock source accuracy and frame format.")

    output = {
        "clock_hz": clock,
        "requested_baud": args.baud,
        "oversampling": args.oversampling,
        "fractional_bits": args.fractional_bits,
        "ideal_divisor": ideal_divisor,
        "quantized_divisor": quantized_divisor,
        "actual_baud": actual_baud,
        "local_error_percent": local_error_percent,
        "peer_error_percent": args.peer_error_percent,
        "combined_abs_error_percent": combined_abs_error,
        "tolerance_percent": args.tolerance_percent,
        "suspicious": suspicious,
        "notes": notes,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_size(text: str) -> int:
    normalized = text.strip().lower()
    multiplier = 1
    if normalized.endswith("khz"):
        multiplier = 1000
        normalized = normalized[:-3]
    elif normalized.endswith("mhz"):
        multiplier = 1000 * 1000
        normalized = normalized[:-3]
    elif normalized.endswith("hz"):
        normalized = normalized[:-2]
    elif normalized.endswith("k"):
        multiplier = 1000
        normalized = normalized[:-1]
    elif normalized.endswith("m"):
        multiplier = 1000 * 1000
        normalized = normalized[:-1]
    try:
        return int(float(normalized) * multiplier)
    except ValueError as exc:
        raise SystemExit(f"Invalid clock: {text}") from exc


if __name__ == "__main__":
    main()
