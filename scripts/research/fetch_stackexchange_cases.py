#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Stack Exchange question metadata into research/public_cases/raw using the official API.")
    parser.add_argument("--query", required=True, help="Search query, e.g. 'i2c sensor nack zephyr'.")
    parser.add_argument("--site", default="electronics", help="Stack Exchange site, e.g. electronics, stackoverflow.")
    parser.add_argument("--tagged", help="Optional semicolon-separated tags.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results to request.")
    parser.add_argument("--out-dir", default="research/public_cases/raw", help="Raw output directory.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = fetch(args.query, args.site, args.tagged, args.limit)
    out_path = out_dir / f"stackexchange_cases_{safe_name(args.site + '_' + args.query)}_{int(time.time())}.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out_path), "result_count": len(payload.get("items", []))}, sort_keys=True))


def fetch(query: str, site: str, tagged: str | None, limit: int) -> dict[str, object]:
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": query,
        "site": site,
        "pagesize": str(max(1, min(limit, 100))),
        "filter": "default",
    }
    if tagged:
        params["tagged"] = tagged
    url = "https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "embedded-debug-public-case-ingestion"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return {"source_api": "stackexchange_search_advanced", "query": query, "site": site, "items": data.get("items", [])}


def safe_name(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    return "_".join(part for part in cleaned.split("_") if part)[:80] or "query"


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
