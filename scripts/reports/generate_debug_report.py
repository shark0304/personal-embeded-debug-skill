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
    parser = argparse.ArgumentParser(description="Generate a markdown debug report from a debug packet.")
    parser.add_argument("--packet", required=True, help="debug_packet.yaml/json")
    parser.add_argument("--analysis", default=None, help="Optional analysis JSON containing hypotheses.")
    parser.add_argument("--out", required=True, help="Output markdown report.")
    args = parser.parse_args()

    packet = load_data(Path(args.packet))
    analysis = load_data(Path(args.analysis)) if args.analysis else {}
    report = render_report(packet, analysis)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")


def load_data(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if yaml is not None:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    raise SystemExit(f"Cannot parse {path}; install PyYAML or provide JSON")


def render_report(packet: dict[str, object], analysis: dict[str, object]) -> str:
    missing = packet.get("missing_evidence") or []
    artifacts = packet.get("artifacts") if isinstance(packet.get("artifacts"), dict) else {}
    hypotheses = analysis.get("hypotheses") if isinstance(analysis.get("hypotheses"), list) else []
    lines = [
        "# Embedded Debug Report",
        "",
        "## 1. Case summary",
        "",
        f"- Case ID: `{packet.get('case_id', 'unknown')}`",
        f"- Platform: `{packet.get('platform', 'unknown')}`",
        f"- Board: `{packet.get('board', 'unknown')}`",
        f"- Shield: `{packet.get('shield', 'unknown')}`",
        f"- Toolchain: `{packet.get('toolchain', 'unknown')}`",
        f"- Build system: `{packet.get('build_system', 'unknown')}`",
        f"- Analysis status: `{packet.get('analysis_status', 'unknown')}`",
        "",
        "## 2. Evidence completeness",
        "",
    ]
    if artifacts:
        for key, value in sorted(artifacts.items()):
            count = len(value) if isinstance(value, list) else 1
            lines.append(f"- {key}: {count} artifact(s)")
    else:
        lines.append("- No artifacts collected.")
    lines.extend(["", "## 3. Missing critical evidence", ""])
    if missing:
        lines.extend(f"- {item}" for item in missing)
    else:
        lines.append("- None listed in packet.")
    lines.extend(["", "## 4. Hypothesis ranking", ""])
    if hypotheses:
        for item in hypotheses:
            lines.extend(render_hypothesis(item))
    else:
        lines.append("- No analysis JSON supplied. Generate hypotheses using the relevant runbook before claiming root cause.")
    lines.extend(["", "## 5. Verification plan", ""])
    if hypotheses:
        for item in hypotheses:
            lines.append(f"- {item.get('hypothesis_id', 'H?')}: {item.get('verification_step', 'missing verification step')}")
    else:
        lines.append("- Complete missing evidence, then create hypothesis entries with verification steps.")
    lines.extend(["", "## 6. Fix plan", ""])
    if hypotheses:
        for item in hypotheses:
            lines.append(f"- {item.get('hypothesis_id', 'H?')}: {item.get('fix_if_confirmed', 'fix not specified')}")
    else:
        lines.append("- No fix should be applied before at least one hypothesis is verified.")
    lines.extend(["", "## 7. Regression recommendation", ""])
    lines.append("- Preserve this debug packet as a golden packet after root cause and verification are complete.")
    return "\n".join(lines) + "\n"


def render_hypothesis(item: dict[str, object]) -> list[str]:
    return [
        f"### {item.get('hypothesis_id', 'H?')}: {item.get('root_cause', 'unspecified')}",
        "",
        f"- Confidence: {item.get('confidence', 'low')}",
        f"- Evidence for: {format_list(item.get('evidence_for'))}",
        f"- Evidence against: {format_list(item.get('evidence_against'))}",
        f"- Missing evidence: {format_list(item.get('missing_evidence'))}",
        f"- Verification step: {item.get('verification_step', 'missing')}",
        f"- Expected observation: {item.get('expected_observation', 'missing')}",
        f"- Fix if confirmed: {item.get('fix_if_confirmed', 'missing')}",
        "",
    ]


def format_list(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value) if value else "none"
    return str(value) if value else "none"


if __name__ == "__main__":
    main()
