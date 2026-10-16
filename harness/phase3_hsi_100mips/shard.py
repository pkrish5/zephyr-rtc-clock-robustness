#!/usr/bin/env python3
"""Run disjoint tail inventory shards while the registered serial batch handles the head."""

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
    parser.add_argument("--shard", type=int, required=True, choices=range(4))
    args = parser.parse_args()
    inventory = list(json.loads(PLAN.read_text())["inventory"])
    # The original serial worker starts at index 0. It cannot reach index 15
    # before these four shorter, disjoint tail shards finish at measured speed.
    versions = [ident for i, ident in enumerate(inventory) if i >= 15 and (i - 15) % 4 == args.shard]
    log = RESULTS / f"tail_shard_{args.shard}.log"
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
