#!/usr/bin/env python3
"""Job A worker; runs inside the pinned container (one process per task).

Stages: build APP | tce CHUNK | run APP {baseline,traced} | timing APP MUTANT.
Writes only new files under /out (job output) and /scratch-builds (build tree).
"""
import gzip
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO, OUT, BUILDS = Path("/repo"), Path("/out"), Path("/scratch-builds")
STUDY = REPO / "notes/mutation_quality_2026-11-21_v1"
COUNTER_BUNDLE = Path("/counter-bundle")
Z = Path("/opt/zephyrproject/zephyr")
SDK = Path("/opt/zephyr-sdk-0.17.4/arm-zephyr-eabi/bin")
MODULES = ["/opt/zephyrproject/modules/hal/" + x for x in ("cmsis", "cmsis_6", "stm32")]
CASE = re.compile(r"-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]")
MARKERS = ("PROJECT EXECUTION SUCCESSFUL", "PROJECT EXECUTION FAILED")
DRIVERS = {"rtc": ("drivers/rtc/rtc_ll_stm32.c", "drivers__rtc"),
           "counter": ("drivers/counter/counter_ll_stm32_rtc.c", "drivers__counter")}
sys.path.insert(0, str(STUDY))
import generate_mutants as gm  # noqa: E402  (pure text application of a mutant)


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x") as f:
        json.dump(d, f, indent=2, sort_keys=True)
        f.write("\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


PLAN = json.loads((STUDY / "joba/plan.json").read_text())
APPS = {a["id"]: a for a in PLAN["apps"]}
PROV = dict(slurm_job_id=os.environ.get("SLURM_JOB_ID"), node=os.environ.get("RTC_NODE_NAME"),
            container_sha256=os.environ.get("RTC_CONTAINER_SHA256"),
            plan_sha256=sha(STUDY / "joba/plan.json"))


def env():
    e = dict(os.environ, ZEPHYR_BASE=str(Z), ZEPHYR_TOOLCHAIN_VARIANT="zephyr",
             ZEPHYR_SDK_INSTALL_DIR="/opt/zephyr-sdk-0.17.4", CCACHE_DISABLE="1", XDG_CACHE_HOME="/var/tmp",
             GIT_CONFIG_COUNT=str(1 + len(MODULES)))
    for i, p in enumerate([str(Z)] + MODULES):
        e[f"GIT_CONFIG_KEY_{i}"] = "safe.directory"
        e[f"GIT_CONFIG_VALUE_{i}"] = p
    return e


def mutants():
    return {m["id"]: m for m in map(json.loads, (REPO / PLAN["mutants"]).read_text().splitlines())}


GEN = json.loads((STUDY / "dryrun_v1/generation_summary.json").read_text())


def original_driver(kind):
    rel = DRIVERS[kind][0]
    if sha(Z / rel) != GEN[Path(rel).name]["source_sha256"]:
        raise RuntimeError("container Zephyr driver differs from the source the mutants were generated from")
    return (Z / rel).read_text()


def resolve(src):
    return Z / src[len("ZEPHYR/"):] if src.startswith("ZEPHYR/") else REPO / src


# ------------------------------------------------------------------ build
def app_dirs(app_id):
    base = BUILDS / app_id
    return base, base / "app", base / "slot", base / "build"


def build(app_id):
    a = APPS[app_id]
    base, app, slot, target = app_dirs(app_id)
    rel, lib = DRIVERS[a["driver"]]
    name = Path(rel).name
    slot.mkdir(parents=True)
    (slot / name).write_text(original_driver(a["driver"]))
    sub = (f'get_target_property(mq_sources {lib} SOURCES)\n'
           f'list(FILTER mq_sources EXCLUDE REGEX "{re.escape(name)}$")\n'
           f'set_property(TARGET {lib} PROPERTY SOURCES "${{mq_sources}}")\n'
           f'target_sources({lib} PRIVATE {slot / name})\n'
           f'target_include_directories({lib} PRIVATE {Z / Path(rel).parent})\n')
    if a["driver"] == "rtc":
        app.mkdir()
        srcs = " ".join(str(resolve(s)) for s in a["sources"])
        (app / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.20.0)\nfind_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})\n"
            f"project(rtc_mutation)\ntarget_sources(app PRIVATE {srcs})\n"
            + (f"target_compile_definitions(app PRIVATE {a['define']})\n" if a["define"] else "") + sub)
        shutil.copyfile(REPO / a["prj_conf"], app / "prj.conf")
        extra = ["-DDTC_OVERLAY_FILE=" + ";".join(str(REPO / o) for o in PLAN["overlays"])]
    else:
        shutil.copytree(COUNTER_BUNDLE / a["bundle_app"], app)
        with (app / "CMakeLists.txt").open("a") as f:
            f.write("\n# mutation study: driver slot substitution\n" + sub)
        extra = ["-DDTC_OVERLAY_FILE=" + str(COUNTER_BUNDLE / a["bundle_overlay"]),
                 "-DEXTRA_CONF_FILE=" + str(COUNTER_BUNDLE / a["bundle_config"])]
    cmds = [["cmake", "-S", str(app), "-B", str(target), "-G", "Ninja", "-DBOARD=stm32f4_disco", *extra,
             "-DZEPHYR_MODULES=" + ";".join(MODULES), "-DPython3_EXECUTABLE=/opt/rtc-python/bin/python",
             "-DPYTHON_EXECUTABLE=/opt/rtc-python/bin/python"],
            ["cmake", "--build", str(target), "--parallel", str(PLAN["compiler_parallelism"])]]
    out = OUT / "builds" / app_id
    out.mkdir(parents=True)
    log, start, code = out / "build.log", time.monotonic(), 0
    with log.open("x") as s:
        for c in cmds:
            try:
                code = subprocess.run(c, env=env(), stdout=s, stderr=subprocess.STDOUT,
                                      timeout=PLAN["build_timeout_seconds"]).returncode
            except subprocess.TimeoutExpired:
                code = 124
            if code:
                break
    elf = target / "zephyr/zephyr.elf"
    rec = dict(app_id=app_id, status="built" if code == 0 and elf.exists() else "build_failure", exit_code=code,
               wall_seconds=round(time.monotonic() - start, 3), commands=cmds, log_sha256=sha(log),
               slot_driver=str(slot / name), timestamp_utc=utc(), **PROV)
    if elf.exists():
        shutil.copyfile(elf, out / "zephyr.elf")
        rec["elf_sha256"] = sha(out / "zephyr.elf")
        for f in ("compile_commands.json", "zephyr/.config"):
            shutil.copyfile(target / f, out / Path(f).name)
            rec[Path(f).name + "_sha256"] = sha(out / Path(f).name)
    save(out / "build_record.json", rec)


# ------------------------------------------------------------------ TCE
def driver_command(app_id):
    a = APPS[app_id]
    slot_src = str(app_dirs(app_id)[2] / Path(DRIVERS[a["driver"]][0]).name)
    cc = json.loads((OUT / "builds" / app_id / "compile_commands.json").read_text())
    e = next(x for x in cc if x["file"] == slot_src)
    args, keep, i = shlex.split(e["command"]), [], 0
    while i < len(args):
        if args[i] in ("-o", "-MF", "-MT", "-MQ"):
            i += 2
            continue
        if args[i] in ("-MD", "-MMD", "-c") or args[i] == slot_src:
            i += 1
            continue
        keep.append(args[i])
        i += 1
    return e["directory"], keep, slot_src


def compile_obj(directory, args, slot_src, text, work):
    """Compile text as the slot file from a private path mapped onto the slot path."""
    work.mkdir(parents=True, exist_ok=True)
    src = work / Path(slot_src).name
    src.write_text(text)
    obj, stripped = work / "m.obj", work / "m.stripped.obj"
    for p in (obj, stripped):
        p.unlink(missing_ok=True)
    maps = [f"-ffile-prefix-map={work}={Path(slot_src).parent}", f"-fmacro-prefix-map={work}={Path(slot_src).parent}"]
    try:
        r = subprocess.run([*args, *maps, "-c", str(src), "-o", str(obj)], cwd=directory, capture_output=True,
                           text=True, timeout=PLAN["tce_compile_timeout_seconds"])
    except subprocess.TimeoutExpired:
        return dict(status="compile_timeout")
    if r.returncode != 0:
        errs = [l for l in r.stderr.splitlines() if "error" in l][:3]
        return dict(status="compile_failure", errors=errs)
    subprocess.run([str(SDK / "arm-zephyr-eabi-objcopy"), "--strip-debug", str(obj), str(stripped)], check=True)
    return dict(status="compiled", object_sha256=sha(stripped))


def tce(chunk):
    tasks = json.loads((OUT / "job_metadata/tce_chunks.json").read_text())[chunk]
    ms = mutants()
    texts = {k: original_driver(k) for k in DRIVERS}
    work = Path("/var/tmp/tce")
    cmds, base, rows = {}, {}, []
    for mid, cfg in tasks:
        if cfg not in cmds:
            cmds[cfg] = driver_command(PLAN["tce_reference_apps"][cfg])
            kind = "counter" if cfg == "counter" else "rtc"
            base[cfg] = compile_obj(*cmds[cfg], texts[kind], work)
            if base[cfg]["status"] != "compiled":
                raise RuntimeError(f"original driver does not compile for {cfg}: {base[cfg]}")
        m = ms[mid]
        kind = "counter" if m["file"].startswith("counter") else "rtc"
        r = compile_obj(*cmds[cfg], gm.apply(texts[kind], m), work)
        r.update(mutant_id=mid, configuration=cfg, original_object_sha256=base[cfg]["object_sha256"])
        if r["status"] == "compiled":
            r["tce_equivalent"] = r["object_sha256"] == base[cfg]["object_sha256"]
        rows.append(r)
    save(OUT / "tce" / f"chunk-{chunk:03d}.json", dict(chunk=chunk, rows=rows, timestamp_utc=utc(), **PROV))


# ------------------------------------------------------------------ simulation
def platform_for(a, path):
    if a["driver"] == "rtc":
        return REPO / PLAN["platform"]
    path.write_text(f'using "/renode/platforms/boards/{PLAN["counter_platform"]}"\nrtc:\n'
                    f'    wakeupTimerFrequency: {PLAN["nominal_hz"]}\nnvic:\n    systickFrequency: 16000000\n')
    return path


def simulate(app_id, elf, rid, folder, traced=False, wall_cap=None):
    a = APPS[app_id]
    sys.path.insert(0, str(REPO / "harness/phase0"))
    from session import RenodeSession
    binary = Path(os.environ.get("RENODE_BIN", "/opt/renode/renode-pinned"))
    version = subprocess.check_output([str(binary), "--version"], text=True).strip()
    if version != PLAN["renode_version"]:
        raise RuntimeError("Renode version differs from plan")
    d = OUT / folder
    paths = {k: d / k / f"{rid}.{ext}" for k, ext in (("uart", "log"), ("monitor", "log"), ("platform", "repl"))}
    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            raise RuntimeError("refusing to replace output")
    trace = Path("/var/tmp") / f"{rid}.pc.txt.gz"
    platform = platform_for(a, paths["platform"])
    started, vns, completed, error = time.monotonic(), 0, False, None
    cap = wall_cap or (a["traced_wall_seconds"] if traced else a["wall_seconds"])
    try:
        with RenodeSession(binary, platform, elf, paths["monitor"]) as s:
            s.command(f"cpu PerformanceInMips {PLAN['cpu_mips']}")
            s.command(f"sysbus.usart2 CreateFileBackend @{paths['uart']} true")
            if traced:
                s.command(f'cpu CreateExecutionTracing "mqcov" @{trace} PC false true')
            while vns < a["max_virtual_seconds"] * 1_000_000_000:
                if time.monotonic() - started > cap:
                    error = "wall cap reached"
                    break
                s.run_for_ns(PLAN["step_ns"])
                vns += PLAN["step_ns"]
                text = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
                if any(m in text for m in MARKERS):
                    completed = True
                    break
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    text = paths["uart"].read_text(errors="replace") if paths["uart"].exists() else ""
    cases = sorted({(c, st.lower()) for st, c in CASE.findall(text)})
    outcome = ("harness_error" if error and error != "wall cap reached" else
               "wall_cap" if error else "complete" if completed else "virtual_timeout")
    rec = dict(run_id=rid, app_id=app_id, traced=traced, outcome=outcome, error=error, completed=completed,
               cases=[dict(case=c, status=s) for c, s in cases], virtual_ns=vns,
               wall_seconds=round(time.monotonic() - started, 3), elf_sha256=sha(elf),
               platform_sha256=sha(platform), renode_version=version, timestamp_utc=utc(),
               uart_sha256=sha(paths["uart"]) if paths["uart"].exists() else None, **PROV)
    return rec, trace


def addr2line_driver_lines(elf, addresses, slot_src):
    """Driver-file lines (with the inline chain) for each address, via binutils addr2line -i."""
    lines = set()
    if not addresses:
        return lines
    proc = subprocess.run([str(SDK / "arm-zephyr-eabi-addr2line"), "-i", "-a", "-e", str(elf)],
                          input="".join(f"0x{x:x}\n" for x in sorted(addresses)), capture_output=True, text=True,
                          check=True)
    for line in proc.stdout.splitlines():
        if line.startswith("0x"):
            continue
        loc = line.split(" (discriminator")[0]
        f, _, n = loc.rpartition(":")
        if f == slot_src and n.isdigit():
            lines.add(int(n))
    return lines


def line_table_addresses(elf):
    out = subprocess.run([str(SDK / "arm-zephyr-eabi-readelf"), "--debug-dump=decodedline", str(elf)],
                         capture_output=True, text=True, check=True).stdout
    addrs = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1].isdigit() and parts[2].startswith("0x"):
            addrs.add(int(parts[2], 16))
    return addrs


def run(app_id, mode):
    out = OUT / "builds" / app_id
    br = json.loads((out / "build_record.json").read_text())
    rid = f"{app_id}-{mode}"
    if br["status"] != "built":
        save(OUT / "records" / f"{rid}.json", dict(run_id=rid, app_id=app_id, outcome="not_run_build_failure", **PROV))
        return
    traced = mode == "traced"
    rec, trace = simulate(app_id, out / "zephyr.elf", rid, "runs", traced=traced)
    if traced:
        if trace.exists():
            pcs = set()
            hexpc = re.compile(rb"0x([0-9A-Fa-f]+)")
            opener = gzip.open if trace.read_bytes()[:2] == b"\x1f\x8b" else open
            n = 0
            with opener(trace, "rb") as f:
                for raw in f:
                    m = hexpc.search(raw)
                    if m:
                        pcs.add(int(m.group(1), 16))
                        n += 1
            slot = br["slot_driver"]
            addressed = addr2line_driver_lines(out / "zephyr.elf", line_table_addresses(out / "zephyr.elf"), slot)
            executed = addr2line_driver_lines(out / "zephyr.elf", pcs, slot) & addressed
            rec.update(trace_bytes=trace.stat().st_size, trace_instructions=n, unique_pcs=len(pcs),
                       driver_addressed_lines=sorted(addressed), driver_executed_lines=sorted(executed),
                       driver_line_coverage=len(executed) / len(addressed) if addressed else None,
                       coverage_method="Renode CreateExecutionTracing PC (text, gzip) + binutils addr2line -i")
            trace.unlink()
        else:
            rec.update(coverage_error="trace file missing")
    save(OUT / "records" / f"{rid}.json", rec)


def timing(app_id, mid):
    a, m = APPS[app_id], mutants()[mid]
    base, app, slot, target = app_dirs(app_id)
    src = slot / Path(DRIVERS[a["driver"]][0]).name
    src.write_text(gm.apply(original_driver(a["driver"]), m))
    rid = f"{app_id}-{mid}"
    t0 = time.monotonic()
    log = OUT / "timing" / f"{rid}.build.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("x") as s:
        code = subprocess.run(["cmake", "--build", str(target), "--parallel", "1"], env=env(), stdout=s,
                              stderr=subprocess.STDOUT, timeout=PLAN["build_timeout_seconds"]).returncode
    build_s = round(time.monotonic() - t0, 3)
    elf = target / "zephyr/zephyr.elf"
    if code:
        save(OUT / "timing" / f"{rid}.json", dict(run_id=rid, app_id=app_id, mutant_id=mid, outcome="build_failure",
                                                  build_seconds=build_s, **PROV))
        return
    rec, _ = simulate(app_id, elf, rid, "timing_runs")
    baseline = json.loads((OUT / "records" / f"{app_id}-baseline.json").read_text())
    same = rec["outcome"] == baseline["outcome"] and rec["cases"] == baseline["cases"]
    rec.update(mutant_id=mid, build_seconds=build_s,
               verdict=("harness_error" if rec["outcome"] == "harness_error" else "survived" if same else "killed"))
    save(OUT / "timing" / f"{rid}.json", rec)


if __name__ == "__main__":
    stage, *rest = sys.argv[1:]
    {"build": lambda: build(rest[0]), "tce": lambda: tce(int(rest[0])),
     "run": lambda: run(rest[0], rest[1]), "timing": lambda: timing(rest[0], rest[1])}[stage]()
