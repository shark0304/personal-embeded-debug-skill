# Embedded Debug Report

## 1. Case summary

- Case ID: `esp32s3_guru_meditation`
- Platform: `esp-idf`
- Board: `esp32s3_devkitc`
- Shield: `unknown`
- Toolchain: `xtensa-esp32s3-elf`
- Build system: `idf.py`
- Analysis status: `incomplete`

## 2. Evidence completeness

- build_log: 1 artifact(s)
- kconfig: 1 artifact(s)
- serial_log: 1 artifact(s)

## 3. Missing critical evidence

- elf
- map

## 4. Hypothesis ranking

### H1: A reconnect callback dereferences a null or stale context pointer after Wi-Fi reconnect.

- Confidence: medium
- Evidence for: serial.log shows LoadProhibited with EXCVADDR 0x00000000; The failure appears after Wi-Fi reconnect; Disabling the reconnect callback is the last known good change
- Evidence against: No ELF is available, so the PC/backtrace is not symbolicated; Heap poisoning output is not included
- Missing evidence: elf; map; full panic dump with symbols
- Verification step: Rebuild with matching ELF, run esp_panic_parse.py, symbolicate the backtrace, and add a guard plus lifetime check around the reconnect context.
- Expected observation: If this branch is correct, symbolication lands inside the reconnect callback and the guard prevents the LoadProhibited panic.
- Fix if confirmed: Fix context ownership or null handling in the reconnect callback and add a panic-log regression packet with the matching ELF.

### H2: Heap corruption damages the callback context before reconnect.

- Confidence: low
- Evidence for: Use-after-free can present as a stale pointer panic
- Evidence against: No heap poisoning assertion appears in the sanitized log
- Missing evidence: heap poisoning log; allocation trace
- Verification step: Enable heap poisoning and allocation tracing around reconnect.
- Expected observation: A heap issue would produce a poisoning violation or allocation lifetime mismatch before the panic.
- Fix if confirmed: Fix ownership and preserve heap trace evidence.


## 5. Verification plan

- H1: Rebuild with matching ELF, run esp_panic_parse.py, symbolicate the backtrace, and add a guard plus lifetime check around the reconnect context.
- H2: Enable heap poisoning and allocation tracing around reconnect.

## 6. Fix plan

- H1: Fix context ownership or null handling in the reconnect callback and add a panic-log regression packet with the matching ELF.
- H2: Fix ownership and preserve heap trace evidence.

## 7. Regression recommendation

- Preserve this debug packet as a golden packet after root cause and verification are complete.
