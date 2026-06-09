#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Check embedded-debug golden packet regression fixtures.")
    parser.add_argument(
        "--skill-dir",
        default=str(Path(__file__).resolve().parents[2]),
        help="Path to embedded-debug skill directory.",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    matrix_path = skill_dir / "tests" / "regression_matrix.yaml"
    matrix = load_yaml_or_json(matrix_path)
    cases = matrix.get("cases", []) if isinstance(matrix, dict) else []
    results = []
    for case in cases:
        results.append(check_case(skill_dir, case))
    failed = [item for item in results if not item["ok"]]
    output = {
        "case_count": len(cases),
        "passed_count": len(results) - len(failed),
        "failed_count": len(failed),
        "failed_cases": [item["id"] for item in failed],
        "results": results,
        "ok": not failed,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    if not output["ok"]:
        raise SystemExit(1)


def check_case(skill_dir: Path, case: dict[str, object]) -> dict[str, object]:
    case_id = str(case.get("id", ""))
    rel_path = str(case.get("path", f"tests/golden_packets/{case_id}"))
    root = skill_dir / rel_path
    required = ["README.symptom.md", "debug_packet.yaml", "expected_root_cause.md", "expected_report.md"]
    missing = [name for name in required if not (root / name).is_file()]
    packet_ok = False
    report_ok = False
    report_missing_sections: list[str] = []
    if not missing:
        packet = load_yaml_or_json(root / "debug_packet.yaml")
        packet_ok = isinstance(packet, dict) and bool(packet.get("case_id"))
        report_text = (root / "expected_report.md").read_text(encoding="utf-8")
        required_sections = [
            "Evidence completeness",
            "Hypothesis ranking",
            "Verification plan",
            "Fix plan",
            "Regression recommendation",
        ]
        report_missing_sections = [section for section in required_sections if section.lower() not in report_text.lower()]
        report_ok = not report_missing_sections
    return {
        "id": case_id,
        "path": rel_path,
        "missing": missing,
        "packet_parse_ok": packet_ok,
        "expected_report_ok": report_ok,
        "expected_report_missing_sections": report_missing_sections,
        "ok": not missing and packet_ok and report_ok,
    }


def load_yaml_or_json(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if yaml is not None:
        return yaml.safe_load(text)
    return parse_simple_yaml(text)


def parse_simple_yaml(text: str) -> object:
    if "cases:" in text:
        cases = []
        current: dict[str, str] | None = None
        for raw in text.splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            if stripped.startswith("- id:"):
                if current:
                    cases.append(current)
                current = {"id": stripped.split(":", 1)[1].strip()}
            elif current is not None and ":" in stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = value.strip()
        if current:
            cases.append(current)
        return {"cases": cases}
    data: dict[str, object] = {}
    for raw in text.splitlines():
        if raw.startswith(" ") or ":" not in raw or raw.strip().startswith("#"):
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


if __name__ == "__main__":
    main()
