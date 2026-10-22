#!/usr/bin/env python3
"""Describe the compute-node probe, choose concurrency, and estimate node-hours."""
import argparse
import json
import math
import os
import re
import socket
import sys
from pathlib import Path

from calibration import exclusive, plan_at
from prepare import sha


def parse_time(text):
    rss = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", text)
    wall = next((line.split("): ", 1)[1].strip() for line in text.splitlines()
                 if "Elapsed (wall clock) time" in line and "): " in line), None)
    if rss is None or wall is None:
        raise ValueError("GNU time -v report is incomplete")
    seconds = 0.0
    for part in wall.split(":"):
        seconds = seconds * 60 + float(part)
    if int(rss.group(1)) <= 0 or seconds <= 0:
        raise ValueError("Resource measurements must be positive")
    return int(rss.group(1)), seconds


def memory_info():
    result = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable"):
            result[key] = int(value.strip().split()[0])
    available = result["MemAvailable"]
    for name in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        p = Path(name)
        if p.exists() and p.read_text().strip().isdigit():
            available = min(available, int(p.read_text().strip()) // 1024)
    return result["MemTotal"], available


def select_concurrency(peak_kib, available_kib, cpus, cap):
    if min(peak_kib, available_kib, cpus, cap) <= 0:
        raise ValueError("Resource limits must be positive")
    memory_limit = math.floor(0.8 * available_kib / (1.5 * peak_kib))
    if memory_limit < 1:
        raise ValueError("A single run exceeds the conservative memory allowance")
    return min(memory_limit, cpus, cap), memory_limit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("probe-report", "capacity", "estimate"))
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--cap", type=int, default=32)
    p.add_argument("--runs", type=int)
    p.add_argument("--nodes", type=int, default=1)
    p.add_argument("--partition", choices=("development", "normal"), default="development")
    p.add_argument("--requested-seconds", type=int, default=5400)
    p.add_argument("--su-rate", type=float, default=1.0)
    a = p.parse_args()
    plan, plan_hash = plan_at(a.bundle)
    base = a.bundle / "study" / plan["output_relative"]
    if (base / "STOP.json").exists():
        raise SystemExit("STOP: calibration stop marker exists")
    probe_report = base / "probe/resource_report.json"
    if a.command == "probe-report":
        if not os.environ.get("SLURM_JOB_ID"):
            raise ValueError("Resource probe must be measured on a Slurm compute node")
        comparison = base / "probe/comparisons" / f"{plan['probe_task_index']:04d}.json"
        c = json.loads(comparison.read_text())
        if c["verdict_agrees"] is not True or c["trace_hash_agrees"] is not True:
            raise ValueError("Probe calibration comparison did not agree")
        peak, wall = parse_time((base / "probe/resources/0.time").read_text())
        total, available = memory_info()
        result = {"peak_rss_kib": peak, "wall_seconds": wall,
                  "node_total_memory_kib": total, "node_available_memory_kib": available,
                  "cpus_available": len(os.sched_getaffinity(0)), "node_name": socket.gethostname(),
                  "slurm_job_id": os.environ["SLURM_JOB_ID"], "calibration_plan_sha256": plan_hash,
                  "comparison_sha256": sha(comparison), "measurement": "GNU time -v command/children maximum RSS",
                  "status": "probe_agrees"}
    else:
        probe = json.loads(probe_report.read_text())
        if probe["calibration_plan_sha256"] != plan_hash or probe["status"] != "probe_agrees":
            raise ValueError("Probe belongs to another plan or did not agree")
        available, cpus = probe["node_available_memory_kib"], probe["cpus_available"]
        if a.command == "capacity":
            _, current = memory_info()
            available = min(available, current)
            cpus = min(cpus, len(os.sched_getaffinity(0)))
        concurrency, memory_limit = select_concurrency(probe["peak_rss_kib"], available, cpus, a.cap)
        runs = a.runs if a.runs is not None else len(plan["tasks"])
        if runs < 1 or a.nodes < 1 or a.su_rate <= 0:
            raise ValueError("Run, node, and SU-rate values must be positive")
        # Single-run timing is only an estimate. Include 50% variation and
        # two minutes of per-job startup; report the reserved upper charge too.
        seconds = 120 + math.ceil(runs / (concurrency * a.nodes)) * probe["wall_seconds"] * 1.5
        result = {"concurrency_per_node": concurrency, "memory_limited_concurrency": memory_limit,
                  "requested_cap": a.cap, "allocated_cpus": cpus, "available_memory_kib": available,
                  "rss_safety_factor": 1.5, "memory_fraction": 0.8,
                  "estimated_reserved_memory_kib": concurrency * probe["peak_rss_kib"] * 1.5,
                  "runs": runs, "nodes": a.nodes, "partition": a.partition,
                  "estimated_wall_seconds": round(seconds, 2),
                  "estimated_su": round(a.nodes * max(seconds / 3600, 0.25) * a.su_rate, 4),
                  "requested_time_limit_su": round(a.nodes * max(a.requested_seconds / 3600, 0.25) * a.su_rate, 4),
                  "su_rate_per_node_hour": a.su_rate,
                  "billing_minimum_hours": 0.25, "requested_seconds": a.requested_seconds,
                  "probe_report_sha256": sha(probe_report), "calibration_plan_sha256": plan_hash,
                  "caveat": "Estimate from one run, not a measured throughput or memory bound",
                  "production_submission": "not authorized by Phase 1"}
        if a.command == "capacity" and seconds > a.requested_seconds:
            print(json.dumps(result, indent=2))
            raise SystemExit("STOP: estimated packed calibration does not fit the development job time limit")
    exclusive(a.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
