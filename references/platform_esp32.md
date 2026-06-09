# ESP32 and ESP-IDF Debug Pack

Use this reference for ESP32-class ESP-IDF projects involving FreeRTOS, dual core scheduling, Guru Meditation crashes, watchdog resets, heap/PSRAM, Wi-Fi/BLE coexistence, flash/cache, and partition/boot issues.

## Evidence to Collect

- Chip target, ESP-IDF version, `sdkconfig`, partition table, boot log, panic output, reset reason.
- Full backtrace with symbols, core ID, exception cause, EXCVADDR, PC/PS, task name.
- Task watchdog/interrupt watchdog configuration and which task/core triggered it.
- Heap stats by capability: internal RAM, SPIRAM/PSRAM, DMA-capable, 8-bit capable.
- Whether code/data used in ISR or flash-cache-disabled paths is in IRAM/DRAM.
- Wi-Fi/BLE/logging activity when timing bugs appear.

## High-Value ESP32 Lessons

- Panic output is usually actionable; decode the backtrace before guessing.
- `LoadProhibited`/`StoreProhibited` often points to NULL or invalid pointer access; EXCVADDR is key.
- ISR code and data used while flash cache is disabled must be IRAM/DRAM safe.
- Task watchdog does not always mean CPU is slow; it can mean a task never yielded, a core is locked, or a critical section is too long.
- PSRAM helps capacity but can hurt latency and DMA compatibility.
- Wi-Fi/BLE coexistence and logging can change scheduling and heap timing.
- Partition table, OTA slot, NVS corruption, brownout, and bootloader version mismatches can masquerade as firmware logic bugs.

## Debug Flow

1. Capture the complete monitor log from boot through panic/reset.
2. Parse the panic summary with `scripts/esp_panic_parse.py`, then decode backtrace with ESP-IDF monitor or addr2line.
3. Identify task/core/context and whether flash cache was disabled.
4. Check heap capabilities and largest free block, not just total free heap.
5. For watchdog, list task priorities, pinned cores, blocking calls, critical sections, and feed points.
6. For peripheral DMA/I2S/SPI/LCD/camera, check DMA-capable memory and cache/PSRAM constraints.

## Useful Commands

```text
idf.py monitor
idf.py size
idf.py partition-table
idf.py gdbgui
espcoredump.py info_corefile
```
