# RK3588 Linux I2C Driver Probe

## Project Goal

Bring up a Linux I2C device driver on RK3588, prove device-tree binding correctness, and capture probe/defer evidence.

## Default Target

- Board: RK3588 SBC or custom carrier.
- Peripheral: I2C sensor, PMIC, codec, GPIO expander, or NPU-adjacent control device.
- Toolchain: vendor BSP or mainline-oriented kernel tree, dtc, dmesg, ftrace when needed.
- Interface: Linux I2C client driver with device-tree binding.

## Milestones

1. Confirm kernel source, defconfig, DTS include chain, and board revision.
2. Add or verify binding, compatible string, regulator, clock, pinctrl, reset, and IRQ properties.
3. Build kernel/DTB/modules and deploy them as a matched set.
4. Capture boot log, `dmesg`, `/proc/device-tree`, and module load evidence.
5. Validate probe path, deferred probe reason, and bus transaction evidence.
6. Add a userspace smoke test or kselftest-style check.

## Validation Criteria

- Running DTB contains the expected node and phandles.
- Driver matches compatible string and reaches probe.
- Regulator/clock/GPIO dependencies are either ready or explicitly deferred.
- Failure logs contain enough evidence to distinguish defer, ENODEV, EIO, and missing node.

## Key Risks

- Edited DTS is not the DTB actually booted.
- Compatible string is absent from driver match table.
- Regulator, clock, reset, or pinctrl dependency causes deferred probe.
- Vendor BSP has out-of-tree binding differences.
- Device address conflicts or board straps differ from schematic.

## Debug Handoff

- Probe failure or `-EPROBE_DEFER`: `$embedded-debug` Linux driver probe runbook.
- Boot/DTB mismatch: `$embedded-debug` boot failure or Linux DTS/probe evidence flow.
- NPU demo latency/memory issue: `$embedded-debug` TinyML or Linux observability runbook.
