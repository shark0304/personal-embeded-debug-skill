# Board Porting Checklist

## Board Identity

- Exact board revision, schematic revision, BOM option, and strap settings.
- Boot mode pins and debug probe wiring.
- Power rails, regulators, enables, reset lines, and sequencing.

## Firmware Description

- Devicetree, pinmux, board header, linker script, and Kconfig/defconfig changes.
- Clock tree, oscillator source, PLL, and peripheral clocks.
- Console UART and boot log path.

## Peripheral Readiness

- Pin ownership and alternate functions.
- Voltage domains and level shifters.
- Pull-up/down requirements.
- Interrupt lines, polarity, wake capability, and shared IRQs.

## Validation

- Board boots a minimal sample.
- Console is stable at the selected baud rate.
- One GPIO toggle is visible.
- One bus scan or known transaction succeeds.
- Power and reset timing are measured when the peripheral depends on them.
