#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    skill_dir = Path(__file__).resolve().parents[1]
    scripts = skill_dir / "scripts"
    results = []

    results.append(run_tool(scripts / "bitfield_decode.py", ["--value", "0x40000000", "--field", "FORCED:30:30"]))
    results.append(run_tool(scripts / "average_current.py", ["--state", "sleep:20uA:9.9s", "--state", "tx:120mA:80ms", "--battery-mah", "1000"]))
    results.append(run_tool(scripts / "boot_log_timeline.py", ["--log", str(skill_dir / "references" / "evaluation_scenarios.md"), "--gap-ms", "500"]))
    results.extend(run_parser_fixture_tests(scripts))
    results.append(run_tool(scripts / "analyze" / "analyze_i2c_init_failure.py", ["--help"]))
    results.append(run_tool(scripts / "analyze" / "analyze_i2c_logic_trace.py", ["--help"]))
    results.extend(run_project_adapter_tests(scripts))
    results.append(run_profile_dossier_check(scripts))
    results.append(
        run_tool(
            scripts / "dma_buffer_check.py",
            ["--address", "0x20000004", "--size", "100", "--cache-line", "32", "--direction", "rx", "--region-cacheable", "true"],
        )
    )
    results.append(
        run_tool(
            scripts / "fault_analyzer.py",
            ["--cfsr", "0x8200", "--hfsr", "0x40000000", "--bfar", "0x20000004", "--exc-return", "0xFFFFFFFD", "--xpsr", "0x01000003"],
        )
    )
    results.append(run_tool(scripts / "i2c_pullup_check.py", ["--pullup", "4.7k", "--capacitance-pf", "200", "--mode", "fast"]))
    results.append(
        run_tool(
            scripts / "latency_budget.py",
            ["--period", "50ms", "--component", "capture:8ms", "--component", "inference:24ms", "--jitter", "5ms", "--watchdog", "100ms"],
        )
    )
    results.append(run_tool(scripts / "linux_log_triage.py", ["--log", str(skill_dir / "references" / "evaluation_scenarios.md")]))
    results.append(
        run_tool(
            scripts / "memory_budget.py",
            ["--flash", "512K", "--ram", "256K", "--model", "180K", "--arena", "96K", "--stack", "16K"],
        )
    )
    results.append(
        run_tool(
            scripts / "nvic_priority_check.py",
            ["--prio-bits", "4", "--irq-priority", "3", "--max-syscall-priority", "5", "--uses-freertos-api"],
        )
    )
    results.append(
        run_tool(
            scripts / "register_write_check.py",
            ["--value", "0x00F00003", "--current", "0x1", "--reserved-zero-mask", "0x00F00000", "--w1c-mask", "0x3", "--rmw"],
        )
    )
    results.append(
        run_tool(
            scripts / "rtos_snapshot_check.py",
            ["--task", "main:3:running:1800:2048", "--task", "logger:1:ready:900:1024", "--heap-free", "12K"],
        )
    )
    results.append(
        run_tool(
            scripts / "symbolicate_addresses.py",
            ["--elf", "firmware.elf", "--addr", "0x08001234", "--tool", "arm-none-eabi-addr2line", "--dry-run"],
        )
    )
    results.append(run_tool(scripts / "uart_baud_check.py", ["--clock", "80M", "--baud", "115200", "--oversampling", "16"]))
    results.append(run_vector_compare(scripts / "vector_compare.py"))
    results.append(run_tool(scripts / "validate_evaluation_scenarios.py", ["--skill-dir", str(skill_dir)]))

    failed = [item for item in results if item["returncode"] != 0]
    output = {"tool_count": len(results), "failed_count": len(failed), "results": results}
    print(json.dumps(output, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


def run_vector_compare(script: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        expected = Path(tmp) / "expected.txt"
        actual = Path(tmp) / "actual.txt"
        expected.write_text("1 2 3 4\n", encoding="utf-8")
        actual.write_text("1 2.001 3 4\n", encoding="utf-8")
        return run_tool(script, ["--expected", str(expected), "--actual", str(actual), "--abs-tol", "0.01"])


def run_parser_fixture_tests(scripts: Path) -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dts = root / "board.dts"
        dts.write_text(
            'i2c0: i2c@40003000 {\n'
            '  compatible = "nordic,nrf-twim";\n'
            '  status = "okay";\n'
            '  clock-frequency = <100000>;\n'
            '};\n',
            encoding="utf-8",
        )
        config = root / ".config"
        config.write_text("CONFIG_I2C=y\n# CONFIG_SPI is not set\n", encoding="utf-8")
        panic = root / "panic.log"
        panic.write_text(
            "Guru Meditation Error: Core  0 panic'ed (LoadProhibited). Exception was unhandled.\n"
            "PC      : 0x400d1234\n"
            "EXCVADDR: 0x00000000\n"
            "Backtrace: 0x400d1234:0x3ffb1230 0x400d5678:0x3ffb1250\n",
            encoding="utf-8",
        )
        map_file = root / "firmware.map"
        map_file.write_text(
            ".text           0x08000000      0x1200\n"
            ".rodata         0x08001200      0x0200\n"
            ".data           0x20000000      0x0100\n"
            ".bss            0x20000100      0x0400\n",
            encoding="utf-8",
        )
        return [
            run_tool(scripts / "dts_probe_check.py", ["--dts", str(dts), "--node", "i2c@40003000", "--expect-compatible", "nordic,nrf-twim", "--require-prop", "clock-frequency"]),
            run_tool(scripts / "kconfig_check.py", ["--config", str(config), "--require", "CONFIG_I2C=y", "--require", "CONFIG_SPI=n"]),
            run_tool(scripts / "esp_panic_parse.py", ["--log", str(panic)]),
            run_tool(scripts / "map_memory_summary.py", ["--map", str(map_file)]),
            run_tool(
                scripts / "freertos_wait_graph.py",
                ["--task", "high:5:blocked:spi", "--task", "low:1:running", "--resource", "spi:low"],
            ),
        ]


def run_profile_dossier_check(scripts: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        profile = root / "profile.json"
        dossier = root / "dossier.json"
        profile.write_text(
            json.dumps(
                {
                    "engineer": {"preferred_language": "zh-CN"},
                    "platforms": {"mcu": ["STM32"]},
                    "tools": {"debug_probes": ["J-Link"]},
                    "preferences": {"warn_before_irreversible_actions": True},
                    "safety_policy": {"require_confirmation_for": ["efuse"]},
                }
            ),
            encoding="utf-8",
        )
        dossier.write_text(
            json.dumps(
                {
                    "project": {"name": "demo", "board_revision": "A"},
                    "hardware": {"mcu_or_soc": "STM32H743"},
                    "firmware": {"toolchain": "arm-none-eabi-gcc"},
                    "debug": {"probe": "J-Link"},
                }
            ),
            encoding="utf-8",
        )
        return run_tool(scripts / "profile_dossier_check.py", ["--profile", str(profile), "--dossier", str(dossier)])


def run_project_adapter_tests(scripts: Path) -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "west.yml").write_text("manifest:\n  remotes: []\n", encoding="utf-8")
        (root / "prj.conf").write_text("CONFIG_I2C=y\n", encoding="utf-8")
        out_dir = root / "debug" / "embedded_debug_adapter"
        return [
            run_tool(scripts / "project" / "detect_project_context.py", ["--project-root", str(root), "--format", "json"]),
            run_tool(
                scripts / "project" / "create_project_adapter.py",
                ["--project-root", str(root), "--out-dir", str(out_dir), "--overwrite"],
            ),
        ]


def run_tool(script: Path, args: list[str]) -> dict[str, object]:
    command = [sys.executable, "-B", str(script), *args]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "script": script.name,
        "returncode": completed.returncode,
        "stdout_first_line": first_line(completed.stdout),
        "stderr_first_line": first_line(completed.stderr),
    }


def first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


if __name__ == "__main__":
    main()
