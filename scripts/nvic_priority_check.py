#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Cortex-M NVIC priority values against a FreeRTOS max-syscall threshold."
    )
    parser.add_argument("--prio-bits", required=True, type=int, help="Implemented NVIC priority bits.")
    parser.add_argument(
        "--irq-priority",
        required=True,
        type=int,
        help="Logical CMSIS priority assigned to the IRQ, unshifted.",
    )
    parser.add_argument(
        "--max-syscall-priority",
        required=True,
        type=int,
        help="Logical FreeRTOS configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY, unshifted.",
    )
    parser.add_argument(
        "--uses-freertos-api",
        action="store_true",
        help="Set when the ISR calls FreeRTOS FromISR APIs or wakes tasks.",
    )
    args = parser.parse_args()

    validate(args.prio_bits, args.irq_priority, args.max_syscall_priority)
    shift = 8 - args.prio_bits
    encoded_irq = args.irq_priority << shift
    encoded_max = args.max_syscall_priority << shift
    too_urgent = args.irq_priority < args.max_syscall_priority

    findings = []
    if args.irq_priority == 0:
        findings.append("IRQ priority 0 is the highest urgency; keep it away from RTOS APIs.")
    if args.max_syscall_priority == 0:
        findings.append("Max-syscall priority 0 usually leaves no safe higher-urgency RTOS API boundary.")
    if args.uses_freertos_api and too_urgent:
        findings.append(
            "Unsafe: this ISR is numerically higher urgency than the FreeRTOS syscall threshold."
        )
    elif args.uses_freertos_api:
        findings.append("OK: this ISR priority is within the FreeRTOS FromISR API range.")
    elif too_urgent:
        findings.append(
            "This IRQ is above the FreeRTOS syscall threshold; this is only OK if it never calls RTOS APIs."
        )
    else:
        findings.append("This IRQ is at or below the FreeRTOS syscall threshold.")

    output = {
        "priority_bits": args.prio_bits,
        "logical": {
            "irq_priority": args.irq_priority,
            "max_syscall_priority": args.max_syscall_priority,
            "lower_number_means_higher_urgency": True,
            "irq_above_syscall_threshold": too_urgent,
        },
        "encoded_8bit_register_values": {
            "irq_priority": hex(encoded_irq),
            "max_syscall_priority": hex(encoded_max),
            "left_shift": shift,
        },
        "uses_freertos_api": args.uses_freertos_api,
        "rtos_api_safe": (not args.uses_freertos_api) or (not too_urgent),
        "findings": findings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def validate(prio_bits: int, irq_priority: int, max_syscall_priority: int) -> None:
    if prio_bits <= 0 or prio_bits > 8:
        raise SystemExit("--prio-bits must be in 1..8")
    max_priority = (1 << prio_bits) - 1
    for name, value in {
        "--irq-priority": irq_priority,
        "--max-syscall-priority": max_syscall_priority,
    }.items():
        if value < 0 or value > max_priority:
            raise SystemExit(f"{name} must be in 0..{max_priority} for {prio_bits} priority bits")


if __name__ == "__main__":
    main()
