#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


MAX_SCAN_FILES = 5000


@dataclass(frozen=True)
class CommandSpec:
    name: str
    command: str
    risk: str
    note: str


@dataclass(frozen=True)
class AdapterSpec:
    adapter_id: str
    label: str
    detector: str
    evidence_patterns: tuple[str, ...]
    artifact_globs: tuple[str, ...]
    safe_commands: tuple[CommandSpec, ...]
    recommended_scripts: tuple[str, ...]
    runbooks: tuple[str, ...]
    next_steps: tuple[str, ...]


ADAPTERS: tuple[AdapterSpec, ...] = (
    AdapterSpec(
        adapter_id="zephyr",
        label="Zephyr / nRF Connect SDK",
        detector="west, prj.conf, generated devicetree/Kconfig artifacts",
        evidence_patterns=("west.yml", "prj.conf", "boards/**/*.overlay", "boards/**/*.conf", "app.overlay", "build/zephyr/zephyr.dts", "build/zephyr/.config"),
        artifact_globs=("build.log", "serial.log", "prj.conf", "boards/**/*.overlay", "*.overlay", "build/zephyr/zephyr.dts", "build/zephyr/.config", "build/zephyr/zephyr.elf", "build/zephyr/zephyr.map"),
        safe_commands=(
            CommandSpec("build", "west build -b <board> .", "safe-local-build", "Replace <board> with the exact board target."),
            CommandSpec("twister", "west twister -T tests -p <board>", "safe-local-test", "Runs local test build cases when tests/ exists."),
            CommandSpec("flash", "west flash", "hardware-write", "Requires the correct target board and confirmation before execution."),
            CommandSpec("serial", "west espressif monitor || minicom -D <serial-port>", "host-io", "Use the monitor that matches the connected probe or UART."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform zephyr --out debug_packet.yaml",
            "scripts/dts_probe_check.py --dts build/zephyr/zephyr.dts --node <node>",
            "scripts/kconfig_check.py --config build/zephyr/.config --require CONFIG_<SYMBOL>=y",
            "scripts/analyze/analyze_i2c_init_failure.py --serial-log serial.log --dts build/zephyr/zephyr.dts --config build/zephyr/.config",
        ),
        runbooks=("references/runbooks/zephyr_dts_kconfig_runbook.md", "references/runbooks/zephyr_sensor_bringup_runbook.md"),
        next_steps=("Capture the exact board target used for the failing build.", "Keep generated zephyr.dts and .config with the serial log.", "For sensor failures, add a short I2C logic trace if available."),
    ),
    AdapterSpec(
        adapter_id="esp-idf",
        label="ESP-IDF",
        detector="sdkconfig, idf_component.yml, idf_component_register",
        evidence_patterns=("sdkconfig", "sdkconfig.defaults", "idf_component.yml", "components/**/CMakeLists.txt"),
        artifact_globs=("build.log", "monitor.log", "serial.log", "sdkconfig", "sdkconfig.defaults", "partitions*.csv", "build/*.elf", "build/*.map", "build/bootloader/*.elf"),
        safe_commands=(
            CommandSpec("build", "idf.py build", "safe-local-build", "Uses the active ESP-IDF environment."),
            CommandSpec("size", "idf.py size", "safe-local-inspection", "Summarizes image and RAM footprint."),
            CommandSpec("flash", "idf.py -p <serial-port> flash", "hardware-write", "Writes flash; verify chip, port, and boot mode first."),
            CommandSpec("monitor", "idf.py -p <serial-port> monitor", "host-io", "Captures panic, WDT, boot, and reset logs."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform esp-idf --out debug_packet.yaml",
            "scripts/esp_panic_parse.py --log serial.log",
            "scripts/memory_budget.py --flash <bytes> --ram <bytes> --model <bytes> --arena <bytes>",
            "scripts/ci/generate_pytest_embedded_case.py --help",
        ),
        runbooks=("references/runbooks/espidf_panic_runbook.md", "references/platform_esp32.md"),
        next_steps=("Save full monitor output from reset through failure.", "Preserve sdkconfig and partition table with the debug packet.", "For WDT/panic, capture decoded backtrace or ELF/map."),
    ),
    AdapterSpec(
        adapter_id="platformio",
        label="PlatformIO",
        detector="platformio.ini",
        evidence_patterns=("platformio.ini",),
        artifact_globs=("platformio.ini", ".pio/build/*/*.elf", ".pio/build/*/*.map", "build.log", "serial.log", "src/**/*", "include/**/*"),
        safe_commands=(
            CommandSpec("build", "pio run", "safe-local-build", "Builds configured environments."),
            CommandSpec("test", "pio test", "safe-local-test", "Runs available PlatformIO tests."),
            CommandSpec("upload", "pio run -t upload", "hardware-write", "Writes firmware to the connected target."),
            CommandSpec("monitor", "pio device monitor", "host-io", "Captures serial logs."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform cortex-m --out debug_packet.yaml",
            "scripts/map_memory_summary.py --map .pio/build/<env>/*.map",
            "scripts/symbolicate_addresses.py --elf .pio/build/<env>/*.elf --addr <pc> --dry-run",
        ),
        runbooks=("references/toolchain_sdk_repro.md", "references/debug_probe_gdb.md"),
        next_steps=("Identify the failing PlatformIO environment.", "Keep .pio build ELF/map artifacts if crash addresses are involved.", "Record upload and monitor logs separately."),
    ),
    AdapterSpec(
        adapter_id="stm32cube",
        label="STM32Cube / STM32CubeIDE",
        detector=".ioc, Core/Src, Drivers/CMSIS",
        evidence_patterns=("*.ioc", "Core/Src/main.c", "Core/Inc/main.h", "Drivers/CMSIS/**", ".project", ".cproject"),
        artifact_globs=("*.ioc", "Core/Src/**/*", "Core/Inc/**/*", "Drivers/CMSIS/**/*", "*.ld", "Debug/*.elf", "Debug/*.map", "Release/*.elf", "Release/*.map", "build.log", "fault*.txt", "serial.log"),
        safe_commands=(
            CommandSpec("cmake-build", "cmake --build build", "safe-local-build", "Use when the Cube project was exported to CMake."),
            CommandSpec("make-build", "make", "safe-local-build", "Use for Makefile exports."),
            CommandSpec("debug-server", "openocd -f <interface.cfg> -f <target.cfg>", "debugger-attached", "Attaches to hardware; confirm target voltage and reset behavior."),
            CommandSpec("flash", "STM32_Programmer_CLI -c port=<probe> -w <firmware.elf>", "hardware-write", "Writes flash; confirm option bytes and target first."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform cortex-m --out debug_packet.yaml",
            "scripts/fault_analyzer.py --cfsr <hex> --hfsr <hex>",
            "scripts/map_memory_summary.py --map <firmware.map>",
            "scripts/register_write_check.py --help",
        ),
        runbooks=("references/platform_stm32.md", "references/runbooks/cortexm_hardfault_runbook.md", "references/peripheral_bringup.md"),
        next_steps=("Save the .ioc file because it is generated-code evidence.", "Pair HardFault registers with the exact ELF/map from the failing build.", "For peripheral bring-up, capture RCC/GPIO/alternate-function register state."),
    ),
    AdapterSpec(
        adapter_id="arduino",
        label="Arduino / arduino-cli",
        detector=".ino sketch files",
        evidence_patterns=("*.ino",),
        artifact_globs=("*.ino", "libraries/**/*", "build.log", "serial.log", "*.elf", "*.map"),
        safe_commands=(
            CommandSpec("compile", "arduino-cli compile --fqbn <fqbn> .", "safe-local-build", "Requires a fully qualified board name."),
            CommandSpec("upload", "arduino-cli upload -p <serial-port> --fqbn <fqbn> .", "hardware-write", "Writes firmware to the selected board."),
            CommandSpec("monitor", "arduino-cli monitor -p <serial-port>", "host-io", "Captures serial output."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform cortex-m --out debug_packet.yaml",
            "scripts/uart_baud_check.py --clock <clock> --baud <baud>",
            "scripts/i2c_pullup_check.py --pullup <ohms> --capacitance-pf <pf>",
        ),
        runbooks=("references/uart_i2c_signal_debug.md", "references/peripheral_bringup.md"),
        next_steps=("Record board FQBN and core package version.", "Capture serial output from boot to failure.", "For bus failures, keep wiring, pull-up, and logic analyzer evidence."),
    ),
    AdapterSpec(
        adapter_id="cmake-baremetal",
        label="Bare-metal CMake",
        detector="CMakeLists.txt with linker/startup embedded artifacts",
        evidence_patterns=("CMakeLists.txt",),
        artifact_globs=("CMakeLists.txt", "*.ld", "startup_*.s", "startup_*.S", "build/**/*.elf", "build/**/*.map", "build.log", "fault*.txt", "serial.log"),
        safe_commands=(
            CommandSpec("configure", "cmake -S . -B build", "safe-local-build", "Configure with the active toolchain file if needed."),
            CommandSpec("build", "cmake --build build", "safe-local-build", "Builds the firmware image."),
            CommandSpec("debug", "arm-none-eabi-gdb build/<firmware>.elf", "debugger-attached", "May attach to hardware depending on the target config."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform cortex-m --out debug_packet.yaml",
            "scripts/map_memory_summary.py --map build/<firmware>.map",
            "scripts/symbolicate_addresses.py --elf build/<firmware>.elf --addr <pc> --dry-run",
        ),
        runbooks=("references/cortex_m_faults.md", "references/debug_probe_gdb.md", "references/toolchain_sdk_repro.md"),
        next_steps=("Record the toolchain file and compiler version.", "Keep linker script, startup file, ELF, and map together.", "For crashes, capture fault registers before reset."),
    ),
    AdapterSpec(
        adapter_id="make-baremetal",
        label="Bare-metal Make",
        detector="Makefile plus embedded artifacts",
        evidence_patterns=("Makefile",),
        artifact_globs=("Makefile", "*.mk", "*.ld", "startup_*.s", "startup_*.S", "*.elf", "*.map", "build.log", "fault*.txt", "serial.log"),
        safe_commands=(
            CommandSpec("build", "make", "safe-local-build", "Builds the default target."),
            CommandSpec("clean-build", "make clean && make", "safe-local-build", "Use only when cleaning generated objects is acceptable."),
            CommandSpec("flash", "make flash", "hardware-write", "Common target name, but project-specific and writes firmware."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform cortex-m --out debug_packet.yaml",
            "scripts/map_memory_summary.py --map <firmware.map>",
            "scripts/fault_analyzer.py --cfsr <hex> --hfsr <hex>",
        ),
        runbooks=("references/toolchain_sdk_repro.md", "references/runbooks/cortexm_hardfault_runbook.md"),
        next_steps=("Inspect Makefile targets before running flash/debug targets.", "Capture compiler/linker versions and build log.", "Keep ELF/map from the exact failing binary."),
    ),
    AdapterSpec(
        adapter_id="embedded-linux",
        label="Embedded Linux BSP / Driver",
        detector="Kbuild, Kconfig, device tree, defconfig, module patterns",
        evidence_patterns=("Kbuild", "Kconfig", "arch/**/boot/dts/**/*.dts", "arch/**/configs/*defconfig", "*.dts", "*.dtsi"),
        artifact_globs=("dmesg.log", "boot.log", "*.dts", "*.dtsi", "*.dtb", "Kconfig", "Kbuild", "Makefile", "modules.order", "*.ko", "trace*.txt", "debugfs/**/*", "sysfs/**/*"),
        safe_commands=(
            CommandSpec("module-build", "make -C <kernel-tree> M=$PWD modules", "safe-local-build", "Builds an out-of-tree module when kernel headers are configured."),
            CommandSpec("dtbs", "make dtbs", "safe-local-build", "Builds device tree blobs inside a BSP tree."),
            CommandSpec("insmod", "insmod <module>.ko", "kernel-runtime-change", "Changes kernel runtime state; requires target access and rollback path."),
            CommandSpec("dmesg", "dmesg -T | tee dmesg.log", "host-io", "Captures kernel-visible evidence."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform embedded-linux --out debug_packet.yaml",
            "scripts/linux_log_triage.py --log dmesg.log",
            "scripts/boot_log_timeline.py --log boot.log",
            "scripts/dts_probe_check.py --dts <board>.dts --node <node>",
        ),
        runbooks=("references/runbooks/linux_driver_probe_runbook.md", "references/linux_device_tree_probe.md", "references/linux_trace_observability.md"),
        next_steps=("Capture full dmesg from boot or module insertion.", "Preserve DTS/DTB and kernel config that produced the running image.", "Record compatible string, bus path, and deferred-probe lines."),
    ),
    AdapterSpec(
        adapter_id="freertos",
        label="FreeRTOS",
        detector="FreeRTOSConfig.h and kernel sources",
        evidence_patterns=("FreeRTOSConfig.h", "*/FreeRTOSConfig.h", "**/tasks.c", "**/queue.c", "**/timers.c"),
        artifact_globs=("FreeRTOSConfig.h", "**/FreeRTOSConfig.h", "build.log", "serial.log", "fault*.txt", "*.elf", "*.map", "rtos_snapshot*.json", "rtos_snapshot*.txt"),
        safe_commands=(
            CommandSpec("build", "<project build command>", "safe-local-build", "Use the project build system detected above."),
            CommandSpec("gdb", "arm-none-eabi-gdb <firmware>.elf", "debugger-attached", "Attach only with confirmed target and reset policy."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform freertos --out debug_packet.yaml",
            "scripts/rtos_snapshot_check.py --task <name:prio:state:stack_free:stack_total>",
            "scripts/nvic_priority_check.py --prio-bits <n> --irq-priority <p> --max-syscall-priority <p>",
            "scripts/freertos_wait_graph.py --task <name:prio:state:resource>",
        ),
        runbooks=("references/runbooks/freertos_deadlock_runbook.md", "references/rtos_irq_priority.md", "references/rtos_runtime_debug.md"),
        next_steps=("Capture task list, stack high-water marks, heap state, and blocked resources.", "Check ISR priorities before trusting queue/semaphore symptoms.", "Pair RTOS snapshot with crash/fault registers when available."),
    ),
    AdapterSpec(
        adapter_id="tinyml",
        label="TinyML / TFLite Micro",
        detector="TFLite Micro sources, .tflite model, arena/model files",
        evidence_patterns=("*.tflite", "**/tensorflow/lite/micro/**", "**/micro_mutable_op_resolver*", "**/model.cc", "**/model_data.cc"),
        artifact_globs=("*.tflite", "**/model*.cc", "**/model*.h", "build.log", "serial.log", "*.elf", "*.map", "golden*.csv", "input*.csv", "output*.csv", "latency*.txt"),
        safe_commands=(
            CommandSpec("build", "<project build command>", "safe-local-build", "Use the project build system detected above."),
            CommandSpec("unit-vectors", "<project test command for golden vectors>", "safe-local-test", "Compare firmware outputs to known vectors."),
        ),
        recommended_scripts=(
            "scripts/collect/collect_debug_packet.py --project-root . --platform tinyml --out debug_packet.yaml",
            "scripts/memory_budget.py --flash <bytes> --ram <bytes> --model <bytes> --arena <bytes>",
            "scripts/vector_compare.py --expected expected.txt --actual actual.txt --abs-tol 0.01",
            "scripts/latency_budget.py --period <ms> --component inference:<ms>",
        ),
        runbooks=("references/runbooks/tinyml_latency_memory_runbook.md", "references/tinyml_deployment.md", "references/tflm_arena_ops.md"),
        next_steps=("Keep model, resolver/op list, arena size, and map file together.", "Compare firmware preprocessing against training preprocessing.", "Capture latency distribution, not only one average inference time."),
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect embedded project context and suggest a safe debug adapter.")
    parser.add_argument("--project-root", required=True, help="Project root to inspect.")
    parser.add_argument("--out", help="Optional JSON output path.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format for stdout.")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    context = detect_project_context(root)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(context, indent=2, sort_keys=True), encoding="utf-8")

    if args.format == "markdown":
        print(render_markdown(context))
    else:
        print(json.dumps(context, indent=2, sort_keys=True))


def detect_project_context(root: Path) -> dict[str, object]:
    if not root.exists():
        raise SystemExit(f"project root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"project root is not a directory: {root}")

    files = scan_files(root)
    adapters = []
    for spec in ADAPTERS:
        score, evidence = score_adapter(root, files, spec)
        if score > 0:
            adapters.append(adapter_payload(spec, score, evidence))

    adapters.sort(key=lambda item: (-float(item["confidence"]), str(item["id"])))
    primary = adapters[0]["id"] if adapters else "unknown"
    return {
        "project_root": str(root),
        "detected_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_adapter": primary,
        "adapters": adapters,
        "global_artifact_globs": sorted(set(glob for item in adapters for glob in item["artifact_globs"])),
        "risk_policy": {
            "safe-local-build": "May run locally without touching target hardware.",
            "safe-local-inspection": "Reads or summarizes local build artifacts only.",
            "safe-local-test": "Runs local tests/build checks only.",
            "host-io": "Reads logs or opens a serial/host connection.",
            "debugger-attached": "Requires hardware confirmation before attaching.",
            "hardware-write": "Writes firmware/flash or otherwise changes target state; require explicit confirmation.",
            "kernel-runtime-change": "Changes a running target kernel state; require rollback plan.",
        },
        "next_steps": build_next_steps(adapters),
    }


def scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if len(files) >= MAX_SCAN_FILES:
            break
        if should_skip(path):
            continue
        if path.is_file():
            files.append(path.relative_to(root))
    return files


def should_skip(path: Path) -> bool:
    skip_parts = {".git", ".pio", "node_modules", "__pycache__", ".pytest_cache"}
    return any(part in skip_parts for part in path.parts)


def score_adapter(root: Path, files: list[Path], spec: AdapterSpec) -> tuple[float, list[str]]:
    evidence: list[str] = []
    for pattern in spec.evidence_patterns:
        evidence.extend(match_pattern(files, pattern))

    text_bonus = 0.0
    text_evidence = text_signals(root, files, spec.adapter_id)
    if text_evidence:
        evidence.extend(text_evidence)
        text_bonus = 0.2

    evidence = sorted(set(evidence))
    if not evidence:
        return 0.0, []

    base = min(0.9, 0.35 + 0.12 * len(evidence))
    confidence = min(0.99, base + text_bonus)

    if spec.adapter_id in {"cmake-baremetal", "make-baremetal"}:
        if any(item.startswith("FreeRTOS") for item in evidence):
            confidence -= 0.08
        if any("sdkconfig" in item for item in evidence):
            confidence -= 0.2
    return max(0.1, round(confidence, 2)), evidence


def match_pattern(files: list[Path], pattern: str) -> list[str]:
    normalized = pattern.replace("\\", "/")
    matches: list[str] = []
    for rel_path in files:
        rel = rel_path.as_posix()
        if rel_path.match(normalized) or Path(rel_path.name).match(normalized):
            matches.append(rel)
    return matches


def text_signals(root: Path, files: list[Path], adapter_id: str) -> list[str]:
    candidates = [path for path in files if path.name in {"CMakeLists.txt", "Makefile", "Kbuild", "Kconfig", "FreeRTOSConfig.h", "platformio.ini"}]
    signals: list[str] = []
    for rel_path in candidates[:50]:
        text = read_small_text(root / rel_path)
        if not text:
            continue
        if adapter_id == "esp-idf" and re.search(r"idf_component_register|IDF_PATH|project\.cmake", text):
            signals.append(f"{rel_path}:esp-idf-marker")
        elif adapter_id == "embedded-linux" and re.search(r"\bobj-m\b|modules_install|CONFIG_OF\b|dtb-", text):
            signals.append(f"{rel_path}:linux-kbuild-marker")
        elif adapter_id == "freertos" and re.search(r"configUSE_PREEMPTION|FreeRTOSConfig|xTaskCreate|vTaskStartScheduler", text):
            signals.append(f"{rel_path}:freertos-marker")
        elif adapter_id == "tinyml" and re.search(r"tflite|MicroInterpreter|TensorFlowLite|arena", text, flags=re.IGNORECASE):
            signals.append(f"{rel_path}:tinyml-marker")
        elif adapter_id == "cmake-baremetal" and re.search(r"arm-none-eabi|CMAKE_SYSTEM_NAME|LINKER_SCRIPT|\.ld", text):
            signals.append(f"{rel_path}:baremetal-cmake-marker")
    return signals


def read_small_text(path: Path) -> str:
    try:
        if path.stat().st_size > 256_000:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def adapter_payload(spec: AdapterSpec, confidence: float, evidence: list[str]) -> dict[str, object]:
    return {
        "id": spec.adapter_id,
        "label": spec.label,
        "confidence": confidence,
        "detector": spec.detector,
        "evidence": evidence[:40],
        "artifact_globs": list(spec.artifact_globs),
        "safe_commands": [command.__dict__ for command in spec.safe_commands],
        "recommended_scripts": list(spec.recommended_scripts),
        "runbooks": list(spec.runbooks),
        "next_steps": list(spec.next_steps),
    }


def build_next_steps(adapters: list[dict[str, object]]) -> list[str]:
    if not adapters:
        return [
            "Run the project build once and save build.log.",
            "Add board/MCU/SoC, toolchain, debugger, and symptom context to the debug packet.",
            "Run scripts/collect/collect_debug_packet.py --project-root . --platform auto --out debug_packet.yaml.",
        ]
    primary_steps = list(adapters[0].get("next_steps", []))
    return [
        "Review detected adapter confidence and evidence before running project commands.",
        *primary_steps[:3],
        "Generate a packet with scripts/collect/collect_debug_packet.py after collecting logs/artifacts.",
    ]


def render_markdown(context: dict[str, object]) -> str:
    lines = [
        "# Project Debug Context",
        "",
        f"- Project root: `{context['project_root']}`",
        f"- Primary adapter: `{context['primary_adapter']}`",
        "",
        "## Detected Adapters",
        "",
    ]
    adapters = context.get("adapters", [])
    if not isinstance(adapters, list) or not adapters:
        lines.append("No specific adapter detected. Start with a generic debug packet and build/serial logs.")
    else:
        for adapter in adapters:
            if not isinstance(adapter, dict):
                continue
            lines.extend(
                [
                    f"### {adapter['label']} (`{adapter['id']}`)",
                    "",
                    f"- Confidence: `{adapter['confidence']}`",
                    f"- Evidence: {', '.join(f'`{item}`' for item in adapter.get('evidence', [])[:8]) or 'none'}",
                    "",
                    "Suggested commands:",
                    "",
                ]
            )
            for command in adapter.get("safe_commands", []):
                if isinstance(command, dict):
                    lines.append(f"- `{command['command']}` - {command['risk']}: {command['note']}")
            lines.extend(["", "Recommended scripts:", ""])
            for script in adapter.get("recommended_scripts", []):
                lines.append(f"- `{script}`")
            lines.append("")
    lines.extend(["## Next Steps", ""])
    for step in context.get("next_steps", []):
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
