#!/usr/bin/env python3
"""Audit raw 100-MIPS HSI records and summarize registered screens and flips."""

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "subjects/phase3_hsi_100mips/plan.json"
RESULTS = ROOT / "results/phase3_hsi_100mips/qualified"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def wilson(fails: int, n: int) -> list[float] | None:
    if not n:
        return None
    z = 1.959963984540054
    p = fails / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - r), min(1.0, c + r)]


def expected_setting(plan: dict, condition: str, index: int) -> tuple[int, int]:
    if condition == "nominal" and 0 <= index < 5:
        return plan["nominal_frequency_hz"], plan["nominal_cpu_mips"]
    if condition == "seeded" and 0 <= index < 100:
        return plan["seeded_frequencies_hz"][index], plan["seeded_cpu_mips"][index]
    if condition in ("min", "max") and index == 0:
        offset = 0 if condition == "min" else 1
        return plan["endpoint_frequencies_hz"][offset], plan["endpoint_cpu_mips"][offset]
    raise ValueError(f"Unregistered condition/index: {condition}/{index}")


def main() -> None:
    plan = json.loads(PLAN.read_text())
    plan_hash = sha(PLAN)
    metadata = json.loads((RESULTS.parent / "execution_metadata.json").read_text())
    if (metadata["plan_sha256"] != plan_hash
            or sha(ROOT / metadata["qualified_runner_path"]) != metadata["qualified_runner_sha256"]
            or sha(ROOT / metadata["first_sandboxed_launch_record"]) != metadata["first_sandboxed_launch_sha256"]):
        raise ValueError("HSI execution metadata hash mismatch")
    first = json.loads((ROOT / metadata["first_sandboxed_launch_record"]).read_text())
    if first["outcome"] != "harness_error" or first["virtual_ns"] != 0:
        raise ValueError("Initial sandboxed infrastructure error was overwritten")
    for name, path_key, hash_key in (("orchestration.json", "shard_runner_path", "shard_runner_sha256"),
                                     ("orchestration_amendment.json", "script_path", "script_sha256")):
        schedule = json.loads((RESULTS.parent / name).read_text())
        if sha(ROOT / schedule[path_key]) != schedule[hash_key]:
            raise ValueError(f"HSI worker script changed: {name}")
    for name in ("semaphore_shard_amendment.json", "pending_shard_amendment.json",
                 "timer_screen_advance.json", "timer_shard_amendment.json",
                 "timer_middle_seed_amendment.json"):
        seed_shards = json.loads((RESULTS.parent / name).read_text())
        if sha(ROOT / seed_shards["runner_path"]) != seed_shards["runner_sha256"]:
            raise ValueError(f"HSI seed-shard runner changed: {name}")
    if sha(ROOT / plan["protocol_path"]) != plan["protocol_sha256"]:
        raise ValueError("Registered HSI protocol changed")
    records = {}
    platform_template = None
    for path in sorted((RESULTS / "records").glob("*.json")):
        row = json.loads(path.read_text())
        ident, condition, index = row["version_id"], row["condition"], row["index"]
        if ident not in plan["inventory"] or path.stem != row["run_id"]:
            raise ValueError(f"Unregistered or misnamed record: {path}")
        key = (ident, condition, index)
        if key in records:
            raise ValueError(f"Duplicate record: {key}")
        version = plan["inventory"][ident]
        hz, mips = expected_setting(plan, condition, index)
        if (row["plan_sha256"] != plan_hash or row["hsi_frequency_hz"] != hz
                or row["systick_frequency_hz"] != hz or row["cpu_performance_mips"] != mips
                or row["quantum_ns"] != plan["quantum_ns"]
                or row["observation_step_ns"] != plan["observation_step_ns"]
                or row["max_virtual_sec"] != plan["max_virtual_sec"]
                or row["hsi_bound_hz"] != plan["hsi_bound_hz"]
                or row["renode_version"] != plan["renode_version"]
                or row["elf_sha256"] != version["elf_sha256"]
                or row["elf_path"] != version["elf_path"]
                or row["selected_case"] != version["case"]
                or row["task_id"] != version["task_id"]):
            raise ValueError(f"Frozen input mismatch: {path}")
        if row["source_path"] != version.get("source_path") or row["source_sha256"] != version.get("source_sha256"):
            raise ValueError(f"Frozen source mismatch: {path}")
        if sha(ROOT / row["elf_path"]) != version["elf_sha256"]:
            raise ValueError(f"ELF changed after run: {path}")
        if version["kind"] == "agent":
            if sha(ROOT / row["source_path"]) != version["source_sha256"]:
                raise ValueError(f"Test source changed after run: {path}")
        else:
            for relative, expected in version["selected_case_sources"].items():
                if sha(ROOT / relative) != expected:
                    raise ValueError(f"Upstream selected source changed: {path}")
        for artifact in ("platform", "uart", "monitor", "trace"):
            saved_hash = row[artifact + "_sha256"]
            saved_path = ROOT / row[artifact + "_path"]
            if saved_hash and sha(saved_path) != saved_hash:
                raise ValueError(f"{artifact} hash mismatch: {path}")
        monitor_text = (ROOT / row["monitor_path"]).read_text(errors="replace")
        if (row["outcome"] != "harness_error" and
                (f"cpu PerformanceInMips {mips}" not in monitor_text
                 or 'emulation SetGlobalQuantum "0.000001"' not in monitor_text)):
            raise ValueError(f"Renode CPU/quantum command missing: {path}")
        if row["outcome"] == "harness_error" and row["virtual_ns"] != 0:
            raise ValueError(f"Harness error after virtual-time advance requires review: {path}")
        platform = (ROOT / row["platform_path"]).read_text()
        setting = f"systickFrequency: {hz}"
        if platform.count(setting) != 1:
            raise ValueError(f"SysTick frequency absent/duplicated: {path}")
        template = platform.replace(setting, "systickFrequency: <HSI>")
        if platform_template is None:
            platform_template = template
        elif template != platform_template:
            raise ValueError(f"Non-HSI platform setting changed: {path}")
        trace = json.loads((ROOT / row["trace_path"]).read_text())
        if (trace["run_id"] != row["run_id"] or trace["outcome"] != row["outcome"]
                or trace["cases"] != row["cases"] or trace["hsi_frequency_hz"] != hz
                or trace["cpu_performance_mips"] != mips):
            raise ValueError(f"Trace mismatch: {path}")
        if row["outcome"] in ("pass", "fail"):
            if version["kind"] == "upstream" and not any(
                    case["case"] == version["case"] and case["status"] == row["outcome"]
                    for case in row["cases"]):
                raise ValueError(f"Selected upstream verdict missing: {path}")
            if version["kind"] == "agent" and not row["cases"]:
                raise ValueError(f"Generated case verdict missing: {path}")
        records[key] = row

    versions = {}
    pairs = []
    for ident, version in plan["inventory"].items():
        nominal = [records.get((ident, "nominal", i)) for i in range(5)]
        nominal_counts = dict(Counter(r["outcome"] if r else "missing" for r in nominal))
        eligible = all(r is not None and r["outcome"] == "pass" for r in nominal)
        seeded = [records.get((ident, "seeded", i)) for i in range(100)]
        seed_counts = dict(Counter(r["outcome"] if r else "missing" for r in seeded))
        if not eligible and any(seeded):
            raise ValueError(f"Seeded run for version without 5/5 nominal screen: {ident}")
        n = seed_counts.get("pass", 0) + seed_counts.get("fail", 0)
        versions[ident] = {
            "task_id": version["task_id"], "kind": version["kind"],
            "nominal_statuses": nominal_counts, "nominal_5_of_5": eligible,
            "seeded_statuses": seed_counts,
            "evaluable": n, "failures": seed_counts.get("fail", 0),
            "flip_rate": seed_counts.get("fail", 0) / n if n else None,
            "wilson_95": wilson(seed_counts.get("fail", 0), n),
            "endpoints": {side: records.get((ident, side, 0), {}).get("outcome", "missing")
                          for side in ("min", "max")},
        }
    for ident, version in plan["inventory"].items():
        if version["kind"] != "agent" or not versions[ident]["nominal_5_of_5"]:
            continue
        upstream_id = f"upstream/{version['task_id']}"
        cells = Counter()
        for seed in range(100):
            left = records.get((upstream_id, "seeded", seed))
            right = records.get((ident, "seeded", seed))
            if left and right and left["outcome"] in ("pass", "fail") and right["outcome"] in ("pass", "fail"):
                cells[left["outcome"] + "/" + right["outcome"]] += 1
        pairs.append({"task_id": version["task_id"], "agent_version": ident,
                      "upstream_version": upstream_id, "evaluable_paired_seeds": sum(cells.values()),
                      "both_pass": cells["pass/pass"], "both_fail": cells["fail/fail"],
                      "upstream_only_fail": cells["fail/pass"],
                      "agent_only_fail": cells["pass/fail"]})
    task_summary = defaultdict(lambda: {"upstream": None, "agent_versions": [],
                                        "eligible_agent_versions": [], "agent_failures": 0,
                                        "agent_evaluable": 0})
    for ident, row in versions.items():
        task = task_summary[row["task_id"]]
        if row["kind"] == "upstream":
            task["upstream"] = {"version": ident, "nominal_5_of_5": row["nominal_5_of_5"],
                                "seeded_statuses": row["seeded_statuses"],
                                "evaluable": row["evaluable"], "failures": row["failures"]}
        else:
            task["agent_versions"].append(ident)
            if row["nominal_5_of_5"]:
                task["eligible_agent_versions"].append(ident)
                task["agent_failures"] += row["failures"]
                task["agent_evaluable"] += row["evaluable"]
    completed = (all(v["nominal_statuses"].get("missing", 0) == 0 for v in versions.values())
                 and all((not v["nominal_5_of_5"] or
                          v["seeded_statuses"].get("missing", 0) == 0 and
                          all(x != "missing" for x in v["endpoints"].values()))
                         for v in versions.values()))
    if completed:
        record_ids = {row["run_id"] for row in records.values()}
        for artifact, suffix in (("monitor", ".log"), ("traces", ".json"), ("uart", ".log")):
            artifact_ids = {p.stem for p in (RESULTS / artifact).glob("*" + suffix)}
            if artifact_ids - record_ids:
                raise ValueError(f"Unrecorded {artifact} artifacts: {sorted(artifact_ids - record_ids)[:4]}")
            if artifact in ("monitor", "traces") and artifact_ids != record_ids:
                raise ValueError(f"Missing {artifact} artifacts after schedule completion")
    summary = {
        "plan_sha256": plan_hash, "raw_record_count": len(records),
        "candidate_versions": len(plan["inventory"]), "schedule_mips_counts": dict(Counter(plan["seeded_cpu_mips"])),
        "max_quantization_error_mips": max(abs(m - 100 * f / 16_000_000)
                                           for m, f in zip(plan["seeded_cpu_mips"], plan["seeded_frequencies_hz"])),
        "complete": completed, "versions": versions,
        "task_summary": dict(task_summary), "paired": pairs,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    paired_path = RESULTS / "paired_schedules.csv"
    with paired_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["seed", "hsi_frequency_hz", "cpu_mips"] + list(plan["inventory"]))
        for seed in range(100):
            writer.writerow([seed, plan["seeded_frequencies_hz"][seed], plan["seeded_cpu_mips"][seed]] +
                            [records.get((ident, "seeded", seed), {}).get("outcome", "missing")
                             for ident in plan["inventory"]])
    print(f"Audited {len(records)} HSI records; {len(versions)} candidates; complete={completed}; "
          f"eligible={sum(v['nominal_5_of_5'] for v in versions.values())}")


if __name__ == "__main__":
    main()
