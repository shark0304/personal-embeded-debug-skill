# Expected Report

## Case summary

Cortex-M precise BusFault with valid BFAR.

## Evidence completeness

- fault registers: present
- ELF/map: present
- stacked PC symbolication: missing

## Missing critical evidence

- symbolicated stacked PC
- BFAR address owner

## Hypothesis ranking

### H1

- root_cause: invalid data access at BFAR
- confidence: medium
- evidence_for: PRECISERR and BFARVALID
- evidence_against: no symbolicated PC yet
- missing_evidence: stacked PC source line
- verification_step: run fault_analyzer.py and symbolicate_addresses.py
- expected_observation: stacked PC points to the access path for BFAR
- fix_if_confirmed: fix pointer/peripheral/MPU ownership

## Verification plan

- Decode fault registers and symbolicate stacked PC.

## Fix plan

- Apply fix only after BFAR and PC agree.

## Regression recommendation

- Preserve registers, ELF/map, and expected symbolication as a golden packet.
