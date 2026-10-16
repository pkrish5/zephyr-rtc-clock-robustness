#!/usr/bin/env python3
"""Audit Phase 2 frozen generation, build, and nominal records; report attrition."""

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COHORT = os.environ.get("PHASE2_COHORT", "luna_primary")
COHORT_PATHS = {
    "sol_pilot": ("subjects/phase2_tasks.json", "phase2"),
    "luna_primary": ("subjects/phase2_tasks.json", "phase2_luna"),
    "rtc_bound_supplement": ("subjects/phase2_rtc_bound_tasks.json", "phase2_rtc_bound"),
    "sol_comparison": ("subjects/phase2_tasks_v2.json", "phase2_sol_comparison"),
    "astra_comparison": ("subjects/phase2_tasks_v2.json", "phase2_astra_comparison"),
    "luna_rtc_extension": ("subjects/rtc_extension_tasks.json", "luna_rtc_extension"),
}
if COHORT not in COHORT_PATHS:
    raise RuntimeError("Unknown Phase 2 cohort")
task_file, cohort_directory = COHORT_PATHS[COHORT]
GENERATED = ROOT / "generated" / cohort_directory
RESULTS = ROOT / "results" / cohort_directory
TASKS = ROOT / task_file
TEMPLATE = ROOT / "generated/phase2/prompt_template.txt"
SCHEMA = ROOT / "generated/phase2/response.schema.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def keyed(records: list[dict], name: str) -> dict:
    result = {item["run_id"]: item for item in records}
    if len(result) != len(records):
        raise ValueError(f"Duplicate {name} run IDs")
    return result


def main() -> None:
    manifest = json.loads((GENERATED / "generation_manifest.json").read_text())
    tasks = json.loads(TASKS.read_text())["tasks"]
    if (sha256(TASKS) != manifest["task_manifest_sha256"]
            or sha256(TEMPLATE) != manifest["prompt_template_sha256"]
            or sha256(SCHEMA) != manifest["response_schema_sha256"]
            or manifest["k"] != 5):
        raise ValueError("Frozen generation inputs changed")
    generation = keyed(read_jsonl(RESULTS / "generation.jsonl"), "generation")
    builds = keyed(read_jsonl(RESULTS / "builds.jsonl"), "build")
    nominal = keyed(read_jsonl(RESULTS / "nominal_runs.jsonl"), "nominal")
    review_path = ROOT / "analysis" / f"phase2_oracle_decisions_{COHORT}.json"
    reviews = json.loads(review_path.read_text())["decisions"] if review_path.exists() else {}
    # The resource amendment reclassified the first Sol output as a one-sample
    # feasibility pilot; the frozen manifest still records its original k=5 plan.
    selected_tasks = tasks if COHORT != "sol_pilot" else [t for t in tasks if t["id"] == "rtc_alarm_callback"]
    indices = range(1, 6) if COHORT != "sol_pilot" else (1,)
    planned = {f"{t['id']}-r{i:02d}" for t in selected_tasks for i in indices}
    if (set(generation) | set(builds) | set(nominal) | set(reviews)) - planned:
        raise ValueError("Unregistered Phase 2 run ID")
    if set(builds) - set(generation) or set(nominal) - set(builds):
        raise ValueError("Build or nominal record lacks prior stage")
    rows = []
    total_usage = Counter()
    for task in selected_tasks:
        task_runs = []
        prompt_hashes = set()
        for index in indices:
            run_id = f"{task['id']}-r{index:02d}"
            g = generation.get(run_id)
            b = builds.get(run_id)
            n = nominal.get(run_id)
            review = reviews.get(run_id)
            if g:
                suite = GENERATED / "suites" / task["id"] / f"r{index:02d}"
                saved = json.loads((suite / "metadata.json").read_text())
                if saved != g or g["model_requested"] != manifest["model_requested"]:
                    raise ValueError(f"Generation record mismatch: {run_id}")
                if sha256(suite / "prompt.txt") != g["prompt_sha256"]:
                    raise ValueError(f"Prompt changed: {run_id}")
                prompt_hashes.add(g["prompt_sha256"])
                if g["source_sha256"] is not None and sha256(suite / "test.c") != g["source_sha256"]:
                    raise ValueError(f"Source changed: {run_id}")
                if g["usage"]:
                    total_usage.update(g["usage"])
            if b:
                if b["source_sha256"] != g["source_sha256"]:
                    raise ValueError(f"Build used changed source: {run_id}")
                if sha256(suite / "metadata.json") != b["generation_metadata_sha256"]:
                    raise ValueError(f"Generation metadata changed after build: {run_id}")
                if sha256(suite / "CMakeLists.txt") != b["cmake_sha256"] or sha256(suite / "prj.conf") != b["prj_conf_sha256"]:
                    raise ValueError(f"Build wrapper/config changed: {run_id}")
                for path, digest in b["overlay_sha256"].items():
                    if sha256(ROOT / path) != digest:
                        raise ValueError(f"Board overlay changed: {run_id}: {path}")
                if sha256(ROOT / b["build_log_path"]) != b["build_log_sha256"]:
                    raise ValueError(f"Build log changed: {run_id}")
                if b["elf_sha256"] is not None and sha256(ROOT / b["elf_path"]) != b["elf_sha256"]:
                    raise ValueError(f"ELF changed: {run_id}")
            if n:
                if n["elf_sha256"] != b["elf_sha256"] or n["source_sha256"] != g["source_sha256"]:
                    raise ValueError(f"Nominal inputs changed: {run_id}")
                if sha256(ROOT / n["platform_path"]) != n["platform_sha256"]:
                    raise ValueError(f"Platform changed: {run_id}")
                if sha256(ROOT / n["trace_path"]) != n["trace_sha256"]:
                    raise ValueError(f"Trace changed: {run_id}")
                if n["uart_sha256"] and sha256(ROOT / n["uart_path"]) != n["uart_sha256"]:
                    raise ValueError(f"UART changed: {run_id}")
                if not (ROOT / n["monitor_path"]).exists():
                    raise ValueError(f"Monitor transcript missing: {run_id}")
                if n["outcome"] == "pass" and not any(case["status"] == "pass" for case in n["cases"]):
                    raise ValueError(f"Nominal pass without a passing case: {run_id}")
            oracle_status = "not_reviewed"
            if review:
                if review["source_sha256"] != g["source_sha256"]:
                    raise ValueError(f"Oracle review source changed: {run_id}")
                judgments = [review["feature_path_exercised"]] + [o["judgment"] for o in review["oracles"]]
                if "pending" in judgments:
                    oracle_status = "pending"
                elif "not_met" in judgments:
                    oracle_status = "inadequate"
                elif "uncertain" in judgments:
                    oracle_status = "uncertain"
                else:
                    oracle_status = "adequate"
            task_runs.append({"run_id": run_id,
                              "generation": g["status"] if g else "missing",
                              "build": b["status"] if b else "not_run",
                              "nominal": n["outcome"] if n else "not_run",
                              "oracle": oracle_status})
        if len(prompt_hashes) > 1:
            raise ValueError(f"Repeated samples received different prompts: {task['id']}")
        rows.append({"task_id": task["id"], "arm": task["arm"],
                     "human_case": task["human_case"],
                     "prompt_sha256": next(iter(prompt_hashes), None), "runs": task_runs})
    flat = [run for row in rows for run in row["runs"]]
    summary = {
        "cohort": COHORT, "model_requested": manifest["model_requested"],
        "scope_note": ("55-run primary cohort" if COHORT == "luna_primary" else
                       "Five-run RTC context supplement" if COHORT == "rtc_bound_supplement" else
                       "Ten-run Luna adjacent RTC task extension" if COHORT == "luna_rtc_extension" else
                       "65-run complete-task comparison cohort" if COHORT in ("sol_comparison", "astra_comparison") else
                       "One retained Sol feasibility pilot after the registered resource amendment"),
        "codex_cli_version": manifest["codex_cli_version"],
        "planned_runs": len(planned), "finalized_generations": len(generation),
        "generation_statuses": dict(Counter(r["generation"] for r in flat)),
        "build_statuses": dict(Counter(r["build"] for r in flat)),
        "nominal_statuses": dict(Counter(r["nominal"] for r in flat)),
        "oracle_statuses": dict(Counter(r["oracle"] for r in flat)),
        "usage_totals": dict(total_usage),
        "tool_events": sum(g["tool_event_count"] for g in generation.values()),
        "api_dollar_cost": None,
        "api_dollar_cost_note": "ChatGPT-authenticated CLI does not expose billed API dollars",
        "rows": rows,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(f"{COHORT}: finalized {len(generation)}/{len(planned)}, "
          f"builds {len(builds)}, nominal {len(nominal)}")


if __name__ == "__main__":
    main()
