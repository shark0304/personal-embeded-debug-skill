from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MINE = ROOT / "scripts" / "research" / "mine_github_projects.py"
SCORE = ROOT / "scripts" / "research" / "score_embedded_relevance.py"
SNAPSHOT = ROOT / "scripts" / "research" / "fetch_project_snapshot.py"
SIGNALS = ROOT / "scripts" / "research" / "extract_project_signals.py"
CORPUS = ROOT / "scripts" / "research" / "build_project_corpus.py"


def run_tool(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", *args], cwd=ROOT, text=True, capture_output=True, check=False)


def make_fixture_repo(root: Path) -> Path:
    repo = root / "fixture_repo"
    repo.mkdir()
    (repo / "west.yml").write_text("manifest:\n  projects: []\n", encoding="utf-8")
    (repo / "prj.conf").write_text("CONFIG_I2C=y\nCONFIG_SENSOR=y\n", encoding="utf-8")
    (repo / "boards").mkdir()
    (repo / "boards" / "demo.overlay").write_text("&i2c0 { status = \"okay\"; };\n", encoding="utf-8")
    (repo / "README.md").write_text("Synthetic Zephyr firmware fixture.\n", encoding="utf-8")
    return repo


def test_mine_github_projects_from_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "github_search.json"
    fixture.write_text(
        json.dumps(
            {
                "query": "zephyr prj.conf embedded firmware",
                "items": [
                    {
                        "full_name": "example/zephyr-sensor",
                        "html_url": "https://github.com/example/zephyr-sensor",
                        "description": "Zephyr prj.conf based firmware",
                        "language": "C",
                        "stargazers_count": 120,
                        "fork": False,
                        "archived": False,
                        "topics": ["zephyr", "embedded"],
                        "default_branch": "main",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "candidates.jsonl"

    completed = run_tool([str(MINE), "--fixture-json", str(fixture), "--out", str(out), "--limit", "10"])

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["candidate_count"] == 1
    row = json.loads(out.read_text(encoding="utf-8").splitlines()[0])
    assert row["full_name"] == "example/zephyr-sensor"


def test_project_snapshot_signals_and_corpus(tmp_path: Path) -> None:
    repo = make_fixture_repo(tmp_path)
    snapshot_root = tmp_path / "snapshots"
    snapshot = run_tool([str(SNAPSHOT), "--repo", "example/zephyr-sensor", "--local-repo", str(repo), "--out-dir", str(snapshot_root)])

    assert snapshot.returncode == 0, snapshot.stderr
    snapshot_result = json.loads(snapshot.stdout)
    snapshot_dir = Path(snapshot_result["snapshot_dir"])
    assert (snapshot_dir / "files" / "west.yml").is_file()
    assert (snapshot_dir / "files" / "prj.conf").is_file()

    signals_dir = tmp_path / "signals"
    signal_out = signals_dir / "example__zephyr-sensor.json"
    signals = run_tool([str(SIGNALS), "--snapshot-dir", str(snapshot_dir), "--out", str(signal_out)])
    assert signals.returncode == 0, signals.stderr
    signal_result = json.loads(signals.stdout)
    assert signal_result["primary_adapter"] == "zephyr"

    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(
        json.dumps(
            {
                "full_name": "example/zephyr-sensor",
                "html_url": "https://github.com/example/zephyr-sensor",
                "description": "Zephyr firmware with prj.conf",
                "manifest_paths": ["west.yml", "prj.conf"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    corpus = run_tool(
        [
            str(CORPUS),
            "--candidates",
            str(candidates),
            "--signals-dir",
            str(signals_dir),
            "--out-csv",
            str(tmp_path / "index.csv"),
            "--out-jsonl",
            str(tmp_path / "index.jsonl"),
        ]
    )
    assert corpus.returncode == 0, corpus.stderr
    indexed = json.loads((tmp_path / "index.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert indexed["score"] >= 40
    assert indexed["primary_adapter"] == "zephyr"


def test_score_embedded_relevance_filters_low_signal(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.jsonl"
    candidates.write_text(
        json.dumps({"full_name": "example/web-app", "description": "frontend web application"}) + "\n"
        + json.dumps({"full_name": "example/freertos-device", "description": "FreeRTOSConfig.h firmware"}) + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "scored.jsonl"

    completed = run_tool([str(SCORE), "--input", str(candidates), "--out", str(out), "--min-score", "20"])

    assert completed.returncode == 0, completed.stderr
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [row["full_name"] for row in rows] == ["example/freertos-device"]
