# ESP32S3 TinyML Motion Classifier

## Project Goal

Create an ESP32-S3 TinyML demo that samples motion data, runs a small classifier, and validates latency, memory, and watchdog safety.

## Default Target

- Board: ESP32-S3 devkit or sensor-enabled module.
- Sensor/peripheral: IMU over I2C/SPI, microphone, or synthetic motion input.
- Toolchain: ESP-IDF, pytest-embedded for regression.
- Runtime: TFLite Micro, ESP-NN, or a compact C inference path.

## Milestones

1. Build and flash a minimal ESP-IDF app with boot/version logging.
2. Bring up the sensor or synthetic input path without inference.
3. Add feature extraction with bounded buffers.
4. Add inference and measure arena size, heap, stack, and latency.
5. Enable watchdog-safe task scheduling.
6. Capture serial logs for reset reason, panic, allocation failures, and timing.
7. Promote stable checks into pytest-embedded or a scripted serial test.

## Validation Criteria

- Serial log reports model version, arena size, heap before/after, stack watermark, and inference time.
- Worst-case inference latency fits the sampling budget.
- No watchdog reset or heap fragmentation over a sustained run.
- Test input produces expected class and confidence range.

## Key Risks

- Tensor arena too small or placed in unsuitable memory.
- Inference blocks sensor sampling or watchdog feeding.
- PSRAM/cache behavior changes latency under load.
- Sensor init failure is hidden by ML logs.
- Quantization mismatch between training and embedded preprocessing.

## Debug Handoff

- Guru Meditation, panic, or watchdog: `$embedded-debug` ESP-IDF panic/field diagnostics runbooks.
- TinyML memory or latency miss: `$embedded-debug` TinyML latency/memory runbook.
- Sensor probe failure: `$embedded-debug` Zephyr/ESP bus bring-up style evidence packet.
