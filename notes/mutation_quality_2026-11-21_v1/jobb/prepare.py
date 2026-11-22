#!/usr/bin/env python3
"""Seal Job B (local, no firmware). Writes jobb/plan.json, pairs.json, execution.json.

Pairs come from the committed Job A output by the Job A rule: for each RTC app with
Job A coverage, every mutant of rtc_ll_stm32.c on an executed driver line that is
compiled, not TCE-equivalent and first of its duplicate class in the app's
configuration. Refuses to overwrite.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
JOBA_OUT = ROOT / "artifacts/mutation_joba_20261122_v1/returned/extracted/output"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
RETRACE = ["astra-range_present-rtc_alarm_pending-r03", "astra-range_present-rtc_alarm_pending-r04"]
EXPECTED_SEALED_PAIRS = 17375  # artifacts/mutation_joba_20261122_v1/summary.json recost_job_b.rtc_pairs


def main():
    outs = [HERE / f for f in ("plan.json", "pairs.json", "execution.json", "execution.sha256")]
    if any(p.exists() for p in outs):
        sys.exit("refusing to overwrite a sealed plan")
    a_plan = json.loads((STUDY / "joba/plan.json").read_text())
    a_exec = json.loads((STUDY / "joba/execution.json").read_text())
    ms = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / a_plan["mutants"]).read_text().splitlines()}
    tce = {}
    tce_files = sorted((JOBA_OUT / "tce").glob("chunk-*.json"))
    for f in tce_files:
        for r in json.loads(f.read_text())["rows"]:
            tce[(r["mutant_id"], r["configuration"])] = r
    first = {}
    runnable = {"rtc_alarm": [], "rtc_counting": [], "counter": []}
    for (mid, cfg), r in sorted(tce.items()):
        if r["status"] == "compiled" and not r["tce_equivalent"]:
            if first.setdefault((cfg, r["object_sha256"]), mid) == mid:
                runnable[cfg].append(mid)
    pairs, traced_files = {}, []
    for a in a_plan["apps"]:
        if a["driver"] != "rtc":
            continue
        f = JOBA_OUT / "records" / f"{a['id']}-traced.json"
        if not f.exists():
            assert a["id"] in RETRACE, a["id"]
            continue
        traced_files.append(f)
        t = json.loads(f.read_text())
        ex = set(t.get("driver_executed_lines") or [])
        assert ex, a["id"]
        pairs[a["id"]] = [mid for mid in runnable[a["config"]]
                          if ms[mid]["file"] == "rtc_ll_stm32.c" and ms[mid]["line"] in ex]
    total = sum(map(len, pairs.values()))
    assert len(pairs) == 67 and total == EXPECTED_SEALED_PAIRS, (len(pairs), total)
    (HERE / "pairs.json").write_text(json.dumps(dict(
        rule=__doc__.split("\n\n")[1].replace("\n", " "), source="artifacts/mutation_joba_20261122_v1",
        pairs=pairs, total_pairs=total, runnable_by_config=runnable), indent=1, sort_keys=True) + "\n")

    plan = copy.deepcopy(a_plan)
    for k in ("timing", "stop", "su_cap", "walltime", "partition", "stages", "job"):
        plan.pop(k)
    for a in plan["apps"]:
        if a["driver"] == "counter":
            a.update(wall_seconds=5400, traced_wall_seconds=7200)
    plan.update(
        job="B", partition="normal", su_cap=15, walltime="15:00:00", retrace=RETRACE,
        chunk_size=40, chunk_task_timeout_seconds=30000,
        replay=dict(seed="mutation-quality-jobb-replay-v1", count=30, rule=(
            "After the mutant stage, take the 30 killed (app, mutant) pairs with the smallest "
            "sha256(seed+app_id+mutant_id); replay each in a fresh build; reproduced = same outcome and case vector.")),
        joba=dict(slurm_job_id="3604920", summary_sha256=sha(ROOT / "artifacts/mutation_joba_20261122_v1/summary.json")),
        stages=["counter build + counter baseline/traced alongside", "build", "baseline (+ re-trace 2 apps)",
                "mutants (round-robin chunks)", "replay 30 kills"],
        kill_rule=("killed if outcome or case vector differs from the in-job untraced baseline; "
                   "harness_error and build_failure are neither killed nor survived"),
        stop="Report usage, mutation score, coverage and the counter cost; submit nothing else.")
    (HERE / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")

    code = ["jobb/coordinator.py", "jobb/worker.py", "jobb/job.sbatch", "jobb/submit.py", "jobb/pairs.json",
            "generate_mutants.py", "dryrun_v1/mutants.jsonl", "dryrun_v1/generation_summary.json"]
    execution = dict(
        plan_sha256=sha(HERE / "plan.json"), study_code_sha256={c: sha(STUDY / c) for c in code},
        input_sha256=a_exec["input_sha256"], image_relative=a_exec["image_relative"],
        image_sha256=a_exec["image_sha256"], account="CCR26073", partition="normal", su_cap=15,
        total_study_ceiling_su=50, frozen_code_reused=a_exec["frozen_code_reused"],
        frozen_code_sha256=a_exec["frozen_code_sha256"],
        joba_evidence_sha256={str(p.relative_to(ROOT)): sha(p) for p in tce_files + traced_files})
    for rel, h in execution["input_sha256"].items():
        assert sha(ROOT / rel) == h, rel
    for rel, h in execution["frozen_code_sha256"].items():
        assert sha(ROOT / rel) == h, rel
    (HERE / "execution.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    (HERE / "execution.sha256").write_text(f"{sha(HERE / 'execution.json')}  execution.json\n")
    print(json.dumps(dict(sealed_apps=len(pairs), sealed_pairs=total, retrace=RETRACE,
                          plan_sha256=execution["plan_sha256"],
                          execution_sha256=sha(HERE / "execution.json")), indent=2))


if __name__ == "__main__":
    main()
