#!/usr/bin/env python3
"""Seal Job C (local, no firmware). Writes jobc/plan.json, pairs.json, execution.json.

Precondition (registered): Job B's counter_basic baseline completed and its traced
run gave readable coverage; both records are copied from Job B's loose output into
PRECONDITION_DIR before sealing. Pairs: every counter mutant that is compiled, not
TCE-equivalent and first of its duplicate class (jobb/pairs.json runnable_by_config
'counter') on a driver line executed in that traced run. Refuses to overwrite.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
PRE = ROOT / "artifacts/mutation_jobb_20261122_v1/counter_precondition"
APP = "upstream-counter_basic"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    outs = [HERE / f for f in ("plan.json", "pairs.json", "execution.json", "execution.sha256")]
    if any(p.exists() for p in outs):
        sys.exit("refusing to overwrite a sealed plan")
    base = json.loads((PRE / f"{APP}-baseline.json").read_text())
    traced = json.loads((PRE / f"{APP}-traced.json").read_text())
    if base.get("outcome") != "complete":
        sys.exit(f"precondition failed: Job B counter baseline outcome {base.get('outcome')}")
    if not traced.get("driver_executed_lines"):
        sys.exit(f"precondition failed: counter coverage {traced.get('coverage_error') or traced.get('outcome')}")
    b_plan = json.loads((STUDY / "jobb/plan.json").read_text())
    b_exec = json.loads((STUDY / "jobb/execution.json").read_text())
    b_pairs = json.loads((STUDY / "jobb/pairs.json").read_text())
    ms = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / b_plan["mutants"]).read_text().splitlines()}
    ex = set(traced["driver_executed_lines"])
    runnable = b_pairs["runnable_by_config"]["counter"]
    mids = [m for m in runnable if ms[m]["file"] == "counter_ll_stm32_rtc.c" and ms[m]["line"] in ex]
    (HERE / "pairs.json").write_text(json.dumps(dict(
        rule=__doc__.split("\n\n")[1].replace("\n", " "), pairs={APP: mids}, total_pairs=len(mids),
        runnable_counter=len(runnable), uncovered_counter=len(runnable) - len(mids),
        coverage=traced.get("driver_line_coverage"), source_job="3605243"), indent=1, sort_keys=True) + "\n")
    plan = copy.deepcopy(b_plan)
    for k in ("retrace", "replay", "chunk_size", "joba"):
        plan.pop(k, None)
    plan["apps"] = [a for a in plan["apps"] if a["id"] == APP]
    plan["apps"][0].update(wall_seconds=5400, traced_wall_seconds=7200)
    plan.update(job="C", partition="normal", su_cap=20, walltime="20:00:00", chunk_task_timeout_seconds=8100,
                jobb=dict(slurm_job_id="3605243",
                          precondition_sha256={f.name: sha(f) for f in sorted(PRE.glob("*.json"))}),
                stages=["build counter", "baseline alongside", "one mutant per fresh build"],
                kill_rule=("verdicts computed afterwards: killed if outcome or case vector differs from the "
                           "Job C in-job untraced baseline; harness_error and build_failure are neither"),
                stop="Report usage, counter mutation score and coverage; submit nothing else.")
    (HERE / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    code = ["jobc/coordinator.py", "jobc/worker.py", "jobc/job.sbatch", "jobc/submit.py", "jobc/pairs.json",
            "generate_mutants.py", "dryrun_v1/mutants.jsonl", "dryrun_v1/generation_summary.json"]
    execution = dict(
        plan_sha256=sha(HERE / "plan.json"), study_code_sha256={c: sha(STUDY / c) for c in code},
        input_sha256=b_exec["input_sha256"], image_relative=b_exec["image_relative"],
        image_sha256=b_exec["image_sha256"], account="CCR26073", partition="normal", su_cap=20,
        total_study_budget_su=500, frozen_code_reused=b_exec["frozen_code_reused"],
        frozen_code_sha256=b_exec["frozen_code_sha256"])
    for g in ("input_sha256", "frozen_code_sha256"):
        for rel, h in execution[g].items():
            assert sha(ROOT / rel) == h, rel
    (HERE / "execution.json").write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    (HERE / "execution.sha256").write_text(f"{sha(HERE / 'execution.json')}  execution.json\n")
    print(json.dumps(dict(pairs=len(mids), runnable=len(runnable), coverage=traced.get("driver_line_coverage"),
                          baseline_wall=base.get("wall_seconds"), plan_sha256=execution["plan_sha256"],
                          execution_sha256=sha(HERE / "execution.json")), indent=2))


if __name__ == "__main__":
    main()
