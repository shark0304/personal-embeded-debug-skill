# Suggested Startup Delay Patch

This is a verification patch template, not a confirmed fix. Apply only for an
experiment where serial logs and scope capture show the first I2C transaction
occurs before the IMU rail is stable.

Example overlay snippet:

```dts
/ {
	lsm6ds3tr-c-en {
		startup-delay-us = <5000>;
	};
};
```

Optional isolation changes while measuring:

```dts
&i2c0 {
	clock-frequency = <I2C_BITRATE_STANDARD>;
};
```

Experiment protocol:

1. Capture the failing baseline waveform.
2. Increase `startup-delay-us` in one step.
3. Rebuild and boot at least ten times.
4. Confirm the first I2C address phase ACKs and the serial log no longer reports
   the LSM6DSL init error.
5. Keep the smallest delay with margin and preserve the capture in the golden
   packet.
