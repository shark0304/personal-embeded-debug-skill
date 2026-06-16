# Synthetic Project Fixtures

These projects are synthetic examples for local testing and documentation. They are not real customer projects, real board bring-up logs, or real experiment results.

Use them to try the safe triage path:

```bash
python scripts/project/run_project_triage.py \
  --project-root examples/projects/zephyr_i2c_probe_fail \
  --symptom "I2C sensor probe failed"
```
