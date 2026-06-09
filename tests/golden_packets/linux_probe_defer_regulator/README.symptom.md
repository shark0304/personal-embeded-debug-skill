# linux_probe_defer_regulator

Symptom: Embedded Linux driver remains in deferred probe state because a supply is missing.

Expected behavior: report should inspect `devices_deferred`, regulator summary, DTS supply property, and supplier config.
