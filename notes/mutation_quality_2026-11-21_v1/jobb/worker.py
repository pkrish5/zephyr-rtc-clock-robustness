#!/usr/bin/env python3
"""Job B worker; runs inside the pinned container (one process per task).

Derived from the sealed Job A worker (joba/worker.py). Changes:
- the traced run disables (flushes) Renode execution tracing before the session
  closes, and an unreadable trace becomes a recorded coverage_error, not a crash;
- builds can use a private tagged tree (one per mutant chunk or replay);
- new stages `mutants` (a chunk of mutants for one app) and `replay`.
Stages: build APP | run APP {baseline,traced} | mutants KEY | replay INDEX.
Writes only new files under /out (job output) and /scratch-builds (build trees).
"""
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib
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


PLAN = json.loads((STUDY / "jobb/plan.json").read_text())
APPS = {a["id"]: a for a in PLAN["apps"]}
PROV = dict(slurm_job_id=os.environ.get("SLURM_JOB_ID"), node=os.environ.get("RTC_NODE_NAME"),
            container_sha256=os.environ.get("RTC_CONTAINER_SHA256"),
            plan_sha256=sha(STUDY / "jobb/plan.json"))


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
def app_dirs(app_id, tag=None):
    base = BUILDS / (app_id if tag is None else f"{app_id}--{tag}")
    return base, base / "app", base / "slot", base / "build"


def build(app_id, tag=None):
    """Configure and build APP with the unmutated slot driver. A tagged build uses a
    private tree, records under /out/chunk_builds and keeps no ELF copy."""
    a = APPS[app_id]
    base, app, slot, target = app_dirs(app_id, tag)
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
    out = OUT / "builds" / app_id if tag is None else OUT / "chunk_builds" / f"{app_id}--{tag}"
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
    rec = dict(app_id=app_id, tag=tag, status="built" if code == 0 and elf.exists() else "build_failure",
               exit_code=code, wall_seconds=round(time.monotonic() - start, 3), commands=cmds, log_sha256=sha(log),
               slot_driver=str(slot / name), timestamp_utc=utc(), **PROV)
    if elf.exists() and tag is None:
        shutil.copyfile(elf, out / "zephyr.elf")
        rec["elf_sha256"] = sha(out / "zephyr.elf")
        for f in ("compile_commands.json", "zephyr/.config"):
            shutil.copyfile(target / f, out / Path(f).name)
            rec[Path(f).name + "_sha256"] = sha(out / Path(f).name)
    elif elf.exists():
        rec["elf_sha256"] = sha(elf)
    if rec["status"] == "built" and tag is not None:
        log.unlink()  # successful chunk build logs are not kept (file-count budget); the hash stays
    save(out / "build_record.json", rec)
    return rec


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
    started, vns, completed, error, trace_note = time.monotonic(), 0, False, None, None
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
            if traced:
                # Job A fix: flush and close the trace while Renode is alive; the frozen
                # session force-terminates Renode 5 s after `quit`.
                try:
                    s.command("cpu DisableExecutionTracing")
                    trace_note = "disabled_before_quit"
                except Exception as exc:  # recorded; coverage is then judged by readability
                    trace_note = f"disable_failed: {type(exc).__name__}: {exc}"[:500]
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
    if traced:
        rec["trace_note"] = trace_note
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


def read_trace(trace):
    """(unique PCs, instruction count, error or None). A truncated stream is an error."""
    pcs, n = set(), 0
    hexpc = re.compile(rb"0x([0-9A-Fa-f]+)")
    with trace.open("rb") as f:
        opener = gzip.open if f.read(2) == b"\x1f\x8b" else open
    try:
        with opener(trace, "rb") as f:
            for raw in f:
                m = hexpc.search(raw)
                if m:
                    pcs.add(int(m.group(1), 16))
                    n += 1
    except (EOFError, OSError, zlib.error) as exc:
        return pcs, n, f"{type(exc).__name__}: {exc}"
    return pcs, n, None


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
        if not trace.exists():
            rec.update(coverage_error="trace file missing")
        else:
            pcs, n, err = read_trace(trace)
            rec.update(trace_bytes=trace.stat().st_size, trace_instructions=n, unique_pcs=len(pcs))
            if err:
                rec.update(coverage_error="trace unreadable; partial coverage not used: " + err)
            else:
                slot = br["slot_driver"]
                addressed = addr2line_driver_lines(out / "zephyr.elf", line_table_addresses(out / "zephyr.elf"), slot)
                executed = addr2line_driver_lines(out / "zephyr.elf", pcs, slot) & addressed
                rec.update(driver_addressed_lines=sorted(addressed), driver_executed_lines=sorted(executed),
                           driver_line_coverage=len(executed) / len(addressed) if addressed else None,
                           coverage_method="Renode CreateExecutionTracing PC (text, gzip) + binutils addr2line -i")
            trace.unlink()
    save(OUT / "records" / f"{rid}.json", rec)


# ------------------------------------------------------------------ mutants
def verdict(rec, reference):
    """Kill rule: outcome or case vector differs from the reference run."""
    if rec["outcome"] == "harness_error":
        return "harness_error", None
    if rec["outcome"] == reference["outcome"] and rec["cases"] == reference["cases"]:
        return "survived", None
    cause = rec["outcome"] if rec["outcome"] in ("wall_cap", "virtual_timeout") else "case_vector"
    return "killed", cause


def mutate_build_run(app_id, mid, tag, folder, rid):
    """Write mutant MID into the tagged tree's slot, rebuild incrementally, run once."""
    a, m = APPS[app_id], mutants()[mid]
    base, app, slot, target = app_dirs(app_id, tag)
    src = slot / Path(DRIVERS[a["driver"]][0]).name
    src.write_text(gm.apply(original_driver(a["driver"]), m))
    t0 = time.monotonic()
    log = Path("/var/tmp") / f"{rid}.build.log"
    with log.open("w") as s:
        try:
            code = subprocess.run(["cmake", "--build", str(target), "--parallel", "1"], env=env(), stdout=s,
                                  stderr=subprocess.STDOUT, timeout=PLAN["build_timeout_seconds"]).returncode
        except subprocess.TimeoutExpired:
            code = 124
    build_s = round(time.monotonic() - t0, 3)
    if code:
        tail = log.read_text(errors="replace").splitlines()[-15:]
        log.unlink()
        return dict(run_id=rid, app_id=app_id, mutant_id=mid, outcome="build_failure", verdict="build_failure",
                    build_exit_code=code, build_seconds=build_s, build_log_tail=tail, timestamp_utc=utc(), **PROV)
    log.unlink()
    rec, _ = simulate(app_id, target / "zephyr/zephyr.elf", rid, folder)
    rec.update(mutant_id=mid, build_seconds=build_s)
    return rec


def mutant_chunk(key):
    """KEY = '<app_id>#<k>': fresh tagged build, then each mutant in the chunk once."""
    mids = json.loads((OUT / "job_metadata/mutant_chunks.json").read_text())[key]
    app_id, k = key.rsplit("#", 1)
    tag = f"c{int(k):03d}"
    baseline = json.loads((OUT / "records" / f"{app_id}-baseline.json").read_text())
    br = build(app_id, tag)
    try:
        for mid in mids:
            p = OUT / "mutants" / app_id / f"{mid}.json"
            if p.exists():
                continue
            if br["status"] != "built":
                save(p, dict(run_id=f"{app_id}-{mid}", app_id=app_id, mutant_id=mid, outcome="not_run_build_failure",
                             verdict="build_failure", chunk=key, **PROV))
                continue
            rec = mutate_build_run(app_id, mid, tag, "mutant_runs", f"{app_id}-{mid}")
            if rec["outcome"] != "build_failure":
                rec["verdict"], rec["kill_cause"] = verdict(rec, baseline)
                rec["baseline_elf_sha256"] = baseline["elf_sha256"]
            rec["chunk"] = key
            save(p, rec)
    finally:
        shutil.rmtree(app_dirs(app_id, tag)[0], ignore_errors=True)  # scratch inode budget


def replay(index):
    sel = json.loads((OUT / "job_metadata/replay_selection.json").read_text())["selected"][index]
    app_id, mid = sel["app_id"], sel["mutant_id"]
    original = json.loads((OUT / "mutants" / app_id / f"{mid}.json").read_text())
    tag = f"r{index:03d}"
    br = build(app_id, tag)
    try:
        if br["status"] != "built":
            rec = dict(outcome="not_run_build_failure")
        else:
            rec = mutate_build_run(app_id, mid, tag, "replay_runs", f"replay-{index:03d}-{app_id}-{mid}")
        rec.update(replay_index=index, app_id=app_id, mutant_id=mid, original_outcome=original["outcome"],
                   original_cases=original["cases"], original_verdict=original["verdict"],
                   reproduced=(rec.get("outcome") == original["outcome"] and rec.get("cases") == original["cases"]))
        save(OUT / "replays" / f"{index:03d}.json", rec)
    finally:
        shutil.rmtree(app_dirs(app_id, tag)[0], ignore_errors=True)


if __name__ == "__main__":
    stage, *rest = sys.argv[1:]
    {"build": lambda: build(rest[0]), "run": lambda: run(rest[0], rest[1]),
     "mutants": lambda: mutant_chunk(rest[0]), "replay": lambda: replay(int(rest[0]))}[stage]()
