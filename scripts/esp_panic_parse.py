#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "guru_meditation": re.compile(r"Guru Meditation Error:\s*Core\s*(\d+)\s+panic'ed \(([^)]+)\)", re.I),
    "task_watchdog": re.compile(r"Task watchdog got triggered|task_wdt", re.I),
    "interrupt_watchdog": re.compile(r"Interrupt wdt timeout|interrupt watchdog", re.I),
    "cache_disabled": re.compile(r"Cache disabled but cached memory region accessed", re.I),
    "brownout": re.compile(r"Brownout detector was triggered", re.I),
    "backtrace": re.compile(r"Backtrace:\s*(.*)", re.I),
    "excvaddr": re.compile(r"EXCVADDR:\s*([0-9a-fxA-F]+)", re.I),
    "pc": re.compile(r"\bPC\s*:\s*([0-9a-fxA-F]+)", re.I),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse ESP-IDF panic/watchdog logs.")
    parser.add_argument("--log", required=True, help="ESP-IDF monitor/panic log.")
    args = parser.parse_args()

    text = Path(args.log).read_text(encoding="utf-8", errors="replace")
    findings = []
    registers = {}
    backtraces = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if match := PATTERNS["guru_meditation"].search(line):
            findings.append({"type": "guru_meditation", "line": lineno, "core": match.group(1), "cause": match.group(2)})
        for key in ("task_watchdog", "interrupt_watchdog", "cache_disabled", "brownout"):
            if PATTERNS[key].search(line):
                findings.append({"type": key, "line": lineno, "text": line.strip()})
        if match := PATTERNS["excvaddr"].search(line):
            registers["EXCVADDR"] = match.group(1)
        if match := PATTERNS["pc"].search(line):
            registers["PC"] = match.group(1)
        if match := PATTERNS["backtrace"].search(line):
            backtraces.append({"line": lineno, "text": match.group(1).strip(), "addresses": re.findall(r"0x[0-9a-fA-F]+", match.group(1))})

    hints = build_hints(findings, registers, backtraces)
    output = {"findings": findings, "registers": registers, "backtraces": backtraces, "hints": hints, "ok": bool(findings or backtraces or registers)}
    print(json.dumps(output, indent=2, sort_keys=True))
    if not output["ok"]:
        raise SystemExit(1)


def build_hints(findings: list[dict[str, object]], registers: dict[str, str], backtraces: list[dict[str, object]]) -> list[str]:
    types = {str(item["type"]) for item in findings}
    hints = []
    if "cache_disabled" in types:
        hints.append("Check ISR/flash-cache-disabled paths for IRAM_ATTR code and DRAM data requirements.")
    if "task_watchdog" in types:
        hints.append("List tasks on each core, blocking calls, critical sections, and watchdog feed points.")
    if "interrupt_watchdog" in types:
        hints.append("Inspect long ISRs, disabled interrupts, spinlocks, and flash/PSRAM stalls.")
    if "brownout" in types:
        hints.append("Check power supply droop, radio current bursts, USB cable, and brownout threshold.")
    if registers.get("EXCVADDR") in {"0x00000000", "0"}:
        hints.append("EXCVADDR is zero; NULL pointer dereference is plausible.")
    if backtraces:
        hints.append("Decode backtrace addresses with ESP-IDF monitor, addr2line, or symbolicate_addresses.py.")
    return hints


if __name__ == "__main__":
    main()
