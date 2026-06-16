from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT_MEMORY = ROOT / "scripts" / "project" / "init_project_memory.py"
TRIAGE = ROOT / "scripts" / "project" / "run_project_triage.py"
NOTEBOOK = ROOT / "scripts" / "project" / "create_failure_notebook.py"
MATCH_PATTERNS = ROOT / "scripts" / "analyze" / "match_failure_patterns.py"
FIX_PLAN = ROOT / "scripts" / "verify" / "generate_fix_verification_plan.py"


def run_tool(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def make_zephyr_project(root: Path) -> Path:
    project = root / "zephyr_project"
    project.mkdir()
    (project / "west.yml").write_text("manifest:\n  projects: []\n", encoding="utf-8")
    (project / "prj.conf").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\n", encoding="utf-8")
    (project / "build.log").write_text("west build -b demo_board .\n", encoding="utf-8")
    (project / "serial.log").write_text("failed to initialize chip: NACK during WHO_AM_I read\n", encoding="utf-8")
    (project / "zephyr.dts").write_text("&i2c0 { sensor@6a { reg = <0x6a>; }; };\n", encoding="utf-8")
    (project / ".config").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\n", encoding="utf-8")
    return project


def test_project_memory_is_loaded_by_triage(tmp_path: Path) -> None:
    project = make_zephyr_project(tmp_path)
    init = run_tool([str(INIT_MEMORY), "--project-root", str(project), "--overwrite"])
    assert init.returncode == 0, init.stderr
    memory = project / ".embedded-debug.yml"
    assert memory.is_file()
    memory.write_text(
        "schema_version: 1\n"
        "project:\n"
        "  id: zephyr_project\n"
        "  platform: zephyr\n"
        "  board: demo_board\n"
        "  board_revision: synthetic\n"
        "  mcu_or_soc: nrf52\n"
        "toolchain:\n"
        "  compiler: arm-zephyr-eabi-gcc\n"
        "  build_system: west\n"
        "safety:\n"
        "  recovery_path: SWD probe\n",
        encoding="utf-8",
    )

    completed = run_tool([str(TRIAGE), "--project-root", str(project), "--symptom", "I2C sensor probe failed"])

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary["project_memory"] is True
    report = (project / "debug" / "project_triage_report.md").read_text(encoding="utf-8")
    assert "Project Memory" in report
    assert "demo_board" in report


def test_pattern_matcher_and_fix_plan(tmp_path: Path) -> None:
    project = make_zephyr_project(tmp_path)
    triage = run_tool([str(TRIAGE), "--project-root", str(project), "--symptom", "WHO_AM_I NACK"])
    assert triage.returncode == 0, triage.stderr
    packet = project / "debug" / "debug_packet.yaml"

    patterns = run_tool([str(MATCH_PATTERNS), "--packet", str(packet), "--format", "json"])
    assert patterns.returncode == 0, patterns.stderr
    result = json.loads(patterns.stdout)
    ids = [item["id"] for item in result["matches"]]
    assert any("zephyr" in pattern_id for pattern_id in ids)

    plan = run_tool([str(FIX_PLAN), "--packet", str(packet), "--hypothesis", "wrong I2C address"])
    assert plan.returncode == 0, plan.stderr
    assert "Fix Verification Plan" in plan.stdout
    assert "wrong I2C address" in plan.stdout


def test_create_failure_notebook(tmp_path: Path) -> None:
    project = make_zephyr_project(tmp_path)
    completed = run_tool([str(NOTEBOOK), "--project-root", str(project), "--symptom", "I2C sensor probe failed", "--case-id", "case-001"])

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    case_dir = Path(summary["case_dir"])
    assert (case_dir / "README.md").is_file()
    assert (case_dir / "debug_packet.yaml").is_file()
    assert (case_dir / "evidence_check.md").is_file()
    assert "Failure Notebook" in (case_dir / "README.md").read_text(encoding="utf-8")
