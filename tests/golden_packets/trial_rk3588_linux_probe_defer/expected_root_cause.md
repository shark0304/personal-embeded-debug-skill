# Expected Root Cause

The camera sensor node references an analog supply that is missing or unresolved
in the board device tree.

Regression evidence:

- `dmesg.log` shows repeated probe-defer messages for regulator acquisition.
- Failing DTS lacks `avdd-supply` in the camera node.
- Adding a regulator-fixed node and `avdd-supply` phandle makes probe succeed in
  the sanitized trial.

Residual evidence gap:

- Runtime DTB is not included, so exact deployed DTB verification remains a
  follow-up check.
