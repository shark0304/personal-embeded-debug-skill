# Low-Power, Suspend/Resume, and Wake Debug

Use this reference for high sleep current, failed wakeup, immediate wake after suspend, runtime PM bugs, watchdog resets after sleep, and battery-life misses.

## Evidence to Collect

- Power rails measured, measurement point, instrument bandwidth, sample rate, and whether debugger/probe is attached.
- Active/sleep state timeline, expected wake sources, GPIO states, clock tree, regulators, and external peripherals.
- For Linux: wakeup sources, runtime PM status, regulator/clk summaries, suspend logs, `pm_test`, and device power/control files.
- For RTOS/MCU: sleep mode, retained RAM, wake reason, clock restore path, GPIO pulls, peripheral stop mode support.
- Battery capacity, duty cycle, average current target, peak current limits, and radio burst timing.

Use `average_current.py` for first-pass duty-cycle current estimates.

## Field Lessons

- A connected debugger can keep clocks, power domains, or debug blocks alive.
- Floating pins, wrong pulls, level shifters, sensors, pull-ups, and LEDs often dominate sleep current.
- "Entered sleep" in firmware does not prove rails or peripherals entered low power.
- Wakeup bugs often come from uncleared interrupt flags, wrong edge polarity, or disabled wake capability.
- Linux runtime PM and system suspend are different paths that can expose different driver bugs.
- Radio and sensor bursts dominate battery life even if average MCU current looks small.

## Triage Flow

1. Measure current with a known-good minimal firmware before debugging the full application.
2. Disable external loads systematically: sensors, radios, level shifters, LEDs, pull-ups.
3. Confirm wake reason and whether wake flag was stale.
4. For Linux, inspect `/sys/kernel/debug/wakeup_sources`, `power/control`, and suspend phase logs.
5. For MCU, verify clock restore, peripheral reinit, and RTOS tickless idle behavior.
6. Build an average-current budget and compare measured current by state.

## Fix Patterns

- Gate sensor/radio rails intentionally and define GPIO safe states before sleep.
- Avoid debugger-attached current numbers for final battery estimates.
- Move logging out of sleep entry/exit hot paths.
- Record wake reason, sleep entry time, and last active subsystem in retention RAM or persistent logs.
