# {{project_name}} Project Plan

## Project Goal

{{project_goal}}

## Board

- Target board: {{board}}
- Board revision: TBD
- Debug probe: {{debug_probe}}

## Sensor / Peripheral

- Device: {{peripheral}}
- Interface: {{interface}}
- Critical signals: power, ground, clock, bus pins, interrupt/reset/enable pins

## Toolchain

- SDK/framework: {{toolchain}}
- Build system: {{build_system}}
- Flash/debug path: {{flash_debug_path}}

## Milestones

| Milestone | Evidence | Exit Criteria |
| --- | --- | --- |
| Environment boots | toolchain version, build log | clean build or documented build failure |
| Board flashes | flash log, serial banner | firmware starts and prints version |
| Bus is alive | scan/read transaction, logic trace if needed | expected device address or ID observed |
| Minimal driver works | ID read, basic register read/write | stable polling path |
| Feature path works | interrupt/FIFO/DMA/NPU/control loop evidence | expected data rate and error budget |
| Regression is captured | script, packet, or CI/HIL case | failure can be reproduced or guarded |

## Risks

- Unknown board revision, strap, or alternate pin mux.
- Datasheet timing requirement missed during init.
- SDK/Kconfig/devicetree option silently disables the intended path.
- Bus-level fault hidden by driver-level logs.
- Power, clock, cache, DMA, or interrupt priority issue appears only under load.

## Validation Criteria

- Build command and exact SDK/toolchain version recorded.
- Flash command recorded and reproducible.
- Serial log includes firmware version, board, and bring-up status.
- Bus-level validation exists for the first device transaction.
- Timing and power assumptions have evidence when they affect correctness.
- A regression packet or test case exists for any confirmed failure.

## Debug Handoff Condition

Hand off to `$embedded-debug` when:

- build, flash, boot, probe, bus, fault, latency, memory, or data-integrity validation fails
- the next conclusion would depend on missing logs, ELF/map, DTS/Kconfig, dmesg, waveform, or board revision evidence
- a candidate root cause needs a ranked hypothesis report before changing design
