#!/usr/bin/env python3
"""Recreate a fixed, comment-stripped source packet for independent RQ1 review."""

import csv
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/blind_rq1"
DECISIONS = json.loads((ROOT / "analysis/phase3_rq1_decisions.json").read_text())["decisions"]
TASKS = {t["id"]: t for t in json.loads((ROOT / "subjects/phase2_tasks.json").read_text())["tasks"]}

# Purposive matched-task sample: no inferred prevalence from these 12 units.
SELECTED = [
    "rtc_alarm_callback-r04", "rtc_api.test_alarm_callback",
    "sleep-r04", "sleep.test_sleep",
    "pending-r03", "pending.test_pending_timer",
    "context-r02", "context_one_cpu.test_k_sleep",
    "fifo_api-r01", "fifo_api.test_fifo_isr2thread",
    "timer_api-r03", "timer_api.test_timer_status_sync",
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def remove_comments(source: str) -> str:
    """Strip C comments, preserving strings/chars and newline positions."""
    out = []
    i = 0
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code" and ch == '"':
            state = "string"
            out.append(ch)
        elif state == "code" and ch == "'":
            state = "char"
            out.append(ch)
        elif state == "code" and ch == "/" and nxt in ("/", "*"):
            state = "line" if nxt == "/" else "block"
            i += 1
        elif state == "line":
            if ch == "\n":
                out.append(ch)
                state = "code"
        elif state == "block":
            if ch == "*" and nxt == "/":
                i += 1
                state = "code"
            elif ch == "\n":
                out.append(ch)
        elif state in ("string", "char"):
            out.append(ch)
            if ch == "\\" and nxt:
                out.append(nxt)
                i += 1
            elif ch == ('"' if state == "string" else "'"):
                state = "code"
        else:
            out.append(ch)
        i += 1
    if state not in ("code", "line"):
        raise ValueError(f"Unterminated lexical state: {state}")
    lines = [line.rstrip() for line in "".join(out).splitlines()]
    compact = []
    for line in lines:
        if line or (compact and compact[-1]):
            compact.append(line)
    return "\n".join(compact).strip() + "\n"


def main() -> None:
    if BASE.exists():
        raise RuntimeError(f"Packet already exists; refusing to overwrite {BASE}")
    rng = random.Random(20260929)
    order = SELECTED.copy()
    rng.shuffle(order)
    BASE.mkdir()
    (BASE / "items").mkdir()
    index = ["# Blinded RQ1 source-review packet — 2026-09-29", "",
             "This is a **purposive, matched-task, 12-unit pilot sample** for independent coding, not a prevalence sample. Read each source item without opening the source key or prior RQ1 decisions. Original C comments, including author/license headers and explanatory comments, and original paths have been removed. The code itself may still reveal provenance to someone who recognizes it; record any such recognition. Each item contains the complete relevant source file(s), so some include other test cases. Judge only the named target case and any helpers it calls. Original licensed files remain unchanged in the repository.", "",
             "Code `unjustified` if a pass/fail assertion depends on a fixed wait, deadline, immediate event check, ordering, or shared-state premise unsupported by the supplied behavior or a documented API/hardware guarantee. Code `none_found` when no such premise is found in the target case. Code `unknown` if contract or execution context is insufficient. A finite timeout alone is not automatically unjustified. `irq_offload()` is synchronous on return. Record the shortest source-level reason and any source identity you recognized. Do not use simulator outcomes. Return the completed [label form](labels.csv); leave the source packet unchanged.", "",
             "| Item | Intended behavior | Source |", "| --- | --- | --- |"]
    key = {"schema_version": 1, "created_date": "2026-09-29",
           "sampling": "Purposive six matched tasks, one agent version and one upstream selected case per task; shuffled with Random(20260929)",
           "source_review_sha256": sha((ROOT / "analysis/phase3_rq1_decisions.json").read_bytes()),
           "items": []}
    label_rows = []
    for n, decision_id in enumerate(order, 1):
        item_id = f"R{n:02d}"
        decision = DECISIONS[decision_id]
        task = TASKS[decision["task_id"]]
        parts = []
        original = []
        for part_n, (path_str, expected_hash) in enumerate(decision["source_files_sha256"].items(), 1):
            path = ROOT / path_str
            raw = path.read_bytes()
            if sha(raw) != expected_hash:
                raise RuntimeError(f"Frozen source changed: {path_str}")
            stripped = remove_comments(raw.decode("utf-8"))
            parts += [f"## Module {part_n}", "", "```c", stripped.rstrip(), "```", ""]
            original.append({"path": path_str, "sha256": expected_hash})
        item_text = f"# Item {item_id}\n\nTarget case: `{decision_id.split('.', 1)[-1] if decision['kind'] == 'upstream' else 'the test case in this source'}`.\n\n" + "\n".join(parts)
        item_path = BASE / "items" / f"{item_id}.md"
        item_path.write_text(item_text)
        index.append(f"| {item_id} | {task['feature_spec']} | [Open source](items/{item_id}.md) |")
        key["items"].append({"item_id": item_id, "decision_id": decision_id,
                             "task_id": decision["task_id"], "kind": decision["kind"],
                             "first_reviewer_label": decision["status"],
                             "source_files": original,
                             "packet_sha256": sha(item_path.read_bytes())})
        label_rows.append({"item_id": item_id, "label": "", "reason": "", "recognized_source": ""})
    (BASE / "PACKET.md").write_text("\n".join(index) + "\n")
    key["packet_sha256"] = sha((BASE / "PACKET.md").read_bytes())
    (ROOT / "analysis/blind_rq1_key.json").write_text(json.dumps(key, indent=2) + "\n")
    with (BASE / "labels.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["item_id", "label", "reason", "recognized_source"])
        writer.writeheader()
        writer.writerows(label_rows)
    print(f"Created {len(order)} blinded items; packet sha256={sha((BASE / 'PACKET.md').read_bytes())}")


if __name__ == "__main__":
    main()
