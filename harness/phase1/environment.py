#!/usr/bin/env python3
"""Record the Phase 1 build/run environment without modifying raw runs."""

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pexpect


ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "subjects" / "upstream"
SDK = Path("/private/tmp/phase1-zephyr-sdk")
RENODE = Path("/private/tmp/renode-mounted/Renode.app/Contents/MacOS/renode")
OUTPUT = ROOT / "results" / "phase1" / "environment.json"


def command(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise RuntimeError(f"Refusing to overwrite environment record: {OUTPUT}")
    components = {}
    for name, directory in {"zephyr": UPSTREAM / "zephyr", "cmsis": UPSTREAM / "modules" / "hal" / "cmsis",
                            "cmsis_6": UPSTREAM / "modules" / "hal" / "cmsis_6",
                            "hal_stm32": UPSTREAM / "modules" / "hal" / "stm32"}.items():
        components[name] = {"commit": command("git", "rev-parse", "HEAD", cwd=directory),
                            "clean": not command("git", "status", "--porcelain", cwd=directory)}
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": platform.platform(),
        "python": sys.version,
        "pexpect": pexpect.__version__,
        "cmake": command(str(ROOT / ".venv" / "bin" / "cmake"), "--version").splitlines()[0],
        "ninja": command("ninja", "--version"),
        "dtc": command("dtc", "--version"),
        "west": command(str(ROOT / ".venv" / "bin" / "west"), "--version"),
        "sdk_version": (SDK / "sdk_version").read_text().strip(),
        "arm_gcc": command(str(SDK / "arm-zephyr-eabi" / "bin" / "arm-zephyr-eabi-gcc"), "--version").splitlines()[0],
        "renode_version": command(str(RENODE), "--version"),
        "renode_stm32f4_base_sha256": sha256(RENODE.parent / "platforms" / "cpus" / "stm32f4.repl"),
        "hsi_overlay_sha256": sha256(ROOT / "subjects" / "phase1_zephyr" / "config" / "stm32f4_hsi.overlay"),
        "components": components,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
