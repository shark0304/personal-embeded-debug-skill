# Embedded Debug Report

## 1. Case summary

- Case ID: `rk3588_linux_probe_defer`
- Platform: `embedded-linux`
- Board: `rk3588_custom_carrier`
- Shield: `unknown`
- Toolchain: `clang`
- Build system: `kernel`
- Analysis status: `analyzed`

## 2. Evidence completeness

- dmesg: 1 artifact(s)
- dts: 1 artifact(s)
- kconfig: 1 artifact(s)

## 3. Missing critical evidence

- dtb

## 4. Hypothesis ranking

### H1: The camera sensor node references an analog supply that is missing or not resolved in the board device tree.

- Confidence: high
- Evidence for: dmesg.log shows repeated -EPROBE_DEFER for the camera sensor; rk3588-board.dts contains a camera node without avdd-supply; Adding a regulator-fixed node and avdd-supply phandle makes probe succeed in the sanitized trial
- Evidence against: The I2C adapter is present before the sensor probe; Kernel config includes regulator and V4L2 sensor support
- Missing evidence: compiled dtb for exact runtime check
- Verification step: Decompile the runtime DTB, confirm avdd-supply resolves to a regulator, and reboot with dynamic debug enabled for the sensor driver.
- Expected observation: The defer loop disappears and the sensor driver logs successful regulator acquisition before probe completion.
- Fix if confirmed: Add the correct regulator-fixed node and avdd-supply phandle to the board DTS, then preserve the decompiled DTB and dmesg.

### H2: The camera reset GPIO polarity is incorrect and holds the sensor in reset.

- Confidence: low
- Evidence for: Reset GPIO errors can prevent camera probe
- Evidence against: The logged failure is a deferred regulator branch rather than a chip ID read failure
- Missing evidence: reset GPIO waveform
- Verification step: Trace regulator_get and reset GPIO transitions with dynamic debug and a scope capture.
- Expected observation: A reset polarity issue would show regulator acquisition succeeds but chip ID read fails or reset remains asserted.
- Fix if confirmed: Correct reset-gpios polarity and preserve scope evidence.


## 5. Verification plan

- H1: Decompile the runtime DTB, confirm avdd-supply resolves to a regulator, and reboot with dynamic debug enabled for the sensor driver.
- H2: Trace regulator_get and reset GPIO transitions with dynamic debug and a scope capture.

## 6. Fix plan

- H1: Add the correct regulator-fixed node and avdd-supply phandle to the board DTS, then preserve the decompiled DTB and dmesg.
- H2: Correct reset-gpios polarity and preserve scope evidence.

## 7. Regression recommendation

- Preserve this debug packet as a golden packet after root cause and verification are complete.
