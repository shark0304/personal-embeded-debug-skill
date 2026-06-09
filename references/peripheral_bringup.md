# MCU Peripheral Bring-Up Debug

Use this reference for GPIO, UART, I2C, SPI, DMA, ADC, timer/PWM, and CAN bring-up on MCU-class systems.

## Universal Bring-Up Ladder

1. Power and reset are correct.
2. Peripheral clock enabled and reset released.
3. Pin mux and alternate function are correct.
4. Peripheral configuration matches datasheet timing.
5. Status/error flags are read directly.
6. Waveform matches expected electrical/protocol behavior.
7. Interrupt/DMA path is checked last.

## GPIO

- Clock gate enabled.
- Mode, pull-up/down, speed, output type.
- Alternate function when used.
- External pull or board conflict.
- Read actual IDR/ODR/AFR registers.

## UART

- TX/RX pin mux and AF mapping.
- Actual peripheral clock and baud divisor.
- Word length, parity, stop bits.
- FIFO threshold and interrupt/DMA mode.
- Error flags: overrun, framing, noise, parity.
- Logic analyzer confirms baud and polarity.

Use `scripts/uart_baud_check.py` when the clock tree, baud divisor, or peer clock tolerance is uncertain.

## I2C

- Pull-ups and bus voltage.
- 7-bit versus shifted address convention.
- Timing register based on actual peripheral clock.
- Bus stuck low before init.
- ACK/NACK, arbitration lost, bus error flags.
- Slave repeated-start or register-address sequence.

Use `scripts/i2c_pullup_check.py` when rise time, bus capacitance, pull-up value, or stuck-low recovery is suspect. Read `uart_i2c_signal_debug.md` for UART/I2C signal-level debug.

## SPI

- CPOL/CPHA, bit order, word size.
- CS polarity and setup/hold timing.
- FIFO threshold.
- MISO contention.
- Max SCK versus slave and wiring.
- DMA buffer alignment and cache coherency.

## DMA

- Correct request line/channel/mux.
- Peripheral and memory width.
- Increment modes.
- Transfer length units.
- Circular versus normal mode.
- Cache clean/invalidate and memory barriers on cached MCUs.
- Buffer address, alignment, linker section, MPU/cacheability, and DMA-accessible memory domain.

Read `dma_cache_coherency.md` when polling works but DMA fails, data is stale, DCache is enabled, or the buffer lives in SRAM regions with different bus/cache properties.

## CAN

- Bit timing from actual CAN clock.
- Transceiver standby/silent pins.
- Termination and ACK from another node.
- Filter configuration.
- Error counters and bus-off state.

## Output Expectations

Return a checklist sorted by probability, then the single next measurement that would eliminate the largest branch.
