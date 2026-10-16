#!/usr/bin/env python3
"""Build frozen RTC tests with an isolated, hash-recorded STM32 RTC driver fault.

The original test C files are compiled by absolute path; the original Zephyr
driver C file is removed from its CMake target and replaced with our copy.
"""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "harness/rtc_driver_variants/rtc_ll_stm32_quality.c"
OVERLAYS = [ROOT / "subjects/phase1_zephyr/config/stm32f4_hsi.overlay",
            ROOT / "subjects/phase1_lsi_rtc/rtc_alias.overlay"]
UPSTREAM = ROOT / "subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src"
HUMAN_APPS = {
    "rtc_alarm_callback": ROOT / "subjects/phase1_lsi_rtc/selected_alarm_callback",
    "rtc_alarm_pending": ROOT / "subjects/rtc_alarm_pending/selected_case",
    "rtc_time_counting": ROOT / "subjects/rtc_counting/selected_case",
}
REFERENCE_APPS = {
    "rtc_alarm_callback": ROOT / "subjects/reference_rtc/callback",
    "rtc_alarm_pending": ROOT / "subjects/reference_rtc/pending",
    "rtc_time_counting": ROOT / "subjects/reference_rtc/counting",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def source_spec(suite_id, versions):
    if suite_id.startswith("reference-"):
        family = suite_id.removeprefix("reference-")
        app = REFERENCE_APPS[family]
        return family, "reference", [app / "test.c"], app / "prj.conf", None
    version = versions[suite_id]
    family, kind = version["family"], version["kind"]
    if kind == "ai":
        source = ROOT / version["source_path"]
        return family, kind, [source], source.parent / "prj.conf", None
    app = HUMAN_APPS[family]
    test = {"rtc_alarm_callback": "test_alarm_callback.c",
            "rtc_alarm_pending": "test_alarm.c",
            "rtc_time_counting": "test_time_incrementing.c"}[family]
    define = "CONFIG_TEST_RTC_ALARM_TIME_MASK=7" if family != "rtc_time_counting" else None
    return family, kind, [UPSTREAM / "main.c", UPSTREAM / test], app / "prj.conf", define


def create_app(out, suite_id, versions, operator, delay_us):
    family, kind, sources, conf, define = source_spec(suite_id, versions)
    if operator not in ("latency", "nonarrival"):
        raise ValueError(operator)
    alarm = family != "rtc_time_counting"
    macros = (["QUALITY_LATENCY_ALARM=1" if alarm else "QUALITY_LATENCY_COUNTING=1",
               f"QUALITY_DELAY_US={delay_us}"] if operator == "latency" else
              ["QUALITY_NONARRIVAL_ALARM=1" if alarm else "QUALITY_NONARRIVAL_COUNTING=1"])
    app = out / "app"
    app.mkdir(parents=True, exist_ok=True)
    cmake = """cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{{ZEPHYR_BASE}})
project(rtc_quality_challenge)
target_sources(app PRIVATE {sources})
{app_define}
get_target_property(rtc_sources drivers__rtc SOURCES)
list(FILTER rtc_sources EXCLUDE REGEX "rtc_ll_stm32\\.c$")
set_property(TARGET drivers__rtc PROPERTY SOURCES "${{rtc_sources}}")
target_sources(drivers__rtc PRIVATE {driver})
target_include_directories(drivers__rtc PRIVATE {driver_include})
target_compile_definitions(drivers__rtc PRIVATE {macros})
""".format(sources=" ".join(str(s) for s in sources),
           app_define=f"target_compile_definitions(app PRIVATE {define})" if define else "",
           driver=DRIVER,
           driver_include=ROOT / "subjects/upstream/zephyr/drivers/rtc",
           macros=" ".join(macros))
    cmake_path, conf_path = app / "CMakeLists.txt", app / "prj.conf"
    if cmake_path.exists():
        if cmake_path.read_text() != cmake or conf_path.read_bytes() != conf.read_bytes():
            raise RuntimeError("Existing quality app changed")
    else:
        cmake_path.write_text(cmake)
        conf_path.write_bytes(conf.read_bytes())
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in
              [*sources, conf, DRIVER, *OVERLAYS, cmake_path, conf_path]}
    return {"suite_id": suite_id, "family": family, "kind": kind,
            "operator": operator, "delay_us": delay_us,
            "app_path": str(app.relative_to(ROOT)), "inputs": inputs,
            "source_paths": [str(s.relative_to(ROOT)) for s in sources]}


def build(out, spec):
    for rel, digest in spec["inputs"].items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Build input changed: {rel}")
    app = ROOT / spec["app_path"]
    build_dir, record = out / "build", out / "build_record.json"
    elf = build_dir / "zephyr/zephyr.elf"
    if record.exists():
        saved = json.loads(record.read_text())
        if saved["status"] != "pass" or sha(elf) != saved["elf_sha256"]:
            raise RuntimeError("Existing build is not valid")
        return saved
    log = out / "build.log"
    if log.exists():
        raise RuntimeError("Unrecorded prior build log exists")
    env = dict(os.environ)
    env["ZEPHYR_BASE"] = str(ROOT / "subjects/upstream/zephyr")
    env["ZEPHYR_SDK_INSTALL_DIR"] = "/private/tmp/zephyr-sdk-0.17.4"
    env["PATH"] = str(ROOT / ".venv/bin") + os.pathsep + env.get("PATH", "")
    command = [str(ROOT / ".venv/bin/west"), "build", "-p", "always", "-b", "stm32f4_disco",
               str(app), "-d", str(build_dir), "--",
               "-DDTC_OVERLAY_FILE=" + ";".join(str(o) for o in OVERLAYS)]
    with log.open("x") as stream:
        result = subprocess.run(command, cwd=ROOT / "subjects/upstream/zephyr",
                                env=env, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=600, check=False)
    saved = {"suite_id": spec["suite_id"], "operator": spec["operator"],
             "delay_us": spec["delay_us"], "timestamp_utc": datetime.now(timezone.utc).isoformat(),
             "command": command, "status": "pass" if result.returncode == 0 and elf.exists() else "build_fail",
             "returncode": result.returncode, "inputs": spec["inputs"],
             "log_path": str(log.relative_to(ROOT)), "log_sha256": sha(log),
             "elf_path": str(elf.relative_to(ROOT)) if elf.exists() else None,
             "elf_sha256": sha(elf) if elf.exists() else None}
    write_new(record, saved)
    print(f"{spec['suite_id']} {spec['operator']} {spec['delay_us']}: {saved['status']}", flush=True)
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("suite_id")
    parser.add_argument("operator", choices=("latency", "nonarrival"))
    parser.add_argument("delay_us", type=int)
    parser.add_argument("out")
    args = parser.parse_args()
    versions = json.loads((ROOT / "results/rtc_factorial_v2/manifest.json").read_text())["versions"]
    out = Path(args.out).resolve()
    spec = create_app(out, args.suite_id, versions, args.operator, args.delay_us)
    build(out, spec)
