# Deployment Checklist

## Release Evidence

- Firmware image, version, git revision, SDK/toolchain version, and board revision.
- Build log, map/size summary, and configuration artifacts.
- Flash/update method and rollback path.

## Runtime Observability

- Boot banner and reset reason.
- Health counters for bus errors, watchdog, queue drops, memory, and latency.
- Field log ring buffer or crash packet when available.

## Update And Recovery

- Bootloader/OTA compatibility.
- Image signing or checksum policy.
- Power-fail behavior during update.
- Safe-mode or factory fallback.

## Handoff To Debug

- Any deployed failure should become a `$embedded-debug` packet before a fix is declared.
- Include last-known-good version, field logs, device metrics, and reproduction boundaries.
