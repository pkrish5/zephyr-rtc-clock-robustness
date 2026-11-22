#!/usr/bin/env python3
"""Job A coordinator (compute node, outside the container), run under run_packed.sh.

Each task is one fresh `apptainer exec` of worker.py with private home/tmp dirs,
at most PLAN['workers'] at a time. Stages run in order; a stage never replaces
an existing output. Failures become recorded missing outcomes, never verdicts.
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
J = N / "joba"
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
    assert os.environ["SLURM_JOB_ACCOUNT"].upper() == "CCR26073" and os.environ["SLURM_JOB_PARTITION"] == "development"
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
           "/repo/notes/mutation_quality_2026-11-21_v1/joba/worker.py", *args]
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


def main():
    guard()
    for f in ("plan.json", "execution.json", "execution.sha256"):
        shutil.copyfile(J / f, OUT / "job_metadata" / f)
    apps = P["apps"]
    # Counter first: its full application is the longest single unit.
    order = sorted(apps, key=lambda a: a["driver"] != "counter")
    t = time.monotonic()
    codes = pool([(f"build-{a['id']}", ["build", a["id"]], P["build_timeout_seconds"] * 2 + 300) for a in order])
    stage_log("build", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes))
    built = {a["id"] for a in apps
             if json.loads((OUT / "builds" / a["id"] / "build_record.json").read_text())["status"] == "built"}
    refs = P["tce_reference_apps"]
    pairs = []
    for line in (R / P["mutants"]).read_text().splitlines():
        m = json.loads(line)
        cfgs = ["counter"] if m["file"].startswith("counter") else ["rtc_alarm", "rtc_counting"]
        pairs += [(m["id"], c) for c in cfgs if refs[c] in built]
    chunks = [pairs[i::P["workers"]] for i in range(P["workers"])]
    save(OUT / "job_metadata/tce_chunks.json", chunks)
    t = time.monotonic()
    codes = pool([(f"tce-{i:03d}", ["tce", str(i)], 3600) for i in range(len(chunks))])
    stage_log("tce", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes),
              pairs=len(pairs), skipped_unbuilt_reference=sorted(c for c, a in refs.items() if a not in built))
    runs = []
    for a in order:
        for mode in ("traced", "baseline"):
            cap = a["traced_wall_seconds"] if mode == "traced" else a["wall_seconds"]
            runs.append((f"run-{a['id']}-{mode}", ["run", a["id"], mode], cap + 300))
    t = time.monotonic()
    codes = pool(runs)
    stage_log("baseline_coverage", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes))
    timing_selection()
    selected = json.loads((OUT / "job_metadata/timing_selection.json").read_text())["selected"]
    t = time.monotonic()
    codes = pool([(f"timing-{s['app_id']}", ["timing", s["app_id"], s["mutant_id"]], 1500) for s in selected])
    stage_log("timing", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes))


def timing_selection():
    seed = P["timing"]["seed"]
    h = lambda s: hashlib.sha256((seed + s).encode()).hexdigest()
    ms = {json.loads(l)["id"]: json.loads(l) for l in (R / P["mutants"]).read_text().splitlines()}
    tce = {}
    for f in sorted((OUT / "tce").glob("chunk-*.json")):
        for r in json.loads(f.read_text())["rows"]:
            tce[(r["mutant_id"], r["configuration"])] = r
    seen = {}
    for (mid, cfg), r in sorted(tce.items()):
        if r["status"] == "compiled" and not r["tce_equivalent"]:
            r["duplicate_of"] = seen.setdefault((cfg, r["object_sha256"]), mid)
    eligible = []
    for a in P["apps"]:
        if a["driver"] != "rtc":
            continue
        try:
            b = json.loads((OUT / "records" / f"{a['id']}-baseline.json").read_text())
            c = json.loads((OUT / "records" / f"{a['id']}-traced.json").read_text())
        except FileNotFoundError:
            continue
        if b.get("outcome") != "complete" or not c.get("driver_executed_lines"):
            continue
        executed = set(c["driver_executed_lines"])
        cands = [mid for mid, m in ms.items() if m["file"] == "rtc_ll_stm32.c" and m["line"] in executed
                 and tce.get((mid, a["config"]), {}).get("duplicate_of") == mid]
        if cands:
            eligible.append((h(a["id"]), a["id"], min(cands, key=lambda mid: h(a["id"] + mid))))
    chosen = sorted(eligible)[:P["timing"]["apps"]]
    save(OUT / "job_metadata/timing_selection.json",
         dict(rule=P["timing"]["rule"], eligible_apps=len(eligible),
              selected=[dict(app_id=a, mutant_id=m) for _, a, m in chosen]))


if __name__ == "__main__":
    try:
        main()
    finally:
        guard()
        save(OUT / "job_metadata/input_after.json", dict(passed=True, end_utc=utc()))
