# Symptom

Sanitized STM32H7 Ethernet RX DMA stress packet. Payload corruption appears only
with D-cache enabled and disappears after cache-line aligned invalidation is
added after RX DMA completion.

This is a real-style trial packet, not a claim of direct hardware access in this
environment.
