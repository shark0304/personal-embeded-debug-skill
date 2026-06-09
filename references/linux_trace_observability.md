# Linux Tracing and Observability

Use this reference when `dmesg` alone is insufficient for embedded Linux: probe order, IRQ storms, latency, driver callbacks, blocked tasks, power/clock transitions, or intermittent runtime failures.

## Evidence to Collect

- Kernel version, config options, tracefs/debugfs availability, and root permissions.
- Full `dmesg`, dynamic debug state, trace clock, enabled events, and reproduction steps.
- Driver/module name, function names to trace, device sysfs path, and subsystem.
- Whether tracing overhead can alter the bug.

Use `linux_log_triage.py` before enabling heavier tracing.

## Dynamic Debug

Use dynamic debug when driver `dev_dbg()`/`pr_debug()` exists but is not printed.

```text
mount -t debugfs none /sys/kernel/debug
cat /proc/dynamic_debug/control
echo 'module my_driver +p' > /proc/dynamic_debug/control
echo 'file drivers/i2c/* +p' > /proc/dynamic_debug/control
dmesg -n 8
```

## Ftrace Basics

Use ftrace when call order, latency, IRQ timing, or scheduler behavior matters.

```text
mount -t tracefs none /sys/kernel/tracing
cd /sys/kernel/tracing
cat available_tracers
echo function_graph > current_tracer
echo my_driver_probe > set_graph_function
echo 1 > tracing_on
cat trace
echo 0 > tracing_on
```

## Event Tracing

Prefer subsystem tracepoints when available because they are more stable than function names.

```text
cat available_events
echo 1 > events/sched/sched_switch/enable
echo 1 > events/irq/irq_handler_entry/enable
echo 1 > events/workqueue/workqueue_execute_start/enable
cat trace_pipe
```

## Debugfs and Sysfs Checks

```text
cat /sys/kernel/debug/devices_deferred
cat /sys/kernel/debug/clk/clk_summary
cat /sys/kernel/debug/regulator/regulator_summary
grep . /sys/kernel/debug/pinctrl/*/pinmux-pins
find /sys/bus -name '*DEVICE*' -maxdepth 4
```

## Field Lessons

- Turn tracing on for the shortest possible reproduction window.
- Function tracing can be noisy; filter aggressively.
- Tracepoints often survive kernel refactors better than private function names.
- Dynamic debug requires code to already contain debug statements.
- Debugfs is not a stable ABI; use it for diagnostics, not production contracts.
- On small systems, tracing buffers can consume meaningful memory.

## Output Expectations

Return a trace plan with the smallest tracer/event set, exact commands, stop condition, and what result would confirm or reject the hypothesis.
