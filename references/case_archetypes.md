# Real-World Failure Archetypes

Use this reference to recognize common embedded failure shapes and ask for the smallest high-value evidence next. Do not treat these as answers; treat them as ranking hints.

## MCU/RTOS

- **Polling works, DMA fails**: suspect DMA request/mux, DMA-inaccessible memory, DCache/MPU, buffer lifetime, width/length units. Ask for buffer address/size/section, DCache state, DMA flags. Use `dma_buffer_check.py`.
- **HardFault after enabling interrupt/DMA**: suspect invalid ISR API use, stack overflow, corrupted callback, DMA overwrite, wrong interrupt priority. Ask for CFSR/HFSR/BFAR/MMFAR, stacked PC/LR/xPSR, IRQ priority, task stack. Use `fault_analyzer.py` and `nvic_priority_check.py`.
- **FreeRTOS queue/semaphore assert**: suspect non-FromISR API in ISR, object lifetime, stack corruption, priority threshold, scheduler not started, heap exhaustion. Ask for assert file/line, ISR context, object creation path, heap hooks.
- **Watchdog reset only under load**: suspect progress marker placement, long critical section, blocked high-priority task, logging, inference latency, bus/DMA stall. Ask for reset reason, last stage marker, task snapshot, watchdog feed location. Use `latency_budget.py`.
- **RTOS deadlock/starvation**: suspect priority inversion, mutex owner blocked, medium-priority interference, queue full, blocking call in callback. Ask for task states, owners/waiters, priorities, stack. Use `rtos_snapshot_check.py`.

## Serial/Peripheral

- **UART garbage/framing error**: suspect wrong peripheral clock, divisor quantization, peer baud error, polarity, stop/parity mismatch, pin mux. Ask for actual PCLK, baud settings, logic analyzer capture of `0x55`. Use `uart_baud_check.py`.
- **I2C NACK or stuck low**: suspect pull-ups/capacitance, address shift convention, bus recovery, slave power/reset, repeated-start sequence. Ask for SDA/SCL idle levels, pull-up value, bus capacitance, address used. Use `i2c_pullup_check.py`.
- **Register write breaks unrelated flags**: suspect reserved bits, W1C flags, read-to-clear bits, write protection, missing ready/busy wait. Ask for manual register table, reset value, proposed write, current value. Use `register_write_check.py`.

## TinyML/Embedded AI

- **Model allocates on PC but not MCU**: suspect arena growth, op resolver, alignment, accelerator memory region, model revision. Ask for op list, arena log, memory map. Use `memory_budget.py`.
- **Model output wrong only on target**: suspect preprocessing mismatch, int8 scale/zero-point, endian/channel order, clipping, fixed-point rounding. Ask for golden raw input, target input tensor dump, output before postprocess. Use `vector_compare.py`.
- **Latency misses after adding model**: suspect preprocessing or memory movement dominates, not inference alone. Ask for stage timings and period/watchdog target. Use `latency_budget.py`.

## Embedded Linux

- **Driver probe never called**: suspect booted DTB mismatch, disabled node, compatible mismatch, driver not built/loaded, parent bus not probed. Ask for booted DTS, compatible, driver match table, dmesg.
- **Probe deferred forever**: suspect missing supplier: regulator, clock, reset, GPIO, PHY, bridge, panel, firmware. Ask for `/sys/kernel/debug/devices_deferred`, regulator/clk summaries, dmesg around supplier.
- **Kernel panic/oops after driver change**: suspect NULL resource, invalid mapped register, bad DMA buffer, use-after-free, IRQ before init complete. Ask for full oops with symbols, taint, stack trace, preceding probe messages. Use `linux_log_triage.py`.
- **Rootfs/init failure**: suspect wrong bootargs, missing storage driver, DT storage node, filesystem, init path, initramfs timing. Ask for full serial boot log, `/proc/cmdline`, root device, kernel config.
- **Zephyr/NCS device not ready**: suspect devicetree/Kconfig mismatch, overlay not applied, disabled node, missing binding, driver not enabled. Ask for generated `zephyr.dts`, `autoconf.h`, build target, `device_is_ready()` result.
