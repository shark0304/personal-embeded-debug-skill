# Expected Report

## Case summary
STM32 HardFault after DMA path.

## Evidence completeness
- fault registers: present
- ELF/MAP: missing

## Missing critical evidence
- ELF/MAP
- DMA buffer address and cacheability

## Hypothesis ranking
### H1
- evidence_for: fault after DMA enable
- evidence_against: no buffer address yet
- verification_step: collect ELF/MAP and run fault_analyzer.py plus dma_buffer_check.py

## Verification plan
- Decode fault frame and validate DMA buffer placement.

## Fix plan
- Fix DMA/cache only after buffer evidence confirms it.

## Regression recommendation
- Preserve fault dump and buffer metadata as golden packet.
