# ESP-IDF Toolchain Bootstrap

Sources to verify before installing:

- ESP-IDF ESP32-S3 getting started: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/index.html
- ESP-IDF tools installer: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/index.html#get-started-get-esp-idf

## Required Tools

- Python
- Git
- `idf.py`
- `cmake`
- `ninja`
- ESP-IDF checkout and exported environment
- ESP32-S3 target support

## Install Commands

Use the official ESP-IDF installer or manual flow for the selected OS. A common
manual flow is:

```bash
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32s3
. ./export.sh
```

## Environment Variables

```bash
export IDF_PATH=~/esp/esp-idf
. "$IDF_PATH/export.sh"
```

## Sanity Checks

```bash
python --version
idf.py --version
idf.py --list-targets | grep esp32s3
cmake --version
ninja --version
```

Run the builder environment check:

```bash
python embedded-project-builder/scripts/check_toolchain_env.py \
  --scenario esp32s3_tinyml_motion_classifier \
  --board esp32s3 \
  --json
```

## First Build Command

From a generated scaffold:

```bash
cd research/real_trials/esp32s3-tinyml
idf.py -C app set-target esp32s3
idf.py -C app build 2>&1 | tee build.log
```

## Common Blockers

- `export.sh` was not sourced in the current shell.
- `IDF_PATH` points to a deleted or mismatched ESP-IDF checkout.
- Target was not set to `esp32s3`.
- Python virtual environment conflicts with ESP-IDF tools.
- Component CMake layout is incomplete after manual edits.

## Handoff To embedded-debug Condition

If `idf.py build` or runtime monitor fails after the toolchain check is green,
capture `build.log`, `sdkconfig`, serial output, reset reason, heap/stack
metrics, and model memory budget. Hand off to `embedded-debug` for ESP-IDF panic
or TinyML latency/memory triage.
