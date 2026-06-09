# Storage, Boot, and Filesystem Debug

Use this reference for boot loops, rootfs mount failures, eMMC/SD/NAND errors, UBI/UBIFS issues, filesystem corruption, slow boot, OTA slot storage problems, and power-loss durability.

## Evidence to Collect

- Full serial boot log from reset, bootargs, partition table, storage type, and rootfs type.
- Kernel config for storage/filesystem drivers and whether they are built-in or modules.
- `dmesg`, `lsblk`, `blkid`, mount options, `/proc/cmdline`, and bootloader environment.
- For eMMC/SD: voltage mode, bus width, speed mode, tuning logs, card detect/write protect, reset/power rails.
- For NAND/UBI: eraseblock size, bad block count, UBI attach logs, volume layout, wear-leveling and power-cut history.
- For power-loss: last write path, fsync policy, journal mode, and whether storage has reliable flush/FUA.

Use `boot_log_timeline.py` for boot delay/gap analysis.

## Field Lessons

- Rootfs failures are often missing built-in storage drivers, wrong `root=`, wrong DT node, or bootloader passing the wrong DTB.
- eMMC/SD failures can be electrical, timing, pinctrl, regulator, or tuning issues before they are filesystem issues.
- NAND/UBI problems need eraseblock and bad-block context; treating raw NAND like block storage is a common mistake.
- Power loss can corrupt application data even when the filesystem survives.
- Slow boot is easier to debug from timestamp gaps than from reading logs linearly.
- OTA partition layouts must be checked against actual image sizes and rollback metadata, not only source config.

## Triage Flow

1. Identify the boot stage that fails: bootloader, kernel mount, init, service, or application.
2. Confirm the actual booted DTB and bootargs.
3. Confirm the storage driver is available before rootfs mount.
4. Inspect storage errors before filesystem errors.
5. For corruption, distinguish media faults, power loss, missing flush, and application write protocol.
6. For slow boot, compute largest timestamp gaps and map them to subsystems.

## Fix Patterns

- Build rootfs-critical storage/filesystem drivers into the kernel, not modules.
- Use explicit partition UUIDs or labels when device enumeration can change.
- Use atomic write/rename patterns and fsync directories for critical small files.
- Keep bootloader environment, partition map, and kernel DTB in versioned release artifacts.
