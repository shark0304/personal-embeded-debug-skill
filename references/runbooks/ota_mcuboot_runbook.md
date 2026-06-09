# OTA and MCUboot Runbook

## Trigger symptoms

- OTA rollback, image not confirmed, boot slot mismatch, secure boot/anti-rollback failure.

## Minimum evidence

- Bootloader log, partition table, slot state, image metadata, signing/encryption/secure version, recovery path.

## Fast triage

1. Identify active slot and rollback state.
2. Verify image size/signature/version against partition table.
3. Confirm app marks image valid after health checks.

## High-probability root causes

- Partition drift, unconfirmed image, anti-rollback policy, bad signature, power loss during update.

## Scripts to run

- `scripts/boot_log_timeline.py`
- `scripts/map_memory_summary.py`

## Manual experiments

- Reproduce on non-production keys/devices with confirmed recovery path.

## Fix patterns

- Fix slot layout, confirmation path, rollback policy, staged rollout guard.

## Regression tests

- Golden OTA packet with slot state and expected report.

## Do-not-guess rules

- Do not recommend fuse/key changes without recovery path.
