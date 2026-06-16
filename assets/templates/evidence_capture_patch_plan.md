# Evidence Capture Patch Plan

Use this when the next debugging step is to add temporary instrumentation. Keep capture patches small, reversible, and tied to one missing evidence item.

## Guardrails

- Do not mix diagnostics with product fixes.
- Put capture code behind a build flag, debug Kconfig option, or clearly named compile-time guard.
- Record where the evidence is stored: RAM retention, serial log, file, trace buffer, or debugfs.
- Remove or disable capture code after the root cause is verified.
- Do not log secrets, customer payloads, private keys, or proprietary firmware blobs.

## Template Selection

| Need | Template |
|---|---|
| Cortex-M fault frame and SCB registers | `assets/templates/hardfault_capture.c` |
| FreeRTOS task and wait snapshot | `assets/templates/freertos_snapshot.c` |
| Zephyr thread snapshot | `assets/templates/zephyr_thread_snapshot.c` |
| Embedded Linux dynamic debug/ftrace | `assets/templates/linux_trace_probe.sh` |
| I2C sensor bring-up measurements | `assets/templates/i2c_sensor_bringup_measurement_plan.md` |
| Lab rail/current/waveform evidence | `assets/templates/lab_measurement_plan.md` |

## Capture Record

- Missing evidence:
- Template used:
- Build flag or patch guard:
- How to trigger:
- Expected observation if hypothesis is true:
- Expected observation if hypothesis is false:
- Removal plan:
