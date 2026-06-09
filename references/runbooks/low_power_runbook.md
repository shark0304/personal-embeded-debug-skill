# Low-Power Runbook

## Trigger symptoms

- Sleep current too high, wakes immediately, battery life short, suspend/resume failure.

## Minimum evidence

- Measurement setup, rails, debugger state, wake source, GPIO states, duty cycle, sleep mode, power tree.

## Fast triage

1. Run `average_current.py`.
2. Compare minimal firmware current to full app.
3. Disable external loads systematically.

## High-probability root causes

- Debugger attached, floating GPIO, external load, radio burst, stale wake flag, runtime PM mismatch.

## Scripts to run

- `scripts/average_current.py`

## Manual experiments

- Measure with debugger detached, isolate rails, log wake reason in retention RAM.

## Fix patterns

- Define sleep GPIO states, gate rails, clear wake flags, reduce logging, fix runtime PM callbacks.

## Regression tests

- Power trace packet with average current threshold.

## Do-not-guess rules

- Do not trust datasheet sleep current without board-level measurement.
