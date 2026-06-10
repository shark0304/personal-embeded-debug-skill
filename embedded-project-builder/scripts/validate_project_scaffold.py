#!/usr/bin/env python3
"""Validate an embedded-project-builder scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = [
    "README.md",
    "project_plan.md",
    "datasheet_reading_note.md",
    "driver_bringup_note.md",
    "validation_plan.md",
]

REQUIRED_DIRS = ["app", "debug"]


def contains_all(text: str, required: dict[str, list[str]]) -> list[str]:
    lower = text.lower()
    missing = []
    for name, alternatives in required.items():
        if not any(term.lower() in lower for term in alternatives):
            missing.append(name)
    return missing


def validate(project_dir: Path) -> dict:
    failures = []
    for rel in REQUIRED_FILES:
        if not (project_dir / rel).exists():
            failures.append({"path": rel, "issue": "missing file"})
    for rel in REQUIRED_DIRS:
        if not (project_dir / rel).is_dir():
            failures.append({"path": rel, "issue": "missing directory"})

    validation_path = project_dir / "validation_plan.md"
    if validation_path.exists():
        missing = contains_all(
            validation_path.read_text(encoding="utf-8", errors="replace"),
            {
                "build condition": ["build validation", "build"],
                "flash condition": ["flash validation", "flash"],
                "runtime condition": ["runtime validation", "runtime"],
                "debug handoff condition": ["debug handoff", "embedded-debug"],
            },
        )
        for item in missing:
            failures.append({"path": "validation_plan.md", "issue": "missing section", "section": item})

    readme_path = project_dir / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8", errors="replace").lower()
        if "embedded-debug" not in readme_text:
            failures.append({"path": "README.md", "issue": "missing embedded-debug handoff"})

    return {
        "project_dir": str(project_dir),
        "failed_count": len(failures),
        "failures": failures,
        "ok": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, help="scaffold directory to validate")
    args = parser.parse_args()

    result = validate(Path(args.project_dir))
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
