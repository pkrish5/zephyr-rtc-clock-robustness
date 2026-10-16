#!/usr/bin/env python3
"""Append prespecified source units to the existing blinded RQ1 packet.

The first 12 packet items, their IDs, and the independent review form are
preserved. Run --final only after the two RTC Luna sources have been frozen and
source-coded; it adds two RTC upstream and two Luna units for 30 total.
"""

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

from make_blind_rq1_packet import remove_comments

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/blind_rq1"
KEY = ROOT / "analysis/blind_rq1_key.json"
DECISIONS = ROOT / "analysis/phase3_rq1_decisions.json"
EXTENSION = ROOT / "analysis/rtc_extension_rq1_decisions.json"

# Chosen for task coverage and explicit uncertain-case representation, before
# reading any independent labels or new RTC timing outcomes.
EXISTING_ADDITIONS = [
    "semaphore.test_sem_give_from_isr",
    "lifo_contexts.test_lifo_isr2thread",
    "msgq_api.test_msgq_isr",
    "queue_api.test_queue_isr2thread",
    "work_1cpu.test_1cpu_basic_schedule",
    "semaphore-r01", "lifo_api-r01", "msgq_api-r01", "queue-r01",
    "workq-r05", "rtc_alarm_callback-r02", "sleep-r01",
    "timer_api-r01", "pending-r01",
]
FINAL_ADDITIONS = [
    "rtc_api.test_time_counting", "rtc_time_counting-r01",
    "rtc_api.test_alarm", "rtc_alarm_pending-r01",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_state() -> tuple[dict, list[dict]]:
    key = json.loads(KEY.read_text())
    if sha(BASE / "PACKET.md") != key["packet_sha256"]:
        raise ValueError("Existing packet index changed")
    for item in key["items"]:
        if sha(BASE / "items" / f"{item['item_id']}.md") != item["packet_sha256"]:
            raise ValueError(f"Existing blinded source changed: {item['item_id']}")
    with (BASE / "labels.csv").open(newline="") as stream:
        labels = list(csv.DictReader(stream))
    if [r["item_id"] for r in labels] != [r["item_id"] for r in key["items"]]:
        raise ValueError("Independent label IDs do not match packet")
    if any(r["label"] or r["reason"] or r["recognized_source"] for r in labels):
        raise ValueError("Independent review has begun; packet must remain frozen")
    return key, labels


def append_item(key: dict, labels: list[dict], decisions: dict, decision_id: str,
                tasks: dict, index_lines: list[str]) -> None:
    if decision_id in {x["decision_id"] for x in key["items"]}:
        return
    decision = decisions[decision_id]
    item_id = f"R{len(key['items']) + 1:02d}"
    modules = []
    original = []
    for part_n, (path_str, expected_hash) in enumerate(decision["source_files_sha256"].items(), 1):
        path = ROOT / path_str
        if sha(path) != expected_hash:
            raise ValueError(f"Frozen source changed: {path_str}")
        modules += [f"## Module {part_n}", "", "```c",
                    remove_comments(path.read_text()).rstrip(), "```", ""]
        original.append({"path": path_str, "sha256": expected_hash})
    target = (decision_id.split(".", 1)[-1] if decision["kind"] == "upstream"
              else "the test case in this source")
    item_path = BASE / "items" / f"{item_id}.md"
    if item_path.exists():
        raise ValueError(f"Refusing to overwrite {item_path}")
    item_path.write_text(f"# Item {item_id}\n\nTarget case: `{target}`.\n\n"
                         + "\n".join(modules))
    index_lines.append(f"| {item_id} | {tasks[decision['task_id']]['feature_spec']} | "
                       f"[Open source](items/{item_id}.md) |")
    key["items"].append({
        "item_id": item_id, "decision_id": decision_id,
        "task_id": decision["task_id"], "kind": decision["kind"],
        "first_reviewer_label": decision["status"],
        "source_files": original, "packet_sha256": sha(item_path),
    })
    labels.append({"item_id": item_id, "label": "", "reason": "",
                   "recognized_source": ""})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    key, labels = load_state()
    decisions = json.loads(DECISIONS.read_text())["decisions"]
    if args.final:
        decisions.update(json.loads(EXTENSION.read_text())["decisions"])
    tasks = {t["id"]: t for file in ("subjects/phase2_tasks.json",
                                    "subjects/rtc_extension_tasks.json")
             for t in json.loads((ROOT / file).read_text())["tasks"]}
    index_lines = (BASE / "PACKET.md").read_text().splitlines()
    rng = random.Random(20260929 + 30)
    additions = EXISTING_ADDITIONS.copy()
    rng.shuffle(additions)
    if args.final:
        extras = FINAL_ADDITIONS.copy()
        rng.shuffle(extras)
        additions.extend(extras)
    for decision_id in additions:
        append_item(key, labels, decisions, decision_id, tasks, index_lines)
    n = len(key["items"])
    if n not in (26, 30):
        raise ValueError(f"Unexpected packet size: {n}")
    header = ("This is a **purposive, task-stratified, 30-unit source-review sample** for independent "
              "coding, not a prevalence sample." if n == 30 else
              "This packet is being prepared for a **purposive, task-stratified, 30-unit source review**; "
              "four registered RTC units remain to be appended before independent coding.")
    index_lines[2] = header + (" Read each source item without opening the source key or prior RQ1 "
        "decisions. Original C comments, including author/license headers and explanatory comments, "
        "and original paths have been removed. The code itself may still reveal provenance to "
        "someone who recognizes it; record any such recognition. Each item contains the complete "
        "relevant source file(s), so some include other test cases. Judge only the named target case "
        "and any helpers it calls. Original licensed files remain unchanged in the repository.")
    (BASE / "PACKET.md").write_text("\n".join(index_lines) + "\n")
    key["sampling"] = ("Purposive task-stratified source sample; original 12 fixed, 14 existing-task "
                       "units prespecified in expand_blind_rq1_packet.py, and four RTC extensions "
                       "if final; no prevalence inference")
    key["packet_sha256"] = sha(BASE / "PACKET.md")
    KEY.write_text(json.dumps(key, indent=2) + "\n")
    with (BASE / "labels.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["item_id", "label", "reason", "recognized_source"])
        writer.writeheader()
        writer.writerows(labels)
    print(f"Packet now has {n} blinded items; ready={n == 30}")


if __name__ == "__main__":
    main()
