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

from collect_debug_packet import collect_artifacts  # noqa: E402
from detect_project_context import detect_project_context  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Score whether an embedded project is ready for safe board bring-up/debug.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument("--memory", default=".embedded-debug.yml", help="Project memory path, relative to project root unless absolute.")
    parser.add_argument("--out", help="Optional output path.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    memory_path = Path(args.memory)
    if not memory_path.is_absolute():
        memory_path = root / memory_path

    result = score_bringup_readiness(root, memory_path)
    text = render_markdown(result) if args.format == "markdown" else json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


def score_bringup_readiness(root: Path, memory_path: Path | None = None) -> dict[str, Any]:
    memory_path = memory_path or root / ".embedded-debug.yml"
    memory = load_project_memory(memory_path)
    context = detect_project_context(root)
    artifacts = collect_artifacts(root)

    checks = [
        score_project_identity(memory, context),
        score_toolchain(memory, context),
        score_safety(memory),
        score_expected_artifacts(memory, artifacts),
        score_observed_evidence(artifacts),
        score_safe_commands(memory, context),
    ]
    score = int(round(sum(float(item["score"]) for item in checks)))
    score = max(0, min(100, score))
    missing: list[str] = []
    for item in checks:
        missing.extend(str(value) for value in item.get("missing", []))

    return {
        "ok": score >= 70 and not any(item.get("blocking") for item in checks),
        "score": score,
        "grade": grade(score),
        "project_root": str(root),
        "memory": str(memory_path),
        "memory_found": bool(memory),
        "primary_adapter": context.get("primary_adapter", "unknown"),
        "checks": checks,
        "missing": missing,
        "next_actions": next_actions(score, bool(memory), missing, context),
    }


def score_project_identity(memory: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    project = mapping(memory.get("project"))
    present = known_fields(project, ["board", "board_revision", "mcu_or_soc"])
    if context.get("primary_adapter") and context.get("primary_adapter") != "unknown":
        present.append("project_adapter")
    missing = missing_fields(project, ["board", "board_revision", "mcu_or_soc"])
    return check("project_identity", 20, present, missing)


def score_toolchain(memory: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    toolchain = mapping(memory.get("toolchain"))
    present = known_fields(toolchain, ["sdk", "compiler", "build_system"])
    if context.get("primary_adapter") in {"zephyr", "esp-idf", "platformio", "stm32cube", "embedded-linux", "freertos"}:
        present.append("adapter_toolchain_hint")
    missing = missing_fields(toolchain, ["sdk", "compiler", "build_system"])
    return check("toolchain_reproducibility", 20, present, missing)


def score_safety(memory: dict[str, Any]) -> dict[str, Any]:
    safety = mapping(memory.get("safety"))
    present = known_fields(safety, ["recovery_path"])
    if has_value(safety.get("require_confirmation_for")):
        present.append("guarded_risky_actions")
    missing = missing_fields(safety, ["recovery_path"])
    if not has_value(safety.get("require_confirmation_for")):
        missing.append("safety.require_confirmation_for")
    return check("safety_and_recovery", 15, present, missing, blocking="safety.recovery_path" in missing)


def score_expected_artifacts(memory: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, Any]:
    artifact_memory = mapping(memory.get("artifacts"))
    present: list[str] = []
    missing: list[str] = []
    if has_value(artifact_memory.get("expected_globs")):
        present.append("artifacts.expected_globs")
    else:
        missing.append("artifacts.expected_globs")
    for name in ("build_log", "serial_log", "dmesg", "boot_log", "dts", "kconfig", "elf", "map"):
        if has_value(artifact_memory.get(name)) or has_value(artifacts.get(name)):
            present.append(name)
    if not any(item in present for item in ("build_log", "serial_log", "dmesg", "boot_log")):
        missing.append("first build/boot/runtime log")
    return check("artifact_map", 20, present, missing)


def score_observed_evidence(artifacts: dict[str, Any]) -> dict[str, Any]:
    evidence_names = ["build_log", "serial_log", "dmesg", "boot_log", "fault_registers", "rtos_snapshot", "logic_trace", "scope_trace"]
    present = [name for name in evidence_names if has_value(artifacts.get(name))]
    missing = []
    if not any(name in present for name in ("build_log", "serial_log", "dmesg", "boot_log")):
        missing.append("save at least one build, serial, dmesg, or boot log")
    return check("observed_evidence", 15, present, missing)


def score_safe_commands(memory: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    commands = mapping(memory.get("commands"))
    present = known_fields(commands, ["safe_build", "safe_test"])
    primary = primary_adapter(context)
    if primary.get("safe_commands"):
        present.append("adapter_safe_commands")
    missing = missing_fields(commands, ["safe_build"])
    return check("safe_commands", 10, present, missing)


def check(name: str, weight: int, present: list[str], missing: list[str], blocking: bool = False) -> dict[str, Any]:
    total = len(present) + len(missing)
    ratio = len(present) / total if total else 0.0
    return {
        "name": name,
        "weight": weight,
        "score": round(weight * ratio, 1),
        "present": present,
        "missing": missing,
        "blocking": blocking,
    }


def load_project_memory(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        if yaml is not None:
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception:
        data = parse_simple_project_memory(text)
    return data if isinstance(data, dict) else {}


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
    for adapter in context.get("adapters", []):
        if isinstance(adapter, dict) and adapter.get("id") == primary_id:
            return adapter
    return {}


def mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def known_fields(data: dict[str, Any], names: list[str]) -> list[str]:
    return [name for name in names if has_value(data.get(name))]


def missing_fields(data: dict[str, Any], names: list[str]) -> list[str]:
    return [name for name in names if not has_value(data.get(name))]


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"unknown", "none", "n/a"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def grade(score: int) -> str:
    if score >= 85:
        return "bring-up-ready"
    if score >= 70:
        return "ready-with-gaps"
    if score >= 45:
        return "needs-prep"
    return "not-ready"


def next_actions(score: int, has_memory: bool, missing: list[str], context: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not has_memory:
        actions.append("Run `scripts/project/init_project_memory.py --project-root . --overwrite`, then fill board, MCU/SoC, toolchain, and recovery path.")
    if any("recovery_path" in item for item in missing):
        actions.append("Document the recovery path before flash/debugger experiments: SWD/JTAG, bootloader, recovery pins, or removable storage path.")
    if any("first build/boot/runtime log" in item or "save at least" in item for item in missing):
        actions.append("Save the first build log and first boot/serial/dmesg log before changing code.")
    if context.get("primary_adapter") == "zephyr":
        actions.append("Preserve generated `zephyr.dts` and `.config` from the exact build directory.")
    if context.get("primary_adapter") == "embedded-linux":
        actions.append("Preserve boot log, full `dmesg`, booted DTS/DTB, and kernel config.")
    if score < 70:
        actions.append("Treat root-cause claims as provisional until readiness reaches at least 70.")
    return unique(actions)


def unique(items: list[str]) -> list[str]:
    out: list[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Bring-up Readiness Score",
        "",
        f"- Project root: `{result['project_root']}`",
        f"- Primary adapter: `{result['primary_adapter']}`",
        f"- Project memory: `{'found' if result['memory_found'] else 'not found'}`",
        f"- Score: **{result['score']}/100** (`{result['grade']}`)",
        f"- Ready for safe bring-up/debug: **{'yes' if result['ok'] else 'no'}**",
        "",
        "## Checks",
        "",
    ]
    for item in result.get("checks", []):
        lines.append(f"- `{item['name']}`: {item['score']}/{item['weight']} present={format_items(item['present'])} missing={format_items(item['missing'])}")
    lines.extend(["", "## Next Actions", ""])
    for action in result.get("next_actions", []):
        lines.append(f"- {action}")
    if not result.get("next_actions"):
        lines.append("- Project is ready for focused evidence capture and triage.")
    return "\n".join(lines)


def format_items(items: Any) -> str:
    if not items:
        return "none"
    if not isinstance(items, list):
        items = [str(items)]
    return ", ".join(f"`{item}`" for item in items)


if __name__ == "__main__":
    main()
