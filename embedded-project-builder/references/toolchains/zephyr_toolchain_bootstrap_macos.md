# Zephyr Toolchain Bootstrap For macOS Intel

Sources to verify before installing:

- Zephyr getting started: https://docs.zephyrproject.org/latest/develop/getting_started/index.html
- Zephyr supported host systems: https://docs.zephyrproject.org/latest/develop/getting_started/index.html#supported-host-systems
- Zephyr SDK installation: https://docs.zephyrproject.org/latest/develop/toolchains/zephyr_sdk.html

## Required Tools

- Python 3.10+ recommended for current Zephyr workflows.
- `west`
- `cmake`
- `ninja`
- `dtc`
- Git
- Zephyr workspace
- Zephyr SDK or another configured supported compiler toolchain

Note: current Zephyr latest documentation states x86-64 macOS is not a
supported host system. For Intel Mac, treat this as a version-sensitive setup:
pin a known Zephyr version that supports your host, use a container/VM/Linux
builder, or use a remote CI builder before spending time on application bugs.

## Install Commands

macOS package prerequisites:

```bash
brew install cmake ninja gperf ccache dfu-util dtc git python
```

Python environment and west:

```bash
python3 -m venv ~/zephyr-venv
source ~/zephyr-venv/bin/activate
pip install --upgrade pip west
```

Workspace:

```bash
west init ~/zephyrproject
cd ~/zephyrproject
west update
west zephyr-export
pip install -r zephyr/scripts/requirements.txt
```

Install the Zephyr SDK that matches the selected Zephyr release. Prefer the
official SDK page for the exact archive name and host support status.

## Environment Variables

```bash
export ZEPHYR_BASE=~/zephyrproject/zephyr
export ZEPHYR_SDK_INSTALL_DIR=/path/to/zephyr-sdk
export PATH="$HOME/zephyr-venv/bin:$PATH"
```

## Sanity Checks

```bash
python --version
west --version
cmake --version
ninja --version
dtc --version
west topdir
west boards | grep -i xiao
```

Run the builder environment check:

```bash
python embedded-project-builder/scripts/check_toolchain_env.py \
  --scenario zephyr_st_imu_sensor_node \
  --board xiao_ble/nrf52840/sense \
  --json
```

## First Build Command

From a generated scaffold:

```bash
cd research/real_trials/imu-node
west build -b xiao_ble/nrf52840/sense app -p always 2>&1 | tee build.log
```

## Common Blockers

- `west` installed in a virtual environment that is not active.
- `ZEPHYR_BASE` points to a stale or missing workspace.
- Zephyr SDK host package does not support the local CPU/OS.
- `west boards` does not list the target board.
- DTS overlay references a bus, GPIO, or compatible that differs from the board
  revision.
- Build is run outside the intended Zephyr workspace.

## Handoff To embedded-debug Condition

If the environment check is green but `west build` fails, collect `build.log`,
`app/prj.conf`, overlays, generated `.config`/DTS when present, and board/SDK
version evidence. Then hand off to `embedded-debug` for Zephyr DTS/Kconfig or
sensor bring-up triage.
