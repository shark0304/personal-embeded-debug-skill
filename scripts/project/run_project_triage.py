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
for path in (SCRIPT_DIR, COLLECT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from collect_debug_packet import build_packet, collect_artifacts, detect_platform, write_packet  # noqa: E402
from detect_project_context import detect_project_context  # noqa: E402
from validate_debug_packet import render_markdown as render_validation_markdown  # noqa: E402
from validate_debug_packet import validate_debug_packet  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run safe project triage: detect project, collect packet metadata, score evidence, and write a triage report.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument("--symptom", default="", help="Short symptom statement.")
    parser.add_argument("--packet-out", default="debug/debug_packet.yaml", help="Output debug packet path.")
    parser.add_argument("--report-out", default="debug/project_triage_report.md", help="Output triage report path.")
    parser.add_argument("--json-out", help="Optional JSON summary output path.")
    parser.add_argument("--no-write-packet", action="store_true", help="Do not write debug_packet.yaml.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    context = detect_project_context(root)
    memory = load_project_memory(root)
    artifacts = collect_artifacts(root)
    platform = detect_platform(root, artifacts)
    if platform == "unknown" and context.get("primary_adapter") in {"zephyr", "esp-idf", "embedded-linux", "freertos", "tinyml"}:
        platform = str(context["primary_adapter"])
    elif platform == "unknown" and context.get("primary_adapter") in {"stm32cube", "platformio", "arduino", "cmake-baremetal", "make-baremetal"}:
        platform = "cortex-m"

    packet = build_packet(root, platform, artifacts)
    apply_project_memory(packet, memory)
    if args.symptom:
        packet["symptoms"] = [args.symptom]
    validation = validate_debug_packet(packet)
    report = render_triage_report(root, context, packet, validation, args.symptom, memory)

    packet_path = Path(args.packet_out)
    report_path = Path(args.report_out)
    if not packet_path.is_absolute():
        packet_path = root / packet_path
    if not report_path.is_absolute():
        report_path = root / report_path

    if not args.no_write_packet:
        write_packet(packet_path, packet)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report + "\n", encoding="utf-8")

    summary = {
        "ok": True,
        "project_root": str(root),
        "primary_adapter": context.get("primary_adapter", "unknown"),
        "platform": platform,
        "evidence_score": validation["score"],
        "evidence_grade": validation["grade"],
        "project_memory": bool(memory),
        "packet": "" if args.no_write_packet else str(packet_path),
        "report": str(report_path),
        "missing_required_evidence": validation["required_evidence"]["missing"],
    }
    if args.json_out:
        json_path = Path(args.json_out)
        if not json_path.is_absolute():
            json_path = root / json_path
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


def render_triage_report(
    root: Path,
    context: dict[str, Any],
    packet: dict[str, Any],
    validation: dict[str, Any],
    symptom: str,
    memory: dict[str, Any] | None = None,
) -> str:
    primary = primary_adapter(context)
    lines = [
        "# Project Triage Report",
        "",
        "This report is generated from local project files only. It does not execute build, flash, debugger, serial, or kernel-runtime commands.",
        "",
        "## Summary",
        "",
        f"- Project root: `{root}`",
        f"- Symptom: {symptom or 'not provided'}",
        f"- Primary adapter: `{primary.get('id', context.get('primary_adapter', 'unknown'))}`",
        f"- Platform for packet: `{packet.get('platform', 'unknown')}`",
        f"- Evidence completeness: **{validation['score']}/100** (`{validation['grade']}`)",
        f"- Project memory: `{'loaded' if memory else 'not found'}`",
        "",
        "## Detected Adapter",
        "",
    ]
    if primary:
        lines.extend(
            [
                f"- Label: {primary.get('label', primary.get('id'))}",
                f"- Confidence: `{primary.get('confidence', 'unknown')}`",
                f"- Evidence: {format_items(primary.get('evidence', [])[:8])}",
                "",
            ]
        )
    else:
        lines.append("No project adapter matched. Start with generic build and serial logs.\n")

    lines.extend(["## Evidence Completeness", "", render_validation_markdown(validation), ""])
    if memory:
        lines.extend(["", "## Project Memory", ""])
        lines.extend(render_project_memory_summary(memory))
    lines.extend(["## Available Artifacts", ""])
    artifacts = packet.get("artifacts", {})
    if isinstance(artifacts, dict) and artifacts:
        for key, paths in sorted(artifacts.items()):
            lines.append(f"- `{key}`: {format_items(paths if isinstance(paths, list) else [str(paths)])}")
    else:
        lines.append("- No recognized artifacts found yet.")

    lines.extend(["", "## Safe Next Commands", ""])
    safe_commands = command_rows(primary, allowed_risks={"safe-local-build", "safe-local-test", "safe-local-inspection", "host-io"})
    if safe_commands:
        for command in safe_commands:
            lines.append(f"- `{command['command']}` - {command['risk']}: {command['note']}")
    else:
        lines.append("- Save build output as `build.log` and runtime output as `serial.log` or `dmesg.log`.")

    lines.extend(["", "## Recommended Analyzers", ""])
    for script in recommended_scripts(primary, symptom):
        lines.append(f"- `{script}`")

    risky = command_rows(primary, allowed_risks={"hardware-write", "debugger-attached", "kernel-runtime-change"})
    lines.extend(["", "## Risk Guardrails", ""])
    lines.append("hardware-changing commands are listed only as guarded actions; this triage script does not execute them.")
    if risky:
        for command in risky:
            lines.append(f"- Do not run `{command['command']}` without confirmation. Risk: `{command['risk']}`.")
    else:
        lines.append("- No adapter-specific high-risk commands were detected.")

    lines.extend(
        [
            "",
            "## Fix Verification Plan",
            "",
            "1. Record the pre-fix observation from logs, registers, or traces.",
            "2. Apply one minimal change tied to one hypothesis.",
            "3. Re-run the same evidence capture path and compare before/after observations.",
            "4. Add the final packet and report to a regression or golden-packet case.",
            "5. Keep workaround evidence separate from confirmed root-cause evidence.",
            "",
            "## Report Boundary",
            "",
            "This triage report can rank next checks, but it should not be treated as a confirmed root cause until the missing required evidence is collected and a verification observation matches the hypothesis.",
        ]
    )
    return "\n".join(lines)


def load_project_memory(root: Path) -> dict[str, Any] | None:
    path = root / ".embedded-debug.yml"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        if yaml is not None:
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception:
        data = parse_simple_project_memory(text)
    return data if isinstance(data, dict) else None


def apply_project_memory(packet: dict[str, Any], memory: dict[str, Any] | None) -> None:
    if not memory:
        return
    project = memory.get("project", {}) if isinstance(memory.get("project"), dict) else {}
    toolchain = memory.get("toolchain", {}) if isinstance(memory.get("toolchain"), dict) else {}
    artifacts = memory.get("artifacts", {}) if isinstance(memory.get("artifacts"), dict) else {}
    if project.get("board") and str(project.get("board")).lower() != "unknown":
        packet["board"] = project["board"]
    if toolchain.get("compiler") and str(toolchain.get("compiler")).lower() != "unknown":
        packet["toolchain"] = toolchain["compiler"]
    elif toolchain.get("sdk") and str(toolchain.get("sdk")).lower() != "unknown":
        packet["toolchain"] = toolchain["sdk"]
    if toolchain.get("build_system") and str(toolchain.get("build_system")).lower() != "unknown":
        packet["build_system"] = toolchain["build_system"]
    packet.setdefault("constraints", [])
    if isinstance(packet["constraints"], list):
        recovery = memory.get("safety", {}).get("recovery_path") if isinstance(memory.get("safety"), dict) else None
        if recovery and str(recovery).lower() != "unknown":
            packet["constraints"].append(f"Recovery path: {recovery}")
    packet_artifacts = packet.setdefault("artifacts", {})
    if isinstance(packet_artifacts, dict):
        for key in ("build_log", "serial_log", "dts", "kconfig", "elf", "map", "dmesg", "boot_log"):
            value = artifacts.get(key)
            if value and key not in packet_artifacts:
                packet_artifacts[key] = [str(value)]


def render_project_memory_summary(memory: dict[str, Any]) -> list[str]:
    project = memory.get("project", {}) if isinstance(memory.get("project"), dict) else {}
    toolchain = memory.get("toolchain", {}) if isinstance(memory.get("toolchain"), dict) else {}
    safety = memory.get("safety", {}) if isinstance(memory.get("safety"), dict) else {}
    return [
        f"- Project id: `{project.get('id', 'unknown')}`",
        f"- Board: `{project.get('board', 'unknown')}`",
        f"- MCU/SoC: `{project.get('mcu_or_soc', 'unknown')}`",
        f"- Build system: `{toolchain.get('build_system', 'unknown')}`",
        f"- Recovery path: `{safety.get('recovery_path', 'unknown')}`",
        "",
    ]


def parse_simple_project_memory(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith(" ") and raw.rstrip().endswith(":"):
            key = raw.strip()[:-1]
            current = {}
            data[key] = current
        elif current is not None and ":" in raw:
            key, value = raw.strip().split(":", 1)
            current[key.strip()] = value.strip().strip("'\"")
    return data


def primary_adapter(context: dict[str, Any]) -> dict[str, Any]:
    primary_id = context.get("primary_adapter")
    adapters = context.get("adapters", [])
    if isinstance(adapters, list):
        for adapter in adapters:
            if isinstance(adapter, dict) and adapter.get("id") == primary_id:
                return adapter
    return {}


def command_rows(adapter: dict[str, Any], allowed_risks: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in adapter.get("safe_commands", []) if adapter else []:
        if isinstance(item, dict) and item.get("risk") in allowed_risks:
            rows.append({key: str(item.get(key, "")) for key in ("command", "risk", "note")})
    return rows


def recommended_scripts(adapter: dict[str, Any], symptom: str) -> list[str]:
    scripts = [str(item) for item in adapter.get("recommended_scripts", [])] if adapter else []
    symptom_l = symptom.lower()
    extra: list[str] = []
    if any(token in symptom_l for token in ("hardfault", "busfault", "cfsr", "hfsr")):
        extra.extend(["scripts/fault_analyzer.py --cfsr <hex> --hfsr <hex>", "scripts/symbolicate_addresses.py --elf <firmware.elf> --addr <pc> --dry-run"])
    if any(token in symptom_l for token in ("i2c", "sensor", "who_am_i", "nack")):
        extra.extend(["scripts/analyze/analyze_i2c_init_failure.py --serial-log serial.log --dts zephyr.dts --config .config", "scripts/i2c_pullup_check.py --pullup <ohms> --capacitance-pf <pf>"])
    if any(token in symptom_l for token in ("panic", "wdt", "guru")):
        extra.append("scripts/esp_panic_parse.py --log serial.log")
    if any(token in symptom_l for token in ("deadlock", "priority inversion", "semaphore", "queue")):
        extra.extend(["scripts/rtos_snapshot_check.py --task <name:prio:state:stack_free:stack_total>", "scripts/freertos_wait_graph.py --task <name:prio:state:resource>"])
    if any(token in symptom_l for token in ("probe defer", "deferred probe", "dmesg", "driver")):
        extra.extend(["scripts/linux_log_triage.py --log dmesg.log", "scripts/dts_probe_check.py --dts <board>.dts --node <node>"])
    merged = []
    for script in [*scripts, *extra]:
        if script not in merged:
            merged.append(script)
    return merged or ["scripts/collect/validate_debug_packet.py --packet debug_packet.yaml --format markdown"]


def format_items(items: Any) -> str:
    if not items:
        return "none"
    if not isinstance(items, list):
        items = [str(items)]
    return ", ".join(f"`{item}`" for item in items)


if __name__ == "__main__":
    main()
