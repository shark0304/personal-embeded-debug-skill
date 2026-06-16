# Debug Recipes

These recipes are quick entry points for common embedded failures. They are intentionally evidence-first: collect the smallest useful artifacts, run deterministic checks, and verify the fix before promoting a root cause.

## Common Flow

```bash
python scripts/project/run_project_triage.py \
  --project-root . \
  --symptom "<short failure statement>"

python scripts/collect/validate_debug_packet.py \
  --packet debug/debug_packet.yaml \
  --format markdown

python scripts/analyze/match_failure_patterns.py \
  --packet debug/debug_packet.yaml \
  --format markdown

python scripts/verify/generate_fix_verification_plan.py \
  --packet debug/debug_packet.yaml \
  --hypothesis "<candidate root cause>"
```

## Recipes

| Symptom | Evidence to collect | Commands to run | Fix verification |
|---|---|---|---|
| Cortex-M HardFault or BusFault | CFSR/HFSR/BFAR/MMFAR, stacked PC/LR/xPSR, exact ELF/map | `fault_analyzer.py`, `symbolicate_addresses.py`, `map_memory_summary.py` | Same fault no longer appears; PC resolves to expected code path; regression packet includes registers and ELF/map |
| Zephyr I2C sensor probe failed | `serial.log`, generated `zephyr.dts`, `.config`, board overlay, optional logic trace | `analyze_i2c_init_failure.py`, `dts_probe_check.py`, `kconfig_check.py`, `i2c_pullup_check.py` | Probe succeeds from cold boot; DTS/Kconfig evidence matches intended bus/address; trace shows ACK |
| ESP-IDF panic or WDT | full monitor log from reset, `sdkconfig`, partition table, ELF/map | `esp_panic_parse.py`, `map_memory_summary.py` | Backtrace no longer repeats; task watchdog budget is measured; exact firmware image is preserved |
| FreeRTOS deadlock or priority inversion | task snapshot, stack high-water marks, heap status, blocked resource, ISR priorities | `rtos_snapshot_check.py`, `freertos_wait_graph.py`, `nvic_priority_check.py` | Blocking graph is removed or bounded; high-priority task resumes under load; regression snapshot is saved |
| DMA/cache corruption | buffer address/size/region, cache-line size, maintenance calls, map file, before/after capture | `dma_buffer_check.py`, `map_memory_summary.py` | Corruption disappears with correct alignment/maintenance; polling and interrupt paths agree |
| Embedded Linux driver probe defer | boot log, full `dmesg`, DTS/DTB, kernel config, driver name, bus path | `linux_log_triage.py`, `dts_probe_check.py`, `boot_log_timeline.py` | Probe succeeds without repeated defer; dependency provider appears before consumer |
| TinyML arena overflow or latency miss | model file, op resolver, arena size, map file, latency samples, golden vectors | `memory_budget.py`, `latency_budget.py`, `vector_compare.py` | Arena margin is measured; latency p95 fits period/watchdog; vector parity is within tolerance |
| UART baud mismatch | clock tree, divisor, oversampling, expected baud, serial capture | `uart_baud_check.py` | Measured baud error is inside receiver tolerance; log corruption disappears |
| I2C rise-time or pull-up issue | pull-up values, bus capacitance estimate, target speed, logic/scope trace | `i2c_pullup_check.py`, `analyze_i2c_logic_trace.py` | Rise time fits mode budget; NACK/timeout rate drops under repeated boot |
| Low-power current drift | duty cycle, state currents, wake source, rail measurement method | `average_current.py` plus low-power runbook | Average current matches budget under repeated sleep/wake cycles |

## Output Contract

Each recipe should end with:

- Evidence packet updated.
- Hypothesis table ranked by evidence for/against.
- One minimal fix candidate at a time.
- Verification observation defined before the fix is accepted.
- Golden packet or regression note preserved after resolution.
