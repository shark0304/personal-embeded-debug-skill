#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from detect_project_context import detect_project_context, render_markdown  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local embedded-debug adapter packet inside a real project.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument(
        "--out-dir",
        help="Output directory. Defaults to <project-root>/debug/embedded_debug_adapter.",
    )
    parser.add_argument("--context", help="Optional precomputed project context JSON.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing adapter files.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else root / "debug" / "embedded_debug_adapter"
    context = load_context(Path(args.context)) if args.context else detect_project_context(root)
    create_adapter(root, out_dir, context, overwrite=args.overwrite)
    print(json.dumps({"ok": True, "out_dir": str(out_dir), "primary_adapter": context["primary_adapter"]}, indent=2, sort_keys=True))


def load_context(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def create_adapter(root: Path, out_dir: Path, context: dict[str, object], overwrite: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "project_debug_context.json": json.dumps(context, indent=2, sort_keys=True) + "\n",
        "PROJECT_DEBUG_ADAPTER.md": render_adapter_markdown(root, context),
        "evidence_manifest.md": render_evidence_manifest(context),
        "command_risk_policy.md": render_risk_policy(context),
    }
    for name, text in files.items():
        path = out_dir / name
        if path.exists() and not overwrite:
            raise SystemExit(f"refusing to overwrite existing file without --overwrite: {path}")
        path.write_text(text, encoding="utf-8")


def render_adapter_markdown(root: Path, context: dict[str, object]) -> str:
    lines = [
        "# Embedded Debug Project Adapter",
        "",
        "This adapter was generated from local project structure only. It does not prove hardware state, toolchain correctness, or root cause.",
        "",
        f"- Project root: `{root}`",
        f"- Primary adapter: `{context.get('primary_adapter', 'unknown')}`",
        "",
        "## Detected Context",
        "",
        render_markdown(context).strip(),
        "",
        "## Recommended First Pass",
        "",
        "1. Run the safe local build command for the detected adapter and save `build.log`.",
        "2. Capture serial, dmesg, fault registers, or waveform evidence that matches the symptom.",
        "3. Generate `debug_packet.yaml` with `scripts/collect/collect_debug_packet.py`.",
        "4. Use the listed runbooks and deterministic scripts before promoting any root-cause claim.",
        "",
        "## Guardrails",
        "",
        "- Commands marked `hardware-write` can flash or erase a target and require explicit human confirmation.",
        "- Commands marked `debugger-attached` can halt or reset hardware and require board/probe confirmation.",
        "- Commands marked `kernel-runtime-change` can alter a running Linux target and require a rollback path.",
        "",
    ]
    return "\n".join(lines)


def render_evidence_manifest(context: dict[str, object]) -> str:
    lines = [
        "# Evidence Manifest",
        "",
        "Use this checklist to collect artifacts without mixing hypotheses into evidence.",
        "",
        "## Artifact Globs",
        "",
    ]
    for glob in context.get("global_artifact_globs", []):
        lines.append(f"- `{glob}`")
    if not context.get("global_artifact_globs"):
        lines.append("- `build.log`")
        lines.append("- `serial.log`")
    lines.extend(["", "## Adapter Evidence", ""])
    for adapter in context.get("adapters", []):
        if not isinstance(adapter, dict):
            continue
        lines.append(f"### {adapter.get('label', adapter.get('id', 'unknown'))}")
        for evidence in adapter.get("evidence", []):
            lines.append(f"- `{evidence}`")
        lines.append("")
    return "\n".join(lines)


def render_risk_policy(context: dict[str, object]) -> str:
    lines = ["# Command Risk Policy", ""]
    policy = context.get("risk_policy", {})
    if isinstance(policy, dict):
        for key, value in policy.items():
            lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "Before running any non-safe command, record the exact board, probe, power source, target voltage, and recovery method.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
