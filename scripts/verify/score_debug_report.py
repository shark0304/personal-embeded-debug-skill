#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


UNSUPPORTED_CERTAINTY = [
    "definitely caused by",
    "must be",
    "root cause is certain",
    "no need to verify",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Score an embedded debug report against the v3 report contract.")
    parser.add_argument("--report", required=True, help="Markdown debug report.")
    parser.add_argument("--out", help="Optional output JSON path. Defaults to stdout only.")
    args = parser.parse_args()

    text = Path(args.report).read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    score = 0
    failed_rules: list[str] = []

    score += section_score(lower, "case summary", 10, failed_rules)
    score += section_score(lower, "evidence completeness", 15, failed_rules)
    score += section_score(lower, "missing critical evidence", 10, failed_rules)
    score += section_score(lower, "hypothesis ranking", 20, failed_rules)
    score += field_score(lower, ["evidence_for", "evidence for"], 10, "hypothesis evidence_for", failed_rules)
    score += field_score(lower, ["evidence_against", "evidence against"], 10, "hypothesis evidence_against", failed_rules)
    score += field_score(lower, ["verification_step", "verification step"], 10, "hypothesis verification_step", failed_rules)
    score += section_score(lower, "fix plan", 10, failed_rules)
    score += section_score(lower, "regression recommendation", 5, failed_rules)

    certainty_hits = [phrase for phrase in UNSUPPORTED_CERTAINTY if phrase in lower]
    if certainty_hits:
        penalty = 10 * len(certainty_hits)
        score = max(0, score - penalty)
        failed_rules.append(f"unsupported certainty: {', '.join(certainty_hits)}")

    hypothesis_count = len(re.findall(r"^###\s+", text, flags=re.MULTILINE))
    if hypothesis_count == 0:
        failed_rules.append("no explicit hypothesis entries")

    ok = score >= 80 and not certainty_hits
    output = {"score": score, "ok": ok, "failed_rules": failed_rules}
    text = json.dumps(output, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    if not ok:
        raise SystemExit(1)


def section_score(text: str, section: str, points: int, failed_rules: list[str]) -> int:
    if section in text:
        return points
    failed_rules.append(f"missing section: {section}")
    return 0


def field_score(text: str, names: list[str], points: int, label: str, failed_rules: list[str]) -> int:
    if any(name in text for name in names):
        return points
    failed_rules.append(f"missing field: {label}")
    return 0


if __name__ == "__main__":
    main()
