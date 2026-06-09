# freertos_real_priority_inversion

Sanitized sample based on common RTOS resource ownership failures.

Symptom: high-priority control task misses watchdog while lower-priority task owns a shared bus mutex.
