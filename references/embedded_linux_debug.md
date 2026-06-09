# Embedded Linux Debug

Use this reference for embedded Linux board bring-up and runtime debug: boot failure, missing device, driver probe failure, deferred probe, rootfs/init failure, kernel panic/oops, performance latency, or hardware described through device tree.

## Evidence to Collect

- SoC/board revision, bootloader, kernel version, kernel config, rootfs/init system.
- Boot arguments and full serial console log from reset to failure.
- DTS/DTSI/DTB actually booted, not only the source file expected by the build.
- Driver name, module name, bus path, compatible string, and binding document.
- `dmesg -T` or raw kernel log, plus `lsmod`, `modinfo`, sysfs bus path, and relevant debugfs output.
- Power rail, reset GPIO, clock, pinctrl, interrupt, DMA, and IOMMU dependencies.

Use `scripts/linux_log_triage.py` for a first pass over `dmesg` or boot logs. Read `linux_device_tree_probe.md` for DT/probe problems.

## Debug Ladder

1. Boot chain: ROM/SPL/U-Boot handoff, kernel image, DTB address, bootargs, initramfs/rootfs.
2. Kernel bring-up: early console, panic/oops, initcall failures, driver core binding.
3. Device description: DT compatible, status, reg, interrupts, clocks, resets, regulators, pinctrl, power domains.
4. Driver probe: module loaded, match table hit, resources acquired, deferred dependencies resolved.
5. Runtime: sysfs/debugfs state, tracepoints, ftrace, dynamic debug, perf/latency tooling.
6. Userspace: udev/systemd ordering, device nodes, permissions, services, and application logs.

## Field Lessons

- A driver not probing is often a device model problem before it is a C code problem: no matching compatible, disabled node, missing bus node, or missing dependency.
- Deferred probe is not random; it usually means a supplier such as regulator, clock, GPIO, PHY, panel, bridge, or firmware is not ready or not described correctly.
- The DTB actually loaded by the bootloader may not match the DTS you edited.
- `dmesg` often hides `dev_dbg()` detail unless dynamic debug and loglevel are enabled.
- Debugfs and sysfs show the kernel's current model of the hardware; use them before changing the driver.
- Never use `devmem` writes or forced GPIO/regulator changes on production hardware without understanding electrical side effects.

## Useful Commands

```text
dmesg -T
cat /proc/cmdline
cat /proc/device-tree/model
dtc -I fs -O dts /sys/firmware/devicetree/base
cat /sys/kernel/debug/devices_deferred
grep . /sys/kernel/debug/pinctrl/*/pinmux-pins
cat /sys/kernel/debug/clk/clk_summary
cat /sys/kernel/debug/regulator/regulator_summary
cat /proc/dynamic_debug/control
cat /sys/kernel/tracing/available_tracers
```

## Output Expectations

Return a layered diagnosis: boot/DT/probe/runtime/userspace. Include the next kernel-visible fact to collect, not only a code guess.
