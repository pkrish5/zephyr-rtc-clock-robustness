#!/usr/bin/env python3
"""Audit persisted original/replay traces; never rewrite raw replay records."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/rtc_factorial_v2"
KEYS = ("lsi_frequency_hz", "observations", "cases", "outcome", "error")

for path in sorted((BASE / "replay_records").glob("*.json")) if (BASE / "replay_records").exists() else []:
    replay = json.loads(path.read_text())
    original = json.loads((BASE / "records" / path.name).read_text())
    a = json.loads((ROOT / original["trace_path"]).read_text())
    b = json.loads((ROOT / replay["trace_path"]).read_text())
    matches = {key: a[key] == b[key] for key in KEYS}
    print(path.stem, "persisted_identical=" + str(all(matches.values())),
          "raw_flag=" + str(replay["identical_trace_and_verdict"]),
          "differing_fields=" + ",".join(k for k, value in matches.items() if not value))
