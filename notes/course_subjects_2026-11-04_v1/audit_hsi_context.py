#!/usr/bin/env python3
"""Run the existing HSI verifier without writing to historical result directories."""
from pathlib import Path
import functools
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
source=ROOT/'analysis/phase3_hsi_summary.py'
src=source.read_text().replace('(RESULTS / "summary.json").write_text','(HERE / "hsi_summary.json").write_text').replace('paired_path = RESULTS / "paired_schedules.csv"','paired_path = HERE / "hsi_paired_schedules.csv"')
ns={'__file__':str(source),'__name__':'hsi_readonly_audit','HERE':HERE}
exec(compile(src,'hsi_readonly_audit','exec'),ns)
ns['sha']=functools.lru_cache(None)(ns['sha'])
ns['main']()
