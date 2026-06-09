# Nordic nRF Connect SDK and Zephyr Debug Pack

Use this reference for Nordic nRF52/nRF53/nRF54/nRF91 projects, nRF Connect SDK, Zephyr drivers, devicetree/Kconfig, BLE/cellular timing, Partition Manager, TF-M secure/non-secure splits, and RTT/UART logging.

## Evidence to Collect

- Board target, exact NCS version, Zephyr revision, west manifest, toolchain, and build directory.
- `prj.conf`, overlays, board files, generated `build/zephyr/zephyr.dts`, `autoconf.h`, and `zephyr.map`.
- Runtime log backend, RTT/UART settings, log level, and whether logging changes timing.
- `device_is_ready()` result, devicetree node status, compatible, and enabled Kconfig symbols.
- BLE/cellular stack state, connection interval, interrupt load, and whether breakpoints disturb timing.
- Partition Manager output, TF-M secure/non-secure target, flash layout, and bootloader/MCUboot config.

## High-Value Nordic/Zephyr Lessons

- Generated files are the truth. Inspect `zephyr.dts` and `autoconf.h` before blaming the driver.
- A devicetree node can exist but still be disabled, missing a binding, or lacking the Kconfig symbol that builds its driver.
- NCS is Zephyr-based but not identical to upstream Zephyr; version and manifest matter.
- BLE/cellular timing can be disrupted by breakpoints, heavy logging, or long critical sections.
- RTT logging is convenient but can still perturb timing if blocking or too verbose.
- Secure/non-secure target mismatch can look like a peripheral or memory fault.
- Partition Manager and MCUboot settings can explain flash/slot/runtime surprises.

## Debug Flow

1. Confirm the board target and NCS version from the build, not memory.
2. Inspect generated `zephyr.dts` for the node path, status, compatible, pins, interrupts, and aliases.
3. Inspect `autoconf.h` for required `CONFIG_*` symbols.
4. Check `device_is_ready()` and init priority if the device exists but is not usable.
5. Use Zephyr thread analyzer for stack/runtime snapshots.
6. Reduce logging and avoid breakpoints in timing-sensitive BLE/cellular windows when testing race/timing bugs.
7. Check Partition Manager, MCUboot, and TF-M output before changing linker or flash assumptions.

## Useful Commands

```text
west build -t menuconfig
west build -t guiconfig
west build -t devicetree
west build -t rom_report
west build -t ram_report
```
