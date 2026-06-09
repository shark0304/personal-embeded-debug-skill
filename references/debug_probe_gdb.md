# GDB, Debug Probe, and Fault Evidence Capture

Use this reference when a Cortex-M/MCU problem needs probe-based evidence: HardFault, lockup, reset-loop, bootloader handoff, vector table issue, stack corruption, watchpoint, or "works only under debugger."

## Evidence to Capture First

- ELF/map file that matches the flashed binary.
- Probe, GDB server, SWD/JTAG speed, reset strategy, and whether connect-under-reset is used.
- Stacked PC/LR/xPSR and handler LR/EXC_RETURN for faults.
- MSP, PSP, CONTROL, VTOR, CFSR, HFSR, MMFAR, BFAR.
- Disassembly around stacked PC and symbolicated addresses.
- Reset reason register and boot mode/option byte state when standalone boot differs.

Use `fault_analyzer.py` for SCB fault registers. Use `symbolicate_addresses.py` when an ELF and raw addresses are available.

## High-Value Lessons

- Always symbolicate the stacked PC before editing code.
- The LR inside the fault handler is often EXC_RETURN; the stacked LR is the interrupted function's LR. Do not confuse them.
- A debugger can change timing, reset sequencing, watchdog behavior, low-power behavior, and semihosting/log output.
- Vector catch is useful for first-fault capture but can hide reset-loop behavior if left enabled.
- Hardware watchpoints are better than printf when hunting buffer overwrite or register corruption.
- Semihosting can halt or distort real-time behavior. RTT/SWO/UART logging each has different timing and loss modes.

## Useful GDB Commands

```text
info registers
x/8wx $sp
x/16i $pc-16
info symbol 0x08001234
list *0x08001234
bt
monitor reset halt
monitor cortex_m vector_catch hard_err bus_err mm_err
watch *(uint32_t*)0x20001000
```

## Common Cortex-M SCB Reads

Verify the core and manual, but common Cortex-M System Control Space fault registers include:

```text
x/wx 0xE000ED28  # CFSR
x/wx 0xE000ED2C  # HFSR
x/wx 0xE000ED34  # MMFAR
x/wx 0xE000ED38  # BFAR
x/wx 0xE000ED08  # VTOR
```

## Probe-Specific Checks

- OpenOCD: reset config, vector catch, adapter speed, connect-under-reset, target voltage.
- J-Link: GDB server device name, interface, speed, reset strategy, RTT mode, monitor-mode debugging availability.
- ST-LINK/CMSIS-DAP: firmware version, SWD speed, low-power/debug freeze settings, option byte access.

## Output Expectations

Return the exact evidence capture sequence before proposing broad fixes. Include commands, expected observation, and how each result changes the hypothesis ranking.
