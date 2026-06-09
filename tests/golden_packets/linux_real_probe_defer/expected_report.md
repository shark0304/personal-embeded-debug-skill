# Expected Report

## Case summary
Linux probe deferred forever.

## Evidence completeness
- dmesg: present
- booted DTS: present

## Missing critical evidence
- devices_deferred
- regulator/clock summaries

## Hypothesis ranking
### H1
- evidence_for: deferred probe symptom
- evidence_against: supplier not identified yet
- verification_step: run linux_log_triage.py and inspect devices_deferred

## Verification plan
- Identify missing supplier and verify DTS/Kconfig.

## Fix plan
- Fix supplier node/config after verification.

## Regression recommendation
- Preserve dmesg, DTS, config, and supplier debugfs output.
