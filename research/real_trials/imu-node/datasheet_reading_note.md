# imu-node Datasheet Reading Note

## Power

- Supply rails, voltage range, current modes:
- Power-up sequencing:
- Decoupling and layout notes:

## Clock

- Required input clocks or internal oscillators:
- Startup/settling timing:
- Clock output or synchronization options:

## Interface

- Bus type: I2C
- Signal voltage level:
- Bus speed and mode:
- Pull-up, termination, polarity, phase, or drive-strength requirements:

## Address

- I2C/SPI/chip-select/MDIO/PCIe address or strap options:
- Default address or ID:
- Address conflicts:

## Registers

| Register | Address | Reset | Purpose | Bring-up Use |
| --- | --- | --- | --- | --- |
| ID / WHO_AM_I | TBD | TBD | identity check | first read |
| reset/control | TBD | TBD | soft reset and mode control | init |
| status | TBD | TBD | ready/error flags | validation |

## Init Sequence

1. Verify rails, reset, and clock readiness.
2. Read identity register.
3. Apply reset or mode transition if required.
4. Configure interface, rate, range, interrupt/FIFO/DMA path.
5. Confirm ready/status bit before enabling high-rate traffic.

## Timing

- Power-on to first transaction:
- Reset release to ready:
- Conversion/sample latency:
- Interrupt pulse/level timing:

## Interrupts

- IRQ pin and polarity:
- Latch/pulse behavior:
- Clear condition:
- Required host GPIO configuration:

## Low Power

- Sleep/standby modes:
- Wake sources:
- State retained across low power:
- First transaction after wake requirements:

## Test Registers

- Identity register:
- Scratch/test register:
- Status/ready flags:
- Error counters or fault flags:
