#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a project-local failure notebook case.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument("--symptom", required=True, help="Short symptom statement.")
    parser.add_argument("--out-dir", default="debug/failure-notebook", help="Notebook root directory.")
    parser.add_argument("--case-id", help="Stable case id. Defaults to date plus symptom slug.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite an existing notebook case.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    notebook_root = Path(args.out_dir)
    if not notebook_root.is_absolute():
        notebook_root = root / notebook_root
    case_id = args.case_id or default_case_id(args.symptom)
    case_dir = notebook_root / case_id
    if case_dir.exists() and not args.overwrite:
        raise SystemExit(f"refusing to overwrite existing notebook case without --overwrite: {case_dir}")
    case_dir.mkdir(parents=True, exist_ok=True)

    context = detect_project_context(root)
    artifacts = collect_artifacts(root)
    platform = detect_platform(root, artifacts)
    if platform == "unknown":
        platform = map_adapter_to_platform(str(context.get("primary_adapter", "unknown")))
    packet = build_packet(root, platform, artifacts)
    packet["symptoms"] = [args.symptom]
    validation = validate_debug_packet(packet)

    write_packet(case_dir / "debug_packet.yaml", packet)
    (case_dir / "context.json").write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (case_dir / "README.md").write_text(render_readme(case_id, args.symptom, context, validation), encoding="utf-8")
    (case_dir / "evidence_check.md").write_text(render_validation_markdown(validation) + "\n", encoding="utf-8")
    (case_dir / "hypotheses.md").write_text(render_hypotheses_template(), encoding="utf-8")
    (case_dir / "outcome.md").write_text(render_outcome_template(), encoding="utf-8")
    copy_template(SKILL_DIR / "assets" / "templates" / "debug_issue_record.md", case_dir / "debug_issue_record.md")
    print(json.dumps({"ok": True, "case_dir": str(case_dir), "case_id": case_id, "evidence_score": validation["score"]}, indent=2, sort_keys=True))


def default_case_id(symptom: str) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = re.sub(r"[^a-z0-9]+", "-", symptom.lower()).strip("-")[:48] or "debug-case"
    return f"{date}-{slug}"


def map_adapter_to_platform(adapter_id: str) -> str:
    if adapter_id in {"zephyr", "esp-idf", "embedded-linux", "freertos", "tinyml"}:
        return adapter_id
    if adapter_id in {"stm32cube", "platformio", "arduino", "cmake-baremetal", "make-baremetal"}:
        return "cortex-m"
    return "unknown"


def render_readme(case_id: str, symptom: str, context: dict[str, Any], validation: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Failure Notebook: {case_id}",
            "",
            "This notebook is a local engineering record. Do not commit sensitive logs, private board identifiers, customer data, or unauthorized firmware blobs.",
            "",
            "## Summary",
            "",
            f"- Symptom: {symptom}",
            f"- Primary adapter: `{context.get('primary_adapter', 'unknown')}`",
            f"- Evidence completeness: **{validation['score']}/100** (`{validation['grade']}`)",
            "",
            "## Files",
            "",
            "- `debug_packet.yaml`: normalized local evidence packet.",
            "- `context.json`: project adapter detection output.",
            "- `evidence_check.md`: missing evidence and readiness score.",
            "- `hypotheses.md`: ranked hypotheses as analysis progresses.",
            "- `outcome.md`: final root cause, fix, and regression note.",
            "- `debug_issue_record.md`: editable issue record template.",
            "",
        ]
    )


def render_hypotheses_template() -> str:
    return (
        "# Hypotheses\n\n"
        "| Rank | Hypothesis | Evidence for | Evidence against | Missing evidence | Verification step | Status |\n"
        "|---|---|---|---|---|---|---|\n"
        "| 1 |  |  |  |  |  | open |\n"
    )


def render_outcome_template() -> str:
    return (
        "# Outcome\n\n"
        "## Confirmed Root Cause\n\n-\n\n"
        "## Fix\n\n-\n\n"
        "## Verification Observation\n\n-\n\n"
        "## Regression / Golden Packet\n\n-\n\n"
        "## Follow-up Prevention\n\n-\n"
    )


def copy_template(src: Path, dst: Path) -> None:
    if src.is_file():
        shutil.copyfile(src, dst)


if __name__ == "__main__":
    main()
