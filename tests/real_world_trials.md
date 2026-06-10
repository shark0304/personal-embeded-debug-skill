# Real World Trials

This file tracks embedded-debug v3.2 trial runs. A trial can be real hardware,
sanitized from a real failure shape, or simulated. Do not treat sanitized trials
as hardware-confirmed validation.

| trial_id | project | platform | fault_domain | debug_packet_generated | missing_evidence | first_hypothesis | verified_root_cause | report_score | golden_packet_added | time_saved_estimate | notes |
|---|---|---|---|---|---|---|---|---:|---|---|---|
| zephyr_st_imu_hardware_followup | Zephyr `samples/sensor/lsm6dsl` on XIAO BLE Sense follow-up | Zephyr | ST IMU I2C bring-up | yes, `tests/trials/zephyr_st_imu_hardware_followup/debug_packet.yaml` | `logic_trace`, `scope_trace` | First I2C transaction reaches IMU before bus or power rail stability is proven | No; sanitized follow-up still lacks hardware waveform evidence | 100 | no | 30-60 min by excluding DTS/Kconfig as primary branch | Keep as trial only until real analyzer/scope captures exist. |
| stm32h7_dma_cache_corruption | STM32H7 Ethernet RX DMA stress packet | Cortex-M | DMA/cache coherency | yes, `tests/trials/stm32h7_dma_cache_corruption/debug_packet.yaml` | `elf` | RX buffers in cacheable memory consumed without aligned invalidate after DMA completion | Yes; corruption disappears after invalidate-on-RX and alignment experiment | 100 | yes | 1-2 h by jumping directly to cache-line span and region checks | Sanitized real-style lab packet; promoted because before/after evidence is present. |
| freertos_priority_inversion | Generic Cortex-M FreeRTOS SPI mutex snapshot | FreeRTOS | Priority inversion | yes, `tests/trials/freertos_priority_inversion/debug_packet.yaml` | `trace_timeline` | Low priority logger holds SPI mutex while high priority control task blocks and medium task runs | Yes; deadline misses disappear after shortening logger SPI critical section | 100 | yes | 45-90 min by turning a timing symptom into a wait graph | Sanitized RTOS snapshot; promoted because wait graph evidence is deterministic. |
| esp32s3_guru_meditation | ESP32-S3 Wi-Fi reconnect panic packet | ESP-IDF | Guru Meditation / LoadProhibited | yes, `tests/trials/esp32s3_guru_meditation/debug_packet.yaml` | `elf`, `map`, full symbolized panic | Null or stale reconnect callback context after Wi-Fi reconnect | No; missing ELF prevents PC/backtrace confirmation | 100 | no | 20-40 min by preventing premature callback root-cause claim | Keep as trial only until matching ELF and symbolized backtrace are preserved. |
| rk3588_linux_probe_defer | RK3588 camera sensor probe-defer packet | Embedded Linux | Driver probe / regulator DT | yes, `tests/trials/rk3588_linux_probe_defer/debug_packet.yaml` | `dtb` | Camera sensor analog supply is missing or unresolved in board DTS | Yes; adding regulator-fixed node and `avdd-supply` phandle makes probe succeed in sanitized trial | 100 | yes | 1-2 h by routing from dmesg defer loop to DT regulator evidence | Sanitized BSP bring-up packet; promoted with DTB still listed as residual evidence gap. |

## Trial output contract

Each trial directory contains:

- `debug_packet.yaml`
- `analysis.json`
- `debug_report.md`
- `score.json`
- Minimal artifacts needed to reproduce the report, such as logs, DTS/config
  excerpts, RTOS snapshots, or DMA snapshots.

## Promotion rule

A trial is promoted to a golden packet only when the packet has a stable symptom,
ranked hypotheses, a report score of at least 80, and either a verified root cause
or a deliberately preserved regression branch. Trials missing decisive hardware
evidence remain trial-only.
