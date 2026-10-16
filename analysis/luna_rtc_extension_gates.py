#!/usr/bin/env python3
"""Audit original and amended Luna RTC-extension gate attrition."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/luna_rtc_extension"
FUNCTIONAL = ROOT / "analysis/luna_rtc_extension_functional_decisions.json"
RQ1 = ROOT / "analysis/rtc_extension_rq1_decisions.json"
VALID_FUNCTIONAL = {"met", "not_met", "unknown", "not_evaluable"}
TIMING_MAP = {"unjustified": "inadequate", "none_found": "no_issue_found",
              "unknown": "unknown"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    summary = json.loads((RESULTS / "summary.json").read_text())
    if summary["cohort"] != "luna_rtc_extension" or summary["planned_runs"] != 10:
        raise ValueError("Unexpected generated cohort or task count")
    functional_ledger = json.loads(FUNCTIONAL.read_text())
    if functional_ledger["split_protocol_sha256"] != sha(ROOT / "analysis/PHASE2_SPLIT_GATE_PROTOCOL.md"):
        raise ValueError("Split-gate protocol changed")
    timing_ledger = json.loads(RQ1.read_text())["decisions"]
    oracle = json.loads((ROOT / "analysis/phase2_oracle_decisions_luna_rtc_extension.json").read_text())["decisions"]
    rows = []
    for task in summary["rows"]:
        for run in task["runs"]:
            run_id = run["run_id"]
            f = functional_ledger["decisions"][run_id]
            t = timing_ledger[run_id]
            o = oracle[run_id]
            if f["functional"] not in VALID_FUNCTIONAL or t["status"] not in TIMING_MAP:
                raise ValueError(f"Invalid source judgment: {run_id}")
            if (f["source_sha256"] != o["source_sha256"] or
                    t["source_files_sha256"].get(f["source_path"]) != f["source_sha256"] or
                    sha(ROOT / f["source_path"]) != f["source_sha256"]):
                raise ValueError(f"Frozen source mismatch: {run_id}")
            rows.append({**run, "task_id": task["task_id"],
                         "functional": f["functional"],
                         "functional_evidence": f["evidence"],
                         "timing_bound": TIMING_MAP[t["status"]],
                         "timing_evidence": t["evidence"],
                         "original_strict_eligible": (run["build"] == "pass" and
                                                      run["nominal"] == "pass" and
                                                      run["oracle"] == "adequate"),
                         "amended_functional_eligible": (run["build"] == "pass" and
                                                         run["nominal"] == "pass" and
                                                         f["functional"] == "met")})
    if len(rows) != 10:
        raise ValueError("Missing source rows")
    output = {
        "source_summary_sha256": sha(RESULTS / "summary.json"),
        "original_review_sha256": sha(ROOT / "analysis/phase2_oracle_decisions_luna_rtc_extension.json"),
        "functional_ledger_sha256": sha(FUNCTIONAL),
        "rq1_source_review_sha256": sha(RQ1),
        "planned": 10,
        "generation": dict(Counter(x["generation"] for x in rows)),
        "build": dict(Counter(x["build"] for x in rows)),
        "nominal": dict(Counter(x["nominal"] for x in rows)),
        "original_oracle": dict(Counter(x["oracle"] for x in rows)),
        "functional": dict(Counter(x["functional"] for x in rows)),
        "timing_bound": dict(Counter(x["timing_bound"] for x in rows)),
        "original_strict_eligible": sum(x["original_strict_eligible"] for x in rows),
        "amended_functional_eligible": sum(x["amended_functional_eligible"] for x in rows),
        "rows": rows,
    }
    (RESULTS / "gate_summary.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
    print(f"RTC extension gates: old={output['original_strict_eligible']}/10, "
          f"amended={output['amended_functional_eligible']}/10, "
          f"nominal={output['nominal']}")


if __name__ == "__main__":
    main()
