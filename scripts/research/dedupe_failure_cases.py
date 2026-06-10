#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Find likely duplicate public failure case summaries.")
    parser.add_argument("--case-dir", default="research/public_cases/extracted", help="Directory containing YAML/JSON case summaries.")
    parser.add_argument("--out", help="Optional JSON output path. Defaults to stdout.")
    args = parser.parse_args()

    cases = load_cases(Path(args.case_dir))
    buckets: dict[str, list[str]] = {}
    for path, case in cases:
        buckets.setdefault(fingerprint(case), []).append(str(path))
    duplicates = {key: value for key, value in buckets.items() if len(value) > 1}
    output = {"ok": True, "case_count": len(cases), "duplicate_groups": duplicates}
    text = json.dumps(output, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


def load_cases(root: Path) -> list[tuple[Path, dict[str, object]]]:
    paths = list(root.glob("*.yaml")) + list(root.glob("*.yml")) + list(root.glob("*.json"))
    cases = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            data = json.loads(text)
        elif yaml is not None:
            data = yaml.safe_load(text)
        else:
            continue
        if isinstance(data, dict):
            cases.append((path, data))
    return cases


def fingerprint(case: dict[str, object]) -> str:
    parts = [
        str(case.get("platform", "")).lower(),
        joined(case.get("symptoms")),
        joined(case.get("candidate_root_causes")),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]


def joined(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(item).lower() for item in value)
    return str(value).lower()


if __name__ == "__main__":
    main()
