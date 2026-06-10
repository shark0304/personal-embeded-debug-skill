# Zephyr ST IMU Sensor Node

## Project Goal

Bring up an ST IMU on Zephyr, publish stable accelerometer/gyro samples, and leave a regression-ready packet for sensor initialization failures.

## Default Target

- Board: `xiao_ble/nrf52840/sense` or another Zephyr board with I2C/SPI sensor bus.
- Sensor/peripheral: LSM6DSL, LSM6DS3, LSM6DSOX, or compatible ST IMU.
- Toolchain: Zephyr SDK, west, Twister for regression.
- Interface: I2C first unless the board wiring is SPI-only.

## Milestones

1. Build the closest Zephyr sensor sample.
2. Confirm `prj.conf` enables `CONFIG_SENSOR`, bus, GPIO, and logging.
3. Confirm DTS has sensor node `status = "okay"`, compatible, `reg`, bus status, pinctrl, and optional `irq-gpios`.
4. Flash and capture boot/probe logs.
5. Read WHO_AM_I or driver identity log.
6. Add polling mode, then trigger/FIFO only after polling is stable.
7. Save a debug packet and Twister-style regression when a failure is confirmed.

## Validation Criteria

- Build log shows the intended board and overlay.
- Serial log prints firmware version, board, bus, address, and ID/probe result.
- Bus-level evidence confirms ACK and address when probe fails.
- Sample rate and queue depth remain stable for at least one sustained run.

## Key Risks

- Compatible string does not bind the intended Zephyr driver.
- I2C address or SA0 strap differs from the sample overlay.
- Power rail is not stable before the first transaction.
- IRQ GPIO polarity or trigger configuration is wrong.
- Stack size or logging load hides a timing issue.

## Debug Handoff

- Build or Kconfig failure: `$embedded-debug` build evidence and Zephyr DTS/Kconfig runbook.
- Sensor init, NACK, WHO_AM_I, or timeout: `$embedded-debug` Zephyr sensor bring-up runbook and I2C analyzers.
- Runtime reset: `$embedded-debug` field diagnostics or Cortex-M hardfault runbook.
