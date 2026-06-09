#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Renode Robot Framework test template.")
    parser.add_argument("--out", default="embedded_debug.robot")
    parser.add_argument("--test-name", default="Golden Packet Boot")
    parser.add_argument("--resc", default="platform.resc")
    args = parser.parse_args()
    text = f"""*** Settings ***
Library    RenodeLibrary

*** Test Cases ***
{args.test_name}
    Execute Command    include @{args.resc}
    Create Terminal Tester    sysbus.uart
    Start Emulation
    Wait For Line On Uart    READY
    Wait For Line On Uart    PASS
"""
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
