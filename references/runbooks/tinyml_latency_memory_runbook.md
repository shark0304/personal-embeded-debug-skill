# TinyML Latency and Memory Runbook

## Trigger symptoms

- Arena allocation failure, wrong inference output, latency miss, watchdog reset after model integration.

## Minimum evidence

- Model file metadata, op list, arena size/log, memory map, input tensor dump, golden vector, stage timings.

## Fast triage

1. Run `memory_budget.py` and `latency_budget.py`.
2. Compare target tensors with `vector_compare.py`.
3. Check DMA/cache for accelerator buffers.

## High-probability root causes

- Arena growth, missing op, preprocessing mismatch, quantization mismatch, memory movement, watchdog period miss.

## Scripts to run

- `scripts/memory_budget.py`
- `scripts/latency_budget.py`
- `scripts/vector_compare.py`
- `scripts/dma_buffer_check.py`

## Manual experiments

- Run one golden input, dump input tensor before invoke, measure each stage separately.

## Fix patterns

- Reduce/replace ops, align preprocessing, resize arena with evidence, move buffers to correct memory.

## Regression tests

- Golden vector packet and latency budget threshold.

## Do-not-guess rules

- Do not retrain before proving firmware preprocessing and quantization are correct.
