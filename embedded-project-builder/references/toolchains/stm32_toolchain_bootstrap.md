# STM32H7 Toolchain Bootstrap

Sources to verify before installing:

- STM32CubeMX product page: https://www.st.com/en/development-tools/stm32cubemx.html
- Arm GNU Toolchain downloads: https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads
- OpenOCD project: https://openocd.org/pages/getting-openocd.html
- pyOCD documentation: https://pyocd.io/

## Required Tools

- `cmake`
- `ninja`
- `arm-none-eabi-gcc`
- OpenOCD or pyOCD for flash/debug validation
- STM32CubeMX is optional for code generation and pin/peripheral review

## Install Commands

Example macOS package flow:

```bash
brew install cmake ninja
brew install --cask gcc-arm-embedded
brew install openocd
python3 -m pip install --user pyocd
```

If Homebrew casks change, use Arm's official GNU Toolchain download and add its
`bin` directory to PATH.

## Environment Variables

```bash
export PATH="/path/to/arm-gnu-toolchain/bin:$PATH"
```

Optional board/debug variables for local scripts:

```bash
export STM32_BOARD=stm32h743
export OPENOCD_INTERFACE=stlink
```

## Sanity Checks

```bash
cmake --version
ninja --version
arm-none-eabi-gcc --version
openocd --version
pyocd --version
```

Run the builder environment check:

```bash
python embedded-project-builder/scripts/check_toolchain_env.py \
  --scenario stm32h7_dma_adc_logger \
  --board stm32h743 \
  --json
```

## First Build Command

The STM32H7 scaffold intentionally does not generate a full HAL project. Start
from a vendor or board-specific project, then use:

```bash
cmake -S app -B build -G Ninja
cmake --build build 2>&1 | tee build.log
```

Only run this after adding a real CMake/HAL project or adapting a vendor
example.

## Common Blockers

- Arm compiler not in PATH.
- Project generated for a different STM32H7 part or board revision.
- Linker script and DMA buffer memory region do not match the actual device.
- OpenOCD/pyOCD probe support is missing.
- D-cache is enabled before DMA buffer policy is defined.

## Handoff To embedded-debug Condition

If the toolchain is ready but build, flash, hardfault, DMA data-integrity, or
runtime timing validation fails, collect build log, map file, linker script,
buffer addresses, cache policy, and runtime logs. Hand off to `embedded-debug`
DMA/cache, Cortex-M fault, or timing-budget runbooks.
