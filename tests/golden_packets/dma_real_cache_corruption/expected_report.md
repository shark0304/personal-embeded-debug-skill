# Expected Report

## Case summary
DMA RX stale data with cache enabled.

## Evidence completeness
- symptom log: present
- buffer metadata: missing

## Missing critical evidence
- buffer address/size/cacheability

## Hypothesis ranking
### H1
- evidence_for: DCache-dependent stale RX data
- evidence_against: buffer address not captured
- verification_step: run dma_buffer_check.py after collecting buffer metadata

## Verification plan
- Test aligned nocache buffer or correct invalidate timing.

## Fix plan
- Align/isolate buffer or fix clean/invalidate protocol.

## Regression recommendation
- Preserve buffer metadata and DMA loopback test.
