#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

COLLECT_DIR = Path(__file__).resolve().parents[1] / "collect"
if str(COLLECT_DIR) not in sys.path:
    sys.path.insert(0, str(COLLECT_DIR))

from validate_debug_packet import load_packet  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Match debug packet evidence against bundled failure patterns.")
    parser.add_argument("--packet", required=True, help="debug_packet.yaml/json path.")
    parser.add_argument("--patterns-dir", default=str(Path(__file__).resolve().parents[2] / "references" / "failure_patterns"))
    parser.add_argument("--project-root", help="Project root for reading artifact snippets. Defaults to packet project_root.")
    parser.add_argument("--out", help="Optional output path.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()

    packet_path = Path(args.packet)
    packet = load_packet(packet_path)
    project_root = Path(args.project_root or packet.get("project_root") or packet_path.parent).resolve()
    patterns = load_patterns(Path(args.patterns_dir))
    haystack = build_haystack(packet, project_root)
    matches = rank_patterns(patterns, haystack, packet)
    result = {"pattern_count": len(patterns), "matches": matches[:10], "project_root": str(project_root)}
    text = render_markdown(result) if args.format == "markdown" else json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


def load_patterns(patterns_dir: Path) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    for path in sorted(patterns_dir.glob("*.yaml")):
        data = load_yaml_like(path)
        for item in data.get("patterns", []) if isinstance(data, dict) else []:
            if isinstance(item, dict):
                item = dict(item)
                item["source"] = str(path)
                patterns.append(item)
    return patterns


def load_yaml_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    return parse_pattern_yaml(text)


def parse_pattern_yaml(text: str) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_key: str | None = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped == "patterns:":
            continue
        if stripped.startswith("- id:"):
            if current:
                patterns.append(current)
            current = {"id": stripped.split(":", 1)[1].strip()}
            current_key = None
        elif current is not None and re.match(r"^[a-zA-Z_]+:", stripped):
            key, value = stripped.split(":", 1)
            current_key = key
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                current[key] = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
            elif value:
                current[key] = value.strip("\"'")
            else:
                current[key] = []
        elif current is not None and stripped.startswith("- ") and current_key:
            current.setdefault(current_key, []).append(stripped[2:].strip())
    if current:
        patterns.append(current)
    return {"patterns": patterns}


def build_haystack(packet: dict[str, Any], project_root: Path) -> str:
    parts = [json.dumps(packet, sort_keys=True)]
    artifacts = packet.get("artifacts", {})
    if isinstance(artifacts, dict):
        for paths in artifacts.values():
            if isinstance(paths, str):
                paths = [paths]
            if not isinstance(paths, list):
                continue
            for rel in paths[:8]:
                path = project_root / str(rel)
                if path.is_file() and path.stat().st_size <= 256_000:
                    try:
                        parts.append(path.read_text(encoding="utf-8", errors="replace"))
                    except OSError:
                        pass
    return "\n".join(parts).lower()


def rank_patterns(patterns: list[dict[str, Any]], haystack: str, packet: dict[str, Any]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    platform = str(packet.get("platform", "")).lower()
    for pattern in patterns:
        symptoms = normalize_list(pattern.get("symptoms"))
        required = normalize_list(pattern.get("required_evidence"))
        terms = keywords([str(pattern.get("id", "")), str(pattern.get("domain", "")), *symptoms])
        hits = sorted({term for term in terms if term and term in haystack})
        score = min(100, int((len(hits) / max(1, len(terms))) * 70))
        domain = str(pattern.get("domain", "")).lower().replace("_", "-")
        if platform and (platform in domain or domain in platform):
            score += 15
        if any(evidence_hint(item) in haystack for item in required):
            score += 10
        score = min(100, score)
        if score > 0:
            ranked.append(
                {
                    "id": pattern.get("id", "unknown"),
                    "domain": pattern.get("domain", "unknown"),
                    "score": score,
                    "matched_terms": hits[:12],
                    "required_evidence": required,
                    "verify": normalize_list(pattern.get("verify")),
                    "fix": normalize_list(pattern.get("fix")),
                    "regression_hint": normalize_list(pattern.get("regression_hint")),
                    "source": pattern.get("source", ""),
                }
            )
    ranked.sort(key=lambda item: (-int(item["score"]), str(item["id"])))
    return ranked


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def keywords(values: list[str]) -> list[str]:
    out: list[str] = []
    stop = {"the", "and", "for", "from", "into", "that", "this", "with", "during", "when", "not", "set", "valid", "actual", "expected", "created", "device", "root"}
    for value in values:
        for token in re.findall(r"[a-zA-Z0-9_./-]{3,}", value.lower()):
            if token not in stop and token not in out:
                out.append(token)
    return out


def evidence_hint(item: str) -> str:
    item_l = item.lower()
    for hint in ["dmesg", "dts", "kconfig", "elf", "map", "serial", "logic", "scope", "cfsr", "hfsr", "bfar", "sdkconfig"]:
        if hint in item_l:
            return hint
    return item_l


def render_markdown(result: dict[str, Any]) -> str:
    lines = ["# Failure Pattern Matches", "", f"- Patterns scanned: `{result['pattern_count']}`", ""]
    matches = result.get("matches", [])
    if not matches:
        lines.append("No pattern matched the available evidence.")
        return "\n".join(lines)
    for idx, match in enumerate(matches, start=1):
        lines.extend(
            [
                f"## {idx}. `{match['id']}`",
                "",
                f"- Domain: `{match['domain']}`",
                f"- Score: `{match['score']}`",
                f"- Matched terms: {format_items(match.get('matched_terms', []))}",
                f"- Required evidence: {format_items(match.get('required_evidence', []))}",
                "",
                "Verification:",
            ]
        )
        for item in match.get("verify", []):
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def format_items(items: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in items) if items else "none"


if __name__ == "__main__":
    main()
