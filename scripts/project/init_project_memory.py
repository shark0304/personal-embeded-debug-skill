#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from detect_project_context import detect_project_context  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a project-local .embedded-debug.yml memory file.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument("--out", default=".embedded-debug.yml", help="Output path, relative to project root unless absolute.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing memory file.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"refusing to overwrite existing project memory without --overwrite: {out_path}")

    context = detect_project_context(root)
    memory = build_project_memory(root, context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_yaml_or_json(out_path, memory)
    print(json.dumps({"ok": True, "out": str(out_path), "primary_adapter": context.get("primary_adapter", "unknown")}, indent=2, sort_keys=True))


def build_project_memory(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    adapter = primary_adapter(context)
    safe_commands = {str(item.get("name", "command")): item for item in adapter.get("safe_commands", []) if isinstance(item, dict)}
    artifacts = adapter.get("artifact_globs", []) if adapter else []
    return {
        "schema_version": 1,
        "project": {
            "id": root.name or "embedded-project",
            "platform": context.get("primary_adapter", "unknown"),
            "board": "unknown",
            "board_revision": "unknown",
            "mcu_or_soc": "unknown",
        },
        "toolchain": {
            "sdk": "unknown",
            "compiler": "unknown",
            "build_system": infer_build_system_name(adapter),
        },
        "commands": {
            "safe_build": command_text(safe_commands, "build"),
            "safe_test": command_text(safe_commands, "test") or command_text(safe_commands, "twister"),
            "risky_flash": first_risky_command(adapter, "hardware-write"),
        },
        "artifacts": {
            "expected_globs": list(artifacts)[:16],
        },
        "safety": {
            "recovery_path": "unknown",
            "require_confirmation_for": ["flash", "debugger_attach", "fuse_or_option_byte_change", "kernel_runtime_change"],
        },
        "notes": [
            "Generated from local project structure only.",
            "Do not commit secrets, customer data, private endpoints, or unauthorized firmware blobs.",
        ],
    }


def primary_adapter(context: dict[str, Any]) -> dict[str, Any]:
    primary_id = context.get("primary_adapter")
    for adapter in context.get("adapters", []):
        if isinstance(adapter, dict) and adapter.get("id") == primary_id:
            return adapter
    return {}


def infer_build_system_name(adapter: dict[str, Any]) -> str:
    adapter_id = str(adapter.get("id", "unknown"))
    return {
        "zephyr": "west",
        "esp-idf": "idf.py",
        "platformio": "platformio",
        "cmake-baremetal": "cmake",
        "make-baremetal": "make",
        "embedded-linux": "make",
    }.get(adapter_id, "unknown")


def command_text(commands: dict[str, dict[str, Any]], name: str) -> str:
    item = commands.get(name)
    return str(item.get("command", "")) if item else ""


def first_risky_command(adapter: dict[str, Any], risk: str) -> str:
    for item in adapter.get("safe_commands", []) if adapter else []:
        if isinstance(item, dict) and item.get("risk") == risk:
            return str(item.get("command", ""))
    return ""


def write_yaml_or_json(path: Path, data: dict[str, Any]) -> None:
    if yaml is not None:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
