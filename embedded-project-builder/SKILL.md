---
name: embedded-project-builder
description: Plan and scaffold embedded learning or product projects from zero to validation. Use for Zephyr sensor nodes, STM32 DMA acquisition, ESP32 TinyML demos, RK3588 Linux driver/NPU demos, TI C2000 control demos, datasheet reading plans, driver bring-up notes, validation plans, and handoff to embedded-debug when failures appear.
metadata:
  short-description: Plan embedded projects from idea to validation
---

# Embedded Project Builder

Use this skill to organize embedded work before debugging starts. It creates project routes, minimal scaffolds, datasheet notes, bring-up plans, validation criteria, and explicit handoff conditions for `$embedded-debug`.

## Operating Model

1. Identify the target scenario, board, peripheral/sensor, toolchain, and user experience level.
2. If the user asks for a learning route or planning docs, run `create_project_plan.py`.
3. If the user asks to "搭项目骨架", "create scaffold", "start a project", or needs files to begin coding, run `create_project_scaffold.py`.
4. If build is blocked by missing tools or SDK/workspace setup, run `check_toolchain_env.py` before editing scaffold code.
5. Generate or update:
   - `project_plan.md`
   - `datasheet_reading_note.md`
   - `driver_bringup_note.md`
   - `validation_plan.md`
6. Keep plans practical: milestone, evidence, test command, expected observation, exit criteria.
7. When build/runtime validation fails after the toolchain is ready, stop guessing and hand the evidence to `$embedded-debug`.

## Scenario Routing

- **Zephyr sensor node**: use `references/project_recipes/zephyr_st_imu_sensor_node.md`.
- **STM32 DMA data acquisition**: use `references/project_recipes/stm32h7_dma_adc_logger.md`.
- **ESP32 TinyML demo**: use `references/project_recipes/esp32s3_tinyml_motion_classifier.md`.
- **RK3588 Linux driver/NPU demo**: use `references/project_recipes/rk3588_linux_i2c_driver_probe.md`.
- **TI C2000 motor/control peripheral demo**: use `references/project_recipes/ti_c2000_adc_pwm_control_loop.md`.

If the user goal does not match a recipe, compose a custom route from:

- `references/learning_paths/embedded_project_learning_path.md`
- `references/datasheet_reading/datasheet_reading_strategy.md`
- `references/driver_bringup/driver_bringup_strategy.md`
- `references/board_porting/board_porting_checklist.md`
- `references/testing_validation/testing_validation_strategy.md`
- `references/deployment/deployment_checklist.md`

## Scripted Workflow

List built-in scenarios:

```bash
python embedded-project-builder/scripts/list_project_recipes.py
```

Create the four planning documents:

```bash
python embedded-project-builder/scripts/create_project_plan.py \
  --scenario zephyr_st_imu_sensor_node \
  --project-name imu-node \
  --board xiao_ble/nrf52840/sense \
  --out-dir ./imu-node-plan
```

Create a scaffold plus planning docs:

```bash
python embedded-project-builder/scripts/create_project_scaffold.py \
  --scenario zephyr_st_imu_sensor_node \
  --project-name imu-node \
  --board xiao_ble/nrf52840/sense \
  --out-dir ./imu-node
```

Check toolchain readiness:

```bash
python embedded-project-builder/scripts/check_toolchain_env.py \
  --scenario zephyr_st_imu_sensor_node \
  --board xiao_ble/nrf52840/sense \
  --json
```

Validate generated planning docs:

```bash
python embedded-project-builder/scripts/validate_project_plan.py --project-dir ./imu-node-plan
python embedded-project-builder/scripts/validate_project_scaffold.py --project-dir ./imu-node
```

## Required Output Contract

For each project plan, include:

- clear project goal, board, sensor/peripheral, and toolchain
- milestones with validation evidence
- risks that can block bring-up
- validation criteria for build, flash, serial log, bus, timing, power, and regression
- debug handoff condition that names the `$embedded-debug` runbook or analyzer

## Handoff To Embedded Debug

Read toolchain bootstrap references before declaring scaffold failure:

- Zephyr missing toolchain: `references/toolchains/zephyr_toolchain_bootstrap_macos.md`
- ESP-IDF missing toolchain: `references/toolchains/espidf_toolchain_bootstrap.md`
- STM32 missing toolchain: `references/toolchains/stm32_toolchain_bootstrap.md`

Use `$embedded-debug` when:

- build fails: collect build log and toolchain details
- Zephyr sensor init fails: use Zephyr sensor bring-up and DTS/Kconfig runbooks
- HardFault or reset occurs: use Cortex-M hardfault or field diagnostics runbooks
- Linux driver probe fails: use Linux driver probe runbook
- DMA data is corrupted: use DMA/cache coherency runbook
- TinyML latency or memory fails: use TinyML latency/memory runbook

Do not convert a workaround into a root cause. The handoff should preserve observed evidence, missing evidence, and the smallest reproduction.
