# Symptom

Sanitized RK3588 Linux BSP bring-up packet. A camera sensor repeatedly defers
probe while waiting for regulator evidence; adding the regulator phandle makes
probe succeed in the sanitized trial.

This packet is promoted because the dmesg pattern and DTS fix branch are stable
and regression-friendly.
