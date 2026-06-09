# Advanced Embedded Debug Workbench v3

v2 introduced evidence-first debug packets, runbooks, failure patterns, report generation, and golden packet structure.

v3 extends the workbench in four areas:

1. Real-style golden packets
   - Adds sanitized field-like packets for Cortex-M, Zephyr, ESP-IDF, Linux probe defer, FreeRTOS, DMA/cache, and TinyML.
   - Adds `expected_root_cause.md` to each packet.

2. Scored reports
   - Adds `scripts/verify/score_debug_report.py`.
   - Reports are expected to contain evidence completeness, hypothesis ranking, verification, fix, and regression sections.

3. CI/HIL and simulation entry points
   - Adds Zephyr Twister template/report adapters.
   - Adds ESP-IDF pytest-embedded template/report adapters.
   - Adds Renode Robot template/report adapters.

4. Field diagnostics
   - Adds reboot reason, ringbuffer, and metrics analyzers.
   - Adds field diagnostics runbook and failure patterns.

The v3 goal is to turn debug outcomes into reproducible packets, scored reports, and regression fixtures without breaking v2 schemas or scripts.
