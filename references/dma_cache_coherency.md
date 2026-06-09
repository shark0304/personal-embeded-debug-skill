# DMA and Cache Coherency Debug

Use this reference when polling works but DMA/interrupt mode fails, data is stale, the first transfer works but later transfers do not, or a buffer behaves differently after enabling DCache/MPU/RTOS.

## Evidence to Collect

- MCU/core and whether DCache is enabled.
- DMA direction: peripheral-to-memory, memory-to-peripheral, or bidirectional.
- Buffer address, size, alignment, linker section, and memory region.
- Cache line size and whether the region is cacheable/shareable.
- Exact cache maintenance calls and their timing relative to DMA start/complete.
- Whether the DMA can access that memory domain.
- Peripheral error flags and DMA transfer/error flags.

Use `scripts/dma_buffer_check.py` when address and size are known.

## Field Lessons

- Polling success does not prove a DMA path is valid. Polling uses the CPU view; DMA uses the bus-visible memory view.
- On cached Cortex-M7-class MCUs, DMA RX buffers usually need invalidate after completion before CPU reads. DMA TX buffers usually need clean before starting DMA.
- Cache maintenance by address must cover whole cache lines. Unaligned buffers can cause maintenance operations to touch adjacent data.
- A non-cacheable MPU region or dedicated nocache linker section is often cleaner for long-lived DMA rings.
- DMA-capable memory is SoC-specific. Some tightly coupled or core-local SRAM regions are invisible to DMA engines.
- Circular DMA plus cacheable buffers is high risk unless ownership boundaries and invalidation windows are explicit.
- If a driver asks for a nocache buffer, moving only the descriptor but not the payload buffer may still fail.

## Triage Flow

1. Confirm DMA request/channel/mux, transfer width, increment mode, and length units.
2. Confirm the buffer is in DMA-accessible memory.
3. Decide whether the buffer region is cacheable.
4. If cacheable, verify cache-line alignment and maintenance span.
5. For TX or memory-to-peripheral, clean the buffer before enabling DMA.
6. For RX or peripheral-to-memory, invalidate after DMA completion and before CPU parsing.
7. Add memory barriers where the vendor HAL or architecture requires them.
8. Compare one transfer with DCache disabled or buffer moved to nocache memory to isolate coherency.

## Red Flags

- `uint8_t rx[LEN]` on the stack used as a DMA destination on a cached MCU.
- DMA descriptor and payload placed in different memory regions without checking both.
- Cache maintenance called with the original unaligned address and length when the API expects aligned addresses.
- Invalidating an RX buffer before consuming unrelated adjacent data in the same cache line.
- RTOS task reads a circular DMA buffer while an ISR/DMA is still writing it.

## Fix Patterns

- Align DMA buffers to the cache line and round allocation size up to the cache line.
- Place DMA buffers in a named linker section with explicit MPU/cache attributes.
- Prefer static buffers for DMA rings; avoid stack buffers unless lifetime and alignment are guaranteed.
- Keep ownership explicit: CPU owns buffer before clean, DMA owns during transfer, CPU owns after complete plus invalidate.
- For Zephyr-style drivers, use nocache allocation/sections when the driver or SoC cache model requires it.

## Output Expectations

Return the likely coherency failure mode, the exact buffer property to verify next, and one controlled experiment such as "move this buffer to nocache SRAM" or "disable DCache only for this test."
