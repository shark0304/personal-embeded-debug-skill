# BLE, Wi-Fi, and Cellular Connectivity Debug

Use this reference for intermittent disconnects, pairing failures, low throughput, high latency, DHCP/DNS/TLS failures, modem attach failures, and radio coexistence issues.

## Evidence to Collect

- Radio stack, SDK version, regulatory region, antenna/module, firmware, and coexistence settings.
- Timestamped logs from connection start through failure, including reason/status codes.
- BLE: role, connection interval, supervision timeout, MTU, PHY, RSSI, security state, and GATT operation.
- Wi-Fi: channel, RSSI, auth mode, DHCP/DNS/TLS stage, power save mode, roaming, AP logs if available.
- Cellular: SIM state, operator, RAT, band, attach status, PDP context, APN, modem firmware, AT trace.
- RTOS task priorities, logging load, heap, buffer pools, and radio coexistence with sensor/DMA workloads.

## Field Lessons

- Disconnect reason codes matter more than generic "lost connection" logs.
- Breakpoints and verbose logging can break BLE/cellular timing.
- BLE throughput is constrained by connection interval, MTU, PHY, packet count, and application buffering.
- Wi-Fi failures should be separated into association, DHCP, DNS, TCP, TLS, and application protocol stages.
- Cellular attach can fail from SIM, RF, operator policy, APN, power supply droop, or modem firmware.
- RF problems and firmware scheduling problems can look identical without timestamps and RSSI/status codes.

## Triage Flow

1. Split the failure by layer: RF/link, IP, TLS, application, or scheduling.
2. Capture reason/status codes and timestamps.
3. Compare failure with logging reduced and debugger detached.
4. Check heap/buffer pools and task priorities under radio load.
5. For coexistence, test radio alone, sensor/DMA alone, then combined.
6. For field failures, record environment, channel/RSSI/operator, and firmware version.

## Fix Patterns

- Add structured connection state telemetry with reason codes.
- Use bounded queues for radio-to-application handoff.
- Avoid long critical sections and blocking storage writes in radio callbacks.
- Treat power integrity as part of connectivity debug for Wi-Fi and cellular bursts.
