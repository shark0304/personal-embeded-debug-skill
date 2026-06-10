#!/usr/bin/env python3
"""Check host toolchain readiness for embedded-project-builder scenarios."""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SUPPORTED_SCENARIOS = {
    "zephyr_st_imu_sensor_node",
    "esp32s3_tinyml_motion_classifier",
    "stm32h7_dma_adc_logger",
}


def run_command(args: list[str], cwd: Path | None = None, timeout: int = 8) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": f"timeout after {timeout}s",
        }
    except Exception as exc:  # pragma: no cover - defensive host guard
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def first_line(text: str) -> str:
    return text.splitlines()[0].strip() if text else ""


def which_check(name: str, executable: str | None = None, required: bool = True) -> dict[str, Any]:
    exe = executable or name
    path = shutil.which(exe)
    result = {
        "name": name,
        "required": required,
        "ok": bool(path),
        "path": path,
        "detail": "found" if path else "missing from PATH",
    }
    if path:
        version_args = {
            "west": [path, "--version"],
            "cmake": [path, "--version"],
            "ninja": [path, "--version"],
            "dtc": [path, "--version"],
            "idf.py": [path, "--version"],
            "arm-none-eabi-gcc": [path, "--version"],
            "openocd": [path, "--version"],
            "pyocd": [path, "--version"],
        }.get(name)
        if version_args:
            cmd = run_command(version_args)
            result["version"] = first_line(cmd["stdout"] or cmd["stderr"])
            if not cmd["ok"] and name not in {"dtc", "openocd"}:
                result["detail"] = cmd["stderr"] or "version command failed"
    return result


def env_path_check(name: str, required: bool = True) -> dict[str, Any]:
    value = os.environ.get(name, "")
    exists = bool(value) and Path(value).exists()
    return {
        "name": name,
        "required": required,
        "ok": exists,
        "value": value,
        "detail": "path exists" if exists else ("not set" if not value else "path does not exist"),
    }


def python_check() -> dict[str, Any]:
    version = platform.python_version()
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 8)
    return {
        "name": "python",
        "required": True,
        "ok": ok,
        "version": version,
        "executable": sys.executable,
        "detail": "python >= 3.8" if ok else "python 3.8+ recommended",
    }


def existing_paths(patterns: list[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        expanded = os.path.expanduser(os.path.expandvars(pattern))
        for item in glob.glob(expanded):
            if Path(item).exists():
                paths.append(item)
    return sorted(set(paths))


def add_check(report: dict[str, Any], check: dict[str, Any]) -> None:
    report["checks"].append(check)
    if check.get("required") and not check.get("ok"):
        report["missing"].append(str(check.get("name", "unknown")))
    elif not check.get("required") and not check.get("ok"):
        report["warnings"].append(f"optional {check.get('name', 'unknown')} not found")


def zephyr_workspace_check() -> dict[str, Any]:
    west = shutil.which("west")
    if west:
        topdir = run_command([west, "topdir"])
        if topdir["ok"] and topdir["stdout"]:
            return {
                "name": "Zephyr workspace",
                "required": True,
                "ok": True,
                "path": topdir["stdout"],
                "detail": "west topdir succeeded",
            }
    candidates = existing_paths(["~/zephyrproject/zephyr", "~/zephyr", "$ZEPHYR_BASE"])
    return {
        "name": "Zephyr workspace",
        "required": True,
        "ok": bool(candidates),
        "candidates": candidates,
        "detail": "candidate workspace found" if candidates else "west workspace not found",
    }


def zephyr_sdk_check() -> dict[str, Any]:
    env = os.environ.get("ZEPHYR_SDK_INSTALL_DIR", "")
    candidates = existing_paths(
        [
            "$ZEPHYR_SDK_INSTALL_DIR",
            "~/zephyr-sdk*",
            "~/zephyrproject/zephyr-sdk*",
            "/opt/zephyr-sdk*",
            "/Applications/zephyr-sdk*",
        ]
    )
    return {
        "name": "Zephyr SDK",
        "required": True,
        "ok": bool(candidates),
        "env": env,
        "candidates": candidates,
        "detail": "Zephyr SDK path found" if candidates else "Zephyr SDK not found in common locations",
    }


def normalize_board(board: str) -> str:
    return board.replace("/", "_").replace("-", "_").lower()


def zephyr_board_support_check(board: str) -> dict[str, Any]:
    west = shutil.which("west")
    if west:
        boards = run_command([west, "boards"], timeout=12)
        if boards["ok"] and boards["stdout"]:
            board_lines = {line.strip() for line in boards["stdout"].splitlines() if line.strip()}
            return {
                "name": "board support",
                "required": True,
                "ok": board in board_lines or normalize_board(board) in {normalize_board(x) for x in board_lines},
                "detail": "checked via west boards",
            }

    search_roots = existing_paths(["$ZEPHYR_BASE/boards", "~/zephyrproject/zephyr/boards", "~/zephyr/boards"])
    token = board.split("/")[0].lower()
    matches: list[str] = []
    for root in search_roots:
        for path in Path(root).rglob("*"):
            if token in path.name.lower():
                matches.append(str(path))
                if len(matches) >= 10:
                    break
    return {
        "name": "board support",
        "required": True,
        "ok": bool(matches),
        "matches": matches,
        "detail": "rough directory match" if matches else "board support not verifiable",
    }


def esp_target_check() -> dict[str, Any]:
    idf = shutil.which("idf.py")
    if not idf:
        return {
            "name": "esp32s3 target",
            "required": True,
            "ok": False,
            "detail": "idf.py missing; target list not verifiable",
        }
    listed = run_command([idf, "--list-targets"], timeout=12)
    text = f"{listed['stdout']}\n{listed['stderr']}"
    return {
        "name": "esp32s3 target",
        "required": True,
        "ok": "esp32s3" in text,
        "detail": "checked via idf.py --list-targets" if listed["ok"] else "idf.py target query failed",
    }


def stm_optional_probe_check() -> dict[str, Any]:
    openocd = shutil.which("openocd")
    pyocd = shutil.which("pyocd")
    return {
        "name": "debug probe tool",
        "required": False,
        "ok": bool(openocd or pyocd),
        "openocd": openocd,
        "pyocd": pyocd,
        "detail": "openocd or pyocd found" if openocd or pyocd else "openocd/pyocd not found",
    }


def stmcubemx_check() -> dict[str, Any]:
    candidates = existing_paths(
        [
            "/Applications/STM32CubeMX.app",
            "~/Applications/STM32CubeMX.app",
            "/usr/local/bin/STM32CubeMX",
            "/Applications/STMicroelectronics/STM32CubeMX.app",
        ]
    )
    return {
        "name": "STM32CubeMX",
        "required": False,
        "ok": bool(candidates),
        "candidates": candidates,
        "detail": "optional GUI/codegen tool found" if candidates else "optional STM32CubeMX not found",
    }


def base_report(scenario: str, board: str) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "board": board,
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
        "ok": False,
        "checks": [],
        "missing": [],
        "warnings": [],
        "next_steps": [],
    }


def check_zephyr(report: dict[str, Any]) -> None:
    for item in [
        python_check(),
        which_check("west"),
        which_check("cmake"),
        which_check("ninja"),
        which_check("dtc"),
        env_path_check("ZEPHYR_BASE"),
        zephyr_workspace_check(),
        zephyr_sdk_check(),
        zephyr_board_support_check(report["board"]),
    ]:
        add_check(report, item)
    if report["missing"]:
        report["next_steps"].extend(
            [
                "Read references/toolchains/zephyr_toolchain_bootstrap_macos.md.",
                "Install west, cmake, ninja, dtc, and the Zephyr SDK.",
                "Initialize or enter a Zephyr workspace and verify `west boards` lists the target board.",
                "Do not mark scaffold build success until `west build` has produced a real build log.",
            ]
        )


def check_espidf(report: dict[str, Any]) -> None:
    for item in [
        python_check(),
        which_check("idf.py"),
        env_path_check("IDF_PATH"),
        which_check("cmake"),
        which_check("ninja"),
        esp_target_check(),
    ]:
        add_check(report, item)
    if report["missing"]:
        report["next_steps"].extend(
            [
                "Read references/toolchains/espidf_toolchain_bootstrap.md.",
                "Install ESP-IDF and export the environment so `idf.py` is in PATH.",
                "Run `idf.py --list-targets` and confirm esp32s3 is available.",
            ]
        )


def check_stm32(report: dict[str, Any]) -> None:
    for item in [
        python_check(),
        which_check("cmake"),
        which_check("ninja"),
        which_check("arm-none-eabi-gcc"),
        stm_optional_probe_check(),
        stmcubemx_check(),
    ]:
        add_check(report, item)
    if report["missing"]:
        report["next_steps"].extend(
            [
                "Read references/toolchains/stm32_toolchain_bootstrap.md.",
                "Install CMake, Ninja, and Arm GNU Toolchain.",
                "Install OpenOCD or pyOCD if flash/debug validation is required.",
            ]
        )


def render_human(report: dict[str, Any]) -> str:
    lines = [
        f"scenario: {report['scenario']}",
        f"board: {report['board']}",
        f"ok: {str(report['ok']).lower()}",
        "checks:",
    ]
    for check in report["checks"]:
        status = "ok" if check.get("ok") else "missing" if check.get("required") else "warning"
        lines.append(f"- {check.get('name')}: {status} ({check.get('detail', '')})")
    if report["missing"]:
        lines.append("missing: " + ", ".join(report["missing"]))
    if report["warnings"]:
        lines.append("warnings:")
        lines.extend(f"- {item}" for item in report["warnings"])
    if report["next_steps"]:
        lines.append("next_steps:")
        lines.extend(f"- {item}" for item in report["next_steps"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(SUPPORTED_SCENARIOS))
    parser.add_argument("--board", required=True)
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--out", help="optional path to write JSON report")
    args = parser.parse_args()

    report = base_report(args.scenario, args.board)
    if args.scenario == "zephyr_st_imu_sensor_node":
        check_zephyr(report)
    elif args.scenario == "esp32s3_tinyml_motion_classifier":
        check_espidf(report)
    elif args.scenario == "stm32h7_dma_adc_logger":
        check_stm32(report)

    report["missing"] = sorted(set(report["missing"]))
    report["warnings"] = sorted(set(report["warnings"]))
    report["ok"] = not report["missing"]

    if args.out:
        try:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError as exc:
            report["warnings"].append(f"could not write --out {args.out}: {exc}")
            report["warnings"] = sorted(set(report["warnings"]))

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text if args.json else render_human(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
