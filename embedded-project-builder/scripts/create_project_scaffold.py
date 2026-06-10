#!/usr/bin/env python3
"""Create an embedded project scaffold plus planning documents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from create_project_plan import OUTPUTS, SCENARIOS, render_template  # noqa: E402


SUPPORTED_SCENARIOS = {
    "zephyr_st_imu_sensor_node",
    "stm32h7_dma_adc_logger",
    "esp32s3_tinyml_motion_classifier",
}


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip()).strip("_")
    return cleaned.lower() or "embedded_project"


def write_file(path: Path, content: str, overwrite: bool, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        summary["skipped"].append(str(path))
        return
    path.write_text(content, encoding="utf-8")
    summary["written"].append(str(path))


def create_dirs(out_dir: Path, summary: dict) -> None:
    for rel in ["app", "debug"]:
        path = out_dir / rel
        path.mkdir(parents=True, exist_ok=True)
        summary["directories"].append(str(path))


def base_readme(project_name: str, scenario: str, board: str) -> str:
    return f"""# {project_name}

Scenario: `{scenario}`

Board: `{board}`

This scaffold is intentionally minimal. It provides the first build/run
surface, planning documents, and a `debug/` handoff folder. Fill in board
revision, SDK version, schematic notes, and measured evidence as bring-up
progresses.

## Build

Use the command expected by the selected SDK. Examples are placeholders:

```bash
# Zephyr
west build -b <board> app

# ESP-IDF
idf.py -C app build
```

## Flash

```bash
# Zephyr
west flash

# ESP-IDF
idf.py -C app flash monitor
```

## Runtime Validation

Capture the first serial boot log, device identity/probe result, reset reason,
and any bus-level trace required by `validation_plan.md`.

## Enter embedded-debug

When build, flash, probe, runtime, latency, memory, DMA/cache, or reset evidence
does not match the plan, stop editing multiple variables and switch to
`embedded-debug`. Put build logs, serial logs, config files, traces, and notes in
`debug/`, then create a debug packet for hypothesis ranking.
"""


def debug_readme(scenario: str) -> str:
    return f"""# Debug Evidence

Scenario: `{scenario}`

Place failure evidence here before handing off to `embedded-debug`:

- build.log
- flash.log
- serial.log
- config files
- DTS/overlay or sdkconfig
- ELF/map when relevant
- logic analyzer or scope exports
- notes about last-known-good behavior
"""


def planning_docs(out_dir: Path, values: dict[str, str], overwrite: bool, summary: dict) -> None:
    for filename, template_name in OUTPUTS.items():
        rendered = render_template(template_name, values)
        write_file(out_dir / filename, rendered, overwrite, summary)


def zephyr_overlay(board: str) -> tuple[str, str]:
    if board == "xiao_ble/nrf52840/sense":
        return (
            "xiao_ble_nrf52840_sense.overlay",
            """/*
 * Zephyr ST IMU overlay template.
 *
 * TODO: Confirm the real sensor bus, address strap, IRQ pin, and board
 * revision before treating this as hardware truth.
 */

/ {
    aliases {
        imu0 = &lsm6dsl;
    };
};

&i2c0 {
    status = "okay";

    lsm6dsl: lsm6dsl@6a {
        compatible = "st,lsm6dsl";
        reg = <0x6a>;
        status = "okay";
        irq-gpios = <&gpio0 11 GPIO_ACTIVE_HIGH>;
    };
};
""",
        )
    return (
        "generic_board.overlay",
        f"""/*
 * Generic Zephyr IMU overlay TODO for board `{board}`.
 *
 * Replace &i2c0, reg, compatible, and irq-gpios with schematic and datasheet
 * evidence before expecting the sample to probe successfully.
 */

/ {{
    aliases {{
        imu0 = &imu_sensor;
    }};
}};

&i2c0 {{
    status = "okay";

    imu_sensor: imu@6a {{
        compatible = "st,lsm6dsl";
        reg = <0x6a>;
        status = "okay";
        /* irq-gpios = <&gpioX PIN GPIO_ACTIVE_HIGH>; */
    }};
}};
""",
    )


def scaffold_zephyr(out_dir: Path, values: dict[str, str], overwrite: bool, summary: dict) -> None:
    project_slug = slug(values["project_name"])
    write_file(
        out_dir / "app" / "CMakeLists.txt",
        f"""cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{{ZEPHYR_BASE}})
project({project_slug})

target_sources(app PRIVATE src/main.c)
""",
        overwrite,
        summary,
    )
    write_file(
        out_dir / "app" / "prj.conf",
        """CONFIG_SENSOR=y
CONFIG_I2C=y
CONFIG_GPIO=y
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3
CONFIG_MAIN_STACK_SIZE=2048
""",
        overwrite,
        summary,
    )
    overlay_name, overlay_text = zephyr_overlay(values["board"])
    write_file(out_dir / "app" / "boards" / overlay_name, overlay_text, overwrite, summary)
    write_file(
        out_dir / "app" / "src" / "main.c",
        """#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(imu_node, LOG_LEVEL_INF);

#if DT_HAS_COMPAT_STATUS_OKAY(st_lsm6dsl)
#define IMU_NODE DT_COMPAT_GET_ANY_STATUS_OKAY(st_lsm6dsl)
#elif DT_NODE_HAS_STATUS(DT_ALIAS(imu0), okay)
#define IMU_NODE DT_ALIAS(imu0)
#else
#error "No enabled IMU node found. Add an imu0 alias or st,lsm6dsl node in the board overlay."
#endif

int main(void)
{
    const struct device *imu = DEVICE_DT_GET(IMU_NODE);

    LOG_INF("IMU scaffold start");
    if (!device_is_ready(imu)) {
        LOG_ERR("IMU device is not ready: %s", imu->name);
        return 0;
    }

    LOG_INF("IMU device ready: %s", imu->name);

    while (1) {
        struct sensor_value accel[3];
        int rc = sensor_sample_fetch(imu);

        if (rc == 0) {
            rc = sensor_channel_get(imu, SENSOR_CHAN_ACCEL_XYZ, accel);
        }

        if (rc == 0) {
            LOG_INF("accel x=%d.%06d y=%d.%06d z=%d.%06d",
                    accel[0].val1, accel[0].val2,
                    accel[1].val1, accel[1].val2,
                    accel[2].val1, accel[2].val2);
        } else {
            LOG_ERR("sensor sample failed: %d", rc);
        }

        k_sleep(K_SECONDS(1));
    }
}
""",
        overwrite,
        summary,
    )


def scaffold_stm32(out_dir: Path, values: dict[str, str], overwrite: bool, summary: dict) -> None:
    (out_dir / "app" / "Core").mkdir(parents=True, exist_ok=True)
    (out_dir / "app" / "Drivers").mkdir(parents=True, exist_ok=True)
    summary["directories"].extend(
        [str(out_dir / "app" / "Core"), str(out_dir / "app" / "Drivers")]
    )
    write_file(
        out_dir / "app" / "README.md",
        """# STM32H7 DMA ADC App Placeholder

This scaffold intentionally does not generate a full HAL or CubeMX project.
Start from the exact vendor example for the selected STM32H7 part, then copy
the DMA/cache checklist into the project review.

Required first evidence:

- polling ADC read works
- timer trigger is confirmed
- DMA callbacks fire
- buffer address, alignment, and linker section are recorded
- cache policy is documented before high-rate validation
""",
        overwrite,
        summary,
    )
    write_file(out_dir / "app" / "Core" / ".gitkeep", "", overwrite, summary)
    write_file(out_dir / "app" / "Drivers" / ".gitkeep", "", overwrite, summary)
    write_file(
        out_dir / "app" / "dma_cache_checklist.md",
        """# DMA / Cache Bring-up Checklist

## Buffer Alignment

- TODO: Align DMA buffers to cache line size.
- TODO: Record buffer address, size, and linker section from the map file.
- TODO: Verify DMA can access the selected SRAM region.

## Cache Maintenance

- TODO: Invalidate RX buffers after DMA writes and before CPU reads.
- TODO: Clean TX buffers before DMA reads from memory.
- TODO: Use full cache-line ranges; avoid partial-line corruption.

## MPU Non-cacheable Option

- TODO: Consider an MPU non-cacheable region for DMA buffers.
- TODO: Document tradeoff against explicit cache maintenance.

## Validation

- Known waveform produces expected sample count and amplitude.
- No repeated stale block after D-cache is enabled.
- DMA error, overrun, half-transfer, and transfer-complete counters are logged.

## embedded-debug Handoff

If data corruption, stale samples, or intermittent DMA failures appear, collect
build log, map file, buffer addresses, linker script, cache policy, and sample
logs, then use the `embedded-debug` DMA/cache coherency runbook.
""",
        overwrite,
        summary,
    )


def scaffold_esp32(out_dir: Path, values: dict[str, str], overwrite: bool, summary: dict) -> None:
    project_slug = slug(values["project_name"])
    write_file(
        out_dir / "app" / "CMakeLists.txt",
        f"""cmake_minimum_required(VERSION 3.16)
include($ENV{{IDF_PATH}}/tools/cmake/project.cmake)
project({project_slug})
""",
        overwrite,
        summary,
    )
    write_file(
        out_dir / "app" / "main" / "CMakeLists.txt",
        """idf_component_register(SRCS "main.c" INCLUDE_DIRS ".")
""",
        overwrite,
        summary,
    )
    write_file(
        out_dir / "app" / "main" / "main.c",
        """#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "tinyml_scaffold";

void app_main(void)
{
    ESP_LOGI(TAG, "TinyML scaffold start");
    ESP_LOGI(TAG, "free heap=%u min_free_heap=%u",
             (unsigned)esp_get_free_heap_size(),
             (unsigned)esp_get_minimum_free_heap_size());

    while (1) {
        int64_t start_us = esp_timer_get_time();

        /* TODO: sample sensor, run feature extraction, then invoke the model. */

        int64_t elapsed_us = esp_timer_get_time() - start_us;
        ESP_LOGI(TAG, "inference_placeholder_us=%lld free_heap=%u",
                 (long long)elapsed_us,
                 (unsigned)esp_get_free_heap_size());
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
""",
        overwrite,
        summary,
    )
    write_file(
        out_dir / "app" / "sdkconfig.defaults",
        """CONFIG_LOG_DEFAULT_LEVEL_INFO=y
CONFIG_ESP_TASK_WDT=y
CONFIG_ESP_TASK_WDT_TIMEOUT_S=5
CONFIG_FREERTOS_WATCHPOINT_END_OF_STACK=y
""",
        overwrite,
        summary,
    )
    write_file(
        out_dir / "app" / "tinyml_budget.md",
        """# TinyML Memory / Latency Budget

## Memory Budget

| Item | Budget | Observed | Evidence |
| --- | --- | --- | --- |
| tensor arena | TBD | TBD | serial log |
| feature buffer | TBD | TBD | code review |
| free heap after init | TBD | TBD | serial log |
| task stack watermark | TBD | TBD | runtime log |

## Latency Budget

- Sampling period:
- Feature extraction budget:
- Inference budget:
- Post-processing budget:
- Worst-case observed latency:

## Watchdog Checklist

- Long inference does not starve watchdog feeding.
- Sensor sampling and model execution are split or bounded.
- Serial logging does not dominate timing.

## embedded-debug Handoff

If watchdog reset, Guru Meditation, allocation failure, arena overflow, or
latency miss appears, collect serial log, reset reason, heap/stack metrics, and
model budget, then use the `embedded-debug` TinyML latency/memory runbook.
""",
        overwrite,
        summary,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True, choices=sorted(SUPPORTED_SCENARIOS))
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    values = dict(SCENARIOS[args.scenario])
    values["project_name"] = args.project_name
    values["board"] = args.board

    summary = {
        "scenario": args.scenario,
        "project_name": args.project_name,
        "board": args.board,
        "out_dir": str(out_dir),
        "written": [],
        "skipped": [],
        "directories": [],
    }

    create_dirs(out_dir, summary)
    write_file(out_dir / "README.md", base_readme(args.project_name, args.scenario, args.board), args.overwrite, summary)
    write_file(out_dir / "debug" / "README.md", debug_readme(args.scenario), args.overwrite, summary)
    planning_docs(out_dir, values, args.overwrite, summary)

    if args.scenario == "zephyr_st_imu_sensor_node":
        scaffold_zephyr(out_dir, values, args.overwrite, summary)
    elif args.scenario == "stm32h7_dma_adc_logger":
        scaffold_stm32(out_dir, values, args.overwrite, summary)
    elif args.scenario == "esp32s3_tinyml_motion_classifier":
        scaffold_esp32(out_dir, values, args.overwrite, summary)

    summary["ok"] = not summary["skipped"]

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"scenario: {args.scenario}")
        print(f"out_dir: {out_dir}")
        for path in summary["written"]:
            print(f"wrote: {path}")
        for path in summary["skipped"]:
            print(f"skipped existing file: {path}")
        if summary["skipped"]:
            print("rerun with --overwrite to replace existing files")
    return 0 if summary["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
