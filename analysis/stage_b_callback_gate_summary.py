#!/usr/bin/env python3
"""Freeze Stage B all-attempt gates before legal-clock or fault challenges."""

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "generated/stage_b_callback_v1"
OUT = ROOT / "results/stage_b_callback_v1"
REVIEW = ROOT / "analysis/stage_b_callback_source_review.json"
TARGET = OUT / "gate_summary.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def build_record(rid):
    paths = [OUT / "build_retry_records" / f"{rid}.retry03.json",
             OUT / "build_retry_records" / f"{rid}.json",
             OUT / "build_records" / f"{rid}.json"]
    return next((read(path) for path in paths if path.exists()), None)


def nominal(rid):
    originals = [OUT / "nominal_records" / f"{rid}-nominal-{i:03d}.json" for i in range(5)]
    if not all(p.exists() for p in originals):
        return {"status": "incomplete", "original": [read(p)["outcome"] if p.exists() else "missing" for p in originals]}
    o = [read(p) for p in originals]
    if all(r["outcome"] == "pass" for r in o):
        return {"status": "pass", "original": ["pass"] * 5, "qualification": "original"}
    access_error = all(
        r["outcome"] == "harness_error" and r["virtual_ns"] == 0 and
        "history' is denied" in (ROOT / r["monitor_path"]).read_text(errors="replace")
        for r in o
    )
    if access_error:
        retry_paths = [OUT / "nominal_access_retry_records" / f"{rid}-access-retry-{i:03d}.json" for i in range(5)]
        retry = [read(p)["outcome"] if p.exists() else "missing" for p in retry_paths]
        return {"status": "pass" if retry == ["pass"] * 5 else "failed",
                "original": [r["outcome"] for r in o], "access_retry": retry,
                "qualification": "separate_access_retry" if retry == ["pass"] * 5 else None}
    return {"status": "failed", "original": [r["outcome"] for r in o]}


def main():
    if TARGET.exists():
        saved = read(TARGET)
        if saved["call_order_sha256"] != sha(BASE / "call_order.json") or saved["source_review_sha256"] != sha(REVIEW):
            raise RuntimeError("Frozen gate input changed")
        print(saved["counts"])
        return
    order = read(BASE / "call_order.json")["calls"]
    if len(order) != 60:
        raise RuntimeError("Expected 60 intended calls")
    review = read(REVIEW)["decisions"]
    rows = []
    for call in order:
        model = call["model"].removeprefix("gpt-6-")
        rid = f"{model}-{call['condition']}-rtc_alarm_callback-r{call['sample_index']:02d}"
        directory = BASE / "suites" / model / call["condition"] / f"r{call['sample_index']:02d}"
        meta = directory / "metadata.json"
        if not meta.exists():
            raise RuntimeError(f"Generation not finalized: {rid}")
        gen = read(meta)
        row = {"run_id": rid, "call_index": call["call_index"], "model": model,
               "condition": call["condition"], "generation_status": gen["status"],
               "attempts": gen["attempts"], "prompt_sha256": gen["prompt_sha256"],
               "source_sha256": gen["source_sha256"]}
        if gen["status"] != "generated":
            row.update(build_status="not_attempted", functional="not_evaluable",
                       timing_bound="not_evaluable", nominal={"status": "not_attempted"}, eligible=False)
        else:
            b = build_record(rid)
            if b is None:
                raise RuntimeError(f"Build not recorded: {rid}")
            row["build_status"] = b["status"]
            row["build_record_sha256"] = sha(next(p for p in
                [OUT / "build_retry_records" / f"{rid}.retry03.json", OUT / "build_retry_records" / f"{rid}.json", OUT / "build_records" / f"{rid}.json"] if p.exists()))
            if b["status"] != "pass":
                row.update(functional="not_evaluable", timing_bound="not_evaluable",
                           nominal={"status": "not_attempted"}, eligible=False)
            else:
                rev = review.get(rid)
                if rev is None or rev["source_sha256"] != b["source_sha256"] or rev["functional"] == "pending":
                    raise RuntimeError(f"Source review unfinished or mismatched: {rid}")
                row.update(functional=rev["functional"], timing_bound=rev["timing_bound"],
                           exact_calendar_oracle=rev["exact_calendar_oracle"],
                           alarm_readback=rev["alarm_readback"])
                if rev["functional"] == "met":
                    nom = nominal(rid)
                    if nom["status"] == "incomplete":
                        raise RuntimeError(f"Nominal screen incomplete: {rid}")
                    row["nominal"] = nom
                    row["eligible"] = nom["status"] == "pass"
                else:
                    row.update(nominal={"status": "not_attempted"}, eligible=False)
                if row["eligible"]:
                    row.update(source_path=b["source_path"], elf_path=b["elf_path"],
                               elf_sha256=b["elf_sha256"])
        rows.append(row)
    summary = {"schema_version": 1, "registered_utc": datetime.now(timezone.utc).isoformat(),
               "status": "frozen_before_variation", "call_order_sha256": sha(BASE / "call_order.json"),
               "source_review_sha256": sha(REVIEW), "rows": rows,
               "counts": dict(Counter("eligible" if r["eligible"] else r["build_status"] if r["build_status"] != "pass" else r["functional"] if r["functional"] != "met" else "nominal_failed" for r in rows))}
    OUT.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if TARGET.exists():
        if TARGET.read_text() != raw:
            raise RuntimeError("Frozen gate summary differs")
    else:
        with TARGET.open("x") as stream:
            stream.write(raw)
    print(summary["counts"])


if __name__ == "__main__":
    main()
