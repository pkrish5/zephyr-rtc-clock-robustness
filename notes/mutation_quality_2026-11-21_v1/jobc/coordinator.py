#!/usr/bin/env python3
"""Job C coordinator (counter-driver mutants; adapted from Job B) (compute node, outside the container), run under run_packed.sh.

Each task is one fresh `apptainer exec` of jobc/worker.py with private home/tmp
dirs, at most PLAN['workers'] at a time; the counter baseline/traced runs use two
extra slots alongside. Stages run in order; nothing replaces an existing output.
Failures become recorded missing outcomes, never verdicts.
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

R = Path(os.environ["RTC_REPO"])
N = R / "notes/mutation_quality_2026-11-21_v1"
J = N / "jobc"
OUT = Path(os.environ["RTC_JOB_OUTPUT"])
BUILDS = Path(os.environ["RTC_BUILD_BASE"])
NODE = Path(os.environ["RTC_NODE_BASE"])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x") as f:
        json.dump(d, f, indent=2, sort_keys=True)
        f.write("\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


E = json.loads((J / "execution.json").read_text())
assert sha(J / "execution.json") == (J / "execution.sha256").read_text().split()[0]
P = json.loads((J / "plan.json").read_text())
CB = R / P["counter_bundle"]


def guard():
    assert os.environ["SLURM_JOB_ACCOUNT"].upper() == "CCR26073" and os.environ["SLURM_JOB_PARTITION"] == "normal"
    assert sha(J / "plan.json") == E["plan_sha256"]
    for rel, h in E["study_code_sha256"].items():
        assert sha(N / rel) == h, rel
    for rel, h in E["input_sha256"].items():
        assert sha(R / rel) == h, rel
    for rel, h in E["frozen_code_sha256"].items():
        assert sha(R / rel) == h, rel
    assert sha(CB / "plan.json") == P["counter_plan_sha256"]


def task(name, args, timeout):
    """One isolated container task; returns its exit code (124 on timeout)."""
    private = NODE / f"task-{name}"
    for d in ("home/.config/renode", "tmp", "work"):
        (private / d).mkdir(parents=True)
    shutil.copytree(CB / "renode-cache", private / "home/.config/renode", dirs_exist_ok=True)
    cmd = ["apptainer", "exec", "--cleanenv", "--containall", "--home", f"{private}/home:/home/rtc", "--pwd", "/",
           "--bind", f"{R}:/repo:ro", "--bind", f"{CB}:/counter-bundle:ro", "--bind", f"{CB}/renode:/renode:ro",
           "--bind", f"{OUT}:/out:rw", "--bind", f"{BUILDS}:/scratch-builds:rw",
           "--bind", f"{private}/tmp:/tmp:rw", "--bind", f"{private}/work:/var/tmp:rw",
           "--env", "XDG_CACHE_HOME=/var/tmp", "--env", f"RTC_CONTAINER_SHA256={E['image_sha256']}",
           "--env", f"RTC_NODE_NAME={os.uname().nodename}", "--env", f"SLURM_JOB_ID={os.environ['SLURM_JOB_ID']}",
           str(R / E["image_relative"]), "/opt/rtc-python/bin/python",
           "/repo/notes/mutation_quality_2026-11-21_v1/jobc/worker.py", *args]
    log = OUT / "stdout" / f"{name}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    with log.open("x") as f:
        try:
            code = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    save(OUT / "processes" / f"{name}.json", dict(name=name, args=args, exit_code=code,
                                                  wall_seconds=round(time.monotonic() - t0, 3), end_utc=utc()))
    shutil.rmtree(private, ignore_errors=True)
    return code


def pool(jobs):
    with ThreadPoolExecutor(max_workers=P["workers"]) as ex:
        return list(ex.map(lambda j: task(*j), jobs))


def stage_log(name, **kw):
    save(OUT / "job_metadata" / f"stage-{name}.json", dict(stage=name, end_utc=utc(), **kw))


def load(p):
    try:
        return json.loads(p.read_text())
    except FileNotFoundError:
        return None


def main():
    guard()
    for f in ("plan.json", "execution.json", "execution.sha256", "pairs.json"):
        shutil.copyfile(J / f, OUT / "job_metadata" / f)
    (a,) = [a for a in P["apps"] if a["driver"] == "counter"]
    sealed = json.loads((J / "pairs.json").read_text())
    mids = sealed["pairs"][a["id"]]
    t = time.monotonic()
    code = task(f"build-{a['id']}", ["build", a["id"]], P["build_timeout_seconds"] * 2 + 300)
    stage_log("build", wall_seconds=round(time.monotonic() - t, 1), nonzero=int(code != 0))
    chunks = {f"{a['id']}#{k}": [m] for k, m in enumerate(mids)}
    save(OUT / "job_metadata/mutant_chunks.json", chunks)
    save(OUT / "job_metadata/mutant_schedule.json", dict(order=list(chunks), pairs=len(mids), apps=1))
    side = ThreadPoolExecutor(max_workers=1)  # the in-job baseline runs alongside the mutants
    base = side.submit(task, f"run-{a['id']}-baseline", ["run", a["id"], "baseline"], a["wall_seconds"] + 3600)
    t = time.monotonic()
    codes = pool([(f"mutants-{key.replace('#', '-c')}", ["mutants", key], P["chunk_task_timeout_seconds"])
                  for key in chunks])
    stage_log("mutants", wall_seconds=round(time.monotonic() - t, 1), chunks=len(chunks),
              nonzero=sum(c != 0 for c in codes))
    side.shutdown(wait=True)
    stage_log("baseline", exit_code=base.result())


if __name__ == "__main__":
    try:
        main()
    finally:
        guard()
        save(OUT / "job_metadata/input_after.json", dict(passed=True, end_utc=utc()))
