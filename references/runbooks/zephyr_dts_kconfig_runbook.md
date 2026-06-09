# Zephyr DTS/Kconfig Runbook

## Trigger symptoms

- `device_is_ready()` false, driver not built, overlay ignored, node missing, probe/init failure.

## Minimum evidence

- Board target, NCS/Zephyr version, west manifest, `prj.conf`, overlays, generated `zephyr.dts`, `autoconf.h`, build log.

## Fast triage

1. Inspect generated files, not only source overlays.
2. Run `dts_probe_check.py` against generated `zephyr.dts`.
3. Run `kconfig_check.py` for required driver symbols.
4. Check node `status`, `compatible`, aliases, chosen nodes, and init priority.

## High-probability root causes

- Overlay not applied, node disabled, compatible typo, missing binding, Kconfig symbol disabled, wrong board target.

## Scripts to run

- `scripts/dts_probe_check.py`
- `scripts/kconfig_check.py`
- `scripts/linux_log_triage.py` for logs shaped like probe/init failures.

## Manual experiments

- Build with verbose CMake, run `west build -t devicetree`, compare generated DTS before/after overlay.
- Add minimal sample using the same node.

## Fix patterns

- Correct overlay path, enable Kconfig, fix compatible/status/alias, update board target or shield overlay.

## Regression tests

- Golden packet containing `zephyr.dts`, `autoconf.h`, and expected node readiness.

## Do-not-guess rules

- Do not judge Zephyr driver state without generated DTS and config.
- Do not edit driver code before proving node/config mismatch is not the cause.
