#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze decoded or raw I2C logic analyzer CSV exports.")
    parser.add_argument("--trace", help="CSV trace. Decoded: time,event,address,rw,ack,data. Raw: time,scl,sda.")
    parser.add_argument("--out", help="Optional output JSON path. Defaults to stdout.")
    args = parser.parse_args()

    output = analyze_trace(Path(args.trace)) if args.trace else missing_trace_output()
    write_output(output, args.out)


def missing_trace_output() -> dict[str, object]:
    return {
        "format_detected": "missing",
        "bus_idle_ok": None,
        "first_start_time": None,
        "addresses_seen": [],
        "nack_events": [],
        "whoami_read_seen": False,
        "stuck_low": {"scl": None, "sda": None},
        "candidate_hypotheses": [
            "No trace was provided; preserve a decoded CSV or raw time,scl,sda CSV before ranking electrical causes."
        ],
        "confidence": "low",
        "limitations": ["Missing trace input"],
    }


def analyze_trace(path: Path) -> dict[str, object]:
    if not path.is_file():
        output = missing_trace_output()
        output["limitations"] = [f"Trace file not found: {path}"]
        return output
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            rows = [{normalize_key(k): (v or "").strip() for k, v in row.items()} for row in reader]
            headers = {normalize_key(item) for item in (reader.fieldnames or [])}
    except Exception as exc:
        output = missing_trace_output()
        output["format_detected"] = "unknown"
        output["limitations"] = [f"Could not parse CSV: {exc}"]
        return output

    if {"time", "event", "address", "rw", "ack", "data"}.issubset(headers):
        return analyze_decoded(rows)
    if {"time", "scl", "sda"}.issubset(headers):
        return analyze_raw(rows)
    output = missing_trace_output()
    output["format_detected"] = "unknown"
    output["limitations"] = [f"Unsupported CSV columns: {', '.join(sorted(headers))}"]
    return output


def analyze_decoded(rows: list[dict[str, str]]) -> dict[str, object]:
    first_start_time = None
    addresses: list[str] = []
    nack_events: list[dict[str, object]] = []
    whoami_read_seen = False
    last_register = None

    for row in rows:
        event = row.get("event", "").lower()
        if first_start_time is None and "start" in event:
            first_start_time = row.get("time") or None

        address = normalize_address(row.get("address", ""))
        if address and address not in addresses:
            addresses.append(address)

        ack = row.get("ack", "").lower()
        if "nack" in event or ack in {"0", "false", "no", "n", "nack"}:
            nack_events.append({"time": row.get("time"), "address": address, "event": row.get("event"), "rw": row.get("rw")})

        data = normalize_data(row.get("data", ""))
        if data == "0x0f" or "who" in event:
            last_register = "WHO_AM_I"
        if last_register == "WHO_AM_I" and (row.get("rw", "").lower().startswith("r") or "read" in event):
            whoami_read_seen = True

    hypotheses = []
    if nack_events:
        hypotheses.append("Address, power timing, pull-up, or bus-level issue causing NACK.")
    if first_start_time is None:
        hypotheses.append("Capture may not include the first I2C transaction or START decode failed.")
    if whoami_read_seen and not nack_events:
        hypotheses.append("WHO_AM_I transaction appears on the bus; compare returned data with the expected sensor identity.")
    if not hypotheses:
        hypotheses.append("Decoded trace has no obvious NACK; correlate with serial log and power timing.")

    return {
        "format_detected": "decoded_csv",
        "bus_idle_ok": True,
        "first_start_time": first_start_time,
        "addresses_seen": addresses,
        "nack_events": nack_events,
        "whoami_read_seen": whoami_read_seen,
        "stuck_low": {"scl": False, "sda": False},
        "candidate_hypotheses": hypotheses,
        "confidence": "medium" if nack_events or whoami_read_seen else "low",
        "limitations": ["Decoded CSV does not prove power rail timing without a correlated scope capture."],
    }


def analyze_raw(rows: list[dict[str, str]]) -> dict[str, object]:
    samples = []
    for row in rows:
        try:
            time_value = float(row.get("time", ""))
            scl = to_level(row.get("scl", ""))
            sda = to_level(row.get("sda", ""))
        except ValueError:
            continue
        if scl is not None and sda is not None:
            samples.append((time_value, scl, sda))

    if not samples:
        output = missing_trace_output()
        output["format_detected"] = "raw_simple_csv"
        output["limitations"] = ["No valid raw samples found"]
        return output

    initial = samples[: min(10, len(samples))]
    bus_idle_ok = majority_high([item[1] for item in initial]) and majority_high([item[2] for item in initial])
    scl_low_ratio = sum(1 for _, scl, _ in samples if scl == 0) / len(samples)
    sda_low_ratio = sum(1 for _, _, sda in samples if sda == 0) / len(samples)
    stuck_low = {"scl": scl_low_ratio > 0.9, "sda": sda_low_ratio > 0.9}
    first_start_time = detect_start_like(samples)

    hypotheses = []
    if stuck_low["scl"] or stuck_low["sda"]:
        hypotheses.append("SCL or SDA is stuck low; check pull-ups, short, held peripheral, or pinmux.")
    if not bus_idle_ok:
        hypotheses.append("Bus idle is not high; check pull-ups, level shifter enable, and sensor power.")
    if first_start_time is None:
        hypotheses.append("No start-like SDA falling edge while SCL high was found in raw capture.")
    if not hypotheses:
        hypotheses.append("Raw trace has idle-high and start-like activity; decode it for address and ACK/NACK evidence.")

    return {
        "format_detected": "raw_simple_csv",
        "bus_idle_ok": bus_idle_ok,
        "first_start_time": first_start_time,
        "addresses_seen": [],
        "nack_events": [],
        "whoami_read_seen": False,
        "stuck_low": stuck_low,
        "candidate_hypotheses": hypotheses,
        "confidence": "medium" if stuck_low["scl"] or stuck_low["sda"] or not bus_idle_ok else "low",
        "limitations": ["Raw CSV check is heuristic and does not decode address, ACK/NACK, or register data."],
    }


def normalize_key(value: str | None) -> str:
    return (value or "").strip().lower().replace(" ", "_")


def normalize_address(value: str) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    try:
        return f"0x{int(text, 0):02x}"
    except ValueError:
        return text


def normalize_data(value: str) -> str | None:
    if not value:
        return None
    text = value.strip().lower()
    try:
        return f"0x{int(text, 0):02x}"
    except ValueError:
        return text


def to_level(value: str) -> int | None:
    text = value.strip().lower()
    if text in {"1", "high", "h", "true"}:
        return 1
    if text in {"0", "low", "l", "false"}:
        return 0
    numeric = float(text)
    return 1 if numeric > 0.5 else 0


def majority_high(values: list[int]) -> bool:
    if not values:
        return False
    return sum(values) / len(values) >= 0.8


def detect_start_like(samples: list[tuple[float, int, int]]) -> float | None:
    previous_sda = samples[0][2]
    for time_value, scl, sda in samples[1:]:
        if scl == 1 and previous_sda == 1 and sda == 0:
            return time_value
        previous_sda = sda
    return None


def write_output(output: dict[str, object], out: str | None) -> None:
    text = json.dumps(output, indent=2, sort_keys=True)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
