#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a simple FreeRTOS task/resource wait graph.")
    parser.add_argument("--task", action="append", required=True, help="Task as NAME:PRIORITY:STATE[:WAITING_ON].")
    parser.add_argument("--resource", action="append", default=[], help="Resource as NAME:OWNER_TASK.")
    parser.add_argument(
        "--higher-number-higher-priority",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="FreeRTOS normally treats higher numeric priority as higher urgency.",
    )
    args = parser.parse_args()

    tasks = {item["name"]: item for item in (parse_task(text) for text in args.task)}
    resources = {name: owner for name, owner in (parse_resource(text) for text in args.resource)}
    inversions = find_priority_inversions(tasks, resources, args.higher_number_higher_priority)
    cycles = find_cycles(tasks, resources)
    output = {
        "tasks": tasks,
        "resources": resources,
        "priority_inversions": inversions,
        "cycles": cycles,
        "ok": not inversions and not cycles,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


def parse_task(text: str) -> dict[str, object]:
    parts = text.split(":")
    if len(parts) not in {3, 4}:
        raise SystemExit(f"Invalid task {text!r}; expected NAME:PRIORITY:STATE[:WAITING_ON]")
    return {
        "name": parts[0],
        "priority": int(parts[1], 0),
        "state": parts[2],
        "waiting_on": parts[3] if len(parts) == 4 and parts[3] else None,
    }


def parse_resource(text: str) -> tuple[str, str]:
    parts = text.split(":")
    if len(parts) != 2:
        raise SystemExit(f"Invalid resource {text!r}; expected NAME:OWNER_TASK")
    return parts[0], parts[1]


def higher_priority(a: int, b: int, higher_number_higher: bool) -> bool:
    return a > b if higher_number_higher else a < b


def find_priority_inversions(tasks: dict[str, dict[str, object]], resources: dict[str, str], higher_number_higher: bool) -> list[dict[str, object]]:
    inversions = []
    for task in tasks.values():
        waiting_on = task.get("waiting_on")
        if not waiting_on or waiting_on not in resources:
            continue
        owner_name = resources[waiting_on]
        owner = tasks.get(owner_name)
        if owner and higher_priority(int(task["priority"]), int(owner["priority"]), higher_number_higher):
            inversions.append(
                {
                    "waiter": task["name"],
                    "waiter_priority": task["priority"],
                    "resource": waiting_on,
                    "owner": owner_name,
                    "owner_priority": owner["priority"],
                }
            )
    return inversions


def find_cycles(tasks: dict[str, dict[str, object]], resources: dict[str, str]) -> list[list[str]]:
    cycles = []
    for task_name in tasks:
        seen = []
        current = task_name
        while current in tasks:
            if current in seen:
                cycles.append(seen[seen.index(current) :] + [current])
                break
            seen.append(current)
            waiting_on = tasks[current].get("waiting_on")
            if not waiting_on or waiting_on not in resources:
                break
            current = resources[waiting_on]
    unique = []
    for cycle in cycles:
        normalized = "->".join(cycle)
        if normalized not in {"->".join(item) for item in unique}:
            unique.append(cycle)
    return unique


if __name__ == "__main__":
    main()
