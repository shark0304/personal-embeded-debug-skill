# {{project_name}} Validation Plan

## Build Validation

- Command:
- SDK/toolchain version:
- Expected result:
- Artifact to keep: build log, ELF/map when relevant.

## Flash Validation

- Command:
- Probe/interface:
- Expected result:
- Artifact to keep: flash log.

## Serial Log Validation

- Port and baud:
- Required boot fields: project, firmware version, board, peripheral, build time.
- Required bring-up fields: bus, address, ID, init status.

## Bus-level Validation

- Instrument: logic analyzer, oscilloscope, bus scanner, or kernel trace.
- First transaction expected:
- Healthy signature:
- Failure signature:

## Timing Validation

- Startup delay:
- Sample/conversion latency:
- ISR/workqueue latency:
- Throughput budget:

## Power Validation

- Rail probe point:
- Startup waveform:
- Brownout/reset threshold:
- Current budget:

## Regression Criteria

- Failure has a minimal reproduction.
- Expected observation is recorded.
- A debug packet, CI/HIL case, or manual checklist exists.
- Fixed behavior is checked by build, flash, runtime log, and domain-specific evidence.
