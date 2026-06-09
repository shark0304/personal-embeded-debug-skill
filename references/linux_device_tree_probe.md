# Linux Device Tree and Driver Probe Debug

Use this reference when a Linux device does not appear, `probe()` is not called, probe returns an error, or the log shows deferred probe.

## Evidence to Collect

- Actual booted DTS from `/sys/firmware/devicetree/base` or `/proc/device-tree`.
- Node path, `compatible`, `status`, `reg`, interrupts, clocks, resets, regulators, GPIOs, pinctrl, power domains, and bus parent.
- Driver `of_match_table`, module aliases, and binding YAML.
- `dmesg` around the device, `devices_deferred`, and sysfs bus entries.
- Whether the dependency is built-in, module, disabled, missing from DT, or probing later.

## Probe Triage

1. Confirm the node exists in the booted DTB.
2. Confirm `status = "okay"` or no disabling status.
3. Confirm the parent bus/controller node is enabled and probed.
4. Confirm the driver has a matching compatible string or bus ID.
5. Confirm required resources match the binding: `reg`, IRQ, clocks, resets, supplies, GPIOs, pinctrl.
6. If deferred, inspect `/sys/kernel/debug/devices_deferred` and search dmesg for the supplier.
7. Enable dynamic debug for the driver or subsystem before adding printk patches.
8. Trace probe/remove only after the static DT/resource checks pass.

Use `scripts/dts_probe_check.py` for a first-pass check of node presence, `compatible`, `status`, and required properties. Use `scripts/kconfig_check.py` when the likely driver or supplier may not be built.

## Common Root Causes

- Editing a DTS that is not the DTB actually loaded.
- Compatible string typo or missing fallback compatible.
- Node disabled by an included `.dtsi` or overlay order.
- Missing `*-supply`, clock, reset, PHY, endpoint, or pinctrl dependency.
- Wrong address/size cells or wrong `reg` value under the parent bus.
- Interrupt specifier mismatched to interrupt controller cells.
- Driver built as a module but not loaded, or built-in dependency probing later.
- GPIO polarity or reset sequencing inverted.

## Dynamic Debug Examples

```text
mount -t debugfs none /sys/kernel/debug
echo 'file drivers/i2c/* +p' > /proc/dynamic_debug/control
echo 'module my_driver +p' > /proc/dynamic_debug/control
dmesg -n 8
```

## Ftrace Examples

```text
mount -t tracefs none /sys/kernel/tracing
echo function_graph > /sys/kernel/tracing/current_tracer
echo 'my_driver_probe' > /sys/kernel/tracing/set_graph_function
echo 1 > /sys/kernel/tracing/tracing_on
cat /sys/kernel/tracing/trace
```

## Output Expectations

Return whether the current evidence points to DT match, supplier dependency, resource parsing, driver code, or userspace visibility. Avoid jumping to driver patches before confirming the kernel's device model state.
