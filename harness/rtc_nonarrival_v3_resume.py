#!/usr/bin/env python3
"""Append-only recovery for interrupted RTC nonarrival v3 suite challenges.

The original namespace, including three interrupted monitor/UART traces, is
preserved. This registration captures only suite IDs without an original
verdict and runs them under the same compiled mutant in a separate namespace.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from rtc_nonarrival_driver_v3 import MANIFEST as ORIGINAL, OUT as ORIGINAL_OUT, validate
from rtc_quality_build import ROOT, build, create_app, sha, write_new
from rtc_quality_run import PLATFORM, simulate

OUT = ROOT / "results/rtc_nonarrival_driver_v3_resume"
MANIFEST = OUT / "manifest.json"
BUILDER = ROOT / "harness/rtc_quality_build.py"
RUNNER = ROOT / "harness/rtc_quality_run.py"


def read(path):
    return json.loads(path.read_text())


def register():
    original = validate()
    missing = sorted(rid for rid, v in original["suites"].items()
                     if v["kind"] != "reference" and
                     not (ORIGINAL_OUT / "records" / f"{rid}.json").exists())
    workers = {str(i): missing[i::3] for i in range(3)}
    interrupted = {}
    for rid in missing:
        paths = {kind: ORIGINAL_OUT / folder / f"{rid}.{ext}"
                 for kind, folder, ext in (("monitor", "monitor", "log"),
                                           ("uart", "uart", "log"),
                                           ("trace", "traces", "json"))}
        present = {str(path.relative_to(ROOT)): sha(path)
                   for path in paths.values() if path.exists()}
        if present:
            interrupted[rid] = present
    suites = {rid: original["suites"][rid] for rid in missing}
    manifest = {"registered_utc": datetime.now(timezone.utc).isoformat(),
                "schema_version": 1,
                "purpose": "append-only recovery of interrupted v3 nonarrival suite challenges",
                "original_manifest_sha256": sha(ORIGINAL),
                "original_runner_sha256": sha(ROOT / "harness/rtc_nonarrival_driver_v3.py"),
                "builder_sha256": sha(BUILDER), "run_tool_sha256": sha(RUNNER),
                "resume_runner_sha256": sha(Path(__file__)),
                "platform_sha256": sha(PLATFORM),
                "renode_version": original["renode_version"],
                "max_virtual_sec": original["max_virtual_sec"],
                "nominal_rtc_hz": original["nominal_rtc_hz"],
                "cpu_performance_mips": original["cpu_performance_mips"],
                "suites": suites, "workers": workers,
                "interrupted_original_artifacts": interrupted}
    write_new(MANIFEST, manifest)
    print(f"Registered {len(missing)} missing v3 suites, "
          f"{len(interrupted)} interrupted originals: {sha(MANIFEST)}", flush=True)


def verify():
    original = validate()
    m = read(MANIFEST)
    for key, path in (("original_manifest_sha256", ORIGINAL),
                      ("original_runner_sha256", ROOT / "harness/rtc_nonarrival_driver_v3.py"),
                      ("builder_sha256", BUILDER), ("run_tool_sha256", RUNNER),
                      ("resume_runner_sha256", Path(__file__)),
                      ("platform_sha256", PLATFORM)):
        if sha(path) != m[key]:
            raise RuntimeError(f"Registered input changed: {path}")
    for rid, v in m["suites"].items():
        if original["suites"][rid] != v or sha(ROOT / v["source_path"]) != v["source_sha256"]:
            raise RuntimeError(f"Frozen suite changed: {rid}")
    for paths in m["interrupted_original_artifacts"].values():
        for rel, digest in paths.items():
            if sha(ROOT / rel) != digest:
                raise RuntimeError(f"Interrupted original artifact changed: {rel}")
    if read(ORIGINAL_OUT / "activation_audit.json")["status"] != "validated":
        raise RuntimeError("Original nonarrival reference activation invalid")
    return m


def worker(index):
    m = verify()
    for rid in m["workers"][str(index)]:
        v = m["suites"][rid]
        # Reuse the original registered app and ELF; build() verifies its hash.
        build_out = ORIGINAL_OUT / "builds" / rid
        spec = create_app(build_out, rid, read(ORIGINAL)["suites"], "nonarrival", 0)
        built = build(build_out, spec)
        if built["status"] != "pass":
            continue
        simulate(OUT, rid, rid, v["family"], v["kind"], v.get("selected_case"),
                 v["source_sha256"], ROOT / built["elf_path"], MANIFEST,
                 max_virtual_sec=m["max_virtual_sec"])
    print(f"v3 nonarrival resume worker {index}: complete", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--worker", type=int, choices=range(3))
    args = parser.parse_args()
    if args.register:
        register()
    elif args.worker is not None:
        worker(args.worker)
    else:
        parser.error("Choose registration or worker")


if __name__ == "__main__":
    main()
