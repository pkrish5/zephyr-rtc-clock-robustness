#!/usr/bin/env python3
"""Job B coordinator (compute node, outside the container), run under run_packed.sh.

Each task is one fresh `apptainer exec` of jobb/worker.py with private home/tmp
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
J = N / "jobb"
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
           "/repo/notes/mutation_quality_2026-11-21_v1/jobb/worker.py", *args]
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


def assemble_pairs():
    """Sealed pairs for apps with Job A coverage; in-job pairs (same rule) for re-traced apps.
    Only apps whose Job B baseline is complete are scheduled."""
    sealed = json.loads((J / "pairs.json").read_text())
    ms = {json.loads(l)["id"]: json.loads(l) for l in (R / P["mutants"]).read_text().splitlines()}
    apps = {a["id"]: a for a in P["apps"]}
    pairs, skipped = {}, {}
    for app_id, a in apps.items():
        if a["driver"] != "rtc":
            continue
        b = load(OUT / "records" / f"{app_id}-baseline.json")
        if not b or b.get("outcome") != "complete":
            skipped[app_id] = "baseline " + ((b or {}).get("outcome") or "missing")
            continue
        if app_id in sealed["pairs"]:
            pairs[app_id] = sealed["pairs"][app_id]
            continue
        c = load(OUT / "records" / f"{app_id}-traced.json")
        if not c or not c.get("driver_executed_lines"):
            skipped[app_id] = "coverage " + ((c or {}).get("coverage_error") or (c or {}).get("outcome") or "missing")
            continue
        executed = set(c["driver_executed_lines"])
        pairs[app_id] = [mid for mid in sealed["runnable_by_config"][a["config"]]
                         if ms[mid]["file"] == "rtc_ll_stm32.c" and ms[mid]["line"] in executed]
    size = P["chunk_size"]
    chunks = {}
    for app_id in sorted(pairs):
        mids = pairs[app_id]
        for k in range(0, len(mids), size):
            chunks[f"{app_id}#{k // size}"] = mids[k:k + size]
    # Round-robin across apps: chunk 0 of every app, then chunk 1, ...
    order = sorted(chunks, key=lambda key: (int(key.rsplit("#", 1)[1]), key))
    save(OUT / "job_metadata/mutant_chunks.json", chunks)
    save(OUT / "job_metadata/mutant_schedule.json",
         dict(order=order, pairs=sum(len(v) for v in pairs.values()), apps=len(pairs), skipped_apps=skipped,
              in_job_pairs={k: len(v) for k, v in pairs.items() if k not in sealed["pairs"]}))
    return order


def replay_selection():
    seed = P["replay"]["seed"]
    h = lambda s: hashlib.sha256((seed + s).encode()).hexdigest()
    killed = []
    for f in sorted((OUT / "mutants").glob("*/*.json")):
        r = json.loads(f.read_text())
        if r.get("verdict") == "killed":
            killed.append((h(r["app_id"] + r["mutant_id"]), r["app_id"], r["mutant_id"]))
    chosen = sorted(killed)[:P["replay"]["count"]]
    save(OUT / "job_metadata/replay_selection.json",
         dict(rule=P["replay"]["rule"], killed_available=len(killed),
              selected=[dict(app_id=a, mutant_id=m) for _, a, m in chosen]))
    return len(chosen)


def main():
    guard()
    for f in ("plan.json", "execution.json", "execution.sha256", "pairs.json"):
        shutil.copyfile(J / f, OUT / "job_metadata" / f)
    apps = P["apps"]
    counter = [a for a in apps if a["driver"] == "counter"]
    rtc = [a for a in apps if a["driver"] == "rtc"]
    side = ThreadPoolExecutor(max_workers=2)
    t = time.monotonic()
    for a in counter:  # counter build first, then its two long runs alongside everything else
        task(f"build-{a['id']}", ["build", a["id"]], P["build_timeout_seconds"] * 2 + 300)
    counter_runs = [side.submit(task, f"run-{a['id']}-{m}", ["run", a["id"], m],
                                (a["traced_wall_seconds"] if m == "traced" else a["wall_seconds"]) + 3600)
                    for a in counter for m in ("baseline", "traced")]
    codes = pool([(f"build-{a['id']}", ["build", a["id"]], P["build_timeout_seconds"] * 2 + 300) for a in rtc])
    stage_log("build", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes))
    runs = [(f"run-{a['id']}-baseline", ["run", a["id"], "baseline"], a["wall_seconds"] + 300) for a in rtc]
    by_id = {a["id"]: a for a in apps}
    runs += [(f"run-{i}-traced", ["run", i, "traced"], by_id[i]["traced_wall_seconds"] + 1800) for i in P["retrace"]]
    t = time.monotonic()
    codes = pool(runs)
    stage_log("baseline", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes))
    order = assemble_pairs()
    t = time.monotonic()
    codes = pool([(f"mutants-{key.replace('#', '-c')}", ["mutants", key], P["chunk_task_timeout_seconds"])
                  for key in order])
    stage_log("mutants", wall_seconds=round(time.monotonic() - t, 1), chunks=len(order),
              nonzero=sum(c != 0 for c in codes))
    n = replay_selection()
    t = time.monotonic()
    codes = pool([(f"replay-{i:03d}", ["replay", str(i)], 3600) for i in range(n)])
    stage_log("replay", wall_seconds=round(time.monotonic() - t, 1), nonzero=sum(c != 0 for c in codes))
    t = time.monotonic()
    side.shutdown(wait=True)
    stage_log("counter", waited_seconds=round(time.monotonic() - t, 1),
              exit_codes=[f.result() for f in counter_runs])


if __name__ == "__main__":
    try:
        main()
    finally:
        guard()
        save(OUT / "job_metadata/input_after.json", dict(passed=True, end_utc=utc()))
