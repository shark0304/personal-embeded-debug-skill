#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_QUERIES = [
    "zephyr prj.conf embedded firmware",
    "esp-idf sdkconfig firmware",
    "platformio.ini embedded",
    "FreeRTOSConfig.h firmware",
    "STM32 .ioc firmware",
    "Kbuild device tree driver embedded linux",
    "tflite micro embedded",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover public embedded-project candidates via GitHub's official search API.")
    parser.add_argument("--query", action="append", help="GitHub repository search query. Can be repeated. Defaults to embedded seed queries.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum candidates across all queries.")
    parser.add_argument("--out", default="research/project_corpus/candidates.jsonl", help="Output JSONL path.")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between API requests in seconds.")
    parser.add_argument("--fixture-json", help="Use a local GitHub search JSON fixture instead of network.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned queries without calling the network.")
    args = parser.parse_args()

    queries = args.query or DEFAULT_QUERIES
    if args.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "queries": queries, "limit": args.limit}, indent=2, sort_keys=True))
        return

    if args.fixture_json:
        payloads = [json.loads(Path(args.fixture_json).read_text(encoding="utf-8"))]
    else:
        payloads = []
        for query in queries:
            if sum(len(payload.get("items", [])) for payload in payloads if isinstance(payload, dict)) >= args.limit:
                break
            payloads.append(fetch_search_page(query, min(100, args.limit)))
            time.sleep(max(0.0, args.delay))

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for payload in payloads:
        for item in payload.get("items", []) if isinstance(payload, dict) else []:
            if not isinstance(item, dict):
                continue
            candidate = normalize_repo(item, str(payload.get("query", "")))
            key = str(candidate.get("full_name"))
            if key and key not in seen:
                seen.add(key)
                candidates.append(candidate)
            if len(candidates) >= args.limit:
                break

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(item, sort_keys=True) for item in candidates) + ("\n" if candidates else ""), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out), "candidate_count": len(candidates)}, indent=2, sort_keys=True))


def fetch_search_page(query: str, per_page: int) -> dict[str, Any]:
    params = urllib.parse.urlencode({"q": query, "per_page": max(1, min(per_page, 100)), "sort": "stars", "order": "desc"})
    request = urllib.request.Request(
        f"https://api.github.com/search/repositories?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "embedded-debug-public-project-miner",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    data["query"] = query
    return data


def normalize_repo(item: dict[str, Any], query: str) -> dict[str, Any]:
    return {
        "source": "github_search_repositories",
        "query": query,
        "full_name": item.get("full_name", ""),
        "html_url": item.get("html_url", ""),
        "description": item.get("description", ""),
        "language": item.get("language", ""),
        "stargazers_count": item.get("stargazers_count", 0),
        "fork": item.get("fork", False),
        "archived": item.get("archived", False),
        "topics": item.get("topics", []),
        "default_branch": item.get("default_branch", "main"),
        "pushed_at": item.get("pushed_at", ""),
    }


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
