# ESP-IDF Panic Runbook

## Trigger symptoms

- Guru Meditation, LoadProhibited/StoreProhibited, watchdog, cache-disabled panic, brownout, reset loop.

## Minimum evidence

- Full monitor log, chip target, ESP-IDF version, sdkconfig, partition table, panic registers, backtrace.

## Fast triage

1. Run `esp_panic_parse.py`.
2. Decode backtrace with ESP-IDF monitor or `symbolicate_addresses.py`.
3. Check task/core, EXCVADDR, WDT type, cache-disabled message.

## High-probability root causes

- NULL pointer, invalid pointer, task WDT, ISR not IRAM safe, PSRAM/DMA misuse, brownout.

## Scripts to run

- `scripts/esp_panic_parse.py`
- `scripts/symbolicate_addresses.py`
- `scripts/average_current.py` for brownout/power bursts.

## Manual experiments

- Reproduce with reduced logging, Wi-Fi/BLE disabled, PSRAM disabled, or smaller workload as isolation.

## Fix patterns

- Fix pointer lifetime, IRAM/DRAM placement, watchdog feed/progress, heap capabilities, power supply.

## Regression tests

- Panic log packet plus expected parsed cause.

## Do-not-guess rules

- Do not ignore EXCVADDR or decoded backtrace.
