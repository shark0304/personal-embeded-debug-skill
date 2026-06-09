# Expected Report

## Case summary
TFLM arena allocation failure after model update.

## Evidence completeness
- arena log: present
- map file: present

## Missing critical evidence
- op list
- recording allocator buckets

## Hypothesis ranking
### H1
- evidence_for: allocation failure after model update
- evidence_against: exact bucket not captured
- verification_step: run memory_budget.py and capture RecordingMicroAllocator output

## Verification plan
- Compare old/new op list and arena buckets.

## Fix plan
- Resize arena or reduce ops after bucket evidence.

## Regression recommendation
- Preserve arena log, map, op list, and memory budget.
