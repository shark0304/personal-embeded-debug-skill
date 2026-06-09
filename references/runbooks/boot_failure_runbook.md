# Boot Failure Runbook

## Trigger symptoms

- Boot loop, rootfs wait, kernel panic during mount, slow boot, wrong DTB.

## Minimum evidence

- Full boot log, bootargs, bootloader env, storage type, partition table, DTB/DTS, kernel config.

## Fast triage

1. Run `boot_log_timeline.py`.
2. Identify failed stage: bootloader, kernel, rootfs, init, app.
3. Check storage errors before filesystem errors.

## High-probability root causes

- Wrong bootargs/root device, missing built-in storage driver, wrong DTB, storage timing/error, init missing.

## Scripts to run

- `scripts/boot_log_timeline.py`
- `scripts/linux_log_triage.py`
- `scripts/kconfig_check.py`

## Manual experiments

- Boot known-good rootfs, dump booted DTB, force init=/bin/sh when safe.

## Fix patterns

- Correct bootargs, build drivers in, fix DT storage node, repair partition layout.

## Regression tests

- Boot log packet and expected largest boot gaps/rootfs state.

## Do-not-guess rules

- Do not reformat media before collecting storage errors and partition evidence.
