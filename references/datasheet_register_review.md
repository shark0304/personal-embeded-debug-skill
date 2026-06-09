# Datasheet and Register Review

Use this reference when reviewing driver initialization against a datasheet/reference manual excerpt.

## Evidence Rules

- Cite user-provided section, page, table, register, and bitfield when available.
- Do not invent register addresses, bit meanings, timing limits, or reset values.
- Do not copy assumptions from a related MCU without labeling them as analogies.
- Check errata before recommending a workaround.

## Register Review Checklist

For each register:

- Name and address offset.
- Reset value.
- Access type: RO, WO, RW, W1C, RC, write-protected, lock/unlock.
- Reserved bit required value.
- Side effects on read or write.
- Clock/reset dependency.
- Required wait or ready flag.
- Synchronization busy flag.
- Interrupt/error flag clear sequence.
- Whether initialization writes are full-register writes or read-modify-write sequences.

Use `scripts/bitfield_decode.py` when the user provides value and field definitions.
Use `scripts/register_write_check.py` when a proposed register write can be checked against reserved-bit masks, required-one masks, preserve masks, or W1C flag masks.

## Timing and Electrical Limits

Extract:

- Min/typ/max values and test conditions.
- Voltage and temperature range.
- Setup/hold time.
- Rise/fall time.
- Absolute maximum versus recommended operating conditions.

Never recommend operating at absolute maximum ratings.

## Driver Review Output

```text
Manual evidence
- Section/table/page:
- Register/bit:
- Constraint:

Code mismatch
- ...

Required initialization order
1. ...

Risk
- ...
```

## Common Datasheet Mistakes

- Writing reserved bits as 1.
- Clearing W1C flags by read-modify-write.
- Clearing read-to-clear or write-one-to-clear status accidentally while preserving unrelated fields.
- Missing clock enable before register access.
- Not waiting for oscillator/PLL/peripheral ready.
- Confusing peripheral reset with system reset.
- Using shifted I2C address where API expects unshifted address.
- Using reset values from a different silicon revision or package variant.
