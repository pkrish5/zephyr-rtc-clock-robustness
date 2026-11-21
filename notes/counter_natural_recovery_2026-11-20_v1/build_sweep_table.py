#!/usr/bin/env python3
"""Rebuild and check the manuscript's natural-phase sweep table (job 3598828).

1. Re-runs analyze_sweep.py on the committed verified assessment and requires
   byte-identical summary.json, primary_cells.csv and boundary_table.tex.
2. Checks every primary record hash cited by the summary against the committed
   record files.
3. Renders paper/draft/tables/counter_sweep_v1.tex and requires it to match the
   committed table (or writes it with --write).
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERIFIED = HERE / "verified-3598828-v1"
REPORT = HERE / "report-3598828-v1"
RECORDS = VERIFIED / "output" / "records"
PAPER_TABLE = ROOT / "paper" / "draft" / "tables" / "counter_sweep_v1.tex"
LABELS = {
    "original": "3 s (V0)",
    "deadline_6": "6 s",
    "derived_fixed": "7.648 s (V1b)",
    "derived_poll": "7.648 s poll (V2)",
    "deadline_8": "8 s",
    "deadline_10": "10 s",
    "deadline_13": "13 s (V1)",
}


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def render(summary):
    lines = [
        "% Generated from notes/counter_natural_recovery_2026-11-20_v1/report-3598828-v1/summary.json (job 3598828).",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Wait & Ideal band & Last rej./ & Slow acc. & Sel.\\",
        r" & (kHz) & first acc. & /12 & P/F\\",
        r"\midrule",
    ]
    for arm in summary["arms"]:
        lo, hi = (x / 1000 for x in arm["ideal_boundary_band_hz"])
        lines.append(
            f"{LABELS[arm['arm']]} & {lo:.2f}--{hi:.2f} & "
            f"{arm['last_sampled_rejected_hz'] // 1000} / {arm['first_sampled_accepted_hz'] // 1000} & "
            f"{arm['slow_faults_accepted']} & {arm['selected_pass']}/{arm['selected_fail']}" + r"\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the paper table instead of checking it")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "report"
        subprocess.run(
            [sys.executable, "-B", str(HERE / "analyze_sweep.py"), "--verified", str(VERIFIED), "--out", str(out)],
            check=True, stdout=subprocess.DEVNULL,
        )
        for name in ["summary.json", "primary_cells.csv", "boundary_table.tex"]:
            if (out / name).read_bytes() != (REPORT / name).read_bytes():
                fail(f"rebuilt {name} differs from committed report")
    print("report: summary.json, primary_cells.csv, boundary_table.tex rebuilt identically")

    summary = json.loads((REPORT / "summary.json").read_text())
    have = {hashlib.sha256(p.read_bytes()).hexdigest() for p in RECORDS.glob("*.json")}
    cited = [h for arm in summary["arms"] for h in arm["primary_record_sha256"]]
    if len(cited) != 98 or len(set(cited)) != 98:
        fail("expected 98 distinct primary record hashes")
    missing = [h for h in cited if h not in have]
    if missing:
        fail(f"{len(missing)} cited primary records not found in {RECORDS.relative_to(ROOT)}")
    print(f"records: all 98 primary record hashes match committed files ({len(have)} records present)")

    table = render(summary)
    if args.write:
        PAPER_TABLE.write_text(table)
        print(f"wrote {PAPER_TABLE.relative_to(ROOT)}")
    elif PAPER_TABLE.read_text() != table:
        fail(f"{PAPER_TABLE.relative_to(ROOT)} does not match summary.json")
    else:
        print(f"paper: {PAPER_TABLE.relative_to(ROOT)} matches summary.json")


if __name__ == "__main__":
    main()
