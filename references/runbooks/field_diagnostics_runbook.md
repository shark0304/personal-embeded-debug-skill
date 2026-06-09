# Field Diagnostics Runbook

## Trigger symptoms

- Field reboot, watchdog reset, brownout, hardfault reset, assert reset, OTA reset, manual reset, or intermittent device return.

## Minimum evidence

- Field log ringbuffer, reset reason, uptime, firmware version, board revision, last progress marker, OTA slot state, power metrics.

## Fast triage

1. Run `analyze_reboot_reason.py`.
2. Run `analyze_log_ringbuffer.py`.
3. Run `analyze_device_metrics.py` when telemetry counters are available.
4. Convert the field bundle into a debug packet artifact list.

## High-probability root causes

- Watchdog starvation, brownout/power droop, assert/fault, OTA rollback/reset, manual reset, thermal or connectivity-triggered reboot.

## Scripts to run

- `scripts/analyze/analyze_reboot_reason.py`
- `scripts/analyze/analyze_log_ringbuffer.py`
- `scripts/analyze/analyze_device_metrics.py`

## Manual experiments

- Reproduce with telemetry enabled, power capture, reduced logging, and last-progress marker.

## Fix patterns

- Move watchdog feed to progress point, add brownout telemetry, preserve fault frame, add OTA validation state, rate-limit logs.

## Regression tests

- Golden packet with field log, reboot classification, and expected root cause branch.

## Do-not-guess rules

- Do not call a field reboot a watchdog without reset-reason evidence.
