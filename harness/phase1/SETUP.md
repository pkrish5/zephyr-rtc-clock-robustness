# Phase 1 host setup (macOS Apple Silicon)

The recorded run used Zephyr v4.3.0 at commit `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056`, Zephyr SDK 0.17.4, Renode 1.17.0, Python 3.12.14 for builds, CMake 3.31.10, and host Python 3.14.6 with pexpect 4.9.0 for simulation. Exact component commits and versions are in [`environment.json`](../../results/phase1/environment.json). This recipe creates the same pinned inputs in the expected paths; use a clean Phase 1 results directory for a fresh data collection. Keep the original raw results intact.

Install `uv`, Homebrew, and the Apple command line tools first. From the project root:

```sh
brew install ninja gperf dtc wget
uv python install 3.12.14
uv venv --python 3.12.14 .venv
UV_CACHE_DIR=/private/tmp/phase1-uv-cache uv pip sync harness/phase1/requirements.lock --python .venv/bin/python
mkdir -p subjects/upstream
git clone --branch v4.3.0 --depth 1 https://github.com/zephyrproject-rtos/zephyr.git subjects/upstream/zephyr
cd subjects/upstream
../../.venv/bin/west init -l zephyr
../../.venv/bin/west update cmsis cmsis_6 hal_stm32
cd ../..
```

Check the four checkout commits against `environment.json`; the Git tag and West manifest determine them. The minimal macOS AArch64 [SDK release](https://github.com/zephyrproject-rtos/sdk-ng/releases/tag/v0.17.4) downloads the ARM toolchain during setup:

```sh
curl -L -o /private/tmp/zephyr-sdk-0.17.4_macos-aarch64_minimal.tar.xz https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.17.4/zephyr-sdk-0.17.4_macos-aarch64_minimal.tar.xz
mkdir -p /private/tmp/phase1-zephyr-sdk
tar -xf /private/tmp/zephyr-sdk-0.17.4_macos-aarch64_minimal.tar.xz -C /private/tmp/phase1-zephyr-sdk --strip-components=1
(cd /private/tmp/phase1-zephyr-sdk && ./setup.sh -t arm-zephyr-eabi)
```

Download the Apple Silicon portable DMG from the [Renode 1.17.0 release](https://github.com/renode/renode/releases/tag/v1.17.0), then mount it at `/private/tmp/renode-mounted` or set `RENODE_BIN` to its executable. The current runner also accepts `ZEPHYR_SDK_INSTALL_DIR` for a different SDK directory. Example mount command after downloading the DMG:

```sh
mkdir -p /private/tmp/renode-mounted
hdiutil attach /path/to/renode-1.17.0.osx-arm64-portable.dmg -mountpoint /private/tmp/renode-mounted -nobrowse
```

Run the build and experiment commands in [`PHASE1_REPORT.md`](../../notes/PHASE1_REPORT.md). The run/replay tools require pexpect and can use `.venv/bin/python`; the original run used host Python as recorded above. Build logs, binaries, hashes, complete UART logs, monitor transcripts, and traces are kept under `results/phase1/`. Build and run tools skip completed records and refuse to overwrite raw artifacts.

**Known limitation:** Renode's [integer MIPS setting](https://renode.readthedocs.io/en/latest/advanced/time_framework.html) cannot follow the STM32F407 HSI's ±1% drift exactly at a 16 MIPS nominal CPU setting. The legal oscillator range is documented, but this study's CPU-to-SysTick relation is model limited. Interpret any timing flip with that constraint and the four-way classification rule.
