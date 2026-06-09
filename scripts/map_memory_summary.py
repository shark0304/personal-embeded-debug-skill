#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECTION_RE = re.compile(r"^(\.[A-Za-z0-9_.$\-]+)\s+0x[0-9a-fA-F]+\s+0x([0-9a-fA-F]+)")
FLASH_PREFIXES = (".text", ".rodata", ".init", ".fini", ".ARM", ".isr_vector")
RAM_PREFIXES = (".data", ".bss", ".noinit", ".heap", ".stack")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize GNU ld map output sections.")
    parser.add_argument("--map", required=True, help="Linker map file.")
    parser.add_argument("--top", default=20, type=int, help="Number of largest sections to report.")
    args = parser.parse_args()

    sections = []
    for lineno, line in enumerate(Path(args.map).read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        match = SECTION_RE.match(line)
        if not match:
            continue
        name = match.group(1)
        size = int(match.group(2), 16)
        sections.append({"line": lineno, "name": name, "size_bytes": size})

    flash = sum(item["size_bytes"] for item in sections if item["name"].startswith(FLASH_PREFIXES))
    ram = sum(item["size_bytes"] for item in sections if item["name"].startswith(RAM_PREFIXES))
    output = {
        "section_count": len(sections),
        "estimated_flash_bytes": flash,
        "estimated_ram_bytes": ram,
        "largest_sections": sorted(sections, key=lambda item: item["size_bytes"], reverse=True)[: args.top],
        "notes": ["This is a heuristic over output section lines; confirm against the toolchain size report."],
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
