#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUSES = {"open", "investigating", "fixed", "verified", "regression-added", "closed"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Update a failure notebook case status and optional lifecycle notes.")
    parser.add_argument("--case-dir", required=True, help="Failure notebook case directory.")
    parser.add_argument("--status", required=True, choices=sorted(STATUSES), help="New case status.")
    parser.add_argument("--note", default="", help="Short status note.")
    parser.add_argument("--hypothesis", default="", help="Current leading hypothesis.")
    parser.add_argument("--verification", default="", help="Verification observation or acceptance criterion.")
    parser.add_argument("--export-golden", help="Optional directory for a golden-packet candidate export.")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    if not case_dir.is_dir():
        raise SystemExit(f"case directory not found: {case_dir}")
    status_path = case_dir / "case_status.json"
    state = load_state(status_path)
    event = {
        "at": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "note": args.note,
        "hypothesis": args.hypothesis,
        "verification": args.verification,
    }
    state["status"] = args.status
    state.setdefault("events", []).append(event)
    status_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_lifecycle(case_dir / "lifecycle.md", event)
    update_readme_status(case_dir / "README.md", args.status)

    export_dir = ""
    if args.export_golden:
        export_dir = str(export_golden_candidate(case_dir, Path(args.export_golden)))

    print(
        json.dumps(
            {
                "ok": True,
                "case_dir": str(case_dir),
                "status": args.status,
                "status_file": str(status_path),
                "export_dir": export_dir,
            },
            indent=2,
            sort_keys=True,
        )
    )


def load_state(path: Path) -> dict[str, Any]:
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"events": []}
    return {"status": "open", "events": []}


def append_lifecycle(path: Path, event: dict[str, str]) -> None:
    if not path.exists():
        path.write_text("# Failure Case Lifecycle\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"## {event['status']} - {event['at']}\n\n")
        if event.get("note"):
            handle.write(f"- Note: {event['note']}\n")
        if event.get("hypothesis"):
            handle.write(f"- Leading hypothesis: {event['hypothesis']}\n")
        if event.get("verification"):
            handle.write(f"- Verification: {event['verification']}\n")
        handle.write("\n")


def update_readme_status(path: Path, status: str) -> None:
    marker = f"- Status: `{status}`"
    if not path.is_file():
        path.write_text(f"# Failure Notebook\n\n{marker}\n", encoding="utf-8")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("- Status:"):
            lines[idx] = marker
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    insert_at = 1 if lines else 0
    lines.insert(insert_at, "")
    lines.insert(insert_at + 1, marker)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_golden_candidate(case_dir: Path, out_dir: Path) -> Path:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("debug_packet.yaml", "README.md", "evidence_check.md", "hypotheses.md", "outcome.md", "lifecycle.md", "case_status.json"):
        src = case_dir / name
        if src.is_file():
            shutil.copyfile(src, out_dir / name)
    manifest = {
        "source_case": str(case_dir),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "next_step": "Review and rename this candidate before committing it under tests/golden_packets/.",
    }
    (out_dir / "golden_candidate_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out_dir


if __name__ == "__main__":
    main()
