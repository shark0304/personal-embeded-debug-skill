#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SIGNALS: list[tuple[str, int, str]] = [
    ("west.yml", 22, "zephyr"),
    ("prj.conf", 18, "zephyr"),
    ("zephyr.dts", 16, "zephyr"),
    ("sdkconfig", 22, "esp-idf"),
    ("idf_component_register", 20, "esp-idf"),
    ("platformio.ini", 22, "platformio"),
    (".ioc", 22, "stm32cube"),
    ("freertosconfig.h", 22, "freertos"),
    ("kbuild", 18, "embedded-linux"),
    ("kconfig", 12, "embedded-linux"),
    (".dts", 14, "embedded-linux"),
    (".dtsi", 14, "embedded-linux"),
    (".tflite", 18, "tinyml"),
    ("tflite micro", 18, "tinyml"),
    ("stm32", 12, "cortex-m"),
    ("nrf52", 12, "zephyr"),
    ("esp32", 12, "esp-idf"),
    ("cortex-m", 12, "cortex-m"),
    ("embedded", 8, "generic"),
    ("firmware", 8, "generic"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Score public repo candidates for embedded-project relevance.")
    parser.add_argument("--input", required=True, help="JSONL candidates, JSON list, or a single candidate JSON object.")
    parser.add_argument("--out", help="Optional JSONL output path.")
    parser.add_argument("--min-score", type=int, default=0, help="Only emit candidates at or above this score.")
    args = parser.parse_args()

    candidates = load_candidates(Path(args.input))
    rows = [score_candidate(candidate) for candidate in candidates]
    rows = [row for row in rows if int(row["score"]) >= args.min_score]
    text = "\n".join(json.dumps(row, sort_keys=True) for row in rows)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + ("\n" if text else ""), encoding="utf-8")
    print(json.dumps({"ok": True, "input_count": len(candidates), "output_count": len(rows), "max_score": max([0, *[int(row["score"]) for row in rows]])}, indent=2, sort_keys=True))


def load_candidates(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return [normalize_github_repo(item) for item in items if isinstance(item, dict)]
        return [data]
    return []


def score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    text = searchable_text(candidate)
    score = 0
    hits: list[str] = []
    families: dict[str, int] = {}
    for signal, points, family in SIGNALS:
        if signal in text:
            score += points
            hits.append(signal)
            families[family] = families.get(family, 0) + points
    score += min(12, int(candidate.get("stargazers_count") or candidate.get("stars") or 0) // 50)
    score = min(100, score)
    family = max(families.items(), key=lambda item: item[1])[0] if families else "unknown"
    return {
        **candidate,
        "score": score,
        "embedded_family": family,
        "matched_signals": sorted(set(hits)),
        "review_priority": priority(score),
    }


def searchable_text(candidate: dict[str, Any]) -> str:
    values = [
        candidate.get("full_name"),
        candidate.get("name"),
        candidate.get("description"),
        candidate.get("language"),
        candidate.get("topics"),
        candidate.get("manifest_paths"),
        candidate.get("files"),
    ]
    return " ".join(flatten(values)).lower()


def flatten(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if isinstance(value, list):
            out.extend(str(item) for item in value)
        elif value is not None:
            out.append(str(value))
    return out


def normalize_github_repo(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "full_name": item.get("full_name", ""),
        "html_url": item.get("html_url", ""),
        "description": item.get("description", ""),
        "language": item.get("language", ""),
        "stargazers_count": item.get("stargazers_count", 0),
        "fork": item.get("fork", False),
        "archived": item.get("archived", False),
        "topics": item.get("topics", []),
        "default_branch": item.get("default_branch", "main"),
    }


def priority(score: int) -> str:
    if score >= 70:
        return "snapshot-now"
    if score >= 40:
        return "review"
    if score >= 20:
        return "keep-candidate"
    return "skip"


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "_", value.lower()).strip("_")


if __name__ == "__main__":
    main()
