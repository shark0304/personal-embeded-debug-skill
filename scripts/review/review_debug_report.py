#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


UNSUPPORTED_CERTAINTY = [
    "definitely caused by",
    "must be the root cause",
    "root cause is certain",
    "no need to verify",
    "obviously the root cause",
]

REQUIRED_SIGNALS = [
    ("case_summary", 8, ["case summary", "summary"]),
    ("evidence_completeness", 12, ["evidence completeness", "evidence score"]),
    ("missing_evidence", 10, ["missing evidence", "missing critical evidence", "next evidence"]),
    ("hypothesis_ranking", 14, ["hypothesis ranking", "most likely causes", "failure pattern matches"]),
    ("evidence_for", 10, ["evidence for", "matched terms", "observed"]),
    ("evidence_against", 10, ["evidence against", "counter evidence"]),
    ("verification_step", 12, ["verification step", "first verification", "fix verification"]),
    ("fix_plan", 8, ["fix plan", "fix candidates", "fix verification plan"]),
    ("regression", 8, ["regression", "golden packet"]),
    ("boundary", 8, ["report boundary", "should not be treated as a confirmed root cause", "not a confirmed root cause"]),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Review an embedded debug report for evidence discipline and premature conclusions.")
    parser.add_argument("--report", required=True, help="Markdown debug report path.")
    parser.add_argument("--out", help="Optional output path.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--min-score", type=int, default=0, help="Exit nonzero if review score is below this threshold.")
    args = parser.parse_args()

    report_path = Path(args.report)
    result = review_report(report_path, report_path.read_text(encoding="utf-8", errors="replace"))
    text = render_markdown(result) if args.format == "markdown" else json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    if args.min_score and int(result["score"]) < args.min_score:
        raise SystemExit(1)


def review_report(path: Path, text: str) -> dict[str, Any]:
    lower = text.lower()
    checks: list[dict[str, Any]] = []
    score = 0
    for name, points, patterns in REQUIRED_SIGNALS:
        hit = any(pattern in lower for pattern in patterns)
        checks.append({"name": name, "points": points, "passed": hit, "patterns": patterns})
        if hit:
            score += points

    certainty_hits = [phrase for phrase in UNSUPPORTED_CERTAINTY if phrase in lower]
    if certainty_hits:
        score = max(0, score - 10 * len(certainty_hits))
    hypothesis_entries = count_hypotheses(text)
    if hypothesis_entries >= 2:
        score = min(100, score + 5)
    elif hypothesis_entries == 0:
        checks.append({"name": "hypothesis_entries", "points": 0, "passed": False, "patterns": ["### hypothesis", "numbered causes"]})

    findings = build_findings(checks, certainty_hits, hypothesis_entries)
    return {
        "ok": score >= 80 and not certainty_hits,
        "score": score,
        "grade": grade(score),
        "report": str(path),
        "hypothesis_entries": hypothesis_entries,
        "unsupported_certainty": certainty_hits,
        "checks": checks,
        "findings": findings,
    }


def count_hypotheses(text: str) -> int:
    markdown_headers = len(re.findall(r"^###\s+", text, flags=re.MULTILINE))
    numbered = len(re.findall(r"^\d+\.\s+`?[\w.-]+", text, flags=re.MULTILINE))
    return max(markdown_headers, numbered)


def build_findings(checks: list[dict[str, Any]], certainty_hits: list[str], hypothesis_entries: int) -> list[str]:
    findings: list[str] = []
    for check in checks:
        if not check.get("passed"):
            findings.append(f"Missing or weak: {check['name']}.")
    if certainty_hits:
        findings.append("Report uses unsupported certainty language; keep root-cause claims provisional until verified.")
    if hypothesis_entries == 0:
        findings.append("No explicit hypothesis entries were detected.")
    if not findings:
        findings.append("Report is evidence-disciplined enough for handoff review.")
    return findings


def grade(score: int) -> str:
    if score >= 90:
        return "handoff-ready"
    if score >= 80:
        return "review-ready"
    if score >= 60:
        return "needs-evidence"
    return "premature"


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Debug Report Review",
        "",
        f"- Report: `{result['report']}`",
        f"- Score: **{result['score']}/100** (`{result['grade']}`)",
        f"- Ready for handoff: **{'yes' if result['ok'] else 'no'}**",
        f"- Hypothesis entries detected: `{result['hypothesis_entries']}`",
        "",
        "## Findings",
        "",
    ]
    for finding in result.get("findings", []):
        lines.append(f"- {finding}")
    lines.extend(["", "## Checks", ""])
    for check in result.get("checks", []):
        lines.append(f"- `{'pass' if check['passed'] else 'fail'}` {check['name']} ({check['points']} pts)")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
