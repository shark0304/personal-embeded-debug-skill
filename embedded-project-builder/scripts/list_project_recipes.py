#!/usr/bin/env python3
"""List embedded-project-builder project recipes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent

RECIPES = [
    {
        "id": "zephyr_st_imu_sensor_node",
        "project": "Zephyr ST IMU sensor node",
        "platform": "Zephyr / Nordic nRF52840",
        "fault_handoff": "Zephyr sensor bring-up, DTS/Kconfig, I2C logic trace",
        "recipe": "references/project_recipes/zephyr_st_imu_sensor_node.md",
    },
    {
        "id": "stm32h7_dma_adc_logger",
        "project": "STM32H7 DMA ADC logger",
        "platform": "STM32H7 / Cortex-M7",
        "fault_handoff": "DMA/cache coherency, Cortex-M hardfault, RTOS/IRQ budget",
        "recipe": "references/project_recipes/stm32h7_dma_adc_logger.md",
    },
    {
        "id": "esp32s3_tinyml_motion_classifier",
        "project": "ESP32-S3 TinyML motion classifier",
        "platform": "ESP-IDF / ESP32-S3",
        "fault_handoff": "ESP-IDF panic, TinyML memory/latency, watchdog",
        "recipe": "references/project_recipes/esp32s3_tinyml_motion_classifier.md",
    },
    {
        "id": "rk3588_linux_i2c_driver_probe",
        "project": "RK3588 Linux I2C driver probe",
        "platform": "Embedded Linux / RK3588",
        "fault_handoff": "Linux driver probe, DTB mismatch, deferred probe",
        "recipe": "references/project_recipes/rk3588_linux_i2c_driver_probe.md",
    },
    {
        "id": "ti_c2000_adc_pwm_control_loop",
        "project": "TI C2000 ADC/PWM control loop",
        "platform": "TI C2000",
        "fault_handoff": "Register review, timing budget, field diagnostics",
        "recipe": "references/project_recipes/ti_c2000_adc_pwm_control_loop.md",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="output recipe list as JSON")
    args = parser.parse_args()

    rows = []
    for item in RECIPES:
        row = dict(item)
        row["recipe_path"] = str(SKILL_ROOT / item["recipe"])
        rows.append(row)

    if args.json:
        print(json.dumps({"recipes": rows, "count": len(rows)}, indent=2))
        return 0

    print("Available embedded project recipes:")
    for row in rows:
        print(f"- {row['id']}: {row['project']}")
        print(f"  platform: {row['platform']}")
        print(f"  handoff: {row['fault_handoff']}")
        print(f"  recipe: {row['recipe']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
