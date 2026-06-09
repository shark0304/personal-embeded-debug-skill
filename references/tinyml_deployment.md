# TinyML Deployment Debug

Use this reference for MCU/edge AI deployment issues: memory overflow, tensor arena failure, unsupported ops, quantization accuracy drop, latency misses, and input pipeline mismatch.

## Required Evidence

- Target MCU/accelerator, clock, Flash, SRAM, external memory.
- Runtime: TFLite Micro, CMSIS-NN, vendor NPU/DSP runtime, ONNX Runtime embedded, custom C.
- Model size and operator list.
- Tensor arena or activation memory requirement.
- Input shape, sampling rate, preprocessing, normalization.
- Quantization type, scale, zero-point, representative dataset.
- Required latency and duty cycle.

Use `scripts/memory_budget.py` for first-pass Flash/RAM sizing.
Read `tflm_arena_ops.md` for TensorFlow Lite Micro arena recording, operator resolver, int8 quantization, and golden-vector workflows.
Read `latency_watchdog_budget.md` and use `scripts/latency_budget.py` when inference timing, task period, duty cycle, or watchdog resets are part of the symptom.

## Triage Order

1. Does the model fit Flash with firmware/runtime overhead?
2. Does RAM fit tensor arena, stacks, heap, DMA/input/output buffers, and reserve?
3. Are all operators supported by the target runtime?
4. Does firmware preprocessing match training preprocessing byte-for-byte?
5. Does int8 scale/zero-point handling match the exported model?
6. Does target output match golden vectors?
7. Does latency include sensor capture, preprocessing, inference, and postprocessing?
8. Does the worst-case path fit the task period and watchdog window with RTOS jitter?

## Accuracy Debug

- Export one golden raw input.
- Run it through Python preprocessing and firmware preprocessing.
- Dump target input tensor before inference.
- Compare tensor values and clipping.
- Compare logits/output before postprocessing.

## Runtime Debug

- Tensor arena too small.
- Missing kernel/operator.
- Incorrect memory alignment.
- Cache coherency issue for accelerator buffers.
- Input channel/order/endian mismatch.
- Quantized model using unsupported per-channel op.
- Latency spikes from RTOS scheduling or DMA contention.

## Output Expectations

Return:

- Fit/fail budget.
- Most likely deployment blocker.
- Golden-vector validation plan.
- On-target timing plan.
- One concrete next artifact to collect.
