# Expected Root Cause

DMA RX buffers are in cacheable memory and are consumed without cache-line
aligned invalidation after DMA completion.

Regression evidence:

- RX buffer address is not 32-byte aligned.
- Corruption occurs only with D-cache enabled.
- The invalidate-on-RX experiment reduces the CRC mismatch counter to zero.

Residual evidence gap:

- ELF is not included, so this packet should not be used for PC/source
  symbolication.
