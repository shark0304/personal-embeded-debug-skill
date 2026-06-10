# STM32H7 DMA ADC Logger

## Project Goal

Build a high-rate ADC acquisition path on STM32H7 using DMA, cache-safe buffers, timestamping, and a repeatable data-integrity test.

## Default Target

- Board: STM32H743/H750/H7 Nucleo or custom STM32H7 board.
- Peripheral: ADC + DMA + timer trigger + optional SD/UART/USB logging.
- Toolchain: STM32CubeMX/CubeIDE, CMake + GCC, or Zephyr on STM32H7.
- Interface: DMA circular or double-buffer mode.

## Milestones

1. Validate clocks, ADC input pin, reference voltage, and sampling time.
2. Build a polling ADC read before enabling DMA.
3. Configure timer-triggered ADC and DMA with fixed buffer size.
4. Place DMA buffers in cache-safe memory or add explicit cache maintenance.
5. Add overrun, half-transfer, transfer-complete, and error counters.
6. Validate sample continuity with a known waveform.
7. Capture map file, linker sections, cache policy, and data-integrity evidence.

## Validation Criteria

- ADC reads expected DC level in polling mode.
- DMA buffer addresses and alignment are visible in map/linker evidence.
- Known sine/square input produces expected sample count and amplitude.
- No repeated stale blocks, missing half-buffer callbacks, or overrun counters under load.

## Key Risks

- D-cache invalidation/cleaning is missing or applied to the wrong range.
- DMA buffer is in inaccessible SRAM region.
- ADC clock/sample time exceeds source impedance limits.
- ISR priority conflicts with RTOS or logging.
- Storage/logging path backpressures the acquisition loop.

## Debug Handoff

- Data corruption or stale samples: `$embedded-debug` DMA/cache coherency runbook.
- HardFault: `$embedded-debug` Cortex-M hardfault runbook with ELF/map.
- Missed callbacks or RTOS stalls: `$embedded-debug` RTOS/IRQ priority runbooks.
