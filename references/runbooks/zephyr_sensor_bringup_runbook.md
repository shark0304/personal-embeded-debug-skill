# Zephyr Sensor Bring-up Runbook

Use this runbook for Zephyr sensor probe/init failures, especially I2C/SPI IMUs,
accelerometers, gyros, pressure sensors, and magnetometers. Keep DTS/Kconfig
facts separate from bus and power hypotheses.

## Trigger symptoms

- `device_is_ready()` is false for a sensor device.
- Logs contain `failed to initialize`, `device not ready`, `I2C error`, `bus error`,
  `NACK`, `timeout`, `WHO_AM_I`, `LSM6DSL`, `LSM6DS3`, or similar probe messages.
- Sensor sample builds but no data is printed, trigger count remains zero, or the
  first register read fails.

## Minimum evidence

- Board target, board revision, Zephyr/NCS version, SDK/toolchain version.
- `prj.conf`, overlays, generated `zephyr.dts`, generated `.config` or
  `autoconf.h`, build log, and serial log from boot through sensor probe.
- Sensor part number, bus type, schematic excerpt for address select, power
  enable/reset pins, interrupt pin, pull-ups, and voltage rail.
- Logic analyzer capture for SDA/SCL or SPI lines when logs show NACK, timeout,
  line error, or WHO_AM_I failure.
- Scope capture for sensor VDD, enable/reset pin, and first bus transaction when
  a power rail or startup delay is plausible.

## DTS checks

1. Inspect generated `zephyr.dts`, not only source overlays.
2. Confirm sensor node `status = "okay"` or no disabling status.
3. Confirm `compatible` exactly matches an enabled Zephyr binding/driver.
4. Confirm `reg` matches schematic address straps or SPI chip-select index.
5. Confirm the parent bus node is enabled and has required `pinctrl` entries.
6. Confirm `irq-gpios` or `interrupt-gpios` property name matches the binding.
7. Confirm regulator, enable GPIO, reset GPIO, and `startup-delay-us` are modeled
   when the sensor is not always powered.

## Kconfig checks

- `CONFIG_SENSOR=y`
- Bus driver: `CONFIG_I2C=y` or `CONFIG_SPI=y`
- `CONFIG_GPIO=y` when interrupt, reset, or enable GPIOs are used.
- Sensor driver symbol, for example `CONFIG_LSM6DSL=y`.
- Trigger symbol, for example `CONFIG_LSM6DSL_TRIGGER_GLOBAL_THREAD=y`, only when
  trigger mode is expected.
- Logging level high enough for probe evidence, for example `CONFIG_LOG=y` and a
  sensor log level that exposes init failures.
- Stack sizes for main, workqueue, and sensor own thread when triggers/FIFO/logging
  are enabled.

## Bus-level checks

- For I2C: verify pull-ups, idle-high levels, clock rate, address, ACK/NACK, and
  whether the first transaction occurs after sensor power is stable.
- For SPI: verify mode, bit order, maximum frequency, chip select polarity/timing,
  and MISO response during WHO_AM_I.
- Check for bus instance conflicts such as `i2c0` vs `spi0` sharing pins or
  peripheral hardware on Nordic/STM32 boards.
- Reduce speed to standard-mode I2C or a conservative SPI frequency while
  isolating electrical problems.

## Sensor identity checks

- Read the sensor identity register with the Zephyr driver path and, if possible,
  with a minimal bus transaction tool.
- Treat a WHO_AM_I NACK as bus/power/address evidence, not as a confirmed bad
  silicon diagnosis.
- Treat a WHO_AM_I wrong value as evidence for wrong compatible, wrong part
  variant, wrong bus mode, or signal integrity before changing driver code.

## Power and startup timing checks

- Scope sensor VDD, enable GPIO, reset GPIO, and the first SDA/SCL or SPI
  transaction on the same time base.
- Verify regulator `startup-delay-us` covers the measured sensor rail rise and
  data-sheet startup timing with margin.
- Check whether firmware accesses the sensor before board-specific power enable
  completes.
- Check brownout, inrush, shared rail sequencing, and level shifter enable when
  the bus shows line errors.

## Interrupt / trigger checks

- Confirm the interrupt pin, GPIO controller, polarity, and route match the
  schematic and binding property.
- Start in polling mode if probe succeeds but trigger/FIFO mode fails.
- Check trigger thread stack, system workqueue stack, and logging backpressure.
- Verify trigger counter increments only after basic sample fetch works.

## Logic analyzer checks

- Export decoded CSV with `time,event,address,rw,ack,data` when the tool supports
  protocol decode.
- Export raw/simple CSV with `time,scl,sda` when only digital samples are
  available.
- Run `scripts/analyze/analyze_i2c_logic_trace.py` before ranking electrical
  hypotheses.
- Preserve the capture together with `serial.log`, `zephyr.dts`, and `.config` in
  the debug packet.

## Candidate root causes

- Compatible mismatch or unsupported part variant.
- Wrong I2C address or SPI chip-select/mode.
- Parent bus disabled or wrong bus instance selected.
- Missing or incorrect pinctrl.
- Missing pull-up, excessive bus capacitance, stuck-low SDA/SCL, or level shifter
  not enabled.
- Power rail not stable before first transaction.
- Missing or insufficient startup delay.
- WHO_AM_I read NACK or wrong value.
- Trigger GPIO wrong polarity, wrong pin, or missing GPIO driver.
- Stack size or logging overhead hiding a later trigger/FIFO problem.

## Verification experiments

- Run `analyze_i2c_init_failure.py` on serial log, DTS, and config.
- Run `dts_probe_check.py` for the exact sensor node, not a broad substring that
  also matches regulators.
- Run `kconfig_check.py` for sensor, bus, GPIO, driver, trigger, logging, and
  stack symbols.
- Capture power rail plus bus lines from reset to first sensor transaction.
- Sweep startup delay and bus speed one change at a time.
- Force polling mode to separate probe/bus failures from interrupt path failures.

## Fix patterns

- Fix `compatible`, `reg`, bus node, overlay path, or board target when generated
  DTS proves a mismatch.
- Enable missing Kconfig symbols through project config or board defconfig.
- Add or correct regulator/enable/reset GPIO modeling and `startup-delay-us`.
- Correct pull-up/pinctrl/bus speed based on measured waveform.
- Correct `irq-gpios` polarity or pin only after polling mode works.
- Increase only the thread stack that measurement shows is low.

## Regression packet guidance

- Preserve `debug_packet.yaml`, `expected_report.md`, `serial.log`,
  generated `zephyr.dts`, generated `.config`, and the exact logic/scope capture.
- Add `expected_logic_trace_format.md` when a capture is still missing.
- Add `expected_power_rail_measurement.md` when power sequencing remains the
  decisive unknown.
- Include the minimal DTS/Kconfig patch that verified the fix.

## Do-not-guess rules

- Do not call a sensor dead without WHO_AM_I and bus/power evidence.
- Do not diagnose a Zephyr driver bug before generated DTS and Kconfig are checked.
- Do not call a wrong I2C address without schematic straps or bus capture.
- Do not call a startup-delay fix confirmed without rail timing or repeated boot
  verification.
- Do not use a broad DTS node query that also matches regulators or helper nodes.
