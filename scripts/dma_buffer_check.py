#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check DMA buffer cache-line alignment and maintenance span."
    )
    parser.add_argument("--address", required=True, help="Buffer start address.")
    parser.add_argument("--size", required=True, help="Buffer size, e.g. 1536, 4K.")
    parser.add_argument("--cache-line", default="32", help="Cache line size in bytes.")
    parser.add_argument(
        "--direction",
        choices=["rx", "tx", "bidirectional", "unknown"],
        default="unknown",
        help="DMA direction from CPU perspective: rx=peripheral-to-memory, tx=memory-to-peripheral.",
    )
    parser.add_argument(
        "--region-cacheable",
        choices=["true", "false", "unknown"],
        default="unknown",
        help="Whether the buffer memory region is cacheable.",
    )
    args = parser.parse_args()

    address = parse_int(args.address)
    size = parse_size(args.size)
    cache_line = parse_int(args.cache_line)
    if size <= 0:
        raise SystemExit("--size must be positive")
    if cache_line <= 0 or cache_line & (cache_line - 1):
        raise SystemExit("--cache-line must be a positive power of two")

    span_start = align_down(address, cache_line)
    span_end = align_up(address + size, cache_line)
    extra_before = address - span_start
    extra_after = span_end - (address + size)
    aligned_start = extra_before == 0
    aligned_end = extra_after == 0

    warnings = build_warnings(
        aligned_start=aligned_start,
        aligned_end=aligned_end,
        region_cacheable=args.region_cacheable,
        direction=args.direction,
    )
    recommendations = build_recommendations(args.direction, args.region_cacheable)

    output = {
        "buffer": {
            "address": hex(address),
            "size_bytes": size,
            "end_exclusive": hex(address + size),
        },
        "cache_line_bytes": cache_line,
        "alignment": {
            "start_aligned": aligned_start,
            "end_aligned": aligned_end,
            "extra_bytes_before": extra_before,
            "extra_bytes_after": extra_after,
        },
        "maintenance_span": {
            "start": hex(span_start),
            "end_exclusive": hex(span_end),
            "size_bytes": span_end - span_start,
            "cache_lines": (span_end - span_start) // cache_line,
        },
        "direction": args.direction,
        "region_cacheable": args.region_cacheable,
        "warnings": warnings,
        "recommendations": recommendations,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def build_warnings(
    *,
    aligned_start: bool,
    aligned_end: bool,
    region_cacheable: str,
    direction: str,
) -> list[str]:
    warnings: list[str] = []
    if region_cacheable != "false" and (not aligned_start or not aligned_end):
        warnings.append(
            "Cache maintenance span touches bytes outside the requested buffer; isolate or align DMA buffers."
        )
    if region_cacheable == "unknown":
        warnings.append("Cacheability is unknown; verify MPU/linker section before blaming the peripheral.")
    if region_cacheable == "true" and direction == "unknown":
        warnings.append("Direction is unknown; cache clean/invalidate timing cannot be chosen safely.")
    if region_cacheable == "false" and (not aligned_start or not aligned_end):
        warnings.append("Nocache buffers can still require DMA controller alignment or descriptor alignment.")
    return warnings


def build_recommendations(direction: str, region_cacheable: str) -> list[str]:
    if region_cacheable == "false":
        return [
            "Cache maintenance is normally unnecessary for this buffer; still verify DMA-accessible memory.",
            "Keep descriptor and payload buffers in regions the DMA engine can access.",
        ]

    recommendations = [
        "Align buffer start and allocation size to the cache line, or move it to a nocache DMA section.",
        "Use the rounded maintenance span when the vendor API requires aligned address/size.",
    ]
    if direction in {"tx", "bidirectional"}:
        recommendations.append("Clean DCache for the buffer before enabling memory-to-peripheral DMA.")
    if direction in {"rx", "bidirectional"}:
        recommendations.append("Invalidate DCache for the buffer after DMA completion and before CPU reads.")
    if direction == "rx":
        recommendations.append("Avoid CPU writes to the RX buffer while DMA owns it.")
    if direction == "unknown":
        recommendations.append("Record transfer direction before selecting clean versus invalidate.")
    return recommendations


def align_down(value: int, alignment: int) -> int:
    return value & ~(alignment - 1)


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def parse_size(text: str) -> int:
    normalized = text.strip().lower()
    multiplier = 1
    if normalized.endswith("kb"):
        multiplier = 1024
        normalized = normalized[:-2]
    elif normalized.endswith("k"):
        multiplier = 1024
        normalized = normalized[:-1]
    elif normalized.endswith("mb"):
        multiplier = 1024 * 1024
        normalized = normalized[:-2]
    elif normalized.endswith("m"):
        multiplier = 1024 * 1024
        normalized = normalized[:-1]
    try:
        return int(float(normalized) * multiplier)
    except ValueError as exc:
        raise SystemExit(f"Invalid size: {text}") from exc


def parse_int(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise SystemExit(f"Invalid integer: {text}") from exc


if __name__ == "__main__":
    main()
