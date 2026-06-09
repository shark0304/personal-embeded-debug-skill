# Expected Report

## Case summary

Linux driver probe is deferred because a supplier regulator is unavailable.

## Evidence completeness

- dmesg: present
- DTS: present
- Kconfig: present
- devices_deferred: missing

## Missing critical evidence

- devices_deferred output
- regulator summary

## Hypothesis ranking

### H1

- root_cause: missing regulator supplier
- confidence: medium
- evidence_for: deferred probe symptom
- evidence_against: supplier list not captured yet
- missing_evidence: devices_deferred and regulator_summary
- verification_step: run linux_log_triage.py and inspect devices_deferred
- expected_observation: deferred device names missing regulator supplier
- fix_if_confirmed: fix supply property, regulator node, or supplier driver config

## Verification plan

- Collect devices_deferred and regulator summary.

## Fix plan

- Fix DT/Kconfig supplier after verification.

## Regression recommendation

- Preserve dmesg, DTS, config, and devices_deferred as golden packet.
