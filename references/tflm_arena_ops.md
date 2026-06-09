# TFLite Micro Arena, Ops, and Quantization Debug

Use this reference for TensorFlow Lite Micro deployments that build successfully but fail at allocation, miss latency, produce wrong outputs, or break after changing the model.

## Evidence to Collect

- `.tflite` size, model schema/version, and operator list.
- Resolver type and exact ops registered.
- Tensor arena size, alignment, address, and memory region.
- Allocation log from `RecordingMicroAllocator` when available.
- Input tensor type, shape, scale, zero-point, and preprocessing pipeline.
- Golden-vector output from desktop TFLite and target firmware.
- Whether CMSIS-NN, vendor NPU, DMA, or cached external memory is involved.

Use `scripts/memory_budget.py` for first-pass Flash/RAM sizing.
Use `scripts/vector_compare.py` when comparing desktop golden vectors against firmware dumps.

## Arena Failures

- An arena that fits one model revision may fail after converter/operator changes.
- Temporary tensors, persistent tensors, op data, and scratch buffers all compete for the same arena.
- Recording allocation is more useful than guessing a larger arena because it shows which bucket grew.
- Alignment and memory region matter. Some accelerators require arena or scratch buffers in specific SRAM.
- External SDRAM/PSRAM can solve capacity but introduce cache and latency problems.

## Operator Failures

- A model can be valid TFLite but unsupported by a micro resolver.
- `AllOpsResolver` is useful for diagnosis but often too large for production firmware.
- A custom or minimal resolver should match the model's actual operator list.
- Optimized kernels can have stricter constraints than reference kernels, especially around quantization, channel layout, and tensor shapes.

## Quantization and Accuracy Failures

- Firmware preprocessing must match training/export preprocessing byte-for-byte.
- For int8 tensors, compare raw quantized input bytes before inference, not just floating-point source data.
- Check input scale/zero-point and output dequantization before changing the model.
- Representative datasets must cover real sensor ranges; otherwise saturation can look like a firmware bug.
- Channel order, endian conversion, windowing, and fixed-point rounding are common embedded-only mismatch sources.

## Debug Procedure

1. Dump model metadata and op list from the `.tflite`.
2. Start with a resolver that proves op support, then reduce it.
3. Enable allocation recording and capture arena bucket sizes.
4. Run one golden raw input through desktop preprocessing and firmware preprocessing.
5. Dump target input tensor bytes immediately before `Invoke()`.
6. Compare output tensor before application postprocessing.
7. Measure capture, preprocessing, inference, and postprocessing separately.

## Output Expectations

Return the first failing contract: memory, op support, quantization, preprocessing, latency, or accelerator/cache integration. Ask for only the next artifact that can separate those contracts.
