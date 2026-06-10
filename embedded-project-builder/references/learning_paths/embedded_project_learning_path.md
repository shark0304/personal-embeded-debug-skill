# Embedded Project Learning Path

Use this path when the user wants to learn by building rather than only reading.

## Stage 1: Environment And Board Confidence

- Install the SDK/toolchain and record exact versions.
- Build and flash an unmodified vendor or upstream sample.
- Capture a serial boot banner with board, firmware version, and build time.
- Keep the first successful build log as the baseline.

## Stage 2: Datasheet-Driven Peripheral Understanding

- Read only the sections that affect bring-up first: power, clock, interface, address, reset, identity/status registers, timing, interrupts, and low power.
- Convert every assumption into a checkable note in `datasheet_reading_note.md`.
- Mark unknowns that require a scope, logic analyzer, or board schematic.

## Stage 3: Minimal Driver Bring-up

- Start with one safe identity/status read.
- Add the smallest configuration sequence that makes polling work.
- Delay interrupt, FIFO, DMA, and ML/control paths until basic read/write evidence is stable.
- Log return codes, raw register values, and bus/device identity.

## Stage 4: Feature Path

- Add interrupts, FIFO, DMA, model inference, NPU, or control-loop logic one feature at a time.
- Define rate, latency, memory, and data-integrity budgets before optimizing.
- Capture failure evidence before changing multiple variables.

## Stage 5: Validation And Regression

- Preserve build, flash, serial, bus, timing, and power evidence.
- Promote confirmed failures to a debug packet, golden packet, or CI/HIL test.
- Use `$embedded-debug` for evidence-first triage when behavior diverges from the plan.
