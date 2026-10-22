#!/usr/bin/env python3
"""Prepare an immutable transfer bundle from existing local records; no runs."""
import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLIPPING = ["sol-range_absent-rtc_alarm_pending-r01",
            "sol-range_absent-rtc_alarm_pending-r03",
            "astra-range_absent-rtc_alarm_pending-r05"]
STRATA = [("astra", "range_absent", "rtc_alarm_callback"),
          ("sol", "range_present", "rtc_alarm_callback"),
          ("luna", "range_absent", "rtc_time_counting"),
          ("luna", "range_present", "rtc_time_counting"),
          ("astra", "range_present", "rtc_alarm_pending")]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--renode-cache", type=Path, default=Path.home() / "Library/Application Support/renode")
    args = a.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"Use a new bundle directory; refusing overwrite: {out}")
    mrel = "results/rtc_factorial_v2/manifest.json"
    m = json.loads((ROOT / mrel).read_text())
    versions = m["versions"]
    records = ROOT / "results/rtc_factorial_v2/records"

    def originals(sid):
        rows = [json.loads(p.read_text()) for p in records.glob(f"{sid}-*.json")]
        rows.sort(key=lambda x: (0 if x["condition"] == "seeded" else 1,
                                 x["seed"] if x["seed"] is not None else x["condition"]))
        if len(rows) != 102:
            raise ValueError(f"Incomplete original suite: {sid}")
        return rows

    passing = []
    for stratum in STRATA:
        candidates = []
        for sid, v in sorted(versions.items()):
            if (v["model"], v.get("prompt_condition"), v["family"]) == stratum:
                if all(r["outcome"] == "pass" for r in originals(sid)):
                    candidates.append(sid)
        if not candidates:
            raise ValueError(f"No complete-passing suite in {stratum}")
        passing.append(candidates[0])
    selected = FLIPPING + passing
    inputs = {mrel, "subjects/phase3_rtc/plan.json", "results/phase1/environment.json"}
    tasks = []
    for sid in selected:
        v = versions[sid]
        for kind in ("source", "elf"):
            p = ROOT / v[f"{kind}_path"]
            if sha(p) != v[f"{kind}_sha256"]:
                raise ValueError(f"Frozen {kind} missing or changed: {sid}")
            inputs.add(v[f"{kind}_path"])
        for r in originals(sid):
            rel = f"results/rtc_factorial_v2/records/{r['run_id']}.json"
            for kind in ("platform", "trace"):
                if sha(ROOT / r[f"{kind}_path"]) != r[f"{kind}_sha256"]:
                    raise ValueError(f"Frozen {kind} changed: {r['run_id']}")
                inputs.add(r[f"{kind}_path"])
            inputs.add(rel)
            tasks.append({"index": len(tasks), "suite_id": sid, "run_id": r["run_id"],
                          "condition": r["condition"], "seed": r["seed"],
                          "frequency_hz": r["lsi_frequency_hz"], "original_record": rel,
                          "original_record_sha256": sha(ROOT / rel),
                          "expected_outcome": r["outcome"],
                          "expected_trace_sha256": r["trace_sha256"]})
    assert len(tasks) == 816 and len(set(selected)) == 8
    cache = args.renode_cache
    if not (cache / "binaries_index").is_file() or not (cache / "cached_binaries/bin0").is_file():
        raise ValueError("The saved Renode SVD cache is required (history is never copied)")
    # This package intentionally contains the study's only cached resource.
    svd = cache / "cached_binaries/bin0"
    if sha(svd) != "6e2b0146a335a932b3f3791dac0926d3576f7879900456f6508e2e0738d9375c":
        raise ValueError("Cached SVD differs from the inspected STM32F40x resource")
    out.mkdir(parents=True)
    files = {}
    for rel in sorted(inputs):
        dest = out / "study" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)
        files[f"study/{rel}"] = sha(dest)
    for rel in ("binaries_index", "cached_binaries/bin0"):
        dest = out / "renode-cache" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cache / rel, dest)
        files[f"renode-cache/{rel}"] = sha(dest)
    code = [ROOT / "harness/rtc_factorial_v2.py", ROOT / "harness/phase3_rtc/run.py",
            ROOT / "harness/phase0/session.py"]
    code += sorted((ROOT / "harness/tacc_phase1").glob("*.py"))
    code += sorted((ROOT / "harness/tacc_phase1").glob("*.sh"))
    code += sorted((ROOT / "harness/tacc_phase1").glob("*.sbatch"))
    code += [ROOT / "harness/tacc_phase1/rtc-ls6.def"]
    plan = {"schema_version": 1, "registered_utc": datetime.now(timezone.utc).isoformat(),
            "status": "registered before resource probe and TACC calibration",
            "system": "Lonestar6", "allocation": "TRA25006",
            "apptainer_module": "tacc-apptainer/1.4.1", "launcher_module": "launcher/3.10",
            "output_relative": "results/tacc_phase1_20261022_v1",
            "original_manifest": mrel, "selected_suites": selected,
            "flipping_suites": FLIPPING, "passing_suites": passing,
            "tasks": tasks, "input_sha256": files,
            "code_sha256": {str(p.relative_to(ROOT)): sha(p) for p in code},
            "expected_renode_version": m["renode_version"],
            "probe_task_index": next(t["index"] for t in tasks
                                     if t["suite_id"] == passing[0] and t["condition"] == "min"),
            "agreement": "Exact outcome and complete raw trace-file SHA-256; no normalization",
            "calibration_expected_counts": dict(Counter(t["expected_outcome"] for t in tasks)),
            "approval_gate": "STOP after calibration; do not submit production or edit paper"}
    p = out / "calibration_plan.json"
    p.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (out / "calibration_plan.sha256").write_text(f"{sha(p)}  calibration_plan.json\n")
    print(json.dumps({"bundle": str(out), "plan_sha256": sha(p), "tasks": len(tasks),
                      "expected": plan["calibration_expected_counts"], "passing_suites": passing}, indent=2))


if __name__ == "__main__":
    main()
