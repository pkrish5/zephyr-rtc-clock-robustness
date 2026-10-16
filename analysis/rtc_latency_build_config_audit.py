#!/usr/bin/env python3
"""Verify pilot rebuilds kept the original Kconfig set and driver swap."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_latency_pilot"


def config_set(path):
    return {line for line in path.read_text().splitlines()
            if line.startswith("CONFIG_") or line.startswith("# CONFIG_")}


def main():
    m = json.loads((BASE / "manifest.json").read_text())
    rows = []
    for rid in m["suite_ids"]:
        version = m["suite_versions"][rid]
        original = ROOT / version["elf_path"]
        original_config = config_set(original.parent / ".config")
        for level in m["levels_us"]:
            build = BASE / "builds" / rid / str(level) / "build"
            new_config = config_set(build / "zephyr/.config")
            ninja = (build / "build.ninja").read_text()
            row = {"suite_id": rid, "delay_us": level,
                   "removed_config": sorted(original_config - new_config),
                   "added_config": sorted(new_config - original_config),
                   "quality_driver_compiled": "rtc_ll_stm32_quality.c.obj" in ninja,
                   "original_driver_compiled":
                       "CMakeFiles/drivers__rtc.dir/rtc_ll_stm32.c.obj" in ninja}
            rows.append(row)
    okay = all(not r["removed_config"] and not r["added_config"] and
               r["quality_driver_compiled"] and not r["original_driver_compiled"]
               for r in rows)
    out = {"all_pass": okay, "expected": 136, "observed": len(rows), "rows": rows}
    path = ROOT / "analysis/rtc_latency_build_config_audit.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print("pilot build/config audit", "pass" if okay else "fail", len(rows))
    if not okay or len(rows) != 136:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
