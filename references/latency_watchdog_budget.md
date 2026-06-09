# Embedded AI Latency and Watchdog Budget

Use this reference when an embedded AI workload fits memory but misses deadlines, drops samples, overheats, drains power, or resets under watchdog after inference is enabled.

## Evidence to Collect

- Required sampling period, response deadline, and duty-cycle target.
- Measured time for sensor capture, DMA wait, preprocessing, inference, postprocessing, logging, and communication.
- Worst-case timing, not only average timing.
- RTOS task priority, competing ISRs, DMA contention, and scheduler tick/timer behavior.
- Watchdog timeout, feed location, and whether feeding can happen while inference is stuck.
- Clock frequency, power mode, accelerator/NPU/DSP use, and cache state.

Use `scripts/latency_budget.py` when component timings are known.

## Field Lessons

- "Inference takes 18 ms" is not a deployment budget. The deployed path also includes capture, windowing, feature extraction, postprocessing, and communication.
- Watchdog resets often mean the feed point proves the main loop is alive, not that the inference path made progress safely.
- Average latency hides ISR bursts, cache misses, flash wait states, RTOS blocking, and accelerator setup costs.
- Reducing model size may not reduce latency if preprocessing or memory movement dominates.
- DMA and accelerator offload can improve CPU availability while increasing cache coherency and buffer ownership risk.
- Logging inside a real-time path can turn a passing model into a deadline miss.

## Triage Flow

1. Instrument timestamps at every boundary: capture, preprocess, invoke, postprocess, publish.
2. Separate cold-start timing from steady-state timing.
3. Measure worst-case across enough cycles to include ISR and communication bursts.
4. Compare total worst-case time against task period and watchdog timeout.
5. Move watchdog feed so it represents completed progress, not just loop iteration.
6. If total time fails, decide whether to optimize preprocessing, model, memory placement, accelerator use, or scheduling.

## Fix Patterns

- Use double buffering to overlap capture and preprocessing when ownership is clear.
- Move feature extraction to fixed-point/CMSIS-DSP only after golden-vector parity is established.
- Pin inference task priority intentionally; avoid hidden priority inversion around shared buses.
- Feed watchdog after the critical pipeline stage completes, and record reset reason plus last stage.
- Disable or rate-limit logging on deadline paths.
- Track max latency in firmware and expose it through a debug command or telemetry.
