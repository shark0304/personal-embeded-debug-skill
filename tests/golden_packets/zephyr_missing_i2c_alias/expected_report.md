# Expected Report

## Case summary

Zephyr I2C device is not ready after overlay change.

## Evidence completeness

- generated DTS: present
- autoconf.h: present
- runtime log: missing

## Missing critical evidence

- node alias lookup and driver symbol check

## Hypothesis ranking

### H1

- root_cause: generated DTS/Kconfig mismatch
- confidence: medium
- evidence_for: device_is_ready false with generated artifacts present
- evidence_against: no runtime init log yet
- missing_evidence: exact node status and driver CONFIG value
- verification_step: run dts_probe_check.py and kconfig_check.py
- expected_observation: node is missing/disabled or driver symbol is off
- fix_if_confirmed: fix overlay path/status/compatible or Kconfig

## Verification plan

- Check generated DTS and autoconf.h before driver edits.

## Fix plan

- Patch overlay/Kconfig only after generated files confirm the mismatch.

## Regression recommendation

- Preserve generated DTS/autoconf.h as a golden packet.
