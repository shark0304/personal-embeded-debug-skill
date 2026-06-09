#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description="Symbolicate raw addresses with addr2line-compatible tools.")
    parser.add_argument("--elf", required=True, help="ELF file matching the flashed/running binary.")
    parser.add_argument("--addr", action="append", required=True, help="Address to symbolicate. Repeat as needed.")
    parser.add_argument("--tool", default="addr2line", help="addr2line-compatible command.")
    parser.add_argument("--no-functions", action="store_true", help="Do not request function names.")
    parser.add_argument("--no-inlines", action="store_true", help="Do not expand inline frames.")
    parser.add_argument("--no-demangle", action="store_true", help="Do not demangle C++ symbols.")
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing it.")
    args = parser.parse_args()

    command = build_command(args)
    output = {
        "elf": args.elf,
        "addresses": args.addr,
        "command": command,
        "dry_run": args.dry_run,
        "tool_found": shutil.which(args.tool) is not None,
    }
    if args.dry_run:
        print(json.dumps(output, indent=2, sort_keys=True))
        return
    if not output["tool_found"]:
        output["error"] = f"Tool not found: {args.tool}"
        print(json.dumps(output, indent=2, sort_keys=True))
        raise SystemExit(1)

    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    output["returncode"] = completed.returncode
    output["stdout"] = completed.stdout.splitlines()
    output["stderr"] = completed.stderr.splitlines()
    print(json.dumps(output, indent=2, sort_keys=True))
    if completed.returncode:
        raise SystemExit(completed.returncode)


def build_command(args: argparse.Namespace) -> list[str]:
    command = [args.tool]
    if not args.no_functions:
        command.append("-f")
    if not args.no_inlines:
        command.append("-i")
    if not args.no_demangle:
        command.append("-C")
    command.extend(["-e", args.elf])
    command.extend(args.addr)
    return command


if __name__ == "__main__":
    main()
