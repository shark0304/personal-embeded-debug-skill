#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RESOURCE_RE = re.compile(r"`([^`]+\.(?:md|py|sh|c))`")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate embedded-debug evaluation scenario table.")
    parser.add_argument(
        "--skill-dir",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the embedded-debug skill directory.",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    eval_file = skill_dir / "references" / "evaluation_scenarios.md"
    rows = parse_table(eval_file.read_text(encoding="utf-8"))
    resources = index_resources(skill_dir)

    missing_resources = []
    empty_fields = []
    prefixes: dict[str, int] = {}
    for row in rows:
        scenario_id = row["ID"]
        prefix = scenario_id.split("-", 1)[0]
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
        for field in ("Symptom", "First evidence to ask for", "Expected references/tools", "Bad answer to avoid"):
            if not row[field].strip():
                empty_fields.append({"id": scenario_id, "field": field})
        for resource in RESOURCE_RE.findall(row["Expected references/tools"]):
            if resource not in resources:
                missing_resources.append({"id": scenario_id, "resource": resource})

    output = {
        "scenario_count": len(rows),
        "prefix_counts": dict(sorted(prefixes.items())),
        "missing_resources": missing_resources,
        "empty_fields": empty_fields,
        "ok": not missing_resources and not empty_fields,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    if not output["ok"]:
        raise SystemExit(1)


def parse_table(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.startswith("|")]
    if len(lines) < 3:
        raise SystemExit("No markdown table found")
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            raise SystemExit(f"Bad table row: {line}")
        rows.append(dict(zip(headers, cells)))
    return rows


def index_resources(skill_dir: Path) -> set[str]:
    resources = set()
    for subdir in ("references", "scripts", "assets"):
        root = skill_dir / subdir
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                resources.add(path.name)
                resources.add(str(path.relative_to(skill_dir)))
    return resources


if __name__ == "__main__":
    main()
