# Testing And Validation Strategy

## Validation Layers

- Build: clean build, pinned SDK, recorded flags, stored log.
- Flash: reproducible command, expected target ID, stored flash log.
- Boot: serial banner, firmware version, board, reset reason.
- Peripheral: first transaction, identity read, expected status flags.
- Runtime: throughput, latency, memory, stack, watchdog, and error counters.
- Hardware: bus trace, power rail waveform, timing measurements where needed.
- Regression: packet, script, CI/HIL test, or manual checklist.

## Test Design

- Define expected observation before running the test.
- Avoid changing multiple variables between runs.
- Preserve both success and failure logs for comparison.
- Convert a repeated real failure into a debug packet or golden packet.

## CI/HIL Hooks

- Zephyr: Twister case or sample overlay.
- ESP-IDF: pytest-embedded serial test.
- Linux: kselftest, module probe script, or boot-log parser.
- MCU/RTOS: serial smoke test, Renode test, or hardware lab checklist.
