#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Zephyr Twister testcase.yaml template.")
    parser.add_argument("--out", default="testcase.yaml", help="Output testcase.yaml path.")
    parser.add_argument("--test-name", default="embedded_debug.golden_packet")
    parser.add_argument("--platform", default="native_sim")
    args = parser.parse_args()
    text = f"""tests:
  {args.test_name}:
    platform_allow:
      - {args.platform}
    tags:
      - embedded_debug
      - golden_packet
    harness: console
    harness_config:
      type: one_line
      regex:
        - "PASS"
"""
    write(Path(args.out), text)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
