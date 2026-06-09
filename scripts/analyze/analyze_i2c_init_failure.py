#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LOG_SIGNATURES = {
    "failed_to_initialize": [r"failed to initialize"],
    "device_not_ready": [r"device not ready", r"not ready"],
    "i2c_error": [r"i2c error", r"i2c_nrfx_twim", r"i2c line", r"error 0x[0-9a-f]+"],
    "bus_error": [r"bus error"],
    "nack": [r"\bnack\b", r"not acknowledged"],
    "timeout": [r"\btimeout\b", r"timed out"],
    "who_am_i": [r"who[_ -]?am[_ -]?i"],
    "lsm6dsl": [r"lsm6dsl"],
    "lsm6ds3": [r"lsm6ds3"],
}

REQUIRED_CONFIG = [
    "CONFIG_SENSOR",
    "CONFIG_I2C",
    "CONFIG_GPIO",
    "CONFIG_LSM6DSL",
    "CONFIG_LSM6DSL_TRIGGER_GLOBAL_THREAD",
]

SENSOR_COMPAT_RE = re.compile(r'"([^"]*(?:lsm6dsl|lsm6ds3|sensor)[^"]*)"', re.IGNORECASE)
PROP_RE = re.compile(r"^\s*([A-Za-z0-9_,#\-]+)\s*(?:=|;)", re.MULTILINE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Zephyr I2C sensor initialization failures.")
    parser.add_argument("--serial-log", help="Zephyr serial log from boot through sensor probe.")
    parser.add_argument("--dts", help="Generated zephyr.dts or DTS file.")
    parser.add_argument("--config", help="Generated .config, autoconf.h, or config fragment.")
    parser.add_argument("--out", help="Optional output JSON path. Defaults to stdout.")
    args = parser.parse_args()

    missing: list[str] = []
    serial_text = read_optional(args.serial_log, "serial_log", missing)
    dts_text = read_optional(args.dts, "dts", missing)
    config_text = read_optional(args.config, "kconfig", missing)

    log_signatures = find_log_signatures(serial_text)
    dts_status = parse_dts(dts_text)
    kconfig_status = parse_kconfig_status(config_text)
    detected_sensor = detect_sensor(serial_text, dts_status)
    missing_evidence = build_missing_evidence(missing, log_signatures, dts_status, kconfig_status)
    candidate_hypotheses = build_hypotheses(log_signatures, dts_status, kconfig_status, missing_evidence)
    output = {
        "detected_sensor": detected_sensor,
        "i2c_address": dts_status.get("reg"),
        "bus": dts_status.get("bus"),
        "dts_status": dts_status,
        "kconfig_status": kconfig_status,
        "log_failure_signatures": log_signatures,
        "missing_evidence": missing_evidence,
        "candidate_hypotheses": candidate_hypotheses,
        "recommended_next_measurements": recommend_measurements(log_signatures, dts_status),
    }
    write_output(output, args.out)


def read_optional(path_text: str | None, evidence_name: str, missing: list[str]) -> str:
    if not path_text:
        add_unique(missing, evidence_name)
        return ""
    path = Path(path_text)
    if not path.is_file():
        add_unique(missing, evidence_name)
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        add_unique(missing, evidence_name)
        return ""


def find_log_signatures(text: str) -> list[dict[str, object]]:
    lower = text.lower()
    hits: list[dict[str, object]] = []
    for name, patterns in LOG_SIGNATURES.items():
        matched_lines = []
        for line in text.splitlines():
            line_lower = line.lower()
            if any(re.search(pattern, line_lower) for pattern in patterns):
                matched_lines.append(line.strip())
        if matched_lines or any(re.search(pattern, lower) for pattern in patterns):
            hits.append({"signature": name, "count": len(matched_lines), "examples": matched_lines[:3]})
    return hits


def parse_dts(text: str) -> dict[str, object]:
    if not text:
        return {"ok": False, "reason": "missing dts"}

    lines = text.splitlines()
    blocks = find_blocks(lines)
    sensor = None
    for block in blocks:
        compatibles = parse_compatible(block["body"])
        if any("lsm6dsl" in item.lower() or "lsm6ds3" in item.lower() for item in compatibles):
            sensor = block | {"compatible": compatibles}
            break
    if sensor is None:
        for block in blocks:
            header = str(block["header"])
            props = set(PROP_RE.findall(str(block["body"])))
            if re.search(r"lsm6d", header, flags=re.IGNORECASE) and "reg" in props:
                sensor = block | {"compatible": parse_compatible(block["body"])}
                break
    if sensor is None:
        return {"ok": False, "reason": "sensor node not found"}

    body = str(sensor["body"])
    props = set(PROP_RE.findall(body))
    reg = parse_reg(body)
    status = parse_status(body)
    bus = find_parent_bus(lines, int(sensor["line"]))
    compatible = sensor.get("compatible", [])
    ok = status not in {"disabled", "reserved", "fail"} and bool(compatible) and bool(reg) and bool(bus)
    return {
        "ok": ok,
        "node_header": str(sensor["header"]).strip(),
        "line": sensor["line"],
        "compatible": compatible,
        "reg": reg,
        "irq_gpios_present": "irq-gpios" in props or "interrupt-gpios" in props,
        "status": status,
        "bus": bus,
        "properties": sorted(props),
    }


def find_blocks(lines: list[str]) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    for index, line in enumerate(lines):
        if "{" not in line:
            continue
        body_lines = [line]
        depth = line.count("{") - line.count("}")
        cursor = index + 1
        while cursor < len(lines) and depth > 0:
            body_lines.append(lines[cursor])
            depth += lines[cursor].count("{") - lines[cursor].count("}")
            cursor += 1
        blocks.append({"line": index + 1, "header": line, "body": "\n".join(body_lines)})
    return blocks


def parse_compatible(body: str) -> list[str]:
    match = re.search(r"compatible\s*=\s*([^;]+);", body, re.DOTALL)
    if match:
        return re.findall(r'"([^"]+)"', match.group(1))
    return SENSOR_COMPAT_RE.findall(body)


def parse_reg(body: str) -> str | None:
    match = re.search(r"\breg\s*=\s*<\s*([^>\s]+)", body)
    if not match:
        return None
    value = match.group(1).strip()
    try:
        return f"0x{int(value, 0):x}"
    except ValueError:
        return value


def parse_status(body: str) -> str:
    match = re.search(r'status\s*=\s*"([^"]+)"', body)
    return match.group(1) if match else "okay_or_unspecified"


def find_parent_bus(lines: list[str], line_number: int) -> str | None:
    for index in range(line_number - 2, -1, -1):
        line = lines[index].strip()
        if "{" not in line:
            continue
        if re.search(r"(^&i2c[0-9A-Za-z_]*\s*\{)|(\bi2c@[0-9a-fA-F]+)", line):
            return line.split("{", 1)[0].strip()
        if re.search(r"(^&spi[0-9A-Za-z_]*\s*\{)|(\bspi@[0-9a-fA-F]+)", line):
            return line.split("{", 1)[0].strip()
    return None


def parse_kconfig_status(text: str) -> dict[str, object]:
    if not text:
        return {"ok": False, "reason": "missing kconfig", "checks": []}
    symbols = parse_symbols(text)
    checks = []
    for name in REQUIRED_CONFIG:
        actual = symbols.get(name, "n")
        checks.append({"symbol": name, "expected": "y", "actual": actual, "ok": actual == "y"})
    return {"ok": all(item["ok"] for item in checks), "checks": checks}


def parse_symbols(text: str) -> dict[str, str]:
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


def detect_sensor(serial_text: str, dts_status: dict[str, object]) -> str:
    lower = serial_text.lower()
    if "lsm6ds3" in lower:
        return "LSM6DS3 family"
    if "lsm6dsl" in lower:
        return "LSM6DSL driver path"
    compatibles = dts_status.get("compatible")
    if isinstance(compatibles, list) and compatibles:
        return ", ".join(str(item) for item in compatibles)
    return "unknown"


def build_missing_evidence(
    initial_missing: list[str],
    log_signatures: list[dict[str, object]],
    dts_status: dict[str, object],
    kconfig_status: dict[str, object],
) -> list[str]:
    missing = list(initial_missing)
    signatures = {str(item["signature"]) for item in log_signatures}
    bus_failure = bool(signatures & {"i2c_error", "bus_error", "nack", "timeout", "who_am_i", "failed_to_initialize"})
    if bus_failure:
        add_unique(missing, "logic_trace")
    if bus_failure and dts_status.get("ok") and kconfig_status.get("ok"):
        add_unique(missing, "scope_trace_power_rail")
    return missing


def build_hypotheses(
    log_signatures: list[dict[str, object]],
    dts_status: dict[str, object],
    kconfig_status: dict[str, object],
    missing_evidence: list[str],
) -> list[dict[str, object]]:
    signatures = {str(item["signature"]) for item in log_signatures}
    hypotheses: list[dict[str, object]] = []

    if not dts_status.get("ok"):
        hypotheses.append(
            hypothesis(
                "H_DTS",
                "Generated DTS does not prove an enabled sensor node on a ready bus.",
                "medium",
                ["DTS status is incomplete or not ok"],
                ["No bus-level conclusion is possible until DTS is fixed"],
                ["generated zephyr.dts"] if "dts" in missing_evidence else [],
                "Run dts_probe_check.py for the exact sensor node and parent bus.",
                "The sensor node, compatible, reg, status, and bus path become explicit.",
                "Fix board target, overlay, node status, compatible, reg, or bus node.",
            )
        )

    if not kconfig_status.get("ok"):
        bad = [
            str(item["symbol"])
            for item in kconfig_status.get("checks", [])
            if isinstance(item, dict) and not item.get("ok")
        ]
        hypotheses.append(
            hypothesis(
                "H_KCONFIG",
                "Required Zephyr sensor, bus, GPIO, driver, or trigger config is missing.",
                "medium",
                [f"Missing or unexpected symbols: {', '.join(bad) or 'unknown'}"],
                ["DTS may still be correct, so config must be checked separately"],
                ["generated .config"] if "kconfig" in missing_evidence else [],
                "Run kconfig_check.py for CONFIG_SENSOR, CONFIG_I2C, CONFIG_GPIO, CONFIG_LSM6DSL, and trigger mode.",
                "The failing symbol is visible before runtime debugging begins.",
                "Enable the missing symbol in prj.conf, board defconfig, or selected driver options.",
            )
        )

    if signatures & {"i2c_error", "bus_error", "nack", "timeout", "who_am_i", "failed_to_initialize"}:
        confidence = "medium" if dts_status.get("ok") and kconfig_status.get("ok") else "low"
        hypotheses.append(
            hypothesis(
                "H_BUS_POWER",
                "The first I2C sensor transaction is failing because the address, bus lines, or sensor power path is not valid at probe time.",
                confidence,
                ["Serial log contains I2C/probe failure signatures"],
                ["Generated DTS and Kconfig are ok" if dts_status.get("ok") and kconfig_status.get("ok") else "DTS/Kconfig are not fully cleared"],
                [item for item in missing_evidence if item in {"logic_trace", "scope_trace_power_rail"}],
                "Capture SDA, SCL, sensor VDD, and enable/reset from reset through the first WHO_AM_I or reboot register access.",
                "A NACK, stuck-low line, or bus access before stable VDD identifies the failing branch.",
                "Correct reg address, pull-ups, bus speed, regulator modeling, or startup-delay-us based on the capture.",
            )
        )

    if "device_not_ready" in signatures and dts_status.get("irq_gpios_present") is False:
        hypotheses.append(
            hypothesis(
                "H_IRQ_TRIGGER",
                "Trigger mode may be enabled without the interrupt GPIO evidence needed by the driver.",
                "low",
                ["Log shows device readiness failure and DTS has no irq-gpios or interrupt-gpios property"],
                ["Probe failure may occur before trigger mode is reached"],
                ["polling_mode_result"],
                "Disable trigger mode or force polling mode, then re-run sensor fetch.",
                "Polling works while trigger mode fails if the interrupt path is the branch.",
                "Correct irq-gpios pin/polarity or trigger Kconfig after polling mode passes.",
            )
        )

    if not hypotheses:
        hypotheses.append(
            hypothesis(
                "H_INCOMPLETE",
                "Evidence is insufficient to rank a Zephyr I2C sensor bring-up root cause.",
                "low",
                ["No decisive log/DTS/Kconfig failure signature was found"],
                ["No confirmed negative evidence is available"],
                missing_evidence,
                "Collect serial log, generated DTS, generated .config, and bus capture.",
                "The next packet contains enough evidence for DTS, Kconfig, bus, or power ranking.",
                "Do not patch driver code before the minimum evidence exists.",
            )
        )
    return hypotheses


def hypothesis(
    hypothesis_id: str,
    root_cause: str,
    confidence: str,
    evidence_for: list[str],
    evidence_against: list[str],
    missing_evidence: list[str],
    verification_step: str,
    expected_observation: str,
    fix_if_confirmed: str,
) -> dict[str, object]:
    return {
        "hypothesis_id": hypothesis_id,
        "root_cause": root_cause,
        "confidence": confidence,
        "evidence_for": evidence_for,
        "evidence_against": evidence_against,
        "missing_evidence": missing_evidence,
        "verification_step": verification_step,
        "expected_observation": expected_observation,
        "fix_if_confirmed": fix_if_confirmed,
    }


def recommend_measurements(log_signatures: list[dict[str, object]], dts_status: dict[str, object]) -> list[str]:
    recommendations = [
        "Preserve generated zephyr.dts, generated .config, build log, and serial log in the debug packet.",
    ]
    signatures = {str(item["signature"]) for item in log_signatures}
    if signatures & {"i2c_error", "bus_error", "nack", "timeout", "who_am_i", "failed_to_initialize"}:
        recommendations.extend(
            [
                "Capture decoded I2C CSV with time,event,address,rw,ack,data.",
                "Capture raw SDA/SCL if decode is unavailable and run analyze_i2c_logic_trace.py.",
                "Scope sensor VDD and enable/reset pin against the first I2C transaction.",
                f"Compare decoded address with DTS reg {dts_status.get('reg') or 'unknown'}.",
            ]
        )
    return recommendations


def add_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def write_output(output: dict[str, object], out: str | None) -> None:
    text = json.dumps(output, indent=2, sort_keys=True)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
