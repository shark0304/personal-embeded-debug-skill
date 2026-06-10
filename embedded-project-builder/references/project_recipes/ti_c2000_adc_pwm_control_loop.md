# TI C2000 ADC PWM Control Loop

## Project Goal

Build a deterministic ADC/PWM control-loop demo on TI C2000, validate timing margins, and capture evidence for control-loop faults.

## Default Target

- Board: TI C2000 F28P55x or comparable C2000 LaunchPad/controlCARD.
- Peripheral: ePWM, ADC, CMPSS, trip zone, CLA/CPU task path.
- Toolchain: Code Composer Studio, C2000Ware, TI compiler or GCC where supported.
- Interface: register-level peripheral init with scope-backed timing validation.

## Milestones

1. Start from a C2000Ware peripheral example for the exact device family.
2. Validate clock tree, ePWM frequency, ADC trigger source, and sample window.
3. Toggle a GPIO at ISR entry/exit for timing measurement.
4. Add closed-loop math with saturation and fault-path handling.
5. Validate trip zone, comparator, and safe PWM state.
6. Record CCS project settings, linker command file, memory map, and scope captures.

## Validation Criteria

- PWM frequency, duty range, and dead time match the design.
- ADC sample is phase-aligned to PWM and stable with known input.
- ISR worst-case time stays below the control period with margin.
- Fault input reliably forces the safe output state.

## Key Risks

- ADC acquisition window too short for source impedance.
- Interrupt latency or priority violates the control period.
- PWM shadow load or trip-zone configuration is misunderstood.
- CLA/CPU memory ownership or linker placement is wrong.
- Debugger halt changes real-time peripheral behavior.

## Debug Handoff

- Fault/reset: `$embedded-debug` Cortex-M-style register evidence plus platform notes.
- Timing overrun: `$embedded-debug` latency/watchdog budget runbook.
- Peripheral register mismatch: `$embedded-debug` datasheet/register review workflow.
