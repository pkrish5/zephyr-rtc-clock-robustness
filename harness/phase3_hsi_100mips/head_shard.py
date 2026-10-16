#!/usr/bin/env python3
"""Run disjoint inventory indices 7–14 before the serial worker reaches them."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "subjects/phase3_hsi_100mips/plan.json"
RUNNER = ROOT / "harness/phase3_hsi_100mips/run.py"
RESULTS = ROOT / "results/phase3_hsi_100mips"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, required=True, choices=range(2))
    args = parser.parse_args()
    inventory = list(json.loads(PLAN.read_text())["inventory"])
    versions = [ident for i, ident in enumerate(inventory)
                if 7 <= i <= 14 and (i - 7) % 2 == args.shard]
    log = RESULTS / f"head_shard_{args.shard}.log"
    with log.open("x") as stream:
        for ident in versions:
            print(f"START {ident}", file=stream, flush=True)
            result = subprocess.run([sys.executable, str(RUNNER), "--version", ident],
                                    cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            print(f"END {ident} exit={result.returncode}", file=stream, flush=True)
            if result.returncode:
                raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
