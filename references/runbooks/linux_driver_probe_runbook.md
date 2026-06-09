# Linux Driver Probe Runbook

## Trigger symptoms

- Driver probe never called, probe returns error, probe deferred forever, device missing from sysfs.

## Minimum evidence

- Full dmesg, kernel version, booted DTB/DTS dump, node path, compatible, status, driver match table, `.config`, module state.

## Fast triage

1. Run `linux_log_triage.py`.
2. Run `dts_probe_check.py` on booted DTS.
3. Run `kconfig_check.py` for driver and supplier config.
4. Inspect `/sys/kernel/debug/devices_deferred`, clk, regulator, pinctrl summaries.

## High-probability root causes

- Wrong DTB, disabled node, compatible mismatch, parent bus disabled, missing supplier, driver not built/loaded.

## Scripts to run

- `scripts/linux_log_triage.py`
- `scripts/dts_probe_check.py`
- `scripts/kconfig_check.py`
- `scripts/boot_log_timeline.py`

## Manual experiments

- Dump booted DTB, enable dynamic debug for driver/subsystem, use ftrace only after static DT checks.

## Fix patterns

- Fix DT node/status/compatible/resources, enable driver/supplier config, correct bootloader DTB selection.

## Regression tests

- Golden packet with dmesg, booted DTS, config, expected missing supplier or match failure.

## Do-not-guess rules

- Do not patch probe before proving driver matching and resource availability.
- Do not judge Zephyr/Linux device state without DTS/config evidence.
