# Driver Bring-up Strategy

## Order Of Work

1. Prove board and firmware boot.
2. Prove bus controller readiness.
3. Prove target address or chip select.
4. Read identity or status register.
5. Configure the minimum operating mode.
6. Poll data until stable.
7. Add interrupts, FIFO, DMA, power management, and high-rate paths.

## Logging Requirements

- Print firmware version, board, SDK, bus, address, and selected driver path.
- Log raw error codes, not only friendly messages.
- Include identity register observed value.
- Log runtime counters for timeouts, NACKs, overruns, drops, retries, and resets.

## Escalation Points

- No ACK, timeout, or wrong identity: gather bus trace and use `$embedded-debug`.
- Polling works but interrupt fails: inspect GPIO polarity, clear condition, and thread/ISR context.
- DMA/FIFO works at low rate but corrupts at high rate: inspect cache, alignment, backpressure, and ISR budget.
