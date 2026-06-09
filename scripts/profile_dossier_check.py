#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


PROFILE_REQUIRED = [
    ("engineer", "preferred_language"),
    ("platforms", "mcu"),
    ("tools", "debug_probes"),
    ("preferences", "warn_before_irreversible_actions"),
    ("safety_policy", "require_confirmation_for"),
]

DOSSIER_REQUIRED = [
    ("project", "name"),
    ("project", "board_revision"),
    ("hardware", "mcu_or_soc"),
    ("firmware", "toolchain"),
    ("debug", "probe"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check embedded engineer profile and project dossier completeness.")
    parser.add_argument("--profile", default=None, help="engineer_profile.json")
    parser.add_argument("--dossier", default=None, help="project_bringup_dossier.json")
    args = parser.parse_args()

    results = {}
    if args.profile:
        results["profile"] = check_file(Path(args.profile), PROFILE_REQUIRED)
    if args.dossier:
        results["dossier"] = check_file(Path(args.dossier), DOSSIER_REQUIRED)
    if not results:
        raise SystemExit("Provide --profile, --dossier, or both")

    ok = all(item["ok"] for item in results.values())
    output = {"ok": ok, "results": results}
    print(json.dumps(output, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


def check_file(path: Path, required: list[tuple[str, str]]) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = []
    empty = []
    for section, key in required:
        if section not in data or key not in data[section]:
            missing.append(f"{section}.{key}")
            continue
        value = data[section][key]
        if value in ("", [], {}, None):
            empty.append(f"{section}.{key}")
    return {"path": str(path), "missing": missing, "empty": empty, "ok": not missing and not empty}


if __name__ == "__main__":
    main()
