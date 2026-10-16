#!/usr/bin/env python3
"""Run one disjoint RTC reference task's registered failed-seed union."""

import argparse
import json

from rtc_reference_triage_v2 import FAMILIES, OUT, run


def main():
    p = argparse.ArgumentParser()
    p.add_argument("family", choices=FAMILIES)
    a = p.parse_args()
    manifest = json.loads((OUT / "manifest.json").read_text())
    for seed in manifest["selected_seed_union"][a.family]:
        run(a.family, "seeded", seed)
    print(f"{a.family}: complete", flush=True)


if __name__ == "__main__":
    main()
