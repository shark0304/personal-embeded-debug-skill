# Advanced Embedded Debug Workbench

Repository: `personal-embeded-debug-skill`

Evidence-first Codex skill for embedded engineers debugging Cortex-M, RTOS,
Zephyr sensors, ESP-IDF, embedded Linux bring-up, DMA/cache coherency, boot/OTA,
low power, datasheets/registers, and TinyML deployment.

The skill is designed as a reproducible debugging workbench:

- Collect a `debug_packet.yaml` before making strong root-cause claims.
- Rank hypotheses with evidence for, evidence against, missing evidence, and a
  verification experiment.
- Generate scored debug reports.
- Preserve resolved or representative cases as golden packets for regression.
- Route Zephyr, ESP-IDF, Linux, Cortex-M, RTOS, DMA/cache, field diagnostics,
  MCUboot/OTA, and TinyML issues to focused runbooks and scripts.

## v3.1 focus

v3.1 adds stronger Zephyr sensor bring-up support:

- Zephyr sensor/I2C/IMU runbook.
- I2C initialization failure analyzer for serial log + DTS + Kconfig evidence.
- I2C logic trace analyzer for decoded or raw CSV exports.
- Measurement plan template for SDA/SCL, sensor rail, enable/reset, and log
  correlation.
- Golden packet extensions for the XIAO BLE Sense + LSM6DSL/LSM6DS3 bring-up
  case.

## Quick start

Collect a project packet:

```bash
python scripts/collect/collect_debug_packet.py --project-root . --platform auto --out debug_packet.yaml
```

Generate a report:

```bash
python scripts/reports/generate_debug_report.py --packet debug_packet.yaml --out debug_report.md
python scripts/verify/score_debug_report.py --report debug_report.md
```

Analyze a Zephyr I2C sensor init failure:

```bash
python scripts/analyze/analyze_i2c_init_failure.py \
  --serial-log serial.log \
  --dts zephyr.dts \
  --config .config
```

Analyze a logic analyzer CSV:

```bash
python scripts/analyze/analyze_i2c_logic_trace.py --trace logic_trace.csv
```

## Repository layout

- `SKILL.md`: lightweight Codex entry and routing rules.
- `agents/openai.yaml`: UI-facing skill metadata.
- `references/runbooks/`: focused diagnostic procedures.
- `references/failure_patterns/`: structured failure pattern catalogs.
- `scripts/`: deterministic collectors, analyzers, report generators, CI/HIL
  adapters, and verification tools.
- `profiles/`: board, project, packet, and measurement schemas.
- `assets/templates/`: capture plans and instrumentation templates.
- `tests/golden_packets/`: regression-ready debug packets and expected reports.

## Validation

Run from the skill root:

```bash
python scripts/verify/run_skill_regression.py
python scripts/verify/score_debug_report.py --report tests/golden_packets/zephyr_st_imu_bringup_real/expected_report.md
python scripts/smoke_test_tools.py
python scripts/validate_evaluation_scenarios.py
```

The current v3.1 baseline has 11 golden packets, 24 smoke-tested tools, and 43
evaluation scenarios.

## Boundary

This skill does not replace hardware measurement. It is designed to prevent
guessing by making missing ELF/map, DTS/Kconfig, serial logs, waveform captures,
and board/toolchain context explicit before conclusions are promoted.
