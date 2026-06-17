#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from score_embedded_relevance import score_candidate


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact embedded project corpus index from candidates and snapshot signal JSON files.")
    parser.add_argument("--candidates", required=True, help="Candidates JSONL from mine_github_projects.py.")
    parser.add_argument("--signals-dir", help="Directory containing extract_project_signals.py JSON outputs.")
    parser.add_argument("--out-csv", default="research/project_corpus/embedded_project_index.csv")
    parser.add_argument("--out-jsonl", default="research/project_corpus/embedded_project_index.jsonl")
    args = parser.parse_args()

    candidates = load_jsonl(Path(args.candidates))
    signals = load_signals(Path(args.signals_dir)) if args.signals_dir else {}
    rows = []
    for candidate in candidates:
        repo = str(candidate.get("full_name", ""))
        merged = {**candidate, **signals.get(repo, {})}
        scored = score_candidate(merged)
        rows.append(scored)
    rows.sort(key=lambda item: (-int(item.get("score", 0)), str(item.get("full_name") or item.get("repo", ""))))
    write_outputs(rows, Path(args.out_csv), Path(args.out_jsonl))
    print(json.dumps({"ok": True, "row_count": len(rows), "out_csv": args.out_csv, "out_jsonl": args.out_jsonl}, indent=2, sort_keys=True))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_signals(root: Path) -> dict[str, dict[str, Any]]:
    signals: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            repo = str(data.get("repo", ""))
            if repo:
                signals[repo] = data
    return signals


def write_outputs(rows: list[dict[str, Any]], out_csv: Path, out_jsonl: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["repo", "score", "embedded_family", "review_priority", "primary_adapter", "html_url", "matched_signals"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "repo": row.get("full_name") or row.get("repo", ""),
                    "score": row.get("score", 0),
                    "embedded_family": row.get("embedded_family", "unknown"),
                    "review_priority": row.get("review_priority", "skip"),
                    "primary_adapter": row.get("primary_adapter", ""),
                    "html_url": row.get("html_url", ""),
                    "matched_signals": ";".join(row.get("matched_signals", [])),
                }
            )
    out_jsonl.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


if __name__ == "__main__":
    main()
