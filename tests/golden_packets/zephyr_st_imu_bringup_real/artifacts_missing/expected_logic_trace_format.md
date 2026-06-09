# Expected I2C Logic Trace Format

This packet still needs a real capture from reset through the first LSM6DSL
register transaction.

Preferred decoded CSV columns:

```text
time,event,address,rw,ack,data
```

Minimum rows to preserve:

- First START after boot or sensor enable.
- Address phase for the DTS `reg` value, currently `0x6a`.
- ACK/NACK result for the address phase.
- Register write/read sequence around identity or reboot access.
- STOP or repeated START around the failed transaction.

Acceptable raw/simple CSV columns:

```text
time,scl,sda
```

Raw trace requirements:

- Include at least 5 ms before sensor initialization starts.
- Include the first visible START-like SDA falling edge while SCL is high.
- Preserve idle level before START so pull-up and stuck-low checks are possible.
- Export the analyzer native file too when available.

Run after capture:

```text
python scripts/analyze/analyze_i2c_logic_trace.py --trace logic_trace.csv --out logic_trace_analysis.json
```
