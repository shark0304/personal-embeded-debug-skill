#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parents[1]
COLLECT_DIR = SKILL_DIR / "scripts" / "collect"
for path in (COLLECT_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_debug_packet import load_packet, validate_debug_packet  # noqa: E402


TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"


def main() -> None:
    parser = argparse.ArgumentParser(description="Recommend evidence-capture templates and patches from a packet/symptom.")
    parser.add_argument("--packet", help="debug_packet.yaml/json path.")
    parser.add_argument("--project-root", help="Project root used when packet is not available.")
    parser.add_argument("--platform", default="", help="Platform hint when packet is not available.")
    parser.add_argument("--symptom", default="", help="Short symptom statement.")
    parser.add_argument("--out", help="Optional output path.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    packet: dict[str, Any] = {}
    if args.packet:
        packet = load_packet(Path(args.packet))
    elif args.project_root:
        packet = {"project_root": str(Path(args.project_root).resolve()), "platform": args.platform or "unknown", "artifacts": {}, "symptoms": [args.symptom] if args.symptom else []}
    else:
        raise SystemExit("provide --packet or --project-root")
    if args.symptom:
        packet["symptoms"] = [*normalize_list(packet.get("symptoms")), args.symptom]

    result = suggest_evidence_capture(packet)
    text = render_markdown(result) if args.format == "markdown" else json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


def suggest_evidence_capture(packet: dict[str, Any]) -> dict[str, Any]:
    validation = validate_debug_packet(packet)
    platform = str(packet.get("platform") or "unknown").lower()
    text = " ".join([platform, json.dumps(packet, sort_keys=True), *normalize_list(packet.get("symptoms"))]).lower()
    missing = normalize_list(validation.get("required_evidence", {}).get("missing"))
    recommendations = rank_recommendations(build_recommendations(platform, text, missing))
    return {
        "platform": platform,
        "evidence_score": validation["score"],
        "evidence_grade": validation["grade"],
        "missing_required_evidence": missing,
        "recommendations": recommendations,
        "boundary": "These recommendations add observability or capture existing evidence; they are not root-cause fixes by themselves.",
    }


def build_recommendations(platform: str, text: str, missing: list[str]) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    if any(token in text for token in ("hardfault", "busfault", "memmanage", "usagefault", "cfsr", "hfsr")) or "fault_registers" in missing:
        recs.append(rec("cortexm_fault_capture", 95, "Capture CFSR/HFSR/BFAR/MMFAR and stacked frame before reset.", "hardfault_capture.c", "debugger-attached"))
    if platform in {"freertos", "cortex-m"} or any(token in text for token in ("freertos", "deadlock", "priority inversion", "queue", "semaphore", "task")):
        recs.append(rec("freertos_runtime_snapshot", 82, "Capture task states, stack high-water marks, heap, and blocked resources.", "freertos_snapshot.c", "safe-local-instrumentation"))
    if platform == "zephyr" or "zephyr" in text:
        recs.append(rec("zephyr_thread_snapshot", 78, "Capture Zephyr thread, stack, and scheduler state around the failure.", "zephyr_thread_snapshot.c", "safe-local-instrumentation"))
    if platform == "embedded-linux" or any(token in text for token in ("probe defer", "dmesg", "driver", "device tree", "linux")):
        recs.append(rec("linux_probe_trace", 85, "Capture dmesg, dynamic debug, tracepoints, and debugfs/sysfs state for probe failures.", "linux_trace_probe.sh", "kernel-runtime-change"))
    if any(token in text for token in ("i2c", "sensor", "who_am_i", "nack", "probe failed", "logic")):
        recs.append(rec("i2c_sensor_measurement_plan", 90, "Capture address phase, first identity read, pull-up/rise-time, rail/reset timing, and generated DTS/Kconfig.", "i2c_sensor_bringup_measurement_plan.md", "host-io"))
        recs.append(rec("evidence_capture_patch_plan", 88, "Add only removable logs or counters needed to bind the I2C observation to the exact failing boot.", "evidence_capture_patch_plan.md", "safe-local-instrumentation"))
    if any(token in text for token in ("power", "rail", "brownout", "reset", "scope", "startup delay")) or "scope_trace" in missing:
        recs.append(rec("lab_measurement_plan", 70, "Plan scope/logic capture for rail, reset, boot, and bus timing evidence.", "lab_measurement_plan.md", "lab-measurement"))
    if any(name in missing for name in ("build_log", "serial_log", "dmesg", "boot_log", "dts", "kconfig", "elf", "map", "rtos_snapshot", "logic_trace", "scope_trace")):
        recs.append(rec("evidence_capture_patch_plan", 88, "Write a minimal, removable patch plan that captures missing evidence before changing behavior.", "evidence_capture_patch_plan.md", "safe-local-instrumentation"))
    if "elf" in missing or "map" in missing:
        recs.append(
            {
                "id": "preserve_symbols_and_map",
                "score": 74,
                "why": "ELF/map are required before symbolication, memory-placement claims, or stack-frame root-cause claims.",
                "template": "",
                "template_path": "",
                "action": "Archive the exact failing build's ELF and linker map under the debug packet artifacts.",
                "risk": "host-io",
            }
        )
    if "dts" in missing or "kconfig" in missing:
        recs.append(
            {
                "id": "preserve_generated_config",
                "score": 76,
                "why": "Generated DTS/Kconfig are required before Zephyr/Linux driver-state claims.",
                "template": "",
                "template_path": "",
                "action": "Copy generated `zephyr.dts`, `.config`, `autoconf.h`, booted DTS/DTB, or kernel config from the exact failing build.",
                "risk": "host-io",
            }
        )
    return recs


def rec(rec_id: str, score: int, why: str, template: str, risk: str) -> dict[str, Any]:
    path = TEMPLATE_DIR / template
    return {
        "id": rec_id,
        "score": score,
        "why": why,
        "template": template,
        "template_path": str(path),
        "action": f"Use `{path}` and keep resulting logs/traces in the debug packet.",
        "risk": risk,
    }


def rank_recommendations(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    ranked: list[dict[str, Any]] = []
    for item in sorted(recommendations, key=lambda value: (-int(value["score"]), str(value["id"]))):
        if item["id"] not in seen:
            seen.add(str(item["id"]))
            ranked.append(item)
    return ranked[:8]


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Evidence Capture Suggestions",
        "",
        f"- Platform: `{result['platform']}`",
        f"- Evidence score: **{result['evidence_score']}/100** (`{result['evidence_grade']}`)",
        f"- Missing required evidence: {format_items(result.get('missing_required_evidence', []))}",
        "",
        "## Recommendations",
        "",
    ]
    if not result.get("recommendations"):
        lines.append("- No additional capture template is recommended from the current packet.")
    for item in result.get("recommendations", []):
        lines.extend(
            [
                f"### `{item['id']}`",
                "",
                f"- Score: `{item['score']}`",
                f"- Why: {item['why']}",
                f"- Template: `{item.get('template_path') or 'none'}`",
                f"- Risk label: `{item['risk']}`",
                f"- Action: {item['action']}",
                "",
            ]
        )
    lines.extend(["## Boundary", "", result["boundary"]])
    return "\n".join(lines)


def format_items(items: Any) -> str:
    if not items:
        return "none"
    if not isinstance(items, list):
        items = [str(items)]
    return ", ".join(f"`{item}`" for item in items)


if __name__ == "__main__":
    main()
