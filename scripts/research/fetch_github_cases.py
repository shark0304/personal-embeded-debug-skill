#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public GitHub issue/discussion metadata into research/public_cases/raw.")
    parser.add_argument("--query", required=True, help="GitHub search query, e.g. 'lsm6dsl failed initialize repo:zephyrproject-rtos/zephyr'.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to request.")
    parser.add_argument("--out-dir", default="research/public_cases/raw", help="Raw output directory.")
    parser.add_argument("--use-gh", action="store_true", help="Use gh CLI instead of GitHub REST search API.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = fetch_with_gh(args.query, args.limit) if args.use_gh else fetch_with_rest(args.query, args.limit)
    out_path = out_dir / f"github_cases_{safe_name(args.query)}_{int(time.time())}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out_path), "result_count": result_count(payload)}, sort_keys=True))


def fetch_with_rest(query: str, limit: int) -> dict[str, object]:
    params = urllib.parse.urlencode({"q": query, "per_page": max(1, min(limit, 100))})
    request = urllib.request.Request(
        f"https://api.github.com/search/issues?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "embedded-debug-public-case-ingestion",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {"source_api": "github_rest_search_issues", "query": query, "items": data.get("items", [])}


def fetch_with_gh(query: str, limit: int) -> dict[str, object]:
    command = [
        "gh",
        "search",
        "issues",
        query,
        "--limit",
        str(limit),
        "--json",
        "title,url,state,repository,createdAt,updatedAt,labels",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.stderr.strip() or "gh search failed")
    return {"source_api": "gh_search_issues", "query": query, "items": json.loads(completed.stdout or "[]")}


def safe_name(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    return "_".join(part for part in cleaned.split("_") if part)[:80] or "query"


def result_count(payload: dict[str, object]) -> int:
    items = payload.get("items")
    return len(items) if isinstance(items, list) else 0


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
