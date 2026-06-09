# Hypothesis Ranking Contract

Every candidate root cause must use this structure:

```yaml
hypothesis_id: H1
root_cause: Short candidate cause.
confidence: low | medium | high
evidence_for:
  - Observed artifact supporting the candidate.
evidence_against:
  - Observed artifact weakening the candidate.
missing_evidence:
  - Artifact needed to upgrade or reject the candidate.
verification_step: Concrete command, measurement, or experiment.
expected_observation: What should happen if the hypothesis is true.
fix_if_confirmed: Minimal fix or mitigation after verification.
```

## Confidence Rules

- `low`: plausible pattern match, little direct evidence.
- `medium`: direct evidence exists but at least one critical artifact is missing.
- `high`: direct evidence plus a verification step confirms the branch.

## Prohibitions

- Do not output "confirmed root cause" without `verification_step`.
- Do not treat a workaround as a root cause.
- Do not hide missing evidence inside prose.
- Do not rank by confidence alone; rank by expected diagnostic value and risk.
