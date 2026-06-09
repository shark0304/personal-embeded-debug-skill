# Toolchain, SDK, and Debugger Reproducibility

Use this reference when a project behaves differently across machines, after package updates, after code generation, or when debugger/register views do not match silicon behavior.

## Evidence to Collect

- Compiler name/version, flags, linker script, startup file, and C library.
- Vendor SDK/HAL/Cube/Zephyr/PlatformIO package versions.
- Board package, device tree, Kconfig, or generated project metadata.
- Debug probe firmware, OpenOCD/J-Link/ST-LINK version, and SVD/debug pack.
- Map file, vector table address, bootloader offset, and memory layout.
- Last known good lockfile, package manifest, or generated-code diff.

## Field Lessons

- "Same source" is not the same build if toolchain, SDK, linker script, or generated files drift.
- SVD/register-view mismatches can waste time; trust direct register reads and the reference manual over a stale debugger pack.
- Generated code can overwrite clock tree, pin mux, IRQ priority, or DMA init order.
- Startup/vector table and linker-script mismatches often masquerade as random HardFaults.
- Optimizer level, LTO, newlib/newlib-nano, and floating-point ABI changes can expose stack or ABI bugs.

## Triage Flow

1. Capture exact tool versions and package versions before changing code.
2. Build with a clean tree and compare map files or binary size against last known good.
3. Inspect startup file, linker script, vector table relocation, and bootloader offsets.
4. Confirm generated code did not reorder clock, GPIO, DMA, or IRQ initialization.
5. Read suspect registers directly in GDB or firmware logs before trusting GUI register views.
6. Reproduce on one pinned toolchain before upgrading SDK/framework packages.

## Fix Patterns

- Pin toolchain and SDK/framework versions in project files or lockfiles.
- Commit generated configuration inputs, not only generated C files.
- Keep user code outside generated regions unless the generator contract is reliable.
- Store debugger launch config and SVD/debug pack version with the project.
- Add a minimal "board sanity" firmware that checks clocks, vector table, heap/stack boundaries, and key peripheral IDs.

Use `scripts/map_memory_summary.py` for a first-pass GNU ld map section summary when memory drift is suspect.
