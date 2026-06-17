# Real Project Adapters

Project adapters let Embedded Debug Workbench enter a real firmware or BSP repository without guessing the workflow.

They do four conservative things:

1. Detect likely project families from local files.
2. Generate a local debug adapter packet with evidence globs, suggested commands, runbooks, and deterministic scripts.
3. Mark risky commands such as flash, debugger attach, and kernel runtime changes before anyone runs them.
4. Score whether board identity, toolchain, recovery path, safe commands, and first logs are ready for bring-up.

They do not run hardware-changing commands, fetch metadata from the network, or claim a root cause.

## Quick Start

From the root of a firmware or BSP project:

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/onboard_project.py \
  --project-root . \
  --symptom "short failure statement" \
  --overwrite
```

The onboarding command creates or updates `.embedded-debug.yml`, writes an adapter packet under `debug/onboarding/`, scores bring-up readiness, and creates `debug/README.md` for local engineering artifacts.

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/init_project_memory.py \
  --project-root . \
  --overwrite
```

Check readiness before flashing, debugger attach, or kernel-runtime experiments:

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/score_bringup_readiness.py \
  --project-root . \
  --format markdown
```

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/run_project_triage.py \
  --project-root . \
  --symptom "short failure statement"
```

After triage, ask for the next evidence-capture patch or lab capture plan:

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/suggest_evidence_capture.py \
  --packet debug/debug_packet.yaml \
  --symptom "short failure statement" \
  --format markdown
```

Or run the adapter steps manually:

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/detect_project_context.py \
  --project-root . \
  --format markdown
```

Create a project-local adapter packet:

```bash
python /path/to/personal-embeded-debug-skill/scripts/project/create_project_adapter.py \
  --project-root . \
  --out-dir debug/embedded_debug_adapter \
  --overwrite
```

Then collect the normal debug packet:

```bash
python /path/to/personal-embeded-debug-skill/scripts/collect/collect_debug_packet.py \
  --project-root . \
  --platform auto \
  --out debug_packet.yaml
```

Score the packet before promoting a root cause:

```bash
python /path/to/personal-embeded-debug-skill/scripts/collect/validate_debug_packet.py \
  --packet debug_packet.yaml \
  --format markdown
```

Rank bundled failure patterns and generate a proof plan:

```bash
python /path/to/personal-embeded-debug-skill/scripts/analyze/match_failure_patterns.py \
  --packet debug/debug_packet.yaml \
  --format markdown

python /path/to/personal-embeded-debug-skill/scripts/verify/generate_fix_verification_plan.py \
  --packet debug/debug_packet.yaml \
  --hypothesis "candidate root cause"
```

Review a report before handoff and move a notebook through its lifecycle:

```bash
python /path/to/personal-embeded-debug-skill/scripts/review/review_debug_report.py \
  --report debug/project_triage_report.md \
  --format markdown

python /path/to/personal-embeded-debug-skill/scripts/project/update_failure_case.py \
  --case-dir debug/failure-notebook/<case-id> \
  --status verified \
  --verification "before/after evidence matches"
```

## Supported Project Families

| Adapter | Signals | Typical next evidence |
|---|---|---|
| Zephyr / nRF Connect SDK | `west.yml`, `prj.conf`, generated `zephyr.dts`, `.config` | build log, serial log, generated DTS/Kconfig, I2C traces |
| ESP-IDF | `sdkconfig`, `idf_component.yml`, `idf_component_register` | monitor log, SDK config, partition table, ELF/map |
| PlatformIO | `platformio.ini` | selected environment, `.pio` ELF/map, serial log |
| STM32Cube | `.ioc`, `Core/Src`, `Drivers/CMSIS` | CubeMX `.ioc`, linker script, ELF/map, fault registers |
| Arduino | `.ino` | FQBN, serial log, core/package versions |
| Bare-metal CMake | `CMakeLists.txt`, linker/startup files | toolchain file, build log, ELF/map |
| Bare-metal Make | `Makefile`, linker/startup files | build log, target list, ELF/map |
| Embedded Linux | `Kbuild`, `Kconfig`, DTS/DTSI, module markers | boot log, dmesg, kernel config, DTS/DTB |
| FreeRTOS | `FreeRTOSConfig.h`, kernel sources | task snapshot, heap/stack state, ISR priorities |
| TinyML | `.tflite`, TFLite Micro source/model files | model, arena size, op resolver, latency and golden vectors |

## Risk Labels

| Label | Meaning |
|---|---|
| `safe-local-build` | Local build/configure action; does not touch target hardware. |
| `safe-local-test` | Local tests or build-only validation. |
| `host-io` | Reads logs or opens a host/serial connection. |
| `debugger-attached` | May halt, reset, or inspect target hardware. |
| `hardware-write` | Writes flash or changes target nonvolatile state. |
| `kernel-runtime-change` | Changes a running Linux target; needs rollback. |

## Practical Flow

```mermaid
flowchart LR
    A["Real project"] --> B["Onboard project"]
    B --> C["Load project memory"]
    C --> D["Score bring-up readiness"]
    D --> E["Detect adapter"]
    E --> F["Score evidence"]
    F --> G["Suggest capture"]
    G --> H["Match failure patterns"]
    H --> I["Review report"]
    I --> J["Track case lifecycle"]
    J --> K["Export golden candidate"]
```

Keep the adapter packet in the project `debug/` directory when it helps team handoff. Do not commit logs or captures that contain secrets, customer data, proprietary firmware blobs, or private board identifiers unless your project policy allows it.
