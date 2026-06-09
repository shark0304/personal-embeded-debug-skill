# I2C Sensor Bring-up Measurement Plan

## Required instruments

- Logic analyzer with I2C decode and digital export.
- Oscilloscope with at least four channels when power timing is suspected.
- Short ground spring or low-inductance probe ground for rail and bus captures.
- Serial log capture from boot through the first sensor probe.

## Probe points

- Sensor VDD or local regulator output.
- Sensor enable pin and reset pin when present.
- I2C SDA and SCL at the sensor pins, not only at the MCU pins.
- Optional interrupt pin when trigger mode is part of the failure.

## Power rail measurement

- Trigger capture on reset release, enable GPIO edge, or first serial log marker.
- Measure rail rise time, monotonicity, final voltage, and droop during first bus
  transaction.
- Record whether firmware accesses the sensor before the rail is stable.

## I2C SDA/SCL measurement

- Confirm idle-high levels before the first START.
- Decode the first address phase and record ACK/NACK.
- Record clock rate, rise time, stuck-low intervals, and repeated START behavior.
- Export decoded CSV with `time,event,address,rw,ack,data` when possible.
- Export raw CSV with `time,scl,sda` when protocol decode is unavailable.

## Enable/reset pin measurement

- Capture enable/reset relative to VDD and the first I2C transaction.
- Verify polarity and timing match the board DTS and schematic.
- Check whether reset remains asserted during the first transaction.

## Timing correlation with firmware log

- Add a boot marker before sensor init if existing logs lack timestamps.
- Align serial timestamps with scope/logic timestamps using reset or GPIO marker.
- Preserve firmware build hash and board revision with the capture.

## Expected healthy waveform

- VDD reaches the valid operating range before the first START.
- SDA and SCL idle high, then show a clean START.
- Address phase ACKs at the DTS `reg` address.
- WHO_AM_I or first identity read returns stable data.

## Failure signatures

- SDA or SCL stuck low before START.
- First address NACK while VDD is still rising.
- START-like transition missing or malformed.
- WHO_AM_I register write ACKs but read data is unstable or all ones/zeros.
- Interrupt pin toggles before driver enables trigger handling.

## Data to export for embedded-debug

- `serial.log`
- `logic_trace.csv` or native analyzer file
- `scope_trace.csv` or annotated screenshot plus measurements
- generated `zephyr.dts`
- generated `.config` or `autoconf.h`
- build log and board revision note

## How to update debug_packet after measurement

1. Place exported captures in the project root or `artifacts/`.
2. Re-run `scripts/collect/collect_debug_packet.py --project-root . --platform auto --out debug_packet.yaml`.
3. Run `scripts/analyze/analyze_i2c_logic_trace.py --trace logic_trace.csv`.
4. Update the debug report with the confirmed or rejected hypothesis.
5. Preserve the packet as a golden regression case once the fix is verified.
