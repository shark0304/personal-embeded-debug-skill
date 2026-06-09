# Linux SoC BSP and Board-Port Debug

Use this reference for NXP i.MX, Rockchip, Allwinner, TI, Qualcomm, and similar embedded Linux SoC board ports where bootloader, DT, pinctrl, clocks, regulators, PHYs, and vendor BSP deltas interact.

## Evidence to Collect

- SoC, board revision, PMIC, DDR config, boot media, boot ROM/SPL/U-Boot/kernel versions.
- Vendor BSP version, upstream kernel delta, defconfig, DTS/DTSI stack, overlays, and booted DTB.
- U-Boot environment, bootargs, DDR training logs, power rail sequencing, reset lines, and strap pins.
- For peripherals: pinctrl, clocks, resets, regulators, power domains, PHYs, IOMMU, DMA masks, interrupts.
- For multimedia/display/camera: graph endpoints, bridges, panels, clocks, regulators, media controller graph.

## Field Lessons

- BSP bugs often live at integration boundaries: bootloader DT fixups, PMIC rails, pinctrl, clocks, and reset sequencing.
- Vendor kernels can carry non-upstream bindings; mixing upstream DTS with vendor drivers is risky.
- A peripheral can probe successfully and still fail if clocks, power domains, or graph endpoints are wrong.
- DDR, PMIC, and boot media problems may appear as random kernel failures later.
- Bootloader and kernel may use different DTBs or mutate the DT before boot.

## Triage Flow

1. Identify the boot stage and exact artifacts: SPL, U-Boot, kernel image, DTB, rootfs.
2. Dump the booted DTB and compare it to source.
3. Check PMIC/regulator, clk, reset, and pinctrl debugfs state.
4. Confirm vendor BSP binding expectations before copying upstream examples.
5. For display/camera, inspect media graph and endpoint links.
6. Reduce to one peripheral with minimal overlays before debugging the full board.

## Fix Patterns

- Version bootloader, DTB, kernel, rootfs, and PMIC/DDR configs as one release bundle.
- Keep board-specific DTS small and push shared SoC facts into the right `.dtsi`.
- Add board bring-up logs that print model, DT compatible, bootargs, and key rail/clock status.
