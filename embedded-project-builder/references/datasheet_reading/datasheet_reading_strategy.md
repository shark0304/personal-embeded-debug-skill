# Datasheet Reading Strategy

Read the datasheet to answer engineering questions, not to summarize every page.

## Bring-up Questions

- What rails and voltage levels are legal during reset and first transaction?
- What clock or startup delay is required before the device answers?
- Which bus mode, address, chip select, pull-up, or strap setting selects the intended interface?
- Which register proves identity, readiness, or error state?
- Which bits must be written in a required order?
- What timing, interrupt, FIFO, DMA, or low-power behavior can invalidate a simple driver?

## Evidence To Extract

- Power range, current modes, and reset timing.
- Interface timing, bus mode, maximum speed, and idle levels.
- Address/strap table and default identity value.
- Register reset values for identity, status, control, and error flags.
- Init sequence with required delays and status polling.
- Interrupt polarity, latch/clear behavior, and FIFO watermark rules.

## Output Discipline

- Put facts in the note with page/table/register references when available.
- Put guesses under "unknown" until measured.
- Turn every risky datasheet detail into a validation step.
