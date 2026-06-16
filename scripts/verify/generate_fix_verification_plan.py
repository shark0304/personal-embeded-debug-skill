#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

COLLECT_DIR = Path(__file__).resolve().parents[1] / "collect"
if str(COLLECT_DIR) not in sys.path:
    sys.path.insert(0, str(COLLECT_DIR))

from validate_debug_packet import load_packet, validate_debug_packet  # noqa: E402


PLATFORM_CHECKS = {
    "zephyr": [
        "Rebuild with the same board target and preserve the generated `zephyr.dts` and `.config`.",
        "Capture serial log from reset through the formerly failing probe path.",
        "For bus issues, compare before/after logic analyzer traces when available.",
    ],
    "esp-idf": [
        "Capture full monitor output from reset through the formerly failing path.",
        "Preserve `sdkconfig`, partition table, ELF, and map from the tested image.",
        "Decode any remaining panic or WDT backtrace with the matching ELF.",
    ],
    "cortex-m": [
        "Capture fault registers and stacked frame before and after the fix.",
        "Use the exact ELF/map for address and memory placement checks.",
        "Run repeated reset/power-cycle attempts to check for intermittent recurrence.",
    ],
    "freertos": [
        "Capture task states, stack high-water marks, heap status, and blocked resources before and after.",
        "Check ISR priorities when queue/semaphore behavior changes.",
        "Stress the formerly blocked path under load for a bounded duration.",
    ],
    "embedded-linux": [
        "Capture full boot-to-failure `dmesg` before and after.",
        "Preserve booted DTS/DTB and kernel config from the tested image.",
        "Check `devices_deferred`, dynamic debug, or ftrace evidence if probe behavior changed.",
    ],
    "tinyml": [
        "Compare firmware outputs against golden vectors.",
        "Record arena usage and map file before and after.",
        "Measure latency distribution, not only a single average.",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a fix verification plan from a debug packet and hypothesis.")
    parser.add_argument("--packet", required=True, help="debug_packet.yaml/json path.")
    parser.add_argument("--hypothesis", required=True, help="Hypothesis or fix claim to verify.")
    parser.add_argument("--out", help="Optional markdown output path.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    packet_path = Path(args.packet)
    packet = load_packet(packet_path)
    validation = validate_debug_packet(packet, packet_path=packet_path)
    plan = build_plan(packet, validation, args.hypothesis)
    text = json.dumps(plan, indent=2, sort_keys=True) if args.format == "json" else render_markdown(plan)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


def build_plan(packet: dict[str, Any], validation: dict[str, Any], hypothesis: str) -> dict[str, Any]:
    platform = str(packet.get("platform") or "unknown")
    missing = list(validation.get("required_evidence", {}).get("missing", []))
    return {
        "hypothesis": hypothesis,
        "platform": platform,
        "evidence_score": validation.get("score", 0),
        "preconditions": build_preconditions(validation, missing),
        "before_fix_capture": before_fix_capture(platform, missing),
        "change_control": [
            "Apply one minimal change tied to this hypothesis.",
            "Record commit, patch, config diff, board revision, and firmware image identity.",
            "Do not mix unrelated cleanup with verification changes.",
        ],
        "after_fix_capture": PLATFORM_CHECKS.get(platform, ["Repeat the same evidence capture path used before the fix."]),
        "acceptance_criteria": acceptance_criteria(platform, hypothesis),
        "non_evidence": [
            "A single successful boot without logs is not enough.",
            "A workaround that hides the symptom is not proof of root cause.",
            "A changed timing condition without before/after evidence is not proof.",
        ],
        "regression_record": [
            "Save updated debug_packet.yaml, triage report, verification notes, and final outcome.",
            "Promote to a golden packet or CI/HIL regression when the fix is accepted.",
        ],
    }


def build_preconditions(validation: dict[str, Any], missing: list[str]) -> list[str]:
    items = [f"Evidence completeness is {validation.get('score', 0)}/100 (`{validation.get('grade', 'unknown')}`)."]
    if missing:
        items.append("Collect missing required evidence before accepting the fix: " + ", ".join(f"`{item}`" for item in missing) + ".")
    else:
        items.append("Required evidence is present for the declared platform.")
    return items


def before_fix_capture(platform: str, missing: list[str]) -> list[str]:
    capture = ["Record the exact symptom and trigger before changing code or configuration."]
    if missing:
        capture.append("Fill missing evidence first: " + ", ".join(f"`{item}`" for item in missing) + ".")
    capture.extend(PLATFORM_CHECKS.get(platform, ["Preserve logs, binary identity, build configuration, and reproduction steps."]))
    return capture


def acceptance_criteria(platform: str, hypothesis: str) -> list[str]:
    base = [
        f"The observation predicted by `{hypothesis}` changes in the expected direction.",
        "The original symptom does not recur under the same trigger.",
        "The fix survives repeated reset or reproduction attempts appropriate for the failure.",
    ]
    if platform in {"zephyr", "esp-idf", "cortex-m", "freertos"}:
        base.append("The tested firmware image is tied to a known ELF/map or build identity.")
    if platform == "embedded-linux":
        base.append("The booted kernel, DTB/DTS, module, and config are tied to the tested image.")
    return base


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Fix Verification Plan",
        "",
        f"- Hypothesis: {plan['hypothesis']}",
        f"- Platform: `{plan['platform']}`",
        f"- Evidence score: `{plan['evidence_score']}/100`",
        "",
    ]
    for section in [
        ("Preconditions", "preconditions"),
        ("Before Fix Capture", "before_fix_capture"),
        ("Change Control", "change_control"),
        ("After Fix Capture", "after_fix_capture"),
        ("Acceptance Criteria", "acceptance_criteria"),
        ("What Does Not Count As Proof", "non_evidence"),
        ("Regression Record", "regression_record"),
    ]:
        title, key = section
        lines.extend([f"## {title}", ""])
        for item in plan.get(key, []):
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip()


if __name__ == "__main__":
    main()
