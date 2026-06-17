---
name: embedded-debug
description: Advanced Embedded Failure Intelligence Workbench. Use when helping embedded engineers with evidence-driven Cortex-M/RTOS fault triage, DMA/cache coherency, Zephyr/ESP-IDF, embedded Linux board/driver bring-up, boot/OTA, low power, datasheet/register review, TinyML deployment debugging, project onboarding, bring-up readiness scoring, evidence capture planning, project memory, failure notebook lifecycle tracking, failure pattern matching, public embedded project mining, debug report review, or fix verification planning. Prefer reproducible debug packets, runbooks, verifiable hypotheses, and regression-ready reports.
---

# Embedded Debug

Advanced Embedded Debug Workbench is evidence-first: collect the smallest decisive artifacts, rank hypotheses with verification steps, then preserve resolved cases as notebooks or golden packets.

Use this skill for focused workflows where generic advice is not enough:

1. Cortex-M/RTOS crash and fault triage.
2. RTOS runtime debugging: stack, heap, scheduling, deadlock, priority inversion, ISR-to-task paths.
3. DMA/cache coherency and MCU peripheral bring-up.
4. Datasheet/register review.
5. Embedded Linux board bring-up: boot logs, device tree, driver probe, deferred probe, kernel tracing.
6. TinyML deployment debugging for memory, latency, quantization, and input pipeline issues.
7. Toolchain/SDK reproducibility when build or debugger state is suspect.

Do not use it as a general embedded encyclopedia, desktop Linux administration guide, PCB/RF guide, AUTOSAR workflow, or generic C tutorial.

## First Response Checklist

Before giving conclusions, identify what evidence is available:

- MCU/SoC/module part number and board revision.
- Toolchain, SDK/HAL/RTOS, debugger/probe, and build mode.
- Symptom, expected behavior, actual behavior, and last known good change.
- Logs, fault registers, register dumps, waveforms, code, or datasheet pages.
- Power/clock/reset/boot mode constraints when hardware behavior is involved.
- DMA buffer address/size/memory region/cache state when interrupt or DMA behavior differs from polling.
- RTOS interrupt priorities and ISR API use when a crash involves queues, semaphores, or callbacks.
- RTOS task/thread snapshot, stack high-water marks, heap status, and blocked resource when runtime behavior is involved.
- For embedded Linux: bootloader/kernel version, DTB/DTS, kernel config, full `dmesg`, driver/module name, bus path, and relevant sysfs/debugfs paths.

If critical context is missing, ask for the smallest useful artifact next, not a broad list.

For complex or multi-layer issues, first suggest generating or completing a debug packet:

```text
python scripts/project/run_project_triage.py --project-root . --symptom "<short failure statement>"
python scripts/project/detect_project_context.py --project-root . --format markdown
python scripts/collect/collect_debug_packet.py --project-root . --platform auto --out /tmp/debug_packet.yaml
```

## Operating Rules

- Do not invent register addresses, bit meanings, timing limits, or electrical limits.
- For datasheet/reference-manual claims, cite the user-provided section/page/table when available.
- Distinguish evidence from hypothesis. Prefer testable checks over confident guesses.
- Warn before suggesting risky actions involving voltage rails, current limits, clocks, fuses/option bytes, flash erase, boot pins, or irreversible provisioning.
- When code changes are requested, keep patches small and add diagnostics that can be removed later.
- For TinyML work, check firmware preprocessing, quantization, memory, latency, power, and golden-vector parity.
- Do not claim a confirmed root cause unless a verification step exists.
- Do not ignore toolchain, SDK, board revision, or last known good state.
- Do not treat a workaround as the root cause.
- Do not locate a Cortex-M PC without matching ELF/map evidence.
- Do not decide Zephyr or Linux driver state without generated DTS/DTB and Kconfig evidence.

## Core Workflow

1. Normalize the problem statement, platform, and failure archetype.
2. For complex cases, collect or update a debug packet and list missing evidence.
3. Read core contracts before making strong claims:
   - Evidence first: `references/core/evidence_first.md`
   - Hypothesis ranking: `references/core/hypothesis_ranking.md`
   - Debug report contract: `references/core/debug_report_contract.md`
4. Route to a runbook when the domain is clear:
   - Cortex-M HardFault: `references/runbooks/cortexm_hardfault_runbook.md`
   - FreeRTOS deadlock/starvation: `references/runbooks/freertos_deadlock_runbook.md`
   - DMA/cache corruption: `references/runbooks/dma_cache_corruption_runbook.md`
   - Zephyr DTS/Kconfig: `references/runbooks/zephyr_dts_kconfig_runbook.md`
   - Zephyr sensor bring-up/I2C probe: `references/runbooks/zephyr_sensor_bringup_runbook.md`
   - ESP-IDF panic/WDT: `references/runbooks/espidf_panic_runbook.md`
   - Linux driver probe: `references/runbooks/linux_driver_probe_runbook.md`
   - Boot/rootfs failure: `references/runbooks/boot_failure_runbook.md`
   - OTA/MCUboot: `references/runbooks/ota_mcuboot_runbook.md`
   - TinyML memory/latency: `references/runbooks/tinyml_latency_memory_runbook.md`
   - Low power: `references/runbooks/low_power_runbook.md`
   - Field diagnostics: `references/runbooks/field_diagnostics_runbook.md`
5. Apply v3 routing when artifacts imply a workflow:
   - Real project directory being connected for the first time: run `scripts/project/onboard_project.py` to create project memory, adapter packet, readiness report, and local debug workspace notes.
   - Real project directory before risky board actions: run `scripts/project/score_bringup_readiness.py`, then prefer `scripts/project/run_project_triage.py` for a safe first pass. If the project should remember board/toolchain/recovery facts, create `.embedded-debug.yml` with `scripts/project/init_project_memory.py`.
   - Existing packet needs the next capture point: run `scripts/project/suggest_evidence_capture.py` to choose removable instrumentation or lab capture templates.
   - Failure case needs team handoff: create `debug/failure-notebook/<case>/` with `scripts/project/create_failure_notebook.py`, then advance status with `scripts/project/update_failure_case.py`.
   - Public repository mining for adapter coverage: use `scripts/research/mine_github_projects.py`, `scripts/research/score_embedded_relevance.py`, `scripts/research/fetch_project_snapshot.py`, `scripts/research/extract_project_signals.py`, and `scripts/research/build_project_corpus.py`; keep outputs under ignored `research/project_corpus/`.
   - Existing packet needs likely-pattern ranking: run `scripts/analyze/match_failure_patterns.py`.
   - Proposed fix or hypothesis needs proof: run `scripts/verify/generate_fix_verification_plan.py`.
   - Manual handoff: run `scripts/project/detect_project_context.py`, optionally generate `debug/embedded_debug_adapter/` with `scripts/project/create_project_adapter.py`, then run `scripts/collect/collect_debug_packet.py`.
   - Zephyr project or Twister need: generate or parse CI with `scripts/ci/generate_twister_case.py` and `scripts/ci/parse_twister_report.py`.
   - ESP-IDF project: generate or parse pytest-embedded with `scripts/ci/generate_pytest_embedded_case.py` and `scripts/ci/parse_pytest_embedded_report.py`.
   - Renode simulation request: use `scripts/ci/generate_renode_robot_test.py` and `scripts/ci/parse_renode_report.py`.
   - Linux driver/dmesg: route to `linux_driver_probe_runbook.md`.
   - Field device logs: route to `field_diagnostics_runbook.md`.
   - "Verify the fix": create a regression packet or CI/HIL case.
   - Debug report review: score it with `scripts/review/review_debug_report.py` for handoff discipline or `scripts/verify/score_debug_report.py` for legacy report-contract checks.
   - Zephyr sensor init failed, LSM6DSL/LSM6DS3/IMU init failed, I2C sensor not ready, WHO_AM_I failure, NACK, or sensor probe timeout: route first to `references/runbooks/zephyr_sensor_bringup_runbook.md` and run `scripts/analyze/analyze_i2c_init_failure.py` when serial log, DTS, and config are available.
   - I2C logic analyzer CSV: run `scripts/analyze/analyze_i2c_logic_trace.py` and keep the capture in the debug packet.
6. When the failure shape is unclear, read `references/case_archetypes.md` before ranking causes.
7. Build a ranked root-cause table using `hypothesis_id`, confidence, evidence for/against, missing evidence, verification step, expected observation, and fix if confirmed.
8. Read legacy references only as needed:
   - Cortex-M/RTOS crash triage: `references/cortex_m_faults.md`
   - FreeRTOS/Cortex-M interrupt priority sanity: `references/rtos_irq_priority.md`
   - RTOS runtime, scheduler, and synchronization debug: `references/rtos_runtime_debug.md`
   - MCU peripheral bring-up: `references/peripheral_bringup.md`
   - UART/I2C signal sanity: `references/uart_i2c_signal_debug.md`
   - DMA/cache coherency: `references/dma_cache_coherency.md`
   - Datasheet/register review: `references/datasheet_register_review.md`
   - Embedded Linux boot and runtime debug: `references/embedded_linux_debug.md`
   - Linux device tree and driver probe debug: `references/linux_device_tree_probe.md`
   - GDB, debug probe, and fault-frame evidence capture: `references/debug_probe_gdb.md`
   - Linux tracing, dynamic debug, and debugfs observability: `references/linux_trace_observability.md`
   - Storage, boot, and filesystem debug: `references/storage_boot_filesystem.md`
   - Low-power, suspend/resume, and wake debug: `references/power_low_power_debug.md`
   - BLE, Wi-Fi, and cellular connectivity debug: `references/connectivity_debug.md`
   - OTA, secure boot, anti-rollback, and provisioning debug: `references/ota_secure_boot_debug.md`
   - Linux SoC BSP and board-port debug: `references/linux_soc_bsp_debug.md`
   - Personal engineer profile and project dossier workflow: `references/personal_workflow.md`
   - Problem-specific intake forms: `references/problem_intake_forms.md`
   - Real-world failure archetypes and evidence prompts: `references/case_archetypes.md`
   - Evaluation scenarios for checking skill behavior: `references/evaluation_scenarios.md`
   - Evidence capture templates and when to use them: `references/evidence_capture_templates.md`
   - STM32 platform debug pack: `references/platform_stm32.md`
   - ESP32/ESP-IDF platform debug pack: `references/platform_esp32.md`
   - Nordic/nRF Connect SDK and Zephyr debug pack: `references/platform_nordic_zephyr.md`
   - TinyML deployment debug: `references/tinyml_deployment.md`
   - TFLite Micro arena/operator/quantization debug: `references/tflm_arena_ops.md`
   - Embedded AI latency/watchdog budget: `references/latency_watchdog_budget.md`
   - Toolchain, SDK, generated-code, and debugger-pack drift: `references/toolchain_sdk_repro.md`
9. Use platform packs when the target is clearly STM32, ESP32/ESP-IDF, Nordic/nRF Connect SDK/Zephyr, TI C2000, or Linux SoC BSP.
10. Use scripts for deterministic calculations:
   - `scripts/collect/collect_debug_packet.py` for reproducible debug packet collection.
   - `scripts/collect/validate_debug_packet.py` for evidence completeness scoring and missing-evidence checks.
   - `scripts/project/detect_project_context.py` for detecting Zephyr, ESP-IDF, PlatformIO, STM32Cube, Arduino, bare-metal CMake/Make, embedded Linux, FreeRTOS, and TinyML project context before collecting evidence.
   - `scripts/project/onboard_project.py` for first-time project onboarding: project memory, adapter packet, readiness report, and `debug/README.md`.
   - `scripts/project/create_project_adapter.py` for writing a project-local adapter packet with evidence globs, suggested commands, runbooks, deterministic scripts, and risk labels.
   - `scripts/project/run_project_triage.py` for safe end-to-end project triage: detect context, collect packet metadata, score evidence, and write a triage report without running hardware-changing commands.
   - `scripts/project/init_project_memory.py` for creating a local `.embedded-debug.yml` with board/toolchain/recovery facts.
   - `scripts/project/score_bringup_readiness.py` for checking board identity, toolchain, safe commands, recovery path, and first evidence before bring-up or risky debug actions.
   - `scripts/project/suggest_evidence_capture.py` for recommending evidence-capture templates and removable instrumentation from a packet or symptom.
   - `scripts/project/create_failure_notebook.py` for preserving a local failure case record, packet, evidence score, hypotheses, and outcome.
   - `scripts/project/update_failure_case.py` for failure-case lifecycle states and optional golden-packet candidate export.
   - `scripts/review/review_debug_report.py` for checking reports for evidence discipline, unsupported certainty, missing verification, and handoff readiness.
   - `scripts/research/mine_github_projects.py` for rate-limited public GitHub repository candidate discovery through official API or fixtures.
   - `scripts/research/score_embedded_relevance.py` for ranking candidate repositories by embedded-project signals.
   - `scripts/research/fetch_project_snapshot.py` for manifest-only public project snapshots without default full clones.
   - `scripts/research/extract_project_signals.py` for running adapter detection on snapshots.
   - `scripts/research/build_project_corpus.py` for producing CSV/JSONL project corpus indexes.
   - `scripts/analyze/match_failure_patterns.py` for ranking bundled failure patterns against packet evidence.
   - `scripts/verify/generate_fix_verification_plan.py` for defining before/after evidence, acceptance criteria, and non-evidence for a proposed fix.
   - `scripts/reports/generate_debug_report.py` for markdown debug reports.
   - `scripts/verify/run_skill_regression.py` for golden packet fixture checks.
   - `scripts/verify/score_debug_report.py` for report quality scoring.
   - `scripts/fault_analyzer.py` for Cortex-M fault registers.
   - `scripts/symbolicate_addresses.py` for ELF address-to-source lookup commands/results.
   - `scripts/bitfield_decode.py` for register bitfield decoding.
   - `scripts/register_write_check.py` for reserved-bit, preserve-mask, and W1C write review.
   - `scripts/rtos_snapshot_check.py` for task/thread stack and blocked-state snapshot review.
   - `scripts/linux_log_triage.py` for dmesg/kernel log pattern triage.
   - `scripts/boot_log_timeline.py` for boot log timestamp gap analysis.
   - `scripts/dts_probe_check.py` for DTS/devicetree node, compatible, status, and required-property checks.
   - `scripts/kconfig_check.py` for `.config` or `autoconf.h` symbol checks.
   - `scripts/esp_panic_parse.py` for ESP-IDF panic/WDT/backtrace log parsing.
   - `scripts/map_memory_summary.py` for GNU ld map section summaries.
   - `scripts/freertos_wait_graph.py` for RTOS resource wait and priority inversion checks.
   - `scripts/profile_dossier_check.py` for personal profile and project dossier completeness checks.
   - `scripts/average_current.py` for low-power duty-cycle current budget estimates.
   - `scripts/memory_budget.py` for Flash/RAM/model sizing.
   - `scripts/dma_buffer_check.py` for cache-line alignment and DMA maintenance span checks.
   - `scripts/nvic_priority_check.py` for FreeRTOS/Cortex-M ISR priority checks.
   - `scripts/uart_baud_check.py` for UART clock/divisor error budgets.
   - `scripts/i2c_pullup_check.py` for I2C pull-up and rise-time sanity checks.
   - `scripts/vector_compare.py` for TinyML golden-vector comparisons.
   - `scripts/latency_budget.py` for sensor/preprocess/inference/postprocess period and watchdog budgets.
   - `scripts/analyze/analyze_i2c_init_failure.py` for Zephyr I2C sensor probe logs plus DTS/Kconfig evidence.
   - `scripts/analyze/analyze_i2c_logic_trace.py` for decoded or raw I2C logic analyzer CSV checks.
11. Return a concise report following `references/core/debug_report_contract.md`; it should score at least 80 with `score_debug_report.py`.

Use assets under `assets/templates/` when the user asks for instrumentation, project setup, issue recording, or when a small evidence-capture patch would unblock diagnosis.

## Output Shape

For Cortex-M/RTOS crash triage:

```text
Observed
- ...

Fault evidence
- CFSR/HFSR:
- Stacked PC/LR/xPSR:

Most likely causes
1. ...

Evidence to collect
- ...

Next checks
1. ...

Fix candidates
- ...
```

For peripheral/datasheet work:

```text
Relevant datasheet evidence
- Section/table/page: ...

Register or timing interpretation
- ...

Driver implications
- ...

Unverified assumptions
- ...
```

For embedded Linux:

```text
Layer
- Boot / device tree / probe / runtime / userspace:

Kernel evidence
- dmesg line:
- DT node / compatible:
- driver/module:

Most likely causes
1. ...

Next kernel-visible checks
1. ...

Fix candidates
- ...
```

For TinyML:

```text
Deployment budget
- Flash:
- RAM:
- Latency:
- Input pipeline:

Risks
- ...

Validation plan
- ...
```
