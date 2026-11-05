#!/usr/bin/env python3
"""Reconcile two offline audits and retain source-linked timing observations."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "combined_report_v1"
ORIGINAL = ROOT / "notes/fixed_repeatability_2026-11-04_v1"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
rows = list(csv.DictReader((OUT / "per_run.csv").open()))
assert len(rows) == 180 and len({r["index"] for r in rows}) == 180
plan = read(ORIGINAL / "packet/plan.json")
assert sha(ORIGINAL / "packet/plan.json") == "9c19539dcdf8df60b945debfa2fc69e721021bf80b87e157a1a80dacaa93a613"
assert sha(ORIGINAL / "PROTOCOL.md") == plan["protocol_sha256"]
inputs = read(ORIGINAL / "input_verification.json")
all_cases, sources, comparisons = [], {}, []
timeline = ["# Verified fixed-setting timelines", "",
            "The measurements below come from unchanged full-application ELFs in fresh processes. "
            "Kernel-reported case duration and sampled Renode UART exposure are distinct. "
            "Neither directly timestamps an alarm event, callback entry, or subsecond phase.", ""]
for unit, job, report, filename, line_no in [
    ("f4-rtc", "3552869", "rtc_report_v1", "rtc/rtc_api/src/test_alarm_callback.c", 114),
    ("f4-counter", "3552870", "counter_report_v1", "counter/counter_basic_api/src/test_counter.c", 658),
]:
    verified = HERE / f"verified-{job}-v1"
    extra = list(csv.DictReader((HERE / report / "per_run.csv").open()))
    by_index = {r["index"]: r for r in extra}
    assert len(by_index) == 90
    for r in rows:
        if r["index"] in by_index:
            other = by_index[r["index"]]
            for key in ("cell_id", "case", "frequency_hz", "repeat_index", "selected_outcome",
                        "primary_record_sha256", "trace_sha256", "uart_sha256"):
                assert r[key] == other[key], (r["index"], key)
    summary = read(HERE / report / "summary.json")
    assert summary["primary_records"] == summary["evaluable"] == 90
    assert summary["fixed_settings_verified"] and summary["counter_inputs_unchanged"]
    assert summary["protected_files_unchanged"] == 30067
    for r in csv.DictReader((HERE / report / "all_case_verdicts.csv").open()):
        all_cases.append(dict(unit=unit, **r))
    source = ROOT / "subjects/upstream/zephyr/tests/drivers" / filename
    sources[str(source.relative_to(ROOT))] = sha(source)
    timeline += [f"## {summary['cells'][0]['case']}", "",
                 f"Source: [{source.name}]({source}:{line_no}), SHA256 `{sha(source)}`.", ""]
    if unit == "f4-rtc":
        timeline += ["**Source-based sequence:** lines 114–141 clear callback status, sleep 3 seconds, "
                     "assert no premature callback, sleep another 10 seconds, and require callback status. "
                     "The constants are at lines 13–14. Lines 144–146 reset the RTC calendar, and the loop "
                     "repeats twice. The unchanged ELF therefore retains the fixed 13-second window. "
                     "Calendar reset does not itself measure the retained subsecond phase. "
                     "The phase explanation is supported by source and cross-frequency behavior; "
                     "phase and callback delivery are not directly measured.", ""]
    else:
        driver = ROOT / "subjects/upstream/zephyr/drivers/counter/counter_ll_stm32_rtc.c"
        sources[str(driver.relative_to(ROOT))] = sha(driver)
        timeline += ["**Source-based sequence:** lines 669–675 compute and request a two-tick relative "
                     "alarm for this pinned RTC-only configuration; line 692 busy-waits "
                     "`1.5*counter_ticks_to_us(dev, ticks)` (3 seconds). Lines 693–696 check the callback "
                     "count. Cleanup at lines 698–707 follows the assertion, so assertion failure bypasses it.", "",
                     f"The [counter driver]({driver}:531) explains its compensating tick at lines 531–536. "
                     "The resulting source-based two-to-three-tick interval has a 21.333–32 kHz phase "
                     "envelope against a fixed 3-second wait. This is an inference from the pinned source, "
                     "not a directly measured phase or universal boundary.", ""]
    timeline += ["**Measured in the repeats:** the two time values below were identical across all "
                 "30 processes per cell. UART is sampled every 0.5 Renode virtual seconds. "
                 "Buffered-output exposure can occur long after the selected case; it must not be "
                 "read as the callback's arrival time.", "",
                 "|Clock, kHz|Pass / fail / skip / missing|Kernel-reported case seconds|First sampled verdict exposure, virtual seconds|Representative evidence|",
                 "|---:|---|---:|---:|---|"]
    for c in summary["cells"]:
        rr = [r for r in extra if r["cell_id"] == c["cell_id"]]
        assert len(rr) == 30
        representative = rr[0]
        rid = f"{unit}-repeatability-{int(representative['index']):03d}"
        links = ", ".join(f"[{kind}]({verified / 'output' / kind / (rid + suffix)})"
                          for kind, suffix in [("records", ".json"), ("uart", ".log"), ("traces", ".json")])
        counts = " / ".join(str(c[k + "_count"]) for k in ["pass", "fail", "skip", "missing"])
        timeline.append(f"|{c['frequency_hz']/1000:g}|{counts}|{c['kernel_reported_case_seconds_span']}|"
                        f"{c['sampled_uart_verdict_observation_virtual_seconds_span']}|{links}|")
        baseline = next(b for b in inputs["cells"] if b["cell_id"] == c["cell_id"])
        old_vectors = [read(ROOT / b["path"])["cases"] for b in baseline["baseline_records"]]
        for r in rr:
            rp = verified / "output/records" / f"{unit}-repeatability-{int(r['index']):03d}.json"
            record = read(rp)
            comparisons.append(dict(index=r["index"], cell_id=r["cell_id"],
                                    matches_archived_full_case_vector=record["cases"] in old_vectors))
    timeline += [""]
timeline += ["At 29.143 kHz the unchanged counter application also retains its downstream "
             "single-shot failure; the per-case vectors retain this observation. This repeatability "
             "study does not test a repair or prove that a repair removes the cascade.", "",
             "All 30 selected verdicts agree within every cell: no observed same-setting flakiness "
             "in these cells under this model. Rare flakiness is not ruled out. Between-frequency "
             "differences remain timing sensitivity. No device-frequency population distribution was measured.", ""]
assert all(r["matches_archived_full_case_vector"] for r in comparisons)
with (OUT / "all_case_verdicts.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_cases[0]))
    writer.writeheader()
    writer.writerows(all_cases)
with (OUT / "baseline_vector_comparison.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(comparisons[0]))
    writer.writeheader()
    writer.writerows(comparisons)
case_counts = []
for cell, case in sorted({(r["cell_id"], r["case"]) for r in all_cases}):
    counts = Counter(r["status"] for r in all_cases if r["cell_id"] == cell and r["case"] == case)
    assert sum(counts.values()) == 30
    case_counts.append(dict(cell_id=cell, case=case, **{k: counts[k] for k in ["pass", "fail", "skip"]}, missing=0))
with (OUT / "all_case_counts.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(case_counts[0]))
    writer.writeheader()
    writer.writerows(case_counts)
(OUT / "TIMELINES.md").write_text("\n".join(timeline))
proof = dict(analysis_agreement="180/180", archived_full_case_vector_matches="180/180",
             selected_verdicts=dict(Counter(r["selected_outcome"] for r in rows)),
             source_hashes=sources, old_preflight_attempts_launched=0,
             old_preflight_attempts_are_scientific_results=False, original_records_replaced=False)
(OUT / "claim_audit.json").write_text(json.dumps(proof, indent=2) + "\n")
report = OUT / "REPORT.md"
text = report.read_text().replace("All30 fresh-process", "All 30 fresh-process")
text += "\nBoth independent audit paths agree on all 180 selected verdicts. Every full-application "
text += "case vector matches an archived vector at the same frequency. All capability skips and "
text += "other case outcomes are retained in `all_case_verdicts.csv` and `all_case_counts.csv`. "
text += "The two earlier preflight attempts launched zero processes and are separate from these 180 outcomes.\n"
report.write_text(text)
print(json.dumps(proof, indent=2))
