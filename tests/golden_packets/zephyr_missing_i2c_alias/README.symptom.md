# zephyr_missing_i2c_alias

Symptom: Zephyr application fails because an I2C device is not ready after overlay changes.

Expected behavior: report should inspect generated `zephyr.dts` and `autoconf.h` before editing driver code.
