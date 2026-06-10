# {{project_name}} Driver Bring-up Note

## Minimal Read / Write Test

- First read target: ID or status register.
- First write target: reset/control/scratch register only if safe.
- Log exact transaction: bus, address, register, value, return code.

## WHO_AM_I Or ID Check

- Expected value:
- Observed value:
- Evidence: serial log and bus trace when available.
- Failure handoff: `$embedded-debug` Zephyr sensor or bus bring-up runbook.

## Init Sequence

1. Validate device/bus readiness.
2. Apply startup delay if datasheet requires it.
3. Read ID.
4. Configure minimum operating mode.
5. Poll status until ready.
6. Enable optional interrupt, FIFO, DMA, or ML path only after polling works.

## Polling Mode

- Sampling period:
- Expected data range:
- Error handling for timeout, NACK, stale data, or CRC:

## Interrupt Mode

- IRQ source:
- GPIO polarity and trigger:
- ISR/thread/workqueue path:
- Debounce, clear condition, and race risk:

## FIFO Mode

- Watermark:
- Overflow behavior:
- Timestamp strategy:
- Drain loop and backpressure handling:

## Error Handling

- Retry policy:
- Bus recovery:
- Reset policy:
- Diagnostic log fields:

## Logging Plan

- Boot banner: firmware version, board, device, bus, address.
- Probe logs: Kconfig/DTS path, init result, ID value.
- Runtime logs: sample rate, dropped samples, queue depth, error counters.
- Failure packet: build log, serial log, config/DTS, bus trace, power trace if relevant.
