#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROP_RE = re.compile(r"^\s*([A-Za-z0-9_,#\-\+]+)\s*(?:=|;)", re.MULTILINE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Heuristically inspect a DTS/devicetree node.")
    parser.add_argument("--dts", required=True, help="DTS, DTS dump, or generated zephyr.dts file.")
    parser.add_argument("--node", required=True, help="Node path/name/label substring to find.")
    parser.add_argument("--expect-compatible", action="append", default=[], help="Compatible string expected in node.")
    parser.add_argument("--require-prop", action="append", default=[], help="Required property name. Repeat as needed.")
    args = parser.parse_args()

    text = Path(args.dts).read_text(encoding="utf-8", errors="replace")
    matches = find_node_blocks(text, args.node)
    results = []
    for block in matches:
        props = set(PROP_RE.findall(block["body"]))
        compatibles = parse_compatible(block["body"])
        status = parse_status(block["body"])
        missing_props = [name for name in args.require_prop if name not in props]
        missing_compatible = [item for item in args.expect_compatible if item not in compatibles]
        results.append(
            {
                "line": block["line"],
                "header": block["header"].strip(),
                "status": status,
                "compatible": compatibles,
                "properties": sorted(props),
                "missing_required_properties": missing_props,
                "missing_expected_compatible": missing_compatible,
                "enabled": status not in {"disabled", "reserved", "fail"},
                "ok": not missing_props and not missing_compatible and status not in {"disabled", "reserved", "fail"},
            }
        )

    output = {
        "node_query": args.node,
        "match_count": len(results),
        "matches": results,
        "ok": bool(results) and all(item["ok"] for item in results),
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    if not output["ok"]:
        raise SystemExit(1)


def find_node_blocks(text: str, query: str) -> list[dict[str, str | int]]:
    matches = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if query not in line or "{" not in line:
            continue
        body_lines = [line]
        depth = line.count("{") - line.count("}")
        cursor = index + 1
        while cursor < len(lines) and depth > 0:
            body_lines.append(lines[cursor])
            depth += lines[cursor].count("{") - lines[cursor].count("}")
            cursor += 1
        matches.append({"line": index + 1, "header": line, "body": "\n".join(body_lines)})
    return matches


def parse_compatible(body: str) -> list[str]:
    match = re.search(r"compatible\s*=\s*([^;]+);", body, re.DOTALL)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def parse_status(body: str) -> str:
    match = re.search(r"status\s*=\s*\"([^\"]+)\"", body)
    if not match:
        return "okay_or_unspecified"
    return match.group(1)


if __name__ == "__main__":
    main()
