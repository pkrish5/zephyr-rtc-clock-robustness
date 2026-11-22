#!/usr/bin/env python3
"""Submit Job A exactly once from the LS6 login node.

Usage: python3 submit.py EXPECTED_HEAD
Checks the sealed execution, code/input hashes, the checkout HEAD and a clean
tracked tree, the absence of any prior intent/receipt and of a queued job with
the same name, then writes an exclusive intent, calls sbatch once and writes an
exclusive receipt. Never retries; an uncertain outcome must be inspected.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

r = Path(os.environ["WORK"]) / "zephyr-rtc-clock-robustness"
n = r / "notes/mutation_quality_2026-11-21_v1"
j = n / "joba"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected_head = sys.argv[1]
head = subprocess.check_output(["git", "-C", str(r), "rev-parse", "HEAD"], text=True).strip()
assert head == expected_head, (head, expected_head)
dirty = subprocess.check_output(["git", "-C", str(r), "status", "--porcelain", "--untracked-files=no"], text=True)
assert not dirty.strip(), dirty
e = json.loads((j / "execution.json").read_text())
assert sha(j / "execution.json") == (j / "execution.sha256").read_text().split()[0]
assert sha(j / "plan.json") == e["plan_sha256"]
assert e["account"] == "CCR26073" and e["partition"] == "development" and e["su_cap"] == 2
for group in ("study_code_sha256",):
    for rel, h in e[group].items():
        assert sha(n / rel) == h, rel
for group in ("input_sha256", "frozen_code_sha256"):
    for rel, h in e[group].items():
        assert sha(r / rel) == h, rel
image = r / e["image_relative"]
assert (image.parent / "rtc-ls6-v1.sif.sha256").read_text().split()[0] == e["image_sha256"]
queued = subprocess.run(["squeue", "-h", "-u", os.environ["USER"], "-n", "rtc-mutation-joba"],
                        capture_output=True, text=True, timeout=60)
assert queued.returncode == 0 and not queued.stdout.strip(), queued.stdout
base = r / "tacc_work/20261122-mutation-joba-v1"
base.mkdir(exist_ok=True)
assert not (base / "submission.intent.json").exists() and not (base / "submission.json").exists()
logs = Path(os.environ["SCRATCH"]) / "zephyr-rtc-clock-robustness/mutation-joba-20261122-v1/slurm"
logs.mkdir(parents=True, exist_ok=True)
cmd = ["sbatch", "--parsable", "-A", "CCR26073", "-p", "development", "-N", "1", "-n", "128", "-t", "02:00:00",
       "--chdir=" + str(r), "--output=" + str(logs / "joba-%j.out"), "--error=" + str(logs / "joba-%j.err"),
       "--export=ALL,RTC_REPO=" + str(r), str(j / "job.sbatch")]
with (base / "submission.intent.json").open("x") as f:
    json.dump(dict(time=datetime.now(timezone.utc).isoformat(), head=head, execution_sha256=sha(j / "execution.json"),
                   command=cmd), f, indent=2)
record = dict(state="uncertain", command=cmd, su_cap=2, head=head)
try:
    x = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    record.update(returncode=x.returncode, stdout=x.stdout, stderr=x.stderr)
    ids = re.findall(r"^([0-9]+)(?:;[^\n]*)?$", x.stdout, re.M)
    record["state"] = "accepted" if x.returncode == 0 and len(ids) == 1 else "rejected_or_uncertain"
    if record["state"] == "accepted":
        record["job_id"] = ids[0]
except subprocess.TimeoutExpired:
    record["error"] = "timeout: inspect intent and Slurm; never retry"
with (base / "submission.json").open("x") as f:
    json.dump(record, f, indent=2)
    f.write("\n")
print(json.dumps(record, indent=2))
raise SystemExit(0 if record["state"] == "accepted" else 2)
