#!/usr/bin/env python3
"""Seal the Job A pilot plan (local, no firmware). Writes plan.json, execution.json.

Job A: production-GCC compile + TCE of every dry-run mutant, configure/build every
unmutated app with the driver slot, one untraced baseline and one traced coverage
run per app at 32 kHz, and 40 timed (app, mutant) runs. Refuses to overwrite.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
ROOT = STUDY.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

UPSTREAM_SRC = "ZEPHYR/tests/drivers/rtc/rtc_api/src"  # container /opt/zephyrproject/zephyr
HUMAN = {
    "rtc_alarm_callback": ("subjects/phase1_lsi_rtc/selected_alarm_callback/prj.conf", "test_alarm_callback.c"),
    "rtc_alarm_pending": ("subjects/rtc_alarm_pending/selected_case/prj.conf", "test_alarm.c"),
    "rtc_time_counting": ("subjects/rtc_counting/selected_case/prj.conf", "test_time_incrementing.c"),
}
OVERLAYS = ["subjects/phase1_zephyr/config/stm32f4_hsi.overlay", "subjects/phase1_lsi_rtc/rtc_alias.overlay"]
PLATFORM = "results/phase3_rtc/platforms/stm32f4_rtc_lsi_32000.repl"
COUNTER_BUNDLE = "tacc_work/20261104-counter-repair-v1/bundle"  # relative to the LS6 repo
COUNTER_PLAN_SHA = "c5d2f7f515a59f2d45bcad665ab649b251051904704a1c96186610d08141ea8d"
IMAGE_SHA = "94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1"
RENODE_VERSION = ("Renode v1.17.0\n  build: 1.17.0+20260907gitf1dd1b4af\n  build type: Release\n"
                  "  runtime: .NET 8.0.21")
TIMING_SEED = "mutation-quality-joba-timing-v1"


def apps():
    summary = json.loads((ROOT / "analysis/rtc_factorial_v2_final_summary.json").read_text())
    out = []
    for fam, (conf, test) in HUMAN.items():
        out.append(dict(id=f"upstream-{fam}", set="upstream", family=fam, driver="rtc",
                        config="rtc_counting" if fam == "rtc_time_counting" else "rtc_alarm",
                        sources=[f"{UPSTREAM_SRC}/main.c", f"{UPSTREAM_SRC}/{test}"], prj_conf=conf,
                        define=None if fam == "rtc_time_counting" else "CONFIG_TEST_RTC_ALARM_TIME_MASK=7",
                        max_virtual_seconds=60, wall_seconds=600, traced_wall_seconds=1200))
    for s in sorted(summary["suite_distribution"], key=lambda s: s["suite_id"]):
        model, cond, rest = s["suite_id"].split("-", 2)
        fam, rep = rest.rsplit("-", 1)
        d = f"generated/spec_context_factorial_v1/suites/{model}/{cond}/{fam}/{rep}"
        assert (ROOT / d / "test.c").is_file() and (ROOT / d / "prj.conf").is_file(), d
        out.append(dict(id=s["suite_id"], set={"range_absent": "base", "range_present": "clock"}[cond],
                        family=fam, model=model, driver="rtc",
                        config="rtc_counting" if fam == "rtc_time_counting" else "rtc_alarm",
                        sources=[f"{d}/test.c"], prj_conf=f"{d}/prj.conf", define=None,
                        max_virtual_seconds=60, wall_seconds=600, traced_wall_seconds=1200))
    out.append(dict(id="upstream-counter_basic", set="counter", family="counter_basic", driver="counter",
                    config="counter", bundle_app="apps/V0", bundle_overlay="configs/f4.overlay",
                    bundle_config="configs/counter.conf", max_virtual_seconds=600,
                    wall_seconds=1800, traced_wall_seconds=2700))
    return out


def main():
    plan_path, exe_path = HERE / "plan.json", HERE / "execution.json"
    if plan_path.exists() or exe_path.exists():
        sys.exit("refusing to overwrite a sealed plan")
    mutants = STUDY / "dryrun_v1/mutants.jsonl"
    a = apps()
    counts = {k: sum(x["set"] == k for x in a) for k in ("upstream", "base", "clock", "counter")}
    assert counts == {"upstream": 3, "base": 34, "clock": 32, "counter": 1}, counts
    plan = dict(
        schema=1, study="mutation_quality_2026-11-21_v1", job="A", partition="development",
        account="CCR26073", su_cap=2, walltime="02:00:00", nodes=1, workers=32, compiler_parallelism=2,
        image_sha256=IMAGE_SHA, renode_version=RENODE_VERSION, zephyr_commit="3568e1b6d5cdd51a6b964a2a1d6d29200fea2056",
        nominal_hz=32000, cpu_mips=16, quantum_ns=1000, step_ns=500000000,
        platform=PLATFORM, overlays=OVERLAYS, counter_bundle=COUNTER_BUNDLE,
        counter_plan_sha256=COUNTER_PLAN_SHA, counter_platform="stm32f4_discovery.repl",
        mutants="notes/mutation_quality_2026-11-21_v1/dryrun_v1/mutants.jsonl", mutants_sha256=sha(mutants),
        tce_reference_apps={"rtc_counting": "upstream-rtc_time_counting",
                            "rtc_alarm": "upstream-rtc_alarm_callback", "counter": "upstream-counter_basic"},
        build_timeout_seconds=900, tce_compile_timeout_seconds=120,
        timing=dict(seed=TIMING_SEED, apps=40, rule=(
            "Among RTC apps whose baseline passed and whose coverage is available, take the 40 with the "
            "smallest sha256(seed+app_id); for each, run the covered, compiled, non-TCE-equivalent, "
            "non-duplicate mutant with the smallest sha256(seed+app_id+mutant_id); if fewer than 40 "
            "qualify, run all that do.")),
        stages=["build", "tce", "baseline+coverage", "timing"],
        kill_rule="case vector (case, status) differs from the in-job untraced baseline, or completion differs",
        stop="Report actual usage, coverage, exact mutant counts and revised Job B/C cost; submit nothing else.",
        apps=a)
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    inputs = set()
    for x in a:
        inputs.update(r for r in x.get("sources", []) if not r.startswith("ZEPHYR/"))
        if x.get("prj_conf"):
            inputs.add(x["prj_conf"])
    inputs.update(OVERLAYS + [PLATFORM])
    code = ["joba/coordinator.py", "joba/worker.py", "joba/job.sbatch", "joba/submit.py",
            "generate_mutants.py", "dryrun_v1/mutants.jsonl", "dryrun_v1/generation_summary.json"]
    execution = dict(plan_sha256=sha(plan_path),
                     study_code_sha256={c: sha(STUDY / c) for c in code},
                     input_sha256={r: sha(ROOT / r) for r in sorted(inputs)},
                     image_relative="tacc_work/20261023-v10/images/rtc-ls6-v1.sif", image_sha256=IMAGE_SHA,
                     account="CCR26073", partition="development", su_cap=2,
                     total_study_ceiling_su=50, frozen_code_reused=["harness/tacc_counter_verification/run_packed.sh",
                                                                     "harness/tacc_counter_verification/runtime.sh",
                                                                     "harness/phase0/session.py"],
                     frozen_code_sha256={r: sha(ROOT / r) for r in [
                         "harness/tacc_counter_verification/run_packed.sh",
                         "harness/tacc_counter_verification/runtime.sh", "harness/phase0/session.py",
                         "harness/tacc_storage/publish.py", "harness/tacc_storage/protected_check.py",
                         "harness/tacc_storage/check_headroom.py"]})
    exe_path.write_text(json.dumps(execution, indent=2, sort_keys=True) + "\n")
    (HERE / "execution.sha256").write_text(f"{sha(exe_path)}  execution.json\n")
    print(json.dumps(dict(apps=len(a), sets=counts, plan_sha256=sha(plan_path), execution_sha256=sha(exe_path)),
                     indent=2))


if __name__ == "__main__":
    main()
