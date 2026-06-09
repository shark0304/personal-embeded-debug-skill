#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


ARTIFACT_PATTERNS = {
    "elf": ["*.elf"],
    "map": ["*.map"],
    "build_log": ["build.log"],
    "serial_log": ["serial.log"],
    "fault_registers": ["fault*.txt"],
    "kconfig": ["prj.conf", ".config", "sdkconfig", "autoconf.h"],
    "dts": ["zephyr.dts", "*.dts"],
    "scope_trace": ["scope*.csv", "scope*.txt"],
    "logic_trace": ["logic*.csv", "logic*.txt", "*.sr"],
    "dmesg": ["dmesg.log"],
    "boot_log": ["boot.log"],
    "dtb": ["*.dtb"],
}

REQUIRED_BY_PLATFORM = {
    "zephyr": ["build_log", "dts", "kconfig"],
    "esp-idf": ["build_log", "serial_log", "kconfig"],
    "cortex-m": ["elf", "map", "fault_registers"],
    "embedded-linux": ["boot_log", "dmesg", "dts", "kconfig"],
    "freertos": ["elf", "map", "rtos_snapshot"],
    "tinyml": ["elf", "map"],
    "unknown": ["build_log", "serial_log"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect a reproducible embedded debug packet.")
    parser.add_argument("--project-root", required=True, help="Project root to scan.")
    parser.add_argument("--platform", default="auto", help="auto, zephyr, esp-idf, cortex-m, embedded-linux, freertos, tinyml.")
    parser.add_argument("--out", required=True, help="Output debug_packet.yaml/json path.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    artifacts = collect_artifacts(root)
    platform = detect_platform(root, artifacts) if args.platform == "auto" else args.platform
    packet = build_packet(root, platform, artifacts)
    write_packet(Path(args.out), packet)


def collect_artifacts(root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for key, patterns in ARTIFACT_PATTERNS.items():
        paths: list[str] = []
        for pattern in patterns:
            for path in root.rglob(pattern):
                if path.is_file():
                    paths.append(str(path.relative_to(root)))
        if paths:
            found[key] = sorted(set(paths))
    return found


def detect_platform(root: Path, artifacts: dict[str, list[str]]) -> str:
    files = {path.name for path in root.rglob("*") if path.is_file()}
    if "west.yml" in files or "prj.conf" in files or any(path.endswith("zephyr.dts") for path in artifacts.get("dts", [])):
        return "zephyr"
    if "sdkconfig" in files or "idf_component.yml" in files:
        return "esp-idf"
    if artifacts.get("dmesg") or artifacts.get("dtb") or "defconfig" in files:
        return "embedded-linux"
    if artifacts.get("fault_registers") or artifacts.get("elf") or artifacts.get("map"):
        return "cortex-m"
    return "unknown"


def build_packet(root: Path, platform: str, artifacts: dict[str, list[str]]) -> dict[str, object]:
    required = infer_required_evidence(root, platform, artifacts)
    missing = [name for name in required if not artifacts.get(name)]
    board = infer_board(root, artifacts)
    shield = infer_shield(root, artifacts)
    return {
        "case_id": root.name or "debug_case",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "platform": platform,
        "board": board,
        "shield": shield,
        "toolchain": infer_toolchain(root, artifacts),
        "build_system": infer_build_system(root),
        "artifacts": artifacts,
        "symptoms": [],
        "reproducibility": "unknown",
        "last_known_good": "unknown",
        "measurements": [],
        "constraints": [],
        "missing_evidence": missing,
        "analysis_status": "incomplete" if missing else "new",
    }


def infer_build_system(root: Path) -> str:
    names = {path.name for path in root.iterdir() if path.exists()}
    if "west.yml" in names:
        return "west"
    if "sdkconfig" in names or "idf_component.yml" in names:
        return "idf.py"
    if "platformio.ini" in names:
        return "platformio"
    if "CMakeLists.txt" in names:
        return "cmake"
    if "Makefile" in names:
        return "make"
    return "unknown"


def infer_required_evidence(root: Path, platform: str, artifacts: dict[str, list[str]]) -> list[str]:
    required = list(REQUIRED_BY_PLATFORM.get(platform, REQUIRED_BY_PLATFORM["unknown"]))
    logs = "\n".join(
        read_first(root, artifacts.get(name, []))
        for name in ("serial_log", "build_log", "dmesg", "boot_log")
    ).lower()
    if platform == "zephyr" and any(token in logs for token in ("i2c line", "nack", "timeout", "failed to initialize chip")):
        required.append("logic_trace")
        required.append("scope_trace")
    return sorted(set(required), key=required.index)


def infer_board(root: Path, artifacts: dict[str, list[str]]) -> str:
    config_text = read_first(root, artifacts.get("kconfig", []))
    for pattern in [
        r'^CONFIG_BOARD_TARGET="?([^"\n]+)"?',
        r'^CONFIG_BOARD="?([^"\n]+)"?',
    ]:
        if match := re.search(pattern, config_text, flags=re.MULTILINE):
            return match.group(1).strip()

    build_text = read_first(root, artifacts.get("build_log", []))
    for pattern in [
        r"(?:--board|-b)\s+([A-Za-z0-9_./-]+)",
        r"(?:BOARD|board)\s*[:=]\s*([A-Za-z0-9_./-]+)",
        r"Board:\s*([A-Za-z0-9_./-]+)",
    ]:
        if match := re.search(pattern, build_text):
            return match.group(1).strip()

    return "unknown"


def infer_shield(root: Path, artifacts: dict[str, list[str]]) -> str:
    build_text = read_first(root, artifacts.get("build_log", []))
    for pattern in [
        r"(?:--shield)\s+([A-Za-z0-9_./-]+)",
        r"(?:SHIELD|shield)\s*[:=]\s*([A-Za-z0-9_./-]+)",
    ]:
        if match := re.search(pattern, build_text):
            return match.group(1).strip()
    return "unknown"


def infer_toolchain(root: Path, artifacts: dict[str, list[str]]) -> str:
    config_text = read_first(root, artifacts.get("kconfig", []))
    if match := re.search(r'^CONFIG_TOOLCHAIN_VARIANT="?([^"\n]+)"?', config_text, flags=re.MULTILINE):
        return match.group(1).strip()

    build_text = read_first(root, artifacts.get("build_log", []))
    for pattern in [
        r"ZEPHYR_TOOLCHAIN_VARIANT\s*[:=]\s*([A-Za-z0-9_./-]+)",
        r"Found toolchain:\s*([A-Za-z0-9_./-]+)",
        r"toolchain\s*[:=]\s*([A-Za-z0-9_./-]+)",
    ]:
        if match := re.search(pattern, build_text, flags=re.IGNORECASE):
            return match.group(1).strip()
    return "unknown"


def read_first(root: Path, paths: list[str] | None) -> str:
    if not paths:
        return ""
    for rel_path in paths:
        path = root / rel_path
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
    return ""


def write_packet(path: Path, packet: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None:
        path.write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    else:
        path.write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
