#!/usr/bin/env python3
"""Isolated builds for the preregistered RTC-calendar alarm-offset quality arm."""

from pathlib import Path

from rtc_quality_build import ROOT, OVERLAYS, build, sha, source_spec as base_source_spec

DRIVER = ROOT / "harness/rtc_driver_variants/rtc_ll_stm32_alarm_offset.c"
REFERENCE = ROOT / "subjects/reference_rtc_alarm_offset"


def source_spec(suite_id, versions):
    if suite_id.startswith("reference-"):
        family = suite_id.removeprefix("reference-")
        leaf = {"rtc_alarm_callback": "callback", "rtc_alarm_pending": "pending",
                "rtc_time_counting": "counting"}[family]
        app = REFERENCE / leaf
        return family, "reference", [app / "test.c"], app / "prj.conf", None
    return base_source_spec(suite_id, versions)


def create_app(out: Path, suite_id: str, versions: dict, sign: int):
    if sign not in (-1, 0, 1):
        raise ValueError(sign)
    family, kind, sources, conf, define = source_spec(suite_id, versions)
    app = out / "app"
    app.mkdir(parents=True, exist_ok=True)
    cmake = """cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{{ZEPHYR_BASE}})
project(rtc_alarm_offset_challenge)
target_sources(app PRIVATE {sources})
{app_define}
get_target_property(rtc_sources drivers__rtc SOURCES)
list(FILTER rtc_sources EXCLUDE REGEX "rtc_ll_stm32\\.c$")
set_property(TARGET drivers__rtc PROPERTY SOURCES "${{rtc_sources}}")
target_sources(drivers__rtc PRIVATE {driver})
target_include_directories(drivers__rtc PRIVATE {driver_include})
target_compile_definitions(drivers__rtc PRIVATE QUALITY_ALARM_OFFSET_SIGN={sign})
""".format(sources=" ".join(str(s) for s in sources),
           app_define=f"target_compile_definitions(app PRIVATE {define})" if define else "",
           driver=DRIVER,
           driver_include=ROOT / "subjects/upstream/zephyr/drivers/rtc", sign=sign)
    cmake_path, conf_path = app / "CMakeLists.txt", app / "prj.conf"
    if cmake_path.exists():
        if cmake_path.read_text() != cmake or conf_path.read_bytes() != conf.read_bytes():
            raise RuntimeError("Existing alarm-offset app changed")
    else:
        cmake_path.write_text(cmake)
        conf_path.write_bytes(conf.read_bytes())
    files = [*sources, conf, DRIVER, *OVERLAYS, cmake_path, conf_path]
    if kind == "reference":
        files.append(REFERENCE / "reference_common.h")
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in files}
    return {"suite_id": suite_id, "family": family, "kind": kind,
            "operator": f"alarm_offset_{sign:+d}", "delay_us": 0,
            "app_path": str(app.relative_to(ROOT)), "inputs": inputs,
            "source_paths": [str(s.relative_to(ROOT)) for s in sources]}
