# Evidence First

Use this contract for every non-trivial embedded debug answer.

## Rules

- Do not claim a root cause until the minimum evidence for that domain is available.
- If evidence is missing, ask for the smallest artifact that splits the largest branch.
- Separate observations, hypotheses, verification steps, and fixes.
- Prefer reproducible artifacts: debug packet, logs, ELF/map, DTS/Kconfig, task snapshot, waveforms.
- Mark assumptions explicitly and downgrade confidence when evidence is indirect.

## Minimum Evidence Pattern

1. Platform and board revision.
2. Toolchain/SDK/build mode.
3. Symptom and trigger.
4. Last known good.
5. Domain artifact: fault frame, log, DTS/Kconfig, task snapshot, waveform, model metadata, or boot log.
6. Safety/recovery constraints.

## Debug Packet Priority

For complex issues, first generate or update a `debug_packet.yaml`. Use it as the source of truth for analysis, missing evidence, report generation, and regression packets.
