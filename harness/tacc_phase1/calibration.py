#!/usr/bin/env python3
"""Run and compare Phase 1 records using the unchanged original simulator loop."""
import argparse
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import sha


def exclusive(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")


def plan_at(bundle):
    p = bundle / "calibration_plan.json"
    expected = (bundle / "calibration_plan.sha256").read_text().split()[0]
    if sha(p) != expected:
        raise ValueError("Calibration plan hash differs")
    return json.loads(p.read_text()), expected


def stop(root, reason):
    try:
        exclusive(root / "STOP.json", {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                                      "reason": reason})
    except FileExistsError:
        pass


def run(args):
    bundle = args.bundle.resolve()
    plan, plan_hash = plan_at(bundle)
    study = bundle / "study"
    output = study / plan["output_relative"]
    if (output / "STOP.json").exists():
        raise RuntimeError("Calibration stop marker exists; no further runs authorized")
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Must run on a Slurm compute node")
    index = plan["probe_task_index"] if args.phase == "probe" else args.index
    if index is None or not 0 <= index < len(plan["tasks"]):
        raise ValueError("Invalid calibration task index")
    task = plan["tasks"][index]
    phase_out = output / args.phase
    # A task attempt can never be retried in place, including orphaned artifacts.
    exclusive(phase_out / "claims" / f"{index:04d}.json",
              {"task_index": index, "slurm_job_id": os.environ["SLURM_JOB_ID"]})
    try:
        code_root = Path(__file__).resolve().parents[2]
        for rel, expected in plan["code_sha256"].items():
            # Slurm scripts are checked by the host preflight; Python and the
            # original loop are checked against the image's baked copy here.
            if rel.endswith(".py") and sha(code_root / rel) != expected:
                raise ValueError(f"Baked code differs: {rel}")
        original_path = study / task["original_record"]
        if sha(original_path) != task["original_record_sha256"]:
            raise ValueError("Original record changed")
        original = json.loads(original_path.read_text())
        manifest = json.loads((study / plan["original_manifest"]).read_text())
        version = manifest["versions"][task["suite_id"]]
        for kind in ("source", "elf"):
            if sha(study / version[f"{kind}_path"]) != version[f"{kind}_sha256"]:
                raise ValueError(f"Frozen {kind} changed")
        platform = study / original["platform_path"]
        if sha(platform) != original["platform_sha256"]:
            raise ValueError("Frozen platform changed")
        binary = Path(os.environ["RENODE_BIN"])
        actual_version = subprocess.check_output([str(binary), "--version"], text=True).strip()
        if actual_version != plan["expected_renode_version"]:
            raise ValueError(f"Renode version differs: {actual_version!r}")
        image_hash = os.environ["RTC_CONTAINER_SHA256"]
        if len(image_hash) != 64 or any(c not in "0123456789abcdef" for c in image_hash):
            raise ValueError("Missing or invalid sealed container hash")
        apptainer_version = os.environ["RTC_APPTAINER_VERSION"]
        if not re.search(r"\b1\.4\.1(?:\s|$)", apptainer_version):
            raise ValueError(f"Apptainer 1.4.1 required: {apptainer_version}")
        if os.environ.get("RTC_LAUNCHER_MODULE") != "launcher/3.10":
            raise ValueError("Launcher 3.10 required")
        module_path = code_root / "harness/rtc_factorial_v2.py"
        spec = importlib.util.spec_from_file_location("rtc_frozen_calibration_loop", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT, module.OUT = study, phase_out
        module.MANIFEST = study / plan["original_manifest"]
        # Reuse saved platform bytes, without generating or changing platforms.
        def saved_platform(hz):
            if hz != original["lsi_frequency_hz"]:
                raise ValueError("Requested frequency differs from original")
            return platform
        module.path_for = saved_platform
        saved_writer = module.write_new

        def provenance_writer(path, value):
            if path.parent.name == "records":
                value = {**value, "node_name": os.environ.get("RTC_NODE_NAME", socket.gethostname()),
                         "container_sha256": image_hash, "slurm_job_id": os.environ["SLURM_JOB_ID"],
                         "apptainer_version": apptainer_version,
                         "apptainer_module": "tacc-apptainer/1.4.1", "launcher_module": "launcher/3.10",
                         "slurm_partition": os.environ.get("SLURM_JOB_PARTITION"),
                         "calibration_plan_sha256": plan_hash, "calibration_task_index": index,
                         "calibration_phase": args.phase, "original_record_sha256": task["original_record_sha256"],
                         "actual_renode_version": actual_version}
            saved_writer(path, value)
        module.write_new = provenance_writer
        schedule = json.loads((study / "subjects/phase3_rtc/plan.json").read_text())
        result = module.simulate(manifest, schedule, task["suite_id"],
                                 task["condition"], task["seed"] or 0)
        same_verdict = result["outcome"] == task["expected_outcome"]
        same_trace = result["trace_sha256"] == task["expected_trace_sha256"]
        comparison = {"task_index": index, "run_id": task["run_id"],
                      "expected_outcome": task["expected_outcome"], "observed_outcome": result["outcome"],
                      "verdict_agrees": same_verdict, "trace_hash_agrees": same_trace,
                      "expected_trace_sha256": task["expected_trace_sha256"],
                      "observed_trace_sha256": result["trace_sha256"],
                      "record_sha256": sha(phase_out / "records" / f"{task['run_id']}.json")}
        exclusive(phase_out / "comparisons" / f"{index:04d}.json", comparison)
        if not same_verdict or not same_trace or result["outcome"] not in ("pass", "fail"):
            raise RuntimeError(f"Calibration mismatch or missing verdict: {task['run_id']}")
        print(json.dumps(comparison, sort_keys=True))
    except Exception as exc:
        stop(output, f"{args.phase} task {index}: {type(exc).__name__}: {exc}")
        raise


def verify(args):
    plan, digest = plan_at(args.bundle)
    for rel, expected in plan["input_sha256"].items():
        if sha(args.bundle / rel) != expected:
            raise ValueError(f"Bundle input differs: {rel}")
    if args.repo:
        for rel, expected in plan["code_sha256"].items():
            if sha(args.repo / rel) != expected:
                raise ValueError(f"Build/submission code differs: {rel}")
    print(json.dumps({"status": "input hashes verified", "plan_sha256": digest,
                      "tasks": len(plan["tasks"])}, indent=2))


def compare(args):
    plan, digest = plan_at(args.bundle)
    output = args.bundle / "study" / plan["output_relative"]
    rows = []
    missing = []
    provenance = {"container_sha256": set(), "apptainer_version": set(),
                  "node_name": set(), "slurm_job_id": set()}
    for task in plan["tasks"]:
        path = output / "calibration/comparisons" / f"{task['index']:04d}.json"
        record = output / "calibration/records" / f"{task['run_id']}.json"
        if not path.exists() or not record.exists():
            missing.append(task["index"])
            continue
        r, d = json.loads(path.read_text()), json.loads(record.read_text())
        trace = args.bundle / "study" / d["trace_path"]
        if sha(record) != r["record_sha256"] or sha(trace) != r["observed_trace_sha256"]:
            raise ValueError(f"New record or trace changed: {task['run_id']}")
        if d["calibration_plan_sha256"] != digest:
            raise ValueError("New record has another calibration plan")
        for key in provenance:
            if not d.get(key):
                raise ValueError(f"Missing execution provenance: {task['run_id']}: {key}")
            provenance[key].add(d[key])
        if not re.search(r"\b1\.4\.1(?:\s|$)", d["apptainer_version"]):
            raise ValueError("A record used an unapproved Apptainer version")
        # Recompute agreement; never trust saved boolean flags alone.
        r["verdict_agrees"] = d["outcome"] == task["expected_outcome"]
        r["trace_hash_agrees"] = sha(trace) == task["expected_trace_sha256"]
        rows.append(r)
    mismatch = [r for r in rows if not r["verdict_agrees"] or not r["trace_hash_agrees"]]
    probe = output / "probe/comparisons" / f"{plan['probe_task_index']:04d}.json"
    probe_ok = probe.exists() and all(json.loads(probe.read_text()).get(k) is True
                                    for k in ("verdict_agrees", "trace_hash_agrees"))
    result = {"plan_sha256": digest, "expected": len(plan["tasks"]), "completed": len(rows),
              "verdict_agreement": sum(r["verdict_agrees"] for r in rows),
              "trace_hash_agreement": sum(r["trace_hash_agrees"] for r in rows),
              "missing_task_indices": missing, "mismatches": mismatch, "probe_agrees": probe_ok,
              "outcomes": dict(Counter(r["observed_outcome"] for r in rows)),
              "execution_provenance": {k: sorted(v) for k, v in provenance.items()},
              "status": "agreement_pending_user_approval" if not missing and not mismatch and probe_ok
                        and not (output / "STOP.json").exists() else "STOP_incomplete_or_mismatch",
              "next_action": "STOP and send this report to the user; do not submit production"}
    if len(provenance["container_sha256"]) > 1:
        result["status"] = "STOP_multiple_container_hashes"
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "agreement_pending_user_approval":
        raise SystemExit(2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("verify", "run", "compare"):
        a = sub.add_parser(name)
        a.add_argument("--bundle", type=Path, required=True)
        if name == "verify": a.add_argument("--repo", type=Path)
        if name == "run":
            a.add_argument("--phase", choices=("probe", "calibration"), required=True)
            a.add_argument("--index", type=int)
    args = p.parse_args()
    {"verify": verify, "run": run, "compare": compare}[args.command](args)


if __name__ == "__main__":
    main()
