# Expected Power Rail Measurement

This packet still needs a scope capture that correlates IMU power timing with the
first I2C transaction.

Required channels:

- Sensor VDD or local regulator output.
- LSM6DS3TR-C enable GPIO.
- I2C SCL at the sensor pin.
- I2C SDA at the sensor pin.

Optional channels:

- Sensor reset pin if populated.
- Interrupt pin if trigger mode is being debugged.
- Firmware marker GPIO toggled immediately before sensor init.

Measurements to record:

- Time from enable edge to VDD reaching the valid operating range.
- Time from VDD stable to the first I2C START.
- SDA/SCL idle voltage before the first START.
- Whether the first address phase ACKs or NACKs.
- Any VDD droop or line-level anomaly during the first transaction.

Expected healthy result:

- VDD is stable before the first START.
- SDA/SCL idle high before START.
- The address phase for `0x6a` ACKs.

If the first transaction begins before VDD is stable, verify by increasing
`startup-delay-us` and preserving before/after captures.
