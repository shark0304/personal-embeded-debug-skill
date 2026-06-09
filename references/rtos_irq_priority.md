# RTOS Interrupt Priority Sanity

Use this reference when a Cortex-M RTOS project faults, asserts, deadlocks, or loses events around ISR callbacks, queues, semaphores, DMA completion, USB, Ethernet, or timers.

## Evidence to Collect

- RTOS and port, especially FreeRTOS Cortex-M port.
- `__NVIC_PRIO_BITS` or implemented priority bits.
- `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY` and `configMAX_SYSCALL_INTERRUPT_PRIORITY`.
- IRQ priority values set through CMSIS, HAL, devicetree, or startup code.
- Whether the ISR calls RTOS `FromISR` APIs or wakes tasks.
- Current `SCB->AIRCR` priority grouping if subpriorities are used.

Use `scripts/nvic_priority_check.py` for FreeRTOS-style checks.

## Rules of Thumb

- Lower numeric Cortex-M priority values are more urgent.
- CMSIS `NVIC_SetPriority()` normally takes an unshifted logical priority.
- FreeRTOS APIs from ISR are only valid at priorities numerically equal to or greater than the configured max-syscall priority.
- Priority 0 is often reserved for truly urgent interrupts and must not call FreeRTOS APIs.
- Mixing shifted hardware register values with unshifted CMSIS values is a common source of false confidence.
- Vendor HAL callbacks inherit the IRQ priority of the underlying peripheral interrupt.

## Symptoms

- Works without RTOS, fails after enabling queues/semaphores from ISR.
- Random HardFault or assert after DMA/USB/Ethernet interrupt.
- ISR fires, but task notification or queue receive never happens.
- Fault appears only under load when nested interrupts occur.
- `INVPC`, stack corruption, or impossible return address after an ISR-heavy path.

## Triage Flow

1. List all ISRs that call RTOS APIs.
2. Record their logical NVIC priorities, not only raw register bytes.
3. Compare each against the max-syscall threshold.
4. Check priority grouping; prefer all implemented bits as preemption priority for FreeRTOS.
5. Enable RTOS assert hooks and fault register capture.
6. If a vendor callback calls RTOS APIs, verify the parent IRQ priority, not the callback function.

## Fix Patterns

- Move RTOS-calling ISRs to a numerically lower urgency, for example logical priority 5 or lower urgency when max-syscall is 5.
- Keep hard real-time ISR work above the threshold only if it never calls RTOS APIs.
- Split urgent ISR handling from RTOS notification with a lower-priority software interrupt when needed.
- Centralize IRQ priority assignment instead of scattering it across generated code and application code.
