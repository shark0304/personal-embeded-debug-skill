# Embedded Debug Report

## 1. Case summary

- Case ID: `zephyr-st-imu-debug-loop`
- Platform: `zephyr`
- Board: `xiao_ble/nrf52840/sense`
- Shield: `unknown`
- Toolchain: `zephyr`
- Build system: `cmake`
- Analysis status: `incomplete`

## 2. Evidence completeness

- build_log: 1 artifact(s)
- dts: 2 artifact(s)
- kconfig: 2 artifact(s)
- serial_log: 1 artifact(s)

## 3. Missing critical evidence

- logic_trace
- scope_trace

## 4. Hypothesis ranking

### H1: The IMU is addressed through a valid Zephyr node, but the first I2C transaction happens while the LSM6DS3TR-C power path or bus lines are not yet electrically stable.

- Confidence: medium
- Evidence for: serial.log shows an nRF TWIM I2C line error before LSM6DSL reports failed reboot and failed chip initialization; zephyr.dts contains a board-specific LSM6DS3TR-C regulator enable GPIO and startup-delay-us property; The upstream XIAO BLE Sense DTS models the ST IMU as an I2C device at reg 0x6a, so the failure is after DTS node selection rather than a missing node
- Evidence against: Current sanitized zephyr.dts already contains startup-delay-us = <3000>, so an old-board-DTS timing bug is not proven from this packet alone; No I2C logic trace or regulator enable waveform is available
- Missing evidence: logic_trace; scope_trace for IMU enable rail and first I2C transfer; exact Zephyr/NCS version and board revision from the failing device
- Verification step: Capture IMU enable GPIO, sensor VDD, SDA, and SCL from reset through the first LSM6DSL register read; then repeat with startup-delay-us increased and with any board-local pull-up override removed.
- Expected observation: If this hypothesis is true, the failing capture shows I2C activity before the IMU rail is stable or malformed SDA/SCL levels, and the delay/pull-up fix removes the TWIM line error.
- Fix if confirmed: Keep the board DTS regulator startup delay at the empirically verified minimum, remove incorrect I2C pull-up overrides, and preserve the waveform plus debug packet as a golden regression case.

### H2: The Zephyr DTS or Kconfig path does not enable the LSM6DSL driver instance that the sample expects.

- Confidence: low
- Evidence for: This is a common Zephyr sensor bring-up failure mode when overlays or board targets are wrong
- Evidence against: zephyr.dts contains lsm6ds3tr-c@6a with status okay, compatible st,lsm6dsl, reg 0x6a, and irq-gpios; .config has CONFIG_SENSOR=y, CONFIG_I2C=y, CONFIG_GPIO=y, CONFIG_LSM6DSL=y, and CONFIG_LSM6DSL_TRIGGER_GLOBAL_THREAD=y
- Missing evidence: locally generated zephyr.dts from the exact failing checkout; full build log from the failing machine
- Verification step: Run dts_probe_check.py on build/zephyr/zephyr.dts and kconfig_check.py on build/zephyr/.config for the LSM6DSL node and required symbols.
- Expected observation: If this hypothesis is true, one of the DTS status/compatible/reg/irq-gpios or CONFIG_SENSOR/I2C/GPIO/LSM6DSL checks fails.
- Fix if confirmed: Fix the board target, overlay application, node status, compatible string, I2C address, interrupt GPIO property, or missing Kconfig symbol before modifying driver code.

### H3: The sample's trigger or logging path consumes more stack than the configured runtime budget on this board.

- Confidence: low
- Evidence for: The sample uses trigger mode and floating-point formatted output
- Evidence against: The observed failure occurs during LSM6DSL initialization before sustained trigger/FIFO handling; .config sets main and system workqueue stacks to 2048 bytes
- Missing evidence: thread analyzer output; stack high-water marks from a running board
- Verification step: Enable Zephyr thread analyzer or stack sentinel and capture stack usage after the driver initializes successfully.
- Expected observation: If stack is the root branch, stack margin collapses or a stack sentinel/assert appears after initialization rather than during the first I2C transaction.
- Fix if confirmed: Increase the specific thread stack that underflows and preserve the stack snapshot in the golden packet.


## 5. Verification plan

- Pre-check: Run `scripts/analyze/analyze_i2c_init_failure.py --serial-log serial.log --dts zephyr.dts --config .config --out i2c_init_analysis.json` to keep serial-log signatures, DTS node facts, Kconfig facts, missing evidence, and candidate hypotheses in one JSON artifact.
- H1: Capture IMU enable GPIO, sensor VDD, SDA, and SCL from reset through the first LSM6DSL register read; then repeat with startup-delay-us increased and with any board-local pull-up override removed.
- H2: Run dts_probe_check.py on build/zephyr/zephyr.dts and kconfig_check.py on build/zephyr/.config for the LSM6DSL node and required symbols.
- H3: Enable Zephyr thread analyzer or stack sentinel and capture stack usage after the driver initializes successfully.

Hardware measurement plan:

- Use `assets/templates/i2c_sensor_bringup_measurement_plan.md` as the capture checklist.
- Export decoded I2C CSV as `time,event,address,rw,ack,data` or raw CSV as `time,scl,sda`.
- Run `scripts/analyze/analyze_i2c_logic_trace.py --trace logic_trace.csv --out logic_trace_analysis.json` after capture.
- Scope sensor VDD, IMU enable, SCL, and SDA on the same time base.
- Correlate the first I2C START and address ACK/NACK with the serial-log timestamp and rail stability.
- Keep the result as unconfirmed if waveform evidence is still missing.

## 6. Fix plan

- H1: Keep the board DTS regulator startup delay at the empirically verified minimum, remove incorrect I2C pull-up overrides, and preserve the waveform plus debug packet as a golden regression case.
- H2: Fix the board target, overlay application, node status, compatible string, I2C address, interrupt GPIO property, or missing Kconfig symbol before modifying driver code.
- H3: Increase the specific thread stack that underflows and preserve the stack snapshot in the golden packet.

## 7. Regression recommendation

- Preserve this debug packet as a golden packet after root cause and verification are complete.
- Preserve missing-evidence templates under `artifacts_missing/` until real `logic_trace` and `scope_trace` captures are available.
- If startup delay is verified, add the minimal DTS patch and before/after analyzer outputs to this packet.
