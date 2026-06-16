#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


REQUIRED_BY_PLATFORM = {
    "zephyr": ["build_log", "dts", "kconfig"],
    "esp-idf": ["build_log", "serial_log", "kconfig"],
    "cortex-m": ["elf", "map", "fault_registers"],
    "embedded-linux": ["boot_log", "dmesg", "dts", "kconfig"],
    "freertos": ["elf", "map", "rtos_snapshot"],
    "tinyml": ["elf", "map"],
    "unknown": ["build_log", "serial_log"],
}

CORE_FIELDS = ["case_id", "project_root", "platform", "artifacts"]
CONTEXT_FIELDS = ["board", "toolchain", "build_system", "reproducibility", "last_known_good"]
OPTIONAL_EVIDENCE = ["serial_log", "build_log", "logic_trace", "scope_trace", "dmesg", "boot_log", "elf", "map"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an embedded debug packet and score evidence completeness.")
    parser.add_argument("--packet", required=True, help="debug_packet.yaml/json path.")
    parser.add_argument("--out", help="Optional report output path.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    parser.add_argument("--min-score", type=int, default=0, help="Exit nonzero when score is below this threshold.")
    args = parser.parse_args()

    packet_path = Path(args.packet)
    packet = load_packet(packet_path)
    result = validate_debug_packet(packet, packet_path=packet_path)
    text = render_markdown(result) if args.format == "markdown" else json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.min_score and int(result["score"]) < args.min_score:
        raise SystemExit(1)


def load_packet(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        if yaml is not None:
            data = yaml.safe_load(text)
        else:
            data = parse_simple_yaml(text)
    if not isinstance(data, dict):
        raise SystemExit(f"packet is not a mapping: {path}")
    return data


def validate_debug_packet(packet: dict[str, Any], packet_path: Path | None = None) -> dict[str, Any]:
    artifacts = packet.get("artifacts", {})
    if not isinstance(artifacts, dict):
        artifacts = {}
    platform = str(packet.get("platform") or "unknown")
    required = list(REQUIRED_BY_PLATFORM.get(platform, REQUIRED_BY_PLATFORM["unknown"]))

    core_present = [field for field in CORE_FIELDS if has_value(packet.get(field))]
    core_missing = [field for field in CORE_FIELDS if field not in core_present]
    context_present = [field for field in CONTEXT_FIELDS if is_known(packet.get(field))]
    context_missing = [field for field in CONTEXT_FIELDS if field not in context_present]
    required_present = [name for name in required if has_artifact(artifacts, name)]
    required_missing = [name for name in required if name not in required_present]
    optional_present = [name for name in OPTIONAL_EVIDENCE if has_artifact(artifacts, name) and name not in required_present]

    score = score_packet(core_present, context_present, required_present, required, optional_present, packet)
    warnings = build_warnings(packet, platform, required_missing, context_missing)
    result = {
        "ok": not core_missing and not required_missing,
        "packet": str(packet_path) if packet_path else "",
        "score": score,
        "grade": grade(score),
        "platform": platform,
        "core": {"present": core_present, "missing": core_missing},
        "context": {"present": context_present, "missing": context_missing},
        "required_evidence": {"required": required, "present": required_present, "missing": required_missing},
        "optional_evidence_present": optional_present,
        "warnings": warnings,
        "next_evidence": next_evidence(platform, required_missing, context_missing),
    }
    return result


def score_packet(
    core_present: list[str],
    context_present: list[str],
    required_present: list[str],
    required: list[str],
    optional_present: list[str],
    packet: dict[str, Any],
) -> int:
    score = 0.0
    score += 25.0 * (len(core_present) / max(1, len(CORE_FIELDS)))
    score += 45.0 * (len(required_present) / max(1, len(required)))
    score += 18.0 * (len(context_present) / max(1, len(CONTEXT_FIELDS)))
    score += min(8.0, 2.0 * len(optional_present))
    if has_value(packet.get("symptoms")):
        score += 2.0
    if has_value(packet.get("missing_evidence")):
        score += 2.0
    return int(round(min(100.0, score)))


def has_artifact(artifacts: dict[str, Any], name: str) -> bool:
    value = artifacts.get(name)
    return has_value(value)


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"unknown", "none", "n/a"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def is_known(value: Any) -> bool:
    return has_value(value)


def grade(score: int) -> str:
    if score >= 85:
        return "ready-for-analysis"
    if score >= 65:
        return "triage-usable"
    if score >= 40:
        return "evidence-thin"
    return "insufficient"


def build_warnings(packet: dict[str, Any], platform: str, required_missing: list[str], context_missing: list[str]) -> list[str]:
    warnings: list[str] = []
    if required_missing:
        warnings.append("Do not promote a root cause until required evidence is collected.")
    if "board" in context_missing:
        warnings.append("Board or revision is unknown; hardware-specific conclusions should stay provisional.")
    if platform in {"zephyr", "embedded-linux"} and any(item in required_missing for item in ("dts", "kconfig")):
        warnings.append("Generated devicetree/Kconfig evidence is missing; driver state may be misread.")
    if platform in {"cortex-m", "freertos"} and any(item in required_missing for item in ("elf", "map")):
        warnings.append("ELF/map evidence is missing; do not resolve PCs or memory placement by guesswork.")
    if not has_value(packet.get("last_known_good")):
        warnings.append("Last known good state is unknown; regression boundary is weak.")
    return warnings


def next_evidence(platform: str, required_missing: list[str], context_missing: list[str]) -> list[str]:
    suggestions = [f"Collect `{name}` evidence." for name in required_missing]
    if "board" in context_missing:
        suggestions.append("Record exact board, board revision, MCU/SoC, and probe.")
    if "toolchain" in context_missing:
        suggestions.append("Record compiler, SDK/HAL/RTOS version, and build mode.")
    if platform == "zephyr" and "logic_trace" not in required_missing:
        suggestions.append("For I2C/SPI probe failures, add a short logic analyzer trace when available.")
    if platform == "embedded-linux":
        suggestions.append("Capture full boot-to-failure `dmesg`, not only the final error lines.")
    return suggestions


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Debug Packet Validation",
        "",
        f"- Packet: `{result.get('packet') or 'in-memory'}`",
        f"- Platform: `{result['platform']}`",
        f"- Evidence completeness: **{result['score']}/100** (`{result['grade']}`)",
        f"- Ready for root-cause analysis: **{'yes' if result['ok'] else 'no'}**",
        "",
        "## Required Evidence",
        "",
    ]
    required = result["required_evidence"]
    lines.append(f"- Present: {format_items(required['present'])}")
    lines.append(f"- Missing: {format_items(required['missing'])}")
    lines.extend(["", "## Context", ""])
    context = result["context"]
    lines.append(f"- Present: {format_items(context['present'])}")
    lines.append(f"- Missing: {format_items(context['missing'])}")
    lines.extend(["", "## Warnings", ""])
    for warning in result.get("warnings", []):
        lines.append(f"- {warning}")
    if not result.get("warnings"):
        lines.append("- No blocking warnings.")
    lines.extend(["", "## Next Evidence", ""])
    for item in result.get("next_evidence", []):
        lines.append(f"- {item}")
    if not result.get("next_evidence"):
        lines.append("- Evidence packet is ready for focused analysis.")
    return "\n".join(lines)


def format_items(items: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in items) if items else "none"


def parse_simple_yaml(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    current_map: dict[str, list[str]] | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  ") and current_key and current_map is not None:
            stripped = raw.strip()
            if ":" in stripped:
                key, value = stripped.split(":", 1)
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    current_map[key.strip()] = [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
                else:
                    current_map[key.strip()] = [value.strip("'\"")] if value else []
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                current_key = key
                current_map = {}
                data[key] = current_map
            else:
                data[key] = value.strip("'\"")
                current_key = None
                current_map = None
    return data


if __name__ == "__main__":
    main()
