# OTA, Secure Boot, Anti-Rollback, and Provisioning Debug

Use this reference for OTA rollback, bricked devices, partition mismatch, image verification failure, secure boot, flash encryption, eFuse/option-byte provisioning, and fleet update failures.

## Evidence to Collect

- Bootloader version, partition table, active slot, previous slot, image metadata, rollback state, and boot log.
- Signing/encryption settings, secure version, key digest state, and whether anti-rollback/eFuse/option bytes are programmed.
- OTA transport logs, image length/hash/signature, write offsets, and final validation result.
- Recovery path: serial bootloader, factory slot, rescue image, hardware strap, SWD/JTAG availability.
- Fleet context: device revision, prior firmware version, staged rollout percentage, and failure rate.

## Field Lessons

- Secure boot, flash encryption, anti-rollback, and debug access can make mistakes irreversible.
- OTA success means "written and selected"; product success requires post-boot validation and marking the image valid.
- Partition tables drift between builds more often than teams expect.
- Anti-rollback can block emergency downgrade if secure version policy is not planned.
- Brownout during OTA can expose weak bootloader, rollback, or filesystem assumptions.
- Provisioning must be treated as a manufacturing process with logs and auditability.

## Triage Flow

1. Capture bootloader log and slot state before reflashing.
2. Verify partition table against the actual image size and OTA metadata.
3. Verify signature/encryption/secure-version policy before changing keys or fuses.
4. Confirm rollback confirmation path and when the app marks itself valid.
5. Confirm recovery path on the exact hardware revision.
6. For fleet issues, compare failures by prior version, hardware revision, and provisioning batch.

## Safety Rules

- Warn before touching eFuse, option bytes, secure boot keys, flash encryption, anti-rollback counters, or bootloader partitions.
- Prefer read-only evidence collection first.
- Require a tested recovery path before recommending irreversible provisioning changes.
