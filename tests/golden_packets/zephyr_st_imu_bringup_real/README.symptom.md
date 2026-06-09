# Zephyr ST IMU Debug Loop Case

This local project is a reproducible evidence packet for validating
`embedded-debug` v3 against a real Zephyr + ST IMU bring-up path.

Upstream source inputs:

- Zephyr official `samples/sensor/lsm6dsl` from `zephyrproject-rtos/zephyr`
  commit `11a87708d4158d8c94b4efdb49ebe0fbdc6b6f3d`.
- Zephyr official `boards/seeed/xiao_ble/xiao_ble_nrf52840_sense.dts`
  from the same commit.
- Public failure shape from a Zephyr/NCS XIAO BLE Sense LSM6DSL discussion:
  I2C line error followed by LSM6DSL chip initialization failure.

Local limitations:

- This machine has no `west`, `cmake`, Zephyr SDK, attached XIAO BLE Sense, or
  logic analyzer, so the build and serial artifacts are sanitized samples.
- `build/zephyr/zephyr.dts` is a sanitized DTS artifact copied from the current
  upstream board DTS, not a locally generated post-CMake DTS.
- `serial.log` preserves only the minimal public error shape needed to route the
  case through the Zephyr DTS/Kconfig and field-diagnostics runbooks.
- No confirmed hardware root cause is claimed without regulator timing and I2C
  waveform evidence.
