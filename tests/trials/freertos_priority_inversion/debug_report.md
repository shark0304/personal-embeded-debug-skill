# Embedded Debug Report

## 1. Case summary

- Case ID: `freertos_priority_inversion`
- Platform: `freertos`
- Board: `generic_cortexm`
- Shield: `unknown`
- Toolchain: `arm-none-eabi-gcc`
- Build system: `make`
- Analysis status: `analyzed`

## 2. Evidence completeness

- rtos_snapshot: 1 artifact(s)
- serial_log: 1 artifact(s)

## 3. Missing critical evidence

- trace_timeline

## 4. Hypothesis ranking

### H1: A low priority logger task holds the SPI mutex while a high priority control task blocks behind it and a medium priority task consumes CPU.

- Confidence: high
- Evidence for: rtos_snapshot.yaml shows control blocked on spi_mutex; logger owns spi_mutex at low priority; telemetry runs at medium priority during the missed-deadline window; Shortening the logger SPI critical section removes deadline misses
- Evidence against: No heap exhaustion or stack overflow is present in the snapshot
- Missing evidence: trace_timeline for exact blocking duration
- Verification step: Enable FreeRTOS trace hooks or capture a scheduling timeline while the SPI mutex is held.
- Expected observation: The high priority task remains blocked until the low priority owner releases the mutex, while the medium task preempts the owner.
- Fix if confirmed: Use a FreeRTOS mutex with priority inheritance, shorten the mutex hold time, and move long SPI logging out of the low priority path.

### H2: The high priority control task misses deadlines because its stack is too small.

- Confidence: low
- Evidence for: Deadline misses can be caused by stack corruption
- Evidence against: Snapshot high-water marks have margin; The mutex-hold experiment changes the deadline miss rate
- Missing evidence: stack sentinel log
- Verification step: Enable stack overflow hooks and log high-water marks across the failure window.
- Expected observation: A stack issue would show low margin or overflow independent of mutex timing.
- Fix if confirmed: Increase the specific task stack and preserve high-water evidence.


## 5. Verification plan

- H1: Enable FreeRTOS trace hooks or capture a scheduling timeline while the SPI mutex is held.
- H2: Enable stack overflow hooks and log high-water marks across the failure window.

## 6. Fix plan

- H1: Use a FreeRTOS mutex with priority inheritance, shorten the mutex hold time, and move long SPI logging out of the low priority path.
- H2: Increase the specific task stack and preserve high-water evidence.

## 7. Regression recommendation

- Preserve this debug packet as a golden packet after root cause and verification are complete.
