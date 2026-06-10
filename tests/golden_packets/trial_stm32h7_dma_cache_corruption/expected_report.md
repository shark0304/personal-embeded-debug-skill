# Embedded Debug Report

## 1. Case summary

- Case ID: `stm32h7_dma_cache_corruption`
- Platform: `cortex-m`
- Board: `stm32h743_custom`
- Shield: `unknown`
- Toolchain: `arm-none-eabi-gcc`
- Build system: `cmake`
- Analysis status: `analyzed`

## 2. Evidence completeness

- dma_snapshot: 1 artifact(s)
- map: 1 artifact(s)
- scope_trace: 1 artifact(s)
- serial_log: 1 artifact(s)

## 3. Missing critical evidence

- elf

## 4. Hypothesis ranking

### H1: DMA RX buffers are in cacheable memory and are consumed without cache-line aligned invalidation after DMA completion.

- Confidence: high
- Evidence for: serial.log reports corruption only when D-cache is enabled; dma_snapshot.yaml shows RX buffer address 0x24001204, which is not 32-byte aligned; The invalidate-on-RX experiment removes the corrupted payloads
- Evidence against: No bus fault or hard fault appears in the packet; The last known good build differs only by cache behavior
- Missing evidence: elf for exact symbol cross-check
- Verification step: Move RX buffers to a non-cacheable region or align to 32 bytes and invalidate the full cache-line span after DMA completion, then run the RX stress loop.
- Expected observation: The CRC mismatch counter remains at zero with D-cache enabled.
- Fix if confirmed: Align DMA buffers and descriptors to cache-line size, invalidate RX spans after DMA completion, and clean TX spans before DMA ownership transfer.

### H2: The peripheral is writing outside the intended DMA buffer because of a descriptor length error.

- Confidence: low
- Evidence for: DMA corruption can also come from descriptor length mistakes
- Evidence against: The same descriptor configuration passes when D-cache is disabled; The cache maintenance experiment changes the outcome
- Missing evidence: full descriptor ring dump
- Verification step: Dump descriptor base, length, ownership, and next pointers before and after RX completion.
- Expected observation: A descriptor bug would show an invalid length or pointer independent of cache maintenance.
- Fix if confirmed: Correct descriptor sizing and ownership sequencing.


## 5. Verification plan

- H1: Move RX buffers to a non-cacheable region or align to 32 bytes and invalidate the full cache-line span after DMA completion, then run the RX stress loop.
- H2: Dump descriptor base, length, ownership, and next pointers before and after RX completion.

## 6. Fix plan

- H1: Align DMA buffers and descriptors to cache-line size, invalidate RX spans after DMA completion, and clean TX spans before DMA ownership transfer.
- H2: Correct descriptor sizing and ownership sequencing.

## 7. Regression recommendation

- Preserve this debug packet as a golden packet after root cause and verification are complete.
