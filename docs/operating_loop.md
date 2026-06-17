# Embedded Failure Operating Loop

This loop turns one-off debugging into reusable project memory.

## First-time Project Onboarding

```bash
python scripts/project/onboard_project.py \
  --project-root . \
  --symptom "short failure statement" \
  --overwrite
```

Outputs:

- `.embedded-debug.yml` for board, toolchain, command, artifact, and recovery facts.
- `debug/onboarding/onboarding_report.md` for readiness and next actions.
- `debug/onboarding/embedded_debug_adapter/` for adapter context and risk policy.
- `debug/README.md` for local artifact hygiene.

## Failure Case Loop

```bash
python scripts/project/run_project_triage.py --project-root . --symptom "failure"
python scripts/project/suggest_evidence_capture.py --packet debug/debug_packet.yaml --symptom "failure" --format markdown
python scripts/review/review_debug_report.py --report debug/project_triage_report.md --format markdown
python scripts/project/create_failure_notebook.py --project-root . --symptom "failure"
```

Move status as evidence improves:

```bash
python scripts/project/update_failure_case.py \
  --case-dir debug/failure-notebook/<case-id> \
  --status verified \
  --hypothesis "candidate root cause" \
  --verification "before/after observation" \
  --export-golden debug/golden-candidate
```

## Status Meanings

| Status | Meaning |
|---|---|
| `open` | Case exists but evidence is not yet organized. |
| `investigating` | Evidence capture or hypothesis ranking is in progress. |
| `fixed` | A candidate fix exists, but before/after proof is not complete. |
| `verified` | Verification observation matches the expected before/after change. |
| `regression-added` | A golden packet, CI/HIL case, or repeatable regression record exists. |
| `closed` | Case is complete and no further local action is planned. |

## Boundary

The loop is intentionally conservative. It can make missing evidence visible, but it should not convert a plausible hypothesis into a confirmed root cause without verification evidence.
