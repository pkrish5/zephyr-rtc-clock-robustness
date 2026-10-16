#!/usr/bin/env python3
"""Freeze the complete 13-task input set only after Luna extension gates finish."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "subjects/phase2_tasks.json"
EXTENSION = ROOT / "subjects/rtc_extension_tasks.json"
FULL = ROOT / "subjects/phase2_tasks_v2.json"
LOCK = ROOT / "generated/cross_model_v2/lock.json"
TEMPLATE = ROOT / "generated/phase2/prompt_template.txt"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rendered(task: dict) -> str:
    return TEMPLATE.read_text().format(
        feature_spec=task["feature_spec"],
        oracle_bullets="\n".join(f"- {item}" for item in task["required_oracles"]),
        api_hints=task["api_hints"], build_conf=task["build_conf"].rstrip())


def expected_manifest() -> dict:
    original = json.loads(ORIGINAL.read_text())
    extension = json.loads(EXTENSION.read_text())
    if original["zephyr_commit"] != extension["zephyr_commit"] or original["board"] != extension["board"]:
        raise ValueError("Zephyr or board mismatch")
    tasks = original["tasks"] + extension["tasks"]
    if len(tasks) != 13 or len({t["id"] for t in tasks}) != 13:
        raise ValueError("Expected 13 unique tasks")
    if sum(t["arm"] == "hsi" for t in tasks) != 10 or sum(t["arm"] == "lsi_pilot" for t in tasks) != 3:
        raise ValueError("Unexpected timing strata")
    for name in ("rtc_counting", "rtc_alarm_pending"):
        row = json.loads((ROOT / "results" / name / "qualification.json").read_text())
        if not row["qualified_for_proposed_task_list"] or row["selected_outcomes"] != {"pass": 5}:
            raise ValueError(f"Selected-case qualification incomplete: {name}")
    iwdg = json.loads((ROOT / "results/iwdg_fidelity_configured/summary.json").read_text())
    if iwdg["passes_prespecified_fidelity_probe"]:
        raise ValueError("IWDG scope must be reviewed separately before inclusion")
    return {"schema_version": 2, "zephyr_commit": original["zephyr_commit"],
            "board": original["board"], "tasks": tasks}


def validate_luna_inputs(tasks: list[dict]) -> None:
    extension_summary = json.loads((ROOT / "results/luna_rtc_extension/summary.json").read_text())
    gates = json.loads((ROOT / "results/luna_rtc_extension/gate_summary.json").read_text())
    if extension_summary["finalized_generations"] != 10 or extension_summary["build_statuses"].get("not_run", 0):
        raise ValueError("Luna extension generation/build incomplete")
    if gates["source_summary_sha256"] != sha(ROOT / "results/luna_rtc_extension/summary.json"):
        raise ValueError("Gate summary is stale")
    statuses = {r["run_id"]: r for r in gates["rows"]}
    if len(statuses) != 10:
        raise ValueError("Luna extension gate inventory incomplete")
    for run_id, row in statuses.items():
        if row["build"] == "pass" and row["nominal"] == "not_run":
            raise ValueError(f"Nominal screen incomplete: {run_id}")
    original_luna = ROOT / "generated/phase2_luna/suites"
    new_luna = ROOT / "generated/luna_rtc_extension/suites"
    for task in tasks:
        expected = hashlib.sha256(rendered(task).encode()).hexdigest()
        base = new_luna if task["id"] in ("rtc_time_counting", "rtc_alarm_pending") else original_luna
        for index in range(1, 6):
            suite = base / task["id"] / f"r{index:02d}"
            meta = json.loads((suite / "metadata.json").read_text())
            if (meta["status"] != "generated" or meta["prompt_sha256"] != expected or
                    sha(suite / "prompt.txt") != expected or sha(suite / "test.c") != meta["source_sha256"]):
                raise ValueError(f"Frozen Luna prompt/source mismatch: {task['id']}-r{index:02d}")


def expected_lock() -> dict:
    files = [
        "subjects/phase2_tasks.json", "subjects/rtc_extension_tasks.json",
        "subjects/phase2_tasks_v2.json", "subjects/phase3_hsi_100mips/plan.json",
        "subjects/phase3_rtc/plan.json", "generated/phase2/prompt_template.txt",
        "generated/phase2/response.schema.json", "generated/cross_model_v2/PROTOCOL.md",
        "generated/luna_rtc_extension/PROTOCOL.md",
        "generated/luna_rtc_extension/CLI_TRANSPORT_AMENDMENT.md",
        "generated/phase2_luna/generation_manifest.json",
        "generated/luna_rtc_extension/generation_manifest.json",
        "analysis/PHASE2_SPLIT_GATE_PROTOCOL.md",
        "analysis/phase2_split_gate_decisions.json",
        "analysis/luna_rtc_extension_functional_decisions.json",
        "analysis/rtc_extension_rq1_decisions.json",
        "results/luna_rtc_extension/summary.json",
        "results/luna_rtc_extension/gate_summary.json",
        "results/rtc_counting/qualification.json",
        "results/rtc_alarm_pending/qualification.json",
        "results/iwdg_fidelity_configured/summary.json",
        "harness/phase2/generate.py", "harness/phase2/build_nominal.py",
        "analysis/phase2_summary.py", "analysis/phase2_oracle_review.py",
        "analysis/luna_rtc_extension_gates.py", "analysis/freeze_cross_model_v2.py",
    ]
    return {
        "schema_version": 2, "registered_date": "2026-09-29/30",
        "task_count": 13, "generations_per_task": 5,
        "model_ids": ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"],
        "exclude_sol_feasibility_pilot": True,
        "exclude_rtc_bound_context_supplement": True,
        "input_sha256": {name: sha(ROOT / name) for name in files},
    }


def main() -> None:
    full = expected_manifest()
    validate_luna_inputs(full["tasks"])
    if FULL.exists():
        if json.loads(FULL.read_text()) != full:
            raise ValueError("Frozen complete task manifest changed")
    else:
        FULL.write_text(json.dumps(full, sort_keys=True, indent=2) + "\n")
    lock = expected_lock()
    if LOCK.exists():
        if json.loads(LOCK.read_text()) != lock:
            raise ValueError("Frozen complete-task input lock changed")
    else:
        LOCK.write_text(json.dumps(lock, sort_keys=True, indent=2) + "\n")
    print(f"Frozen 13 tasks, 65 Luna sources, and v2 input lock sha256={sha(LOCK)}")


if __name__ == "__main__":
    main()
