# Cortex-M and RTOS Fault Triage

Use this reference for Cortex-M HardFault, BusFault, UsageFault, MemManage fault, stack overflow, invalid interrupt usage, and RTOS crash triage.

## Required Evidence

Ask for the smallest missing set:

- MCU part number and core generation.
- CFSR, HFSR, DFSR, AFSR.
- MMFAR and BFAR when valid bits are set.
- Stacked R0-R3, R12, LR, PC, xPSR.
- MSP, PSP, CONTROL, active exception number.
- Disassembly around stacked PC.
- Map file or symbolicated address.
- RTOS task list, stack high-water marks, heap status when RTOS is used.

Use `scripts/fault_analyzer.py` when CFSR/HFSR are available.
Read `rtos_irq_priority.md` when the fault involves an ISR, DMA callback, RTOS queue/semaphore, task notification, USB, Ethernet, or timer callback.

## Triage Order

1. Check HFSR.FORCED. If set, decode CFSR first.
2. Check whether MMFAR/BFAR valid bits are set.
3. Decode stacked PC and LR; decide whether the fault happened in thread, ISR, or exception return.
4. Inspect xPSR exception number and EPSR state.
5. Inspect stack pointer bounds and alignment.
6. Identify whether the access was code fetch, data load/store, exception entry, or exception return.
7. Only then rank root causes.

## Common Root Causes

- Corrupted function pointer or callback table.
- Stack overflow corrupting return address or task control block.
- Calling RTOS non-ISR API from interrupt.
- Interrupt priority too high for RTOS API use.
- DMA writing outside buffer.
- Cache not cleaned/invalidated around DMA.
- Disabled peripheral clock causing BusFault on register access.
- Invalid EXC_RETURN or corrupted LR.
- Unaligned access trap.
- Divide-by-zero trap.

## Output Expectations

Return:

- Decoded fault bits.
- Address interpretation.
- EXC_RETURN stack selection and xPSR exception context when available.
- Top 3 likely root causes.
- Exact next GDB commands or register reads.
- Minimal code instrumentation or assertion to confirm.

Avoid generic advice like "check memory corruption" unless paired with a concrete verification step.
