from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ONBOARD = ROOT / "scripts" / "project" / "onboard_project.py"
TRIAGE = ROOT / "scripts" / "project" / "run_project_triage.py"
NOTEBOOK = ROOT / "scripts" / "project" / "create_failure_notebook.py"
UPDATE_CASE = ROOT / "scripts" / "project" / "update_failure_case.py"
REVIEW = ROOT / "scripts" / "review" / "review_debug_report.py"


def run_tool(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def make_zephyr_project(root: Path) -> Path:
    project = root / "zephyr_project"
    project.mkdir()
    (project / "west.yml").write_text("manifest:\n  projects: []\n", encoding="utf-8")
    (project / "prj.conf").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\nCONFIG_BOARD=\"demo_board\"\n", encoding="utf-8")
    (project / "build.log").write_text("west build -b demo_board .\n", encoding="utf-8")
    (project / "serial.log").write_text("failed to initialize chip: NACK during WHO_AM_I read\n", encoding="utf-8")
    (project / "zephyr.dts").write_text("&i2c0 { status = \"okay\"; sensor@6a { reg = <0x6a>; }; };\n", encoding="utf-8")
    (project / ".config").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\n", encoding="utf-8")
    return project


def test_onboard_project_creates_operating_loop_files(tmp_path: Path) -> None:
    project = make_zephyr_project(tmp_path)

    completed = run_tool([str(ONBOARD), "--project-root", str(project), "--symptom", "I2C sensor probe failed", "--overwrite"])

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["primary_adapter"] == "zephyr"
    assert (project / ".embedded-debug.yml").is_file()
    assert (project / "debug" / "onboarding" / "onboarding_report.md").is_file()
    assert (project / "debug" / "onboarding" / "embedded_debug_adapter" / "PROJECT_DEBUG_ADAPTER.md").is_file()
    assert (project / "debug" / "README.md").is_file()
    report = (project / "debug" / "onboarding" / "onboarding_report.md").read_text(encoding="utf-8")
    assert "Recommended Operating Loop" in report
    assert "Bring-up Readiness" in report


def test_failure_case_lifecycle_and_golden_export(tmp_path: Path) -> None:
    project = make_zephyr_project(tmp_path)
    create = run_tool(
        [
            str(NOTEBOOK),
            "--project-root",
            str(project),
            "--symptom",
            "I2C sensor probe failed",
            "--case-id",
            "case-001",
        ]
    )
    assert create.returncode == 0, create.stderr
    case_dir = project / "debug" / "failure-notebook" / "case-001"

    update = run_tool(
        [
            str(UPDATE_CASE),
            "--case-dir",
            str(case_dir),
            "--status",
            "verified",
            "--note",
            "ACK observed after address correction",
            "--hypothesis",
            "wrong I2C address",
            "--verification",
            "cold boot trace shows ACK",
            "--export-golden",
            str(project / "debug" / "golden-candidate"),
        ]
    )

    assert update.returncode == 0, update.stderr
    result = json.loads(update.stdout)
    assert result["status"] == "verified"
    status = json.loads((case_dir / "case_status.json").read_text(encoding="utf-8"))
    assert status["status"] == "verified"
    assert "ACK observed" in (case_dir / "lifecycle.md").read_text(encoding="utf-8")
    assert (project / "debug" / "golden-candidate" / "golden_candidate_manifest.json").is_file()


def test_review_debug_report_accepts_triage_report(tmp_path: Path) -> None:
    project = make_zephyr_project(tmp_path)
    triage = run_tool([str(TRIAGE), "--project-root", str(project), "--symptom", "I2C sensor probe failed"])
    assert triage.returncode == 0, triage.stderr
    report = project / "debug" / "project_triage_report.md"

    completed = run_tool([str(REVIEW), "--report", str(report), "--format", "json", "--min-score", "80"])

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert result["score"] >= 80


def test_review_debug_report_flags_premature_claim(tmp_path: Path) -> None:
    report = tmp_path / "bad_report.md"
    report.write_text(
        "# Debug Report\n\nRoot cause is certain. No need to verify.\n",
        encoding="utf-8",
    )

    completed = run_tool([str(REVIEW), "--report", str(report), "--format", "json", "--min-score", "80"])

    assert completed.returncode != 0
    result = json.loads(completed.stdout)
    assert result["ok"] is False
    assert result["unsupported_certainty"]
