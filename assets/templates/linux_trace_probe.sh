#!/bin/sh
# Embedded Linux tracing capture skeleton. Run as root on a debug image.
set -eu

DRIVER="${1:-}"
FUNCTION="${2:-}"
OUT_DIR="${3:-/tmp/embedded-trace}"

mkdir -p "$OUT_DIR"

dmesg > "$OUT_DIR/dmesg.before.txt" || true
cat /proc/cmdline > "$OUT_DIR/cmdline.txt" || true

mountpoint -q /sys/kernel/debug || mount -t debugfs none /sys/kernel/debug || true
mountpoint -q /sys/kernel/tracing || mount -t tracefs none /sys/kernel/tracing || true

if [ -r /sys/kernel/debug/devices_deferred ]; then
    cat /sys/kernel/debug/devices_deferred > "$OUT_DIR/devices_deferred.txt"
fi

if [ -r /sys/kernel/debug/clk/clk_summary ]; then
    cat /sys/kernel/debug/clk/clk_summary > "$OUT_DIR/clk_summary.txt"
fi

if [ -r /sys/kernel/debug/regulator/regulator_summary ]; then
    cat /sys/kernel/debug/regulator/regulator_summary > "$OUT_DIR/regulator_summary.txt"
fi

if [ -n "$DRIVER" ] && [ -w /proc/dynamic_debug/control ]; then
    echo "module $DRIVER +p" > /proc/dynamic_debug/control || true
fi

TRACE=/sys/kernel/tracing
if [ -d "$TRACE" ]; then
    echo 0 > "$TRACE/tracing_on" || true
    : > "$TRACE/trace" || true
    echo function_graph > "$TRACE/current_tracer" || true
    if [ -n "$FUNCTION" ]; then
        echo "$FUNCTION" > "$TRACE/set_graph_function" || true
    fi
    echo 1 > "$TRACE/tracing_on" || true
    echo "Tracing enabled. Reproduce the issue, then press Enter."
    read _
    echo 0 > "$TRACE/tracing_on" || true
    cat "$TRACE/trace" > "$OUT_DIR/ftrace.txt" || true
fi

dmesg > "$OUT_DIR/dmesg.after.txt" || true
echo "Saved trace artifacts to $OUT_DIR"
