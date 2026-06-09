#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


CFSR_BITS = {
    0: "IACCVIOL: instruction access violation",
    1: "DACCVIOL: data access violation",
    3: "MUNSTKERR: MemManage fault on exception return",
    4: "MSTKERR: MemManage fault on exception entry",
    5: "MLSPERR: MemManage lazy FP state preservation fault",
    7: "MMARVALID: MMFAR holds valid fault address",
    8: "IBUSERR: instruction bus error",
    9: "PRECISERR: precise data bus error",
    10: "IMPRECISERR: imprecise data bus error",
    11: "UNSTKERR: BusFault on exception return",
    12: "STKERR: BusFault on exception entry",
    13: "LSPERR: BusFault lazy FP state preservation fault",
    15: "BFARVALID: BFAR holds valid fault address",
    16: "UNDEFINSTR: undefined instruction",
    17: "INVSTATE: invalid EPSR state",
    18: "INVPC: invalid exception return",
    19: "NOCP: coprocessor disabled or absent",
    24: "UNALIGNED: unaligned access trap",
    25: "DIVBYZERO: divide by zero trap",
}

HFSR_BITS = {
    1: "VECTTBL: fault during vector table read",
    30: "FORCED: configurable fault escalated to HardFault",
    31: "DEBUGEVT: debug event",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode common Cortex-M fault registers.")
    parser.add_argument("--cfsr", default="0", help="Configurable Fault Status Register.")
    parser.add_argument("--hfsr", default="0", help="HardFault Status Register.")
    parser.add_argument("--mmfar", default=None, help="MemManage Fault Address Register.")
    parser.add_argument("--bfar", default=None, help="BusFault Address Register.")
    parser.add_argument("--pc", default=None, help="Stacked PC.")
    parser.add_argument("--lr", default=None, help="Stacked LR.")
    parser.add_argument("--exc-return", default=None, help="Fault handler LR / EXC_RETURN value.")
    parser.add_argument("--xpsr", default=None, help="Stacked xPSR.")
    parser.add_argument("--msp", default=None, help="Main Stack Pointer.")
    parser.add_argument("--psp", default=None, help="Process Stack Pointer.")
    parser.add_argument("--control", default=None, help="CONTROL register.")
    args = parser.parse_args()

    cfsr = parse_int(args.cfsr)
    hfsr = parse_int(args.hfsr)
    findings = decode_bits(cfsr, CFSR_BITS)
    hardfault = decode_bits(hfsr, HFSR_BITS)
    hints = build_hints(cfsr, hfsr)
    addresses = build_addresses(args, cfsr)
    exc_return_value = args.exc_return
    lr_value = normalize_optional_int(args.lr)
    if exc_return_value is None and lr_value is not None and looks_like_exc_return(parse_int(args.lr)):
        exc_return_value = args.lr
        hints.append("LR looks like EXC_RETURN; treating it as exception return metadata.")

    output = {
        "cfsr": hex(cfsr),
        "hfsr": hex(hfsr),
        "cfsr_findings": findings,
        "hfsr_findings": hardfault,
        "addresses": addresses,
        "exc_return": decode_exc_return(exc_return_value),
        "xpsr": decode_xpsr(args.xpsr),
        "hints": hints,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def decode_bits(value: int, names: dict[int, str]) -> list[str]:
    return [text for bit, text in sorted(names.items()) if value & (1 << bit)]


def build_hints(cfsr: int, hfsr: int) -> list[str]:
    hints: list[str] = []
    if hfsr & (1 << 30):
        hints.append("FORCED is set: inspect CFSR first; HardFault is likely escalated.")
    if cfsr & (1 << 9):
        hints.append("PRECISERR is set: BFAR may identify the exact invalid data address.")
    if cfsr & (1 << 10):
        hints.append("IMPRECISERR is set: fault may occur after the offending store; inspect recent writes/DMA.")
    if cfsr & (1 << 18):
        hints.append("INVPC is set: check corrupted LR/EXC_RETURN, stack frame, or invalid function pointer.")
    if cfsr & (1 << 24):
        hints.append("UNALIGNED is set: inspect packed structs, DMA buffers, and unaligned pointer casts.")
    if cfsr & (1 << 25):
        hints.append("DIVBYZERO is set: inspect divisor and compiler/runtime trap settings.")
    if cfsr & (1 << 7):
        hints.append("MMARVALID is set: use MMFAR as the MemManage fault address.")
    if cfsr & (1 << 15):
        hints.append("BFARVALID is set: use BFAR as the precise BusFault address when PRECISERR is set.")
    if not hints:
        hints.append("No specific hint matched; inspect PC/LR, stack, vector table, and recent peripheral access.")
    return hints


def build_addresses(args: argparse.Namespace, cfsr: int) -> dict[str, object]:
    mmfar_valid = bool(cfsr & (1 << 7))
    bfar_valid = bool(cfsr & (1 << 15))
    return {
        "mmfar": {
            "value": normalize_optional_int(args.mmfar),
            "valid": mmfar_valid,
            "note": "Only trust MMFAR when CFSR.MMARVALID is set.",
        },
        "bfar": {
            "value": normalize_optional_int(args.bfar),
            "valid": bfar_valid,
            "note": "Only trust BFAR when CFSR.BFARVALID is set.",
        },
        "stacked_pc": normalize_optional_int(args.pc),
        "stacked_lr": normalize_optional_int(args.lr),
        "msp": normalize_optional_int(args.msp),
        "psp": normalize_optional_int(args.psp),
        "control": normalize_optional_int(args.control),
    }


def decode_xpsr(text: str | None) -> dict[str, object] | None:
    if text is None:
        return None
    value = parse_int(text)
    exception_number = value & 0x1FF
    t_bit = bool(value & (1 << 24))
    return {
        "value": hex(value),
        "exception_number": exception_number,
        "active_context": "Thread" if exception_number == 0 else f"Exception {exception_number}",
        "thumb_state_bit_set": t_bit,
        "notes": build_xpsr_notes(exception_number, t_bit),
    }


def build_xpsr_notes(exception_number: int, t_bit: bool) -> list[str]:
    notes: list[str] = []
    if exception_number:
        notes.append("Stacked xPSR indicates the interrupted context was an exception/ISR.")
    else:
        notes.append("Stacked xPSR indicates the interrupted context was thread mode.")
    if not t_bit:
        notes.append("T bit is clear; invalid EPSR state can trigger UsageFault INVSTATE.")
    return notes


def decode_exc_return(text: str | None) -> dict[str, object] | None:
    if text is None:
        return None
    value = parse_int(text)
    if not looks_like_exc_return(value):
        return {
            "value": hex(value),
            "looks_like_exc_return": False,
            "notes": ["EXC_RETURN values normally have the high bits set and bit 0 set."],
        }

    return_mode = "Thread" if value & (1 << 3) else "Handler"
    stack_pointer = "PSP" if value & (1 << 2) else "MSP"
    frame_type = "basic" if value & (1 << 4) else "extended_fp"
    notes = [
        f"Exception return targets {return_mode} mode using {stack_pointer}.",
        f"Stack frame type appears {frame_type}.",
    ]
    if frame_type == "extended_fp":
        notes.append("Extended FP frame means stacked context includes floating-point state.")
    return {
        "value": hex(value),
        "looks_like_exc_return": True,
        "return_mode": return_mode,
        "stack_pointer": stack_pointer,
        "frame_type": frame_type,
        "notes": notes,
    }


def looks_like_exc_return(value: int) -> bool:
    return (value & 0xFF000000) == 0xFF000000 and bool(value & 1)


def normalize_optional_int(text: str | None) -> str | None:
    if text is None:
        return None
    return hex(parse_int(text))


def parse_int(text: str) -> int:
    try:
        return int(text, 0)
    except ValueError as exc:
        raise SystemExit(f"Invalid integer: {text}") from exc


if __name__ == "__main__":
    main()
