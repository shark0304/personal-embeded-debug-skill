# STM32 Platform Debug Pack

Use this reference for STM32 bare-metal, HAL/LL, CubeMX, FreeRTOS, and STM32H7/F7/U5/H5-style cache/DMA issues.

## Evidence to Collect

- Exact STM32 part, board, silicon revision, clock tree, CubeMX/HAL version, compiler, linker script.
- Full init order for clocks, GPIO, DMA, peripheral, NVIC, RTOS scheduler.
- For DMA: buffer address, section, memory domain, cacheability, alignment, transfer direction, DMA flags.
- For faults: CFSR/HFSR/BFAR/MMFAR, stacked PC/LR/xPSR, MSP/PSP, map file.
- For generated projects: `.ioc`, generated diff, user-code sections, and last known good Cube/HAL version.

## High-Value STM32 Lessons

- On STM32H7/F7-class Cortex-M7 parts, DTCM/ITCM and AXI SRAM have different CPU/DMA/cache visibility.
- DCache plus DMA needs explicit clean/invalidate or non-cacheable MPU/linker regions.
- CubeMX regeneration can silently reorder clocks, DMA init, GPIO AF, NVIC priority, or middleware settings.
- Peripheral register access before clock enable can BusFault or silently fail depending on bus/peripheral.
- HAL callbacks run in ISR context; FreeRTOS API rules still apply.
- ETH, USB, SDMMC, ADC DMA, and camera/display paths are cache/memory-domain heavy; treat them as coherency problems early.
- Option bytes, boot pins, vector table offset, and bootloader handoff often explain "works under debugger, fails standalone."

## Debug Flow

1. Confirm part number and reference manual family; do not transfer register facts from a nearby family without checking.
2. Check clock tree and reset state before peripheral config.
3. Check pin mux and alternate function at registers, not only CubeMX.
4. For DMA, check request line, memory domain, cache line alignment, and maintenance timing.
5. For RTOS, check NVIC priority grouping and max syscall priority.
6. For crashes, decode fault registers and symbolicate stacked PC before changing code.

## Useful Skill Tools

- `fault_analyzer.py`
- `dma_buffer_check.py`
- `nvic_priority_check.py`
- `register_write_check.py`
- `uart_baud_check.py`
- `i2c_pullup_check.py`
