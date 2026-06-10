# Symptom

Sanitized FreeRTOS runtime packet. A high priority control task misses deadlines
while blocked on `spi_mutex`; a low priority logger owns the mutex and a medium
priority telemetry task runs during the failure window.

This packet is promoted because the wait graph is deterministic and the
mitigation experiment changes the deadline miss count.
