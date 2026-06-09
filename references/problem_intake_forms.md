# Problem Intake Forms

Use these forms to ask the smallest useful evidence set for a given symptom. Do not ask every question; pick the first missing artifacts that split the largest branches.

## Cortex-M Fault

- MCU, board revision, build mode, recent change.
- CFSR, HFSR, MMFAR, BFAR, stacked PC/LR/xPSR, handler LR/EXC_RETURN.
- MSP, PSP, CONTROL, active task/ISR, map/ELF.
- Last peripheral/DMA/RTOS change.

## RTOS Runtime

- RTOS/port/tick rate, assert file/line, task snapshot.
- Stack high-water marks, heap free/min-ever-free.
- ISR list that calls RTOS APIs and priorities.
- Mutex/queue/semaphore owner and waiters.

## Peripheral/DMA

- Peripheral clock, pinmux, mode, error flags, waveform.
- DMA request/channel/mux, width, increment, length unit.
- Buffer address, size, section, cacheability, memory domain, lifetime.

## Embedded Linux Probe

- Full boot log/dmesg, kernel version, booted DTB/DTS dump.
- Node path, compatible, status, required resources.
- Driver/module name, match table, Kconfig/module state.
- `devices_deferred`, clk/regulator/pinctrl summaries.

## Storage/Boot

- Serial boot log from reset, bootargs, partition table, storage type.
- Rootfs type, mount options, storage errors before filesystem errors.
- Bootloader env, DTB actually loaded, kernel config for storage drivers.

## Power/Low Power

- Measurement setup, debugger attached or detached, rails measured.
- Active/sleep state timeline, wake source, GPIO states, external loads.
- Sleep current target, measured current, battery capacity, duty cycle.

## Connectivity

- Stack/SDK version, logs with timestamps and reason/status codes.
- BLE parameters or Wi-Fi/cellular layer stage.
- RSSI/operator/channel, heap/buffer pools, task priorities, logging level.

## TinyML

- Target, runtime, model size/op list, arena size/log.
- Input preprocessing, scale/zero-point, golden raw input, target tensor dump.
- Stage timings and watchdog/period budget.

## OTA/Secure Boot

- Bootloader log, slot/partition table, image metadata, rollback state.
- Signing/encryption/secure version, eFuse/option-byte state.
- Recovery path and whether the operation is reversible.
