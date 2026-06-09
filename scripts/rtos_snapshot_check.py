#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Review an RTOS task/thread snapshot.")
    parser.add_argument(
        "--task",
        action="append",
        required=True,
        help="Task as NAME:PRIORITY:STATE:STACK_USED:STACK_SIZE. Repeat for each task.",
    )
    parser.add_argument("--stack-warn-percent", default=80.0, type=float)
    parser.add_argument("--heap-free", default=None, help="Current heap free, e.g. 12K.")
    parser.add_argument("--heap-min-ever-free", default=None, help="Minimum-ever free heap, e.g. 4K.")
    args = parser.parse_args()

    tasks = [parse_task(item) for item in args.task]
    findings = []
    for task in tasks:
        if task["stack_used_percent"] >= args.stack_warn_percent:
            findings.append(
                f"{task['name']} stack usage is {task['stack_used_percent']:.1f}%, above warning threshold."
            )
        if task["stack_unused"] <= 0:
            findings.append(f"{task['name']} stack is over budget or exactly exhausted.")

    blocked = [task for task in tasks if task["state"].lower() in {"blocked", "waiting", "suspended"}]
    ready = [task for task in tasks if task["state"].lower() in {"ready", "runnable"}]
    running = [task for task in tasks if task["state"].lower() == "running"]
    if len(running) > 1:
        findings.append("Multiple tasks are marked running; verify SMP versus stale debugger snapshot.")
    if blocked and not ready and not running:
        findings.append("All tasks appear blocked/suspended; suspect deadlock, sleep forever, or stale snapshot.")

    heap = build_heap(args.heap_free, args.heap_min_ever_free)
    if heap and heap["min_ever_free_bytes"] is not None and heap["min_ever_free_bytes"] <= 0:
        findings.append("Heap minimum-ever-free is zero; allocation failure or heap exhaustion is likely.")

    output = {
        "tasks": sorted(tasks, key=lambda item: (-item["stack_used_percent"], item["priority"])),
        "counts": {
            "blocked_or_waiting": len(blocked),
            "ready_or_runnable": len(ready),
            "running": len(running),
            "total": len(tasks),
        },
        "stack_warn_percent": args.stack_warn_percent,
        "heap": heap,
        "findings": findings,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_task(text: str) -> dict[str, object]:
    parts = text.split(":")
    if len(parts) != 5:
        raise SystemExit(f"Invalid task {text!r}; expected NAME:PRIORITY:STATE:STACK_USED:STACK_SIZE")
    name, priority_text, state, used_text, size_text = parts
    priority = int(priority_text, 0)
    used = parse_size(used_text)
    size = parse_size(size_text)
    if size <= 0:
        raise SystemExit(f"Task {name} stack size must be positive")
    unused = size - used
    return {
        "name": name,
        "priority": priority,
        "state": state,
        "stack_used_bytes": used,
        "stack_size_bytes": size,
        "stack_unused": unused,
        "stack_used_percent": round((used / size) * 100.0, 2),
    }


def build_heap(free_text: str | None, min_text: str | None) -> dict[str, object] | None:
    if free_text is None and min_text is None:
        return None
    return {
        "free_bytes": None if free_text is None else parse_size(free_text),
        "min_ever_free_bytes": None if min_text is None else parse_size(min_text),
    }


def parse_size(text: str) -> int:
    normalized = text.strip().lower()
    multiplier = 1
    if normalized.endswith("kb"):
        multiplier = 1024
        normalized = normalized[:-2]
    elif normalized.endswith("k"):
        multiplier = 1024
        normalized = normalized[:-1]
    elif normalized.endswith("mb"):
        multiplier = 1024 * 1024
        normalized = normalized[:-2]
    elif normalized.endswith("m"):
        multiplier = 1024 * 1024
        normalized = normalized[:-1]
    try:
        return int(float(normalized) * multiplier)
    except ValueError as exc:
        raise SystemExit(f"Invalid size: {text}") from exc


if __name__ == "__main__":
    main()
