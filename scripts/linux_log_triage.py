#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PATTERNS = [
    (
        "kernel_panic_oops",
        re.compile(r"\b(kernel panic|oops|BUG:|NULL pointer|unable to handle kernel|general protection fault)\b", re.I),
        "Capture full panic/oops, symbols, taint flags, and preceding driver messages.",
    ),
    (
        "deferred_probe",
        re.compile(r"\b(EPROBE_DEFER|deferred probe|probe defer|devices_deferred)\b", re.I),
        "Inspect /sys/kernel/debug/devices_deferred and missing supplier resources.",
    ),
    (
        "driver_probe_fail",
        re.compile(r"\b(probe failed|failed to probe|probe of .* failed|error .*probe)\b", re.I),
        "Check driver resource acquisition, DT binding, and errno near the probe failure.",
    ),
    (
        "device_tree",
        re.compile(r"\b(device tree|devicetree|OF:|compatible|dtb|overlay|phandle)\b", re.I),
        "Confirm the booted DTB, compatible string, status, and binding-required properties.",
    ),
    (
        "regulator_clock_reset",
        re.compile(r"\b(regulator|supply|dummy regulator|clk|clock|reset controller|power-domain)\b.*\b(fail|missing|not found|defer|invalid|dummy)\b", re.I),
        "Check supplies, clocks, resets, power domains, and probe order.",
    ),
    (
        "pinctrl_gpio",
        re.compile(r"\b(pinctrl|pinmux|gpio)\b.*\b(fail|busy|invalid|not found|request|conflict)\b", re.I),
        "Check pinctrl state names, GPIO polarity, ownership, and mux conflicts.",
    ),
    (
        "firmware_missing",
        re.compile(r"\b(firmware|request_firmware)\b.*\b(fail|not found|No such file|missing)\b", re.I),
        "Verify firmware path, rootfs contents, initramfs timing, and driver fallback behavior.",
    ),
    (
        "rootfs_boot",
        re.compile(r"\b(unable to mount root fs|VFS:|init not found|No working init|Waiting for root device)\b", re.I),
        "Check bootargs, root device, storage driver, filesystem, and init path.",
    ),
    (
        "bus_timeout_io",
        re.compile(r"\b(timeout|timed out|I/O error|NACK|arbitration lost|CRC error|DMA timeout)\b", re.I),
        "Separate electrical/bus timing, DMA/cache, and driver state-machine causes.",
    ),
    (
        "hang_stall_watchdog",
        re.compile(r"\b(hung task|RCU stall|soft lockup|hard lockup|watchdog)\b", re.I),
        "Use ftrace/perf/lockdep where available and inspect long IRQ-disabled or non-preemptible sections.",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage embedded Linux dmesg/kernel logs for common failure patterns.")
    parser.add_argument("--log", default=None, help="Log file. Reads stdin when omitted.")
    parser.add_argument("--max-lines", default=5, type=int, help="Example lines to keep per category.")
    args = parser.parse_args()

    text = Path(args.log).read_text(encoding="utf-8", errors="replace") if args.log else sys.stdin.read()
    results = {}
    for lineno, line in enumerate(text.splitlines(), start=1):
        for category, pattern, next_check in PATTERNS:
            if pattern.search(line):
                item = results.setdefault(
                    category,
                    {"count": 0, "examples": [], "next_check": next_check},
                )
                item["count"] += 1
                if len(item["examples"]) < args.max_lines:
                    item["examples"].append({"line": lineno, "text": line.strip()})

    output = {
        "categories": results,
        "category_count": len(results),
        "line_count": len(text.splitlines()),
        "summary": build_summary(results),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def build_summary(results: dict[str, dict[str, object]]) -> list[str]:
    if not results:
        return ["No known high-signal Linux bring-up patterns matched; inspect timestamps and subsystem-specific logs."]
    priority = [
        "kernel_panic_oops",
        "rootfs_boot",
        "deferred_probe",
        "driver_probe_fail",
        "regulator_clock_reset",
        "pinctrl_gpio",
        "device_tree",
        "hang_stall_watchdog",
        "bus_timeout_io",
        "firmware_missing",
    ]
    return [f"{name}: {results[name]['count']} match(es)" for name in priority if name in results]


if __name__ == "__main__":
    main()
