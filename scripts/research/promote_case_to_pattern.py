#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote a reviewed public failure case into a failure-pattern candidate YAML.")
    parser.add_argument("--case", required=True, help="Reviewed public failure case YAML/JSON.")
    parser.add_argument("--out", required=True, help="Output pattern YAML/JSON path.")
    parser.add_argument("--pattern-id", help="Optional pattern ID. Defaults to case_id.")
    args = parser.parse_args()

    case = load_case(Path(args.case))
    review = case.get("review") if isinstance(case.get("review"), dict) else {}
    if review.get("review_status") != "reviewed":
        raise SystemExit("Refusing promotion: review.review_status must be reviewed")
    if not review.get("promote_to_pattern"):
        raise SystemExit("Refusing promotion: review.promote_to_pattern is not true")

    pattern = {
        "id": args.pattern_id or safe_id(str(case.get("case_id", "public_failure_case"))),
        "domain": str(case.get("platform", "unknown")).lower().replace(" ", "_"),
        "symptoms": case.get("symptoms", []),
        "required_evidence": case.get("evidence_present", []),
        "confidence_rules": {
            "low": "Public case resembles this pattern but decisive evidence is missing.",
            "medium": "Debug packet matches symptoms and minimum evidence.",
            "high": "Verification steps reproduce and fix the branch.",
        },
        "verify": case.get("verification_steps", []),
        "fix": case.get("outcome", "Promote only after project-specific verification."),
        "regression_hint": "Create a golden packet only after root cause and verification evidence are preserved.",
        "source_case_id": case.get("case_id"),
    }
    write_yaml_or_json(Path(args.out), pattern)
    print(json.dumps({"ok": True, "out": args.out, "pattern_id": pattern["id"]}, sort_keys=True))


def load_case(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
    elif yaml is not None:
        data = yaml.safe_load(text)
    else:
        raise SystemExit("YAML input requires PyYAML; provide JSON instead")
    if not isinstance(data, dict):
        raise SystemExit("Case file must contain an object")
    return data


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "public_failure_case"


def write_yaml_or_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None and path.suffix != ".json":
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
