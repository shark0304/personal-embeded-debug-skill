#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


MANIFEST_NAMES = {
    "west.yml",
    "prj.conf",
    "sdkconfig",
    "sdkconfig.defaults",
    "platformio.ini",
    "FreeRTOSConfig.h",
    "Kbuild",
    "Kconfig",
    "CMakeLists.txt",
    "Makefile",
}
MANIFEST_SUFFIXES = {".ioc", ".dts", ".dtsi", ".overlay", ".conf"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a lightweight public project snapshot: manifest files only, no full clone by default.")
    parser.add_argument("--repo", required=True, help="GitHub repo full name, e.g. zephyrproject-rtos/zephyr.")
    parser.add_argument("--out-dir", default="research/project_corpus/snapshots", help="Snapshot root directory.")
    parser.add_argument("--ref", default="", help="Git ref. Defaults to repository default branch for API mode.")
    parser.add_argument("--local-repo", help="Use a local repository/path fixture instead of GitHub API.")
    parser.add_argument("--max-files", type=int, default=80, help="Maximum manifest files to save.")
    parser.add_argument("--max-bytes", type=int, default=200_000, help="Maximum bytes per file.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir) / safe_repo(args.repo)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.local_repo:
        files = snapshot_local(Path(args.local_repo), out_dir, args.max_files, args.max_bytes)
        source = "local"
        ref = args.ref or "local"
    else:
        files, ref = snapshot_github(args.repo, out_dir, args.ref, args.max_files, args.max_bytes)
        source = "github_api"

    manifest = {"repo": args.repo, "ref": ref, "source": source, "file_count": len(files), "files": files}
    (out_dir / "snapshot_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "snapshot_dir": str(out_dir), "file_count": len(files)}, indent=2, sort_keys=True))


def snapshot_local(root: Path, out_dir: Path, max_files: int, max_bytes: int) -> list[str]:
    copied: list[str] = []
    for path in sorted(root.rglob("*")):
        if len(copied) >= max_files:
            break
        if path.is_file() and is_manifest(path.relative_to(root).as_posix()) and path.stat().st_size <= max_bytes:
            rel = path.relative_to(root)
            dst = out_dir / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dst)
            copied.append(rel.as_posix())
    return copied


def snapshot_github(repo: str, out_dir: Path, ref: str, max_files: int, max_bytes: int) -> tuple[list[str], str]:
    repo_meta = github_json(f"https://api.github.com/repos/{repo}")
    branch = ref or str(repo_meta.get("default_branch") or "main")
    tree = github_json(f"https://api.github.com/repos/{repo}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1")
    files: list[str] = []
    for item in tree.get("tree", []) if isinstance(tree, dict) else []:
        if len(files) >= max_files:
            break
        if not isinstance(item, dict) or item.get("type") != "blob":
            continue
        rel = str(item.get("path", ""))
        size = int(item.get("size") or 0)
        if is_manifest(rel) and size <= max_bytes:
            raw_url = f"https://raw.githubusercontent.com/{repo}/{urllib.parse.quote(branch, safe='')}/{urllib.parse.quote(rel)}"
            data = github_bytes(raw_url)
            dst = out_dir / "files" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data[:max_bytes])
            files.append(rel)
    return files, branch


def github_json(url: str) -> dict[str, Any]:
    return json.loads(github_bytes(url).decode("utf-8"))


def github_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "embedded-debug-public-project-miner",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def is_manifest(rel: str) -> bool:
    name = Path(rel).name
    suffix = Path(rel).suffix
    rel_l = rel.lower()
    return name in MANIFEST_NAMES or suffix in MANIFEST_SUFFIXES or "freertosconfig.h" in rel_l or "idf_component_register" in rel_l


def safe_repo(repo: str) -> str:
    return repo.replace("/", "__").replace(":", "_")


if __name__ == "__main__":
    main()
