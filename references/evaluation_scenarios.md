# Evaluation Scenarios

Use these scenarios to check whether the skill behaves like a senior embedded engineer. A good response asks for the smallest high-value evidence, ranks root causes, uses scripts/templates when useful, and avoids generic guesses.

| ID | Symptom | First evidence to ask for | Expected references/tools | Bad answer to avoid |
| --- | --- | --- | --- | --- |
| CM-01 | Cortex-M HardFault after enabling DMA IRQ | CFSR/HFSR/BFAR/MMFAR, stacked PC/LR/xPSR, handler LR, DMA buffer address | `cortex_m_faults.md`, `fault_analyzer.py`, `dma_buffer_check.py` | "Check memory corruption" without fault decoding |
| CM-02 | Fault only under FreeRTOS when UART callback sends queue | IRQ priority, `configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY`, callback API used | `rtos_irq_priority.md`, `nvic_priority_check.py` | Suggest bigger stack first |
| CM-03 | Works under debugger, fails standalone | reset reason, watchdog, boot pins/option bytes, VTOR, bootloader handoff | `debug_probe_gdb.md`, `platform_stm32.md` | Blame optimization immediately |
| DMA-01 | STM32H7 polling ADC works, DMA data stale | DCache state, buffer address/section/alignment, memory domain, cache maintenance calls | `platform_stm32.md`, `dma_cache_coherency.md`, `dma_buffer_check.py` | Change ADC sample time first |
| DMA-02 | DMA descriptor is in nocache SRAM but payload is still stale | descriptor address, payload address, both memory regions, ownership boundary | `dma_cache_coherency.md`, `dma_buffer_check.py` | Check only the descriptor |
| RTOS-01 | Random queue assert after hours | assert line, task snapshot, heap min-ever-free, ISR context, object lifetime | `rtos_runtime_debug.md`, `rtos_snapshot_check.py` | Assume queue implementation bug |
| RTOS-02 | High-priority task starves lower task | task states/priorities, resource owner/waiters, mutex type | `rtos_runtime_debug.md`, `freertos_wait_graph.py` | Add delays without analyzing ownership |
| RTOS-03 | Stack overflow hook fires but PC points to unrelated code | task high-water marks, stack sentinel, fault frame, last context switch | `rtos_runtime_debug.md`, `fault_analyzer.py` | Trust the final PC as the original bug |
| UART-01 | UART prints garbage at 115200 | actual PCLK, oversampling/divisor, peer error, logic capture of `0x55` | `uart_i2c_signal_debug.md`, `uart_baud_check.py` | Only check TX/RX swap |
| I2C-01 | I2C NACKs above 100 kHz | pull-up value, bus capacitance, measured rise time, address convention | `uart_i2c_signal_debug.md`, `i2c_pullup_check.py` | Increase timeout first |
| REG-01 | Clearing interrupt flag breaks another status | register table, W1C/RC bits, current value, proposed write | `datasheet_register_review.md`, `register_write_check.py` | Use read-modify-write blindly |
| ESP-01 | ESP32 Guru Meditation LoadProhibited | full panic log, EXCVADDR, PC, task/core, decoded backtrace | `platform_esp32.md`, `esp_panic_parse.py`, `symbolicate_addresses.py` | Reinstall ESP-IDF |
| ESP-02 | ESP32 task watchdog after adding camera/TinyML | task/core, watchdog task, PSRAM/DMA memory, stage timings | `platform_esp32.md`, `latency_budget.py` | Disable watchdog as fix |
| ESP-03 | ESP32 panic mentions cache disabled but code accessed flash | panic log, ISR path, IRAM_ATTR usage, data placement, sdkconfig | `platform_esp32.md`, `esp_panic_parse.py` | Treat it as random memory corruption |
| ZEP-01 | Zephyr `device_is_ready()` false | generated `zephyr.dts`, `autoconf.h`, node status, compatible, Kconfig symbol | `platform_nordic_zephyr.md`, `linux_device_tree_probe.md`, `dts_probe_check.py`, `kconfig_check.py` | Edit driver before checking generated files |
| ZEP-02 | NCS BLE disconnects when logging enabled | log backend/mode, connection interval, thread priorities, stack, timing window | `platform_nordic_zephyr.md`, `rtos_runtime_debug.md` | Raise log level further |
| ZEP-03 | Overlay edit appears ignored after rebuild | build target, overlay list, generated `zephyr.dts`, CMake cache, board revision | `platform_nordic_zephyr.md` | Assume devicetree parser bug |
| LNX-01 | Linux driver probe never called | booted DTB, compatible, status, driver match table, module load state | `linux_device_tree_probe.md`, `dts_probe_check.py`, `kconfig_check.py` | Add printk inside probe only |
| LNX-02 | Probe deferred forever | `/sys/kernel/debug/devices_deferred`, regulator/clock/pinctrl summaries | `embedded_linux_debug.md`, `linux_log_triage.py` | Force probe order manually |
| LNX-03 | Kernel panic in driver after IRQ enabled | full oops, symbolicated PC/LR, IRQ handler path, resource init order | `linux_trace_observability.md`, `symbolicate_addresses.py` | Guess NULL pointer without symbols |
| LNX-04 | Probe stops after adding `reg` and unit address to DT node | parent bus, `#address-cells`, `#size-cells`, `ranges`, node path in booted DTB | `linux_device_tree_probe.md`, `dts_probe_check.py` | Remove `reg` without checking bus binding |
| LNX-05 | Deferred probe caused by missing supplier driver config | `devices_deferred`, supplier compatible, kernel config, module state | `linux_device_tree_probe.md`, `linux_log_triage.py`, `kconfig_check.py` | Mark regulator always-on first |
| LNX-06 | Board variant boots wrong DTB and device is absent | bootloader env, `/proc/device-tree/model`, booted DTS dump, overlay list | `embedded_linux_debug.md`, `toolchain_sdk_repro.md` | Edit the source DTS again |
| SOC-01 | New i.MX/Rockchip board boots but display panel stays black | booted DTB, panel/bridge endpoints, clocks, regulators, pinctrl, DRM logs | `linux_soc_bsp_debug.md`, `linux_trace_observability.md` | Tune framebuffer app first |
| SOC-02 | Camera probes but no frames arrive | media graph, endpoints, clocks, power rails, CSI/ISP logs, DMA/IOMMU errors | `linux_soc_bsp_debug.md`, `linux_log_triage.py` | Blame sensor exposure settings first |
| BOOT-01 | Kernel waits forever for root device | full boot log, bootargs, root device, storage driver built-in state, DT storage node | `storage_boot_filesystem.md`, `boot_log_timeline.py` | Reformat the card immediately |
| BOOT-02 | Boot time regressed by several seconds | timestamped boot log, service/kernel gap, storage errors, init system logs | `storage_boot_filesystem.md`, `boot_log_timeline.py` | Optimize application startup first |
| FS-01 | Device corrupts config after power cut | filesystem type, write pattern, fsync/rename policy, mount options, storage flush support | `storage_boot_filesystem.md` | Switch filesystems without write protocol analysis |
| FS-02 | UBI attach fails on NAND after field aging | eraseblock size, bad block count, UBI logs, volume layout, power-loss history | `storage_boot_filesystem.md` | Treat NAND as normal block storage |
| PWR-01 | Sleep current is 2 mA instead of 20 uA | measurement setup, debugger attached, rails, GPIO states, external loads, wake sources | `power_low_power_debug.md`, `average_current.py` | Change MCU sleep mode first |
| PWR-02 | Board wakes immediately after suspend | wakeup sources, GPIO interrupt flags, edge polarity, suspend log, stale wake flags | `power_low_power_debug.md` | Disable the wake source permanently |
| PWR-03 | Battery life is much shorter than lab estimate | duty cycle states, radio bursts, peak current, sleep current, battery capacity | `power_low_power_debug.md`, `average_current.py` | Trust datasheet sleep current alone |
| BLE-01 | BLE disconnects only with sensor streaming enabled | disconnect reason, interval, MTU, RSSI, task priorities, DMA/logging load | `connectivity_debug.md`, `rtos_runtime_debug.md` | Increase supervision timeout first |
| WIFI-01 | Wi-Fi connects but cloud TLS fails | association/DHCP/DNS/TCP/TLS stage logs, time sync, cert bundle, heap | `connectivity_debug.md` | Blame RF signal first |
| CELL-01 | LTE-M/NB-IoT modem attaches in lab but fails in field | AT trace, operator/RAT/band, SIM state, APN, power droop, firmware | `connectivity_debug.md` | Retry attach in a loop only |
| OTA-01 | OTA writes successfully but rolls back on reboot | slot state, image valid marker, bootloader log, app validation path | `ota_secure_boot_debug.md` | Disable rollback |
| OTA-02 | Secure boot device cannot downgrade for recovery | secure version, anti-rollback state, key digest/eFuse state, recovery path | `ota_secure_boot_debug.md` | Burn new fuses before reading state |
| OTA-03 | Fleet update bricks one hardware revision | bootloader/partition versions, hardware rev, previous firmware, failure rate, recovery logs | `ota_secure_boot_debug.md`, `toolchain_sdk_repro.md` | Push same image again |
| AI-01 | TFLM arena fails after model update | model op list, arena recording, tensor arena size/alignment, memory region | `tflm_arena_ops.md`, `memory_budget.py` | Just double arena size |
| AI-02 | Model output differs from Python | raw input, firmware input tensor dump, scale/zero-point, golden vector | `tflm_arena_ops.md`, `vector_compare.py` | Retrain model first |
| AI-03 | Inference meets benchmark but misses system period | capture/preprocess/inference/postprocess timings, watchdog, jitter | `latency_watchdog_budget.md`, `latency_budget.py` | Optimize inference only |
| AI-04 | Accelerator output stale after NPU/DMA inference | tensor buffer address, cacheability, accelerator DMA ownership, invalidate timing | `tflm_arena_ops.md`, `dma_cache_coherency.md`, `dma_buffer_check.py` | Blame quantization first |
| TOOL-01 | Same source behaves differently on teammate machine | exact toolchain/SDK/package versions, generated diff, map file | `toolchain_sdk_repro.md`, `map_memory_summary.py` | Clean build only |

Run `scripts/validate_evaluation_scenarios.py` after editing this file. Run `scripts/smoke_test_tools.py` after changing scripts.
