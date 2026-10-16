#!/usr/bin/env python3
"""Freeze/audit the user-selected 100 MIPS HSI input schedule and existing cohort inventory."""

import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "subjects/phase3_hsi_100mips/PROTOCOL.md"
PLAN = ROOT / "subjects/phase3_hsi_100mips/plan.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def candidate() -> dict:
    tasks_path = ROOT / "subjects/phase2_tasks.json"
    tasks = json.loads(tasks_path.read_text())["tasks"]
    judgments_path = ROOT / "analysis/phase2_split_gate_decisions.json"
    judgments = json.loads(judgments_path.read_text())["decisions"]
    rq1_path = ROOT / "analysis/phase3_rq1_decisions.json"
    rq1 = json.loads(rq1_path.read_text())["decisions"]
    builds_path = ROOT / "results/phase1/builds.jsonl"
    builds = {r["subject_id"]: r for r in map(json.loads, builds_path.read_text().splitlines())}
    inventory = {}
    for task in tasks:
        if task["arm"] != "hsi":
            continue
        tid = task["id"]
        build = builds[tid]
        upstream_id = task["human_case"]
        source_hashes = rq1[upstream_id]["source_files_sha256"]
        for path, expected in source_hashes.items():
            if sha(ROOT / path) != expected:
                raise ValueError(f"Upstream selected-case source changed: {path}")
        if sha(ROOT / build["elf_path"]) != build["elf_sha256"]:
            raise ValueError(f"Upstream ELF changed: {tid}")
        inventory[f"upstream/{tid}"] = {
            "task_id": tid, "case": upstream_id, "kind": "upstream",
            "elf_path": build["elf_path"], "elf_sha256": build["elf_sha256"],
            "selected_case_sources": source_hashes,
            "source_tree_sha256": build["source_tree_sha256"],
            "original_oracle_adequate": None, "functional": "met",
        }
        for key, row in judgments.items():
            if (row["cohort"] != "luna_primary" or row["task_id"] != tid
                    or row["functional"] != "met" or row["build"] != "pass"
                    or row["nominal"] != "pass"):
                continue
            run_id = row["run_id"]
            run_task, replica = run_id.rsplit("-r", 1)
            elf_path = (f"generated/phase2_luna/build/{run_task}/r{replica}/"
                        "zephyr/zephyr.elf")
            if sha(ROOT / row["source_path"]) != row["source_sha256"]:
                raise ValueError(f"Generated source changed: {run_id}")
            inventory[f"luna/{run_id}"] = {
                "task_id": tid, "case": "full_generated_suite", "kind": "agent",
                "elf_path": elf_path, "elf_sha256": sha(ROOT / elf_path),
                "source_path": row["source_path"], "source_sha256": row["source_sha256"],
                "original_oracle_adequate": row["original_oracle"] == "adequate",
                "functional": row["functional"], "timing_bound": row["timing_bound"],
            }
    freqs = [random.Random(seed).randint(15_840_000, 16_160_000) for seed in range(100)]
    mips = [(100 * f * 2 + 16_000_000) // (2 * 16_000_000) for f in freqs]
    # Integer arithmetic above is floor(x + 0.5), where x = 100*f/16 MHz.
    renode_version = json.loads((ROOT / "subjects/phase3_rtc/plan.json").read_text())["renode_version"]
    return {
        "schema_version": 1, "registered_date": "2026-09-29",
        "protocol_path": str(PROTOCOL.relative_to(ROOT)), "protocol_sha256": sha(PROTOCOL),
        "task_manifest_sha256": sha(tasks_path),
        "split_gate_decisions_sha256": sha(judgments_path),
        "rq1_decisions_sha256": sha(rq1_path),
        "phase1_build_records_sha256": sha(builds_path),
        "board": "stm32f4_disco/stm32f407xx", "renode_version": renode_version,
        "nominal_frequency_hz": 16_000_000, "nominal_cpu_mips": 100,
        "hsi_bound_hz": [15_840_000, 16_160_000],
        "bound_source": "STM32F407 DS8626 Rev 12 HSI accuracy at 25 C: +/-1%",
        "quantum_ns": 1000, "observation_step_ns": 250_000_000,
        "max_virtual_sec": 90, "nominal_repeats": 5,
        "seed_start": 0, "seed_count": 100,
        "seed_distribution": "random.Random(seed).randint(15840000, 16160000)",
        "mips_rule": "floor(100*frequency_hz/16000000 + 0.5)",
        "seeded_frequencies_hz": freqs, "seeded_cpu_mips": mips,
        "endpoint_frequencies_hz": [15_840_000, 16_160_000],
        "endpoint_cpu_mips": [99, 101],
        "inventory": dict(sorted(inventory.items())),
    }


def main() -> None:
    expected = candidate()
    if PLAN.exists():
        saved = json.loads(PLAN.read_text())
        if saved != expected:
            raise ValueError("Frozen HSI plan or input changed")
        verb = "Audited"
    else:
        PLAN.write_text(json.dumps(expected, sort_keys=True, indent=2) + "\n")
        verb = "Registered"
    print(f"{verb} HSI plan: {len(expected['inventory'])} existing candidate versions, "
          f"100 seeds, {len(set(expected['seeded_frequencies_hz']))} distinct frequencies, "
          f"CPU MIPS states {sorted(set(expected['seeded_cpu_mips']))}; sha256={sha(PLAN)}")


if __name__ == "__main__":
    main()
