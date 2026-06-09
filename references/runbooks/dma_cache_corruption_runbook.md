# DMA Cache Corruption Runbook

## Trigger symptoms

- Polling works but DMA fails, stale RX data, first transfer works, random buffer corruption.

## Minimum evidence

- Buffer address, size, section, cacheability, direction, cache line size, DMA flags, memory domain.

## Fast triage

1. Run `dma_buffer_check.py`.
2. Confirm buffer is DMA-visible.
3. Check clean/invalidate timing and ownership.

## High-probability root causes

- Cache line overlap, missing clean/invalidate, wrong memory domain, stack buffer lifetime, descriptor/payload split.

## Scripts to run

- `scripts/dma_buffer_check.py`

## Manual experiments

- Move buffer to nocache region, disable DCache for isolation, align buffer and size.

## Fix patterns

- Dedicated DMA section, MPU nocache region, cache-line aligned buffers, explicit ownership protocol.

## Regression tests

- DMA loopback/golden packet with repeated transfers and cache enabled.

## Do-not-guess rules

- Do not tune peripheral timing before proving memory/cache correctness.
