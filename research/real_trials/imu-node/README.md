# imu-node

Scenario: `zephyr_st_imu_sensor_node`

Board: `xiao_ble/nrf52840/sense`

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
