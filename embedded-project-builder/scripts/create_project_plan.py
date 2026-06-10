#!/usr/bin/env python3
"""Create project planning documents from embedded-project-builder templates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"

SCENARIOS = {
    "zephyr_st_imu_sensor_node": {
        "project_goal": "Bring up a Zephyr ST IMU sensor node with stable polling first, then optional trigger/FIFO support.",
        "board": "xiao_ble/nrf52840/sense",
        "peripheral": "ST LSM6DSL/LSM6DS3 IMU",
        "interface": "I2C",
        "debug_probe": "CMSIS-DAP, J-Link, or board bootloader",
        "toolchain": "Zephyr SDK + west",
        "build_system": "west/CMake/Ninja",
        "flash_debug_path": "west flash and serial console",
    },
    "stm32h7_dma_adc_logger": {
        "project_goal": "Acquire ADC samples on STM32H7 using timer-triggered DMA with cache-safe buffers and data-integrity checks.",
        "board": "STM32H7 Nucleo or custom STM32H7 board",
        "peripheral": "ADC + DMA + timer trigger",
        "interface": "memory DMA",
        "debug_probe": "ST-LINK or J-Link",
        "toolchain": "STM32CubeIDE/CMake + GCC",
        "build_system": "CMake, Make, or STM32CubeIDE",
        "flash_debug_path": "ST-LINK flash and SWD debug",
    },
    "esp32s3_tinyml_motion_classifier": {
        "project_goal": "Run a bounded-latency TinyML motion classifier on ESP32-S3 with reset, heap, stack, and watchdog evidence.",
        "board": "ESP32-S3 devkit",
        "peripheral": "IMU or synthetic motion input",
        "interface": "I2C/SPI sensor input plus TFLite Micro",
        "debug_probe": "USB serial/JTAG",
        "toolchain": "ESP-IDF",
        "build_system": "idf.py/CMake/Ninja",
        "flash_debug_path": "idf.py flash monitor",
    },
    "rk3588_linux_i2c_driver_probe": {
        "project_goal": "Bring up an RK3588 Linux I2C client driver with matched DTB, binding, probe, and defer evidence.",
        "board": "RK3588 SBC or custom carrier",
        "peripheral": "I2C sensor, PMIC, codec, or GPIO expander",
        "interface": "Linux I2C client driver",
        "debug_probe": "serial console, SSH, dmesg, ftrace",
        "toolchain": "Linux kernel BSP or mainline-oriented tree",
        "build_system": "kernel make, dtc, module build",
        "flash_debug_path": "boot image/DTB/module deployment and serial console",
    },
    "ti_c2000_adc_pwm_control_loop": {
        "project_goal": "Build a deterministic TI C2000 ADC/PWM control loop with timing, trip-zone, and register evidence.",
        "board": "TI C2000 F28P55x LaunchPad/controlCARD",
        "peripheral": "ePWM + ADC + CMPSS/trip zone",
        "interface": "register-level peripheral control",
        "debug_probe": "XDS debug probe",
        "toolchain": "Code Composer Studio + C2000Ware",
        "build_system": "CCS project or CMake where supported",
        "flash_debug_path": "CCS flash/debug and oscilloscope timing checks",
    },
}

OUTPUTS = {
    "project_plan.md": "project_plan.md",
    "datasheet_reading_note.md": "datasheet_reading_note.md",
    "driver_bringup_note.md": "driver_bringup_note.md",
    "validation_plan.md": "validation_plan.md",
}


def render_template(template_name: str, values: dict[str, str]) -> str:
    template = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    result = template
    for key, value in values.items():
        result = result.replace("{{" + key + "}}", value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS), help="project scenario id")
    parser.add_argument("--project-name", required=True, help="name used in generated document titles")
    parser.add_argument("--board", help="override target board")
    parser.add_argument("--peripheral", help="override sensor/peripheral")
    parser.add_argument("--toolchain", help="override toolchain")
    parser.add_argument("--out-dir", required=True, help="directory for generated planning documents")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing output files")
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()

    values = dict(SCENARIOS[args.scenario])
    values["project_name"] = args.project_name
    if args.board:
        values["board"] = args.board
    if args.peripheral:
        values["peripheral"] = args.peripheral
    if args.toolchain:
        values["toolchain"] = args.toolchain

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = []
    skipped = []
    for filename, template_name in OUTPUTS.items():
        out_path = out_dir / filename
        if out_path.exists() and not args.overwrite:
            skipped.append(str(out_path))
            continue
        out_path.write_text(render_template(template_name, values), encoding="utf-8")
        written.append(str(out_path))

    summary = {
        "scenario": args.scenario,
        "project_name": args.project_name,
        "out_dir": str(out_dir),
        "written": written,
        "skipped": skipped,
        "ok": not skipped,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"scenario: {args.scenario}")
        print(f"out_dir: {out_dir}")
        for path in written:
            print(f"wrote: {path}")
        for path in skipped:
            print(f"skipped existing file: {path}")
        if skipped:
            print("rerun with --overwrite to replace existing files")
    return 0 if not skipped else 2


if __name__ == "__main__":
    raise SystemExit(main())
