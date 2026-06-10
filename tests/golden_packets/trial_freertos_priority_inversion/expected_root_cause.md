# Expected Root Cause

A low priority logger task holds the SPI mutex while the high priority control
task blocks behind it and a medium priority task consumes CPU.

Regression evidence:

- `rtos_snapshot.yaml` shows `control` blocked on `spi_mutex`.
- `logger` owns `spi_mutex` at low priority.
- Reducing logger SPI critical section removes deadline misses.

Residual evidence gap:

- A scheduler trace timeline would quantify exact blocking duration.
