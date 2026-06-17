#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parents[1]
PROJECT_DIR = SKILL_DIR / "scripts" / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from detect_project_context import detect_project_context  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract embedded project signals from a lightweight project snapshot.")
    parser.add_argument("--snapshot-dir", required=True, help="Directory created by fetch_project_snapshot.py.")
    parser.add_argument("--out", help="Optional JSON output path.")
    args = parser.parse_args()

    snapshot_dir = Path(args.snapshot_dir)
    files_root = snapshot_dir / "files"
    manifest = load_manifest(snapshot_dir)
    context = detect_project_context(files_root if files_root.is_dir() else snapshot_dir)
    result = {
        "repo": manifest.get("repo", snapshot_dir.name),
        "ref": manifest.get("ref", ""),
        "snapshot_dir": str(snapshot_dir),
        "file_count": manifest.get("file_count", 0),
        "primary_adapter": context.get("primary_adapter", "unknown"),
        "adapters": summarize_adapters(context),
        "manifest_paths": manifest.get("files", []),
        "risk_policy": context.get("risk_policy", {}),
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


def load_manifest(snapshot_dir: Path) -> dict[str, Any]:
    path = snapshot_dir / "snapshot_manifest.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    return {}


def summarize_adapters(context: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for adapter in context.get("adapters", []):
        if isinstance(adapter, dict):
            out.append(
                {
                    "id": adapter.get("id", "unknown"),
                    "confidence": adapter.get("confidence", 0),
                    "evidence": adapter.get("evidence", []),
                }
            )
    return out


if __name__ == "__main__":
    main()
