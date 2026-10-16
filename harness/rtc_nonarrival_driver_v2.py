#!/usr/bin/env python3
"""Registered driver-path nonarrival mutant, isolated from the legal clock arm."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from rtc_quality_build import DRIVER, ROOT, build, create_app, sha, write_new
from rtc_quality_run import PLATFORM, simulate

OUT = ROOT / "results/rtc_nonarrival_driver_v2"
MANIFEST = OUT / "manifest.json"
V2 = ROOT / "results/rtc_factorial_v2/manifest.json"
BUILD_TOOL = ROOT / "harness/rtc_quality_build.py"
RUN_TOOL = ROOT / "harness/rtc_quality_run.py"
EXPECTED = {
    "rtc_alarm_callback": "callbacks absent past legal-clock ceiling plus service margin",
    "rtc_alarm_pending": "pending absent past legal-clock ceiling plus service margin",
    "rtc_time_counting": "calendar did not reach target by ceiling",
}


def read(path):
    return json.loads(path.read_text())


def register():
    v2 = read(V2)
    versions = v2["versions"]
    if len(versions) != 53:
        raise RuntimeError("Measured v2 suite roster changed")
    gate = read(ROOT / "results/spec_context_factorial_v1/gate_summary.json")
    ai = {row["run_id"] for row in gate["rows"]
          if row["amended_functional_eligible"] and row["task_id"].startswith("rtc_")}
    if len(ai) != 66:
        raise RuntimeError("Eligible RTC AI roster changed")
    all_versions = {k: v for k, v in versions.items() if v["kind"] == "human"}
    for rid in sorted(ai):
        if rid in versions:
            all_versions[rid] = versions[rid]
        else:
            # The unmeasured, functionally eligible suites also enter mutation scores.
            model, condition, family, repeat = rid.split("-", 3)
            source = ROOT / "generated/spec_context_factorial_v1/suites" / model / condition / family / repeat / "test.c"
            all_versions[rid] = {"family": family, "kind": "ai", "model": model,
                                 "prompt_condition": condition,
                                 "source_path": str(source.relative_to(ROOT)),
                                 "source_sha256": sha(source)}
    if len(all_versions) != 69:
        raise RuntimeError("Expected 66 AI and three human suites")
    suites = {f"reference-{family}": {"family": family, "kind": "reference"}
              for family in EXPECTED}
    suites.update(all_versions)
    workers = {str(i): [] for i in range(3)}
    for i, rid in enumerate(sorted(all_versions)):
        workers[str(i % 3)].append(rid)
    for rid, v in suites.items():
        source_path = (ROOT / v["source_path"] if "source_path" in v else
                       ROOT / "subjects/reference_rtc" /
                       {"rtc_alarm_callback": "callback", "rtc_alarm_pending": "pending",
                        "rtc_time_counting": "counting"}[v["family"]] / "test.c")
        if "source_sha256" in v and sha(source_path) != v["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {rid}")
        v["source_path"] = str(source_path.relative_to(ROOT))
        v["source_sha256"] = sha(source_path)
    save = {"registered_utc": datetime.now(timezone.utc).isoformat(),
            "schema_version": 1, "operator": "driver-path nonarrival at nominal 32 kHz RTC",
            "operator_by_family": {
                "rtc_alarm_callback": "clear alarm interrupt but suppress callback and pending flag",
                "rtc_alarm_pending": "clear alarm interrupt but suppress pending flag and callback",
                "rtc_time_counting": "freeze get_time observation at the value set by set_time"},
            "purpose": "third quality mutant after invalid 1 Hz clock mutant; outside RQ2 legal schedules",
            "activation_rule": "all three task-specific references fail the named nonarrival ceiling assertion",
            "expected_reference_assertion": EXPECTED,
            "nominal_rtc_hz": 32000, "cpu_performance_mips": 16,
            "max_virtual_sec": 70, "v2_manifest_sha256": sha(V2),
            "driver_sha256": sha(DRIVER), "builder_sha256": sha(BUILD_TOOL),
            "run_tool_sha256": sha(RUN_TOOL), "runner_sha256": sha(Path(__file__)),
            "platform_sha256": sha(PLATFORM),
            "renode_version": v2["renode_version"],
            "suites": suites, "workers": workers}
    write_new(MANIFEST, save)
    print(f"Registered 3 reference activations, then 69 suite scores: {sha(MANIFEST)}")


def validate():
    m = read(MANIFEST)
    for key, path in (("v2_manifest_sha256", V2), ("driver_sha256", DRIVER),
                      ("builder_sha256", BUILD_TOOL), ("run_tool_sha256", RUN_TOOL),
                      ("runner_sha256", Path(__file__)), ("platform_sha256", PLATFORM)):
        if sha(path) != m[key]:
            raise RuntimeError(f"Registered input changed: {path}")
    for v in m["suites"].values():
        if sha(ROOT / v["source_path"]) != v["source_sha256"]:
            raise RuntimeError(f"Frozen source changed: {v['source_path']}")
    return m


def run_suite(suite_id):
    m = validate()
    v = m["suites"][suite_id]
    out = OUT / "builds" / suite_id
    spec = create_app(out, suite_id, m["suites"], "nonarrival", 0)
    built = build(out, spec)
    if built["status"] != "pass":
        return
    selected = v.get("selected_case")
    simulate(OUT, suite_id, suite_id, v["family"], v["kind"], selected,
             v["source_sha256"], ROOT / built["elf_path"], MANIFEST,
             max_virtual_sec=m["max_virtual_sec"])


def audit_activation():
    m = validate()
    rows = []
    for family, assertion in EXPECTED.items():
        rid = f"reference-{family}"
        path = OUT / "records" / f"{rid}.json"
        if not path.exists():
            raise RuntimeError(f"Reference activation missing: {rid}")
        record = read(path)
        uart = (ROOT / record["uart_path"]).read_text(errors="replace")
        activated = record["outcome"] == "fail" and assertion in uart
        rows.append({"family": family, "run_id": rid, "outcome": record["outcome"],
                     "expected_assertion": assertion, "activated": activated,
                     "record_sha256": sha(path)})
    status = "validated" if all(row["activated"] for row in rows) else "invalid"
    write_new(OUT / "activation_audit.json",
              {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "manifest_sha256": sha(MANIFEST), "status": status, "rows": rows})
    print(f"Nonarrival reference activation: {status}")


def worker(index):
    m = validate()
    audit_path = OUT / "activation_audit.json"
    if not audit_path.exists() or read(audit_path)["status"] != "validated":
        raise RuntimeError("Nonarrival operator not activated on references")
    for rid in m["workers"][str(index)]:
        run_suite(rid)
    print(f"nonarrival worker {index}: complete")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--register", action="store_true")
    p.add_argument("--reference", choices=EXPECTED)
    p.add_argument("--audit-activation", action="store_true")
    p.add_argument("--worker", type=int, choices=range(3))
    a = p.parse_args()
    if a.register:
        register()
    elif a.reference:
        run_suite(f"reference-{a.reference}")
    elif a.audit_activation:
        audit_activation()
    elif a.worker is not None:
        worker(a.worker)
    else:
        p.error("Choose registration, reference, activation audit, or worker")


if __name__ == "__main__":
    main()
