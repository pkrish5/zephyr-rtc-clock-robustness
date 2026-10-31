#!/usr/bin/env python3
"""Compute-node gate before S2/E follow-up execution, not before cleanup."""
import json
import os
from pathlib import Path
import subprocess

if not os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Compute allocation required')
text=subprocess.check_output(['lfs','quota','-u',os.environ['USER'],os.environ['WORK']],text=True)
rows=[line.split() for line in text.splitlines() if len(line.split())>=8 and line.split()[0].rstrip('*').isdigit()]
if len(rows)!=1:raise RuntimeError('Cannot identify current WORK quota count')
count=int(rows[0][-4].rstrip('*'))
print(json.dumps(dict(work_file_count=count,threshold=700000,allowed=count<700000)))
if count>=700000:raise SystemExit('STOP: WORK must be below 700,000 files')
