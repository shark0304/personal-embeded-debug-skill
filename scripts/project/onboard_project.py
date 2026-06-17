#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parents[1]
for path in (SCRIPT_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from create_project_adapter import create_adapter  # noqa: E402
from detect_project_context import detect_project_context  # noqa: E402
from init_project_memory import build_project_memory, write_yaml_or_json  # noqa: E402
from score_bringup_readiness import render_markdown as render_readiness_markdown  # noqa: E402
from score_bringup_readiness import score_bringup_readiness  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Onboard a real embedded project into the Embedded Debug Workbench.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument("--symptom", default="", help="Optional current failure statement.")
    parser.add_argument("--out-dir", default="debug/onboarding", help="Output directory, relative to project root unless absolute.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite generated onboarding files.")
    parser.add_argument("--no-memory", action="store_true", help="Do not create .embedded-debug.yml when missing.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    if out_dir.exists() and any(out_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"refusing to overwrite non-empty onboarding directory without --overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    context = detect_project_context(root)
    memory_path = root / ".embedded-debug.yml"
    memory_created = False
    if not args.no_memory and (args.overwrite or not memory_path.exists()):
        memory = build_project_memory(root, context)
        write_yaml_or_json(memory_path, memory)
        memory_created = True

    adapter_dir = out_dir / "embedded_debug_adapter"
    create_adapter(root, adapter_dir, context, overwrite=True)
    readiness = score_bringup_readiness(root, memory_path)
    report = render_onboarding_report(root, out_dir, context, readiness, memory_path, memory_created, args.symptom)
    (out_dir / "onboarding_report.md").write_text(report + "\n", encoding="utf-8")
    (root / "debug" / "README.md").parent.mkdir(parents=True, exist_ok=True)
    write_debug_readme(root / "debug" / "README.md")

    summary = {
        "ok": True,
        "project_root": str(root),
        "out_dir": str(out_dir),
        "primary_adapter": context.get("primary_adapter", "unknown"),
        "memory": str(memory_path),
        "memory_created": memory_created,
        "readiness_score": readiness["score"],
        "readiness_grade": readiness["grade"],
        "next_actions": readiness.get("next_actions", []),
        "report": str(out_dir / "onboarding_report.md"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def render_onboarding_report(
    root: Path,
    out_dir: Path,
    context: dict[str, Any],
    readiness: dict[str, Any],
    memory_path: Path,
    memory_created: bool,
    symptom: str,
) -> str:
    lines = [
        "# Embedded Project Onboarding Report",
        "",
        "This report is generated from local project files only. It does not build, flash, attach a debugger, or modify target hardware.",
        "",
        "## Project",
        "",
        f"- Project root: `{root}`",
        f"- Primary adapter: `{context.get('primary_adapter', 'unknown')}`",
        f"- Current symptom: {symptom or 'not provided'}",
        f"- Project memory: `{memory_path}` (`{'created/updated' if memory_created else 'existing or skipped'}`)",
        f"- Adapter packet: `{out_dir / 'embedded_debug_adapter'}`",
        "",
        "## Bring-up Readiness",
        "",
        render_readiness_markdown(readiness),
        "",
        "## Recommended Operating Loop",
        "",
        "1. Fill unknown fields in `.embedded-debug.yml`, especially board revision, MCU/SoC, toolchain, and recovery path.",
        "2. Save first build and first boot/runtime logs before changing code.",
        "3. Run `scripts/project/run_project_triage.py --project-root . --symptom \"<failure>\"`.",
        "4. Run `scripts/project/suggest_evidence_capture.py --packet debug/debug_packet.yaml --symptom \"<failure>\" --format markdown`.",
        "5. Open a failure notebook with `scripts/project/create_failure_notebook.py` when the case needs handoff or regression tracking.",
        "",
        "## Guardrail",
        "",
        "Do not treat readiness, pattern matching, or a report score as a confirmed root cause. Confirmation still requires before/after evidence.",
    ]
    return "\n".join(lines)


def write_debug_readme(path: Path) -> None:
    text = "\n".join(
        [
            "# Embedded Debug Workspace",
            "",
            "Generated files in this directory are local engineering artifacts. Do not commit sensitive logs, customer data, private board identifiers, secrets, or unauthorized firmware blobs.",
            "",
            "Typical contents:",
            "",
            "- `onboarding/`: project context, readiness score, adapter packet, and next actions.",
            "- `debug_packet.yaml`: normalized evidence packet for one failure.",
            "- `project_triage_report.md`: safe first-pass triage report.",
            "- `failure-notebook/`: case records with status, hypotheses, evidence, fix verification, and outcomes.",
            "",
        ]
    )
    if not path.exists():
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
