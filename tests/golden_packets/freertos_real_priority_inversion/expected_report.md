# Expected Report

## Case summary
FreeRTOS watchdog miss under shared resource load.

## Evidence completeness
- task snapshot: present
- wait graph: missing

## Missing critical evidence
- resource owner/waiter graph

## Hypothesis ranking
### H1
- evidence_for: high-priority task blocked while lower-priority work continues
- evidence_against: mutex owner trace missing
- verification_step: run freertos_wait_graph.py

## Verification plan
- Capture resource owner and waiter states.

## Fix plan
- Use priority inheritance mutex or redesign ownership after verification.

## Regression recommendation
- Preserve task snapshot and wait graph.
