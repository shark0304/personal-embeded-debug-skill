# UART and I2C Signal-Level Debug

Use this reference when low-speed serial peripherals look configured correctly but fail on hardware: UART garbage bytes, framing errors, missing first byte, I2C NACKs, stuck-low bus, or behavior that changes with cable length, pull-ups, clock source, or logic analyzer connection.

## Evidence to Collect

- Actual peripheral clock after prescalers, not the nominal system clock.
- UART baud, oversampling, divisor/fractional settings, parity, stop bits, polarity, and peer clock accuracy.
- Logic analyzer capture of at least one known byte such as `0x55` for UART.
- I2C bus voltage, pull-up values, estimated/measured capacitance, speed mode, and measured rise time.
- SDA/SCL idle levels before initialization and after failure.
- I2C error flags: NACK, arbitration lost, bus error, timeout, overrun.
- Whether the target uses clock stretching, repeated starts, or 7-bit versus shifted addresses.

## UART Lessons

- A correct baud setting in source code does not prove the actual peripheral clock is correct.
- Baud error comes from clock source error, prescalers, divider quantization, and peer clock error.
- `0x55` is a useful test byte because it creates frequent transitions for measuring bit time.
- Framing errors often point to baud mismatch, stop-bit mismatch, inversion, or sampling near bit edges.
- Missing first bytes often come from enabling TX/RX before GPIO AF, FIFO, DMA, or receiver state is ready.

Use `scripts/uart_baud_check.py` for a first-pass divisor and error calculation. Still verify with the MCU reference manual because UART divider encodings differ by vendor.

## I2C Lessons

- Stuck-low SDA/SCL is a bus-state problem before it is a driver problem.
- 7-bit addresses should not be double-shifted when the HAL already expects a shifted or unshifted form.
- Weak pull-ups and high bus capacitance make edges too slow; strong pull-ups can exceed sink-current limits.
- A logic analyzer can hide marginal pull-ups by adding capacitance or changing thresholds.
- Recovery may require clocking SCL manually and issuing STOP before reinitializing the controller.

Use `scripts/i2c_pullup_check.py` to check whether a pull-up value is plausible for the estimated bus capacitance and speed mode.

## Debug Flow

1. Confirm idle levels and bus voltage.
2. Confirm clock tree and actual peripheral clock.
3. Capture a known UART byte or I2C transaction at the pins.
4. Decode timing first, then protocol fields.
5. Read peripheral error/status flags immediately after failure.
6. Only then change driver state machine, DMA, or RTOS scheduling.

## Output Expectations

Return the most likely physical/timing mismatch, the one measurement that proves it, and the smallest code/config change to test.
