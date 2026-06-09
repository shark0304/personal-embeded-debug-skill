# Cortex-M HardFault Runbook

## Trigger symptoms

- HardFault, BusFault, MemManage, UsageFault, lockup, reset loop, invalid PC, or crash after enabling ISR/DMA/RTOS.

## Minimum evidence

- MCU/core, board revision, build mode, last known good.
- CFSR, HFSR, MMFAR, BFAR, stacked R0-R3/R12/LR/PC/xPSR.
- Handler LR/EXC_RETURN, MSP, PSP, CONTROL, active task/ISR.
- ELF/map matching the flashed binary.

## Fast triage

1. Decode CFSR/HFSR with `fault_analyzer.py`.
2. Symbolicate stacked PC with `symbolicate_addresses.py`.
3. Decide whether the interrupted context was thread or exception.
4. Check BFAR/MMFAR validity before trusting fault addresses.
5. Check stack bounds and RTOS task high-water marks.

## High-probability root causes

- Invalid function pointer or corrupted return address.
- Stack overflow or DMA overwrite.
- Invalid ISR API use or interrupt priority.
- Cache/DMA coherency or inaccessible DMA memory.
- Bad vector table, bootloader handoff, or wrong image.

## Scripts to run

- `scripts/fault_analyzer.py`
- `scripts/symbolicate_addresses.py`
- `scripts/nvic_priority_check.py`
- `scripts/dma_buffer_check.py`

## Manual experiments

- Halt at HardFault handler and capture stacked frame before reset.
- Reproduce with DCache disabled only as an isolation experiment.
- Move suspect DMA buffer to known DMA-safe memory.
- Add hardware watchpoint to suspected overwritten object.

## Fix patterns

- Correct ISR priority/API use.
- Align and isolate DMA buffers.
- Increase or split stack after proving stack pressure.
- Fix vector table/bootloader handoff.

## Regression tests

- Golden fault packet with registers and expected symbolication.
- Unit/HIL test for ISR-to-task path.
- Stack high-water assertion in debug build.

## Do-not-guess rules

- Do not locate the faulting source line without ELF/map.
- Do not trust BFAR/MMFAR unless valid bits are set.
- Do not call "memory corruption" a root cause without overwrite evidence.
