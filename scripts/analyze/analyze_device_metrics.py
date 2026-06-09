#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


METRIC_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(-?[0-9]+(?:\.[0-9]+)?)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse simple key=value device metrics from field logs.")
    parser.add_argument("--log", required=True)
    args = parser.parse_args()
    text = Path(args.log).read_text(encoding="utf-8", errors="replace")
    metrics: dict[str, list[float]] = {}
    for key, value in METRIC_RE.findall(text):
        metrics.setdefault(key, []).append(float(value))
    summary = {
        key: {"count": len(values), "min": min(values), "max": max(values), "last": values[-1]}
        for key, values in metrics.items()
    }
    output = {"metrics": summary, "artifacts": {"metrics_log": args.log}}
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
