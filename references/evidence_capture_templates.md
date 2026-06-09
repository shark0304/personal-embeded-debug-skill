# Evidence Capture Templates

Use these bundled templates when a small instrumentation patch or command script would collect decisive evidence. Adapt them to the user's RTOS, logging backend, compiler, and board support package before applying.

## Templates

- `assets/templates/hardfault_capture.c`: Cortex-M HardFault capture skeleton for stacked registers and SCB fault registers.
- `assets/templates/freertos_snapshot.c`: FreeRTOS task/heap snapshot skeleton using standard task APIs when enabled.
- `assets/templates/zephyr_thread_snapshot.c`: Zephyr thread analyzer and heap/uptime snapshot skeleton.
- `assets/templates/linux_trace_probe.sh`: Embedded Linux dynamic debug/ftrace/debugfs capture script skeleton.

## Usage Rules

- Keep instrumentation behind a debug build flag or narrow command path.
- Do not add heavy logging inside timing-critical ISRs unless the point is to prove observer effect.
- Capture first-failure evidence before reset cleanup code overwrites state.
- For production-like tests, collect timestamps and counters with bounded overhead.
- Remove or gate templates after diagnosis unless they become part of a supported diagnostics interface.
