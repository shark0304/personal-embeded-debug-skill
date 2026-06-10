#!/usr/bin/env python3
"""Validate embedded-project-builder planning document structure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "project_plan.md": [
        "## Project Goal",
        "## Board",
        "## Sensor / Peripheral",
        "## Toolchain",
        "## Milestones",
        "## Risks",
        "## Validation Criteria",
        "## Debug Handoff Condition",
    ],
    "datasheet_reading_note.md": [
        "## Power",
        "## Clock",
        "## Interface",
        "## Address",
        "## Registers",
        "## Init Sequence",
        "## Timing",
        "## Interrupts",
        "## Low Power",
        "## Test Registers",
    ],
    "driver_bringup_note.md": [
        "## Minimal Read / Write Test",
        "## WHO_AM_I Or ID Check",
        "## Init Sequence",
        "## Polling Mode",
        "## Interrupt Mode",
        "## FIFO Mode",
        "## Error Handling",
        "## Logging Plan",
    ],
    "validation_plan.md": [
        "## Build Validation",
        "## Flash Validation",
        "## Serial Log Validation",
        "## Bus-level Validation",
        "## Timing Validation",
        "## Power Validation",
        "## Regression Criteria",
    ],
}


def validate(project_dir: Path) -> dict:
    failures = []
    checked = []
    for filename, headings in REQUIRED.items():
        path = project_dir / filename
        if not path.exists():
            failures.append({"file": filename, "issue": "missing file"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        checked.append(filename)
        for heading in headings:
            if heading not in text:
                failures.append({"file": filename, "issue": "missing heading", "heading": heading})
    return {
        "project_dir": str(project_dir),
        "checked_files": checked,
        "failed_count": len(failures),
        "failures": failures,
        "ok": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, help="directory containing generated planning docs")
    args = parser.parse_args()

    result = validate(Path(args.project_dir))
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
