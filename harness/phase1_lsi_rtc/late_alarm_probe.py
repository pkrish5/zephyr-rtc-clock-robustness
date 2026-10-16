#!/usr/bin/env python3
"""Diagnostic only: inspect the frozen callback state after a slow-LSI test fails."""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from run import ELF, RENODE, RESULTS, ROOT, RenodeSession, freeze, sha256

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--frequency-hz", type=int, default=17_000)
    args = parser.parse_args()
    build = freeze()
    if build.get("variant") != "callback":
        raise SystemExit("Set PHASE1_LSI_VARIANT=callback")
    if not 17_000 <= args.frequency_hz <= 47_000:
        parser.error("LSI frequency must remain within the registered 17–47 kHz bound")
    platform = RESULTS / f"platforms/stm32f4_rtc_lsi_{args.frequency_hz}.repl"
    if not platform.exists():
        raise SystemExit("Run the registered schedule at this LSI frequency first")
    suffix = "" if args.frequency_hz == 17_000 else f"_{args.frequency_hz}hz"
    output = RESULTS / f"late_alarm_probe{suffix}.json"
    uart = RESULTS / f"late_alarm_probe{suffix}.uart.log"
    monitor = RESULTS / f"late_alarm_probe{suffix}.monitor.log"
    for path in (output, uart, monitor):
        if path.exists():
            raise SystemExit(f"Refusing to overwrite diagnostic output: {path}")
    sdk = Path(os.environ.get("ZEPHYR_SDK_INSTALL_DIR", "/private/tmp/phase1-zephyr-sdk"))
    nm = sdk / "arm-zephyr-eabi/bin/arm-zephyr-eabi-nm"
    symbol_table = subprocess.check_output([str(nm), str(ELF)], text=True)
    addresses = re.findall(r"^([0-9a-fA-F]+)\s+\w\s+callback_called_mask_even$", symbol_table, re.MULTILINE)
    if len(addresses) != 1:
        raise SystemExit("Cannot resolve callback_called_mask_even in frozen ELF")
    callback_mask_even_address = int(addresses[0], 16)
    samples = []
    elapsed_ns = 0
    with RenodeSession(RENODE, platform, ELF, monitor) as session:
        session.command("cpu PerformanceInMips 16")
        session.command(f"sysbus.usart2 CreateFileBackend @{uart} true")
        for checkpoint_ns in (3_500_000_000, 13_500_000_000, 20_000_000_000):
            session.run_for_ns(checkpoint_ns - elapsed_ns)
            elapsed_ns = checkpoint_ns
            samples.append({"virtual_ns": elapsed_ns,
                            "callback_mask_even": session.read_word(callback_mask_even_address),
                            "rtc_time_register": session.read_word(0x40002800),
                            "uart_sha256": sha256(uart) if uart.exists() else None})
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Post-failure RTC/callback-state diagnostic; outside the primary rate",
        "lsi_frequency_hz": args.frequency_hz,
        "elf_sha256": build["elf_sha256"],
        "platform_sha256": sha256(platform),
        "renode_version": subprocess.check_output([str(RENODE), "--version"], text=True).strip(),
        "callback_mask_even_address": callback_mask_even_address,
        "samples": samples,
        "uart_path": str(uart.relative_to(ROOT)),
        "monitor_path": str(monitor.relative_to(ROOT)),
    }
    output.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    print(json.dumps(samples, sort_keys=True))
