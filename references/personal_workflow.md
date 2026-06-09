# Personal Embedded Engineer Workflow

Use this reference to make the skill behave like a dedicated embedded engineer for one user's projects instead of a generic assistant.

## Personal Files

Use these templates as project-local or user-local artifacts:

- `assets/templates/engineer_profile.json`: personal tools, platforms, probes, coding preferences, and safety preferences.
- `assets/templates/project_bringup_dossier.json`: board/project facts such as power tree, clocks, boot chain, memory map, RTOS tasks, Linux DT, and known errata.
- `assets/templates/debug_issue_record.md`: issue notebook entry for symptoms, evidence, root cause, fix, and prevention.
- `assets/templates/lab_measurement_plan.md`: scope/logic-analyzer/current-measurement plan.

Use `scripts/profile_dossier_check.py` to check JSON completeness.

## How to Use

1. If a profile or dossier is present, read it before asking broad environment questions.
2. Prefer names, tools, probes, SDKs, and platforms from the profile.
3. Use the project dossier to avoid re-asking stable facts such as board revision, clock tree, memory map, and boot chain.
4. For every new bug, create or update an issue record with evidence and final root cause.
5. When an issue is resolved, add one prevention check: assertion, test, CI check, bring-up checklist item, or telemetry.

## Personalization Rules

- Do not override user-provided project facts with generic vendor assumptions.
- Mark dossier fields as unknown instead of inventing them.
- Separate stable project facts from incident-specific evidence.
- Keep risky operations tied to the user's declared safety policy and recovery path.
- Prefer the user's actual debug tools over generic alternatives when producing commands.
