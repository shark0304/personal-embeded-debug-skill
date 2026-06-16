from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAGE = ROOT / "scripts" / "project" / "run_project_triage.py"
VALIDATE = ROOT / "scripts" / "collect" / "validate_debug_packet.py"


def run_tool(args: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", *args], cwd=cwd, text=True, capture_output=True, check=False)


def test_run_project_triage_generates_packet_and_report(tmp_path: Path) -> None:
    project = tmp_path / "zephyr_project"
    project.mkdir()
    (project / "west.yml").write_text("manifest:\n  projects: []\n", encoding="utf-8")
    (project / "prj.conf").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\nCONFIG_BOARD=\"demo_board\"\n", encoding="utf-8")
    (project / "build.log").write_text("west build -b demo_board .\n", encoding="utf-8")
    (project / "serial.log").write_text("failed to initialize chip: NACK\n", encoding="utf-8")
    (project / "zephyr.dts").write_text("&i2c0 { status = \"okay\"; };\n", encoding="utf-8")
    (project / ".config").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\n", encoding="utf-8")

    completed = run_tool(
        [
            str(TRIAGE),
            "--project-root",
            str(project),
            "--symptom",
            "I2C sensor probe failed",
        ]
    )

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["primary_adapter"] == "zephyr"
    assert summary["platform"] == "zephyr"
    assert summary["evidence_score"] >= 60
    packet = project / "debug" / "debug_packet.yaml"
    report = project / "debug" / "project_triage_report.md"
    assert packet.is_file()
    assert report.is_file()
    report_text = report.read_text(encoding="utf-8")
    assert "Evidence completeness" in report_text
    assert "Risk Guardrails" in report_text
    assert "hardware-changing" in report_text


def test_validate_debug_packet_scores_missing_evidence(tmp_path: Path) -> None:
    packet = tmp_path / "debug_packet.json"
    packet.write_text(
        json.dumps(
            {
                "case_id": "thin_case",
                "project_root": str(tmp_path),
                "platform": "cortex-m",
                "board": "unknown",
                "toolchain": "unknown",
                "build_system": "cmake",
                "artifacts": {"fault_registers": ["fault.txt"]},
            }
        ),
        encoding="utf-8",
    )

    completed = run_tool([str(VALIDATE), "--packet", str(packet), "--format", "json"])

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["ok"] is False
    assert "elf" in result["required_evidence"]["missing"]
    assert "map" in result["required_evidence"]["missing"]
    assert result["score"] < 70


def test_validate_debug_packet_markdown_output(tmp_path: Path) -> None:
    packet = tmp_path / "debug_packet.json"
    packet.write_text(
        json.dumps(
            {
                "case_id": "linux_case",
                "project_root": str(tmp_path),
                "platform": "embedded-linux",
                "board": "synthetic-board",
                "toolchain": "gcc",
                "build_system": "make",
                "artifacts": {
                    "boot_log": ["boot.log"],
                    "dmesg": ["dmesg.log"],
                    "dts": ["board.dts"],
                    "kconfig": ["kernel.config"],
                },
            }
        ),
        encoding="utf-8",
    )

    completed = run_tool([str(VALIDATE), "--packet", str(packet), "--format", "markdown"])

    assert completed.returncode == 0, completed.stderr
    assert "Debug Packet Validation" in completed.stdout
    assert "Ready for root-cause analysis: **yes**" in completed.stdout
