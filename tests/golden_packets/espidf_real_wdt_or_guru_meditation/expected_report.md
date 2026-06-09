# Expected Report

## Case summary
ESP-IDF panic/WDT under load.

## Evidence completeness
- panic log: present
- sdkconfig: present

## Missing critical evidence
- ELF/backtrace decode
- heap capability stats

## Hypothesis ranking
### H1
- evidence_for: WDT/Guru symptom under camera inference
- evidence_against: no decoded frame yet
- verification_step: run esp_panic_parse.py and symbolicate backtrace

## Verification plan
- Parse panic and classify WDT/cache/pointer branch.

## Fix plan
- Apply IRAM/heap/watchdog fix only after branch verification.

## Regression recommendation
- Preserve panic log and decoded backtrace.
