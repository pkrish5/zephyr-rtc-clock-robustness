#!/usr/bin/env python3
"""Find reviewable timing-assumption candidates in matched human and agent tests."""

import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COHORT = os.environ.get("PHASE2_COHORT", "sol_pilot")
COHORT_PATHS = {
    "sol_pilot": ("subjects/phase2_tasks.json", "phase2"),
    "luna_primary": ("subjects/phase2_tasks.json", "phase2_luna"),
    "rtc_bound_supplement": ("subjects/phase2_rtc_bound_tasks.json", "phase2_rtc_bound"),
}
if COHORT not in COHORT_PATHS:
    raise RuntimeError(f"Unknown Phase 2 cohort: {COHORT}")
task_file, cohort_directory = COHORT_PATHS[COHORT]
TASKS = json.loads((ROOT / task_file).read_text())["tasks"]
GENERATED = ROOT / "generated" / cohort_directory
OUT = ROOT / "results" / cohort_directory / "static_candidates.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask_noncode(source: str) -> str:
    pattern = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*', re.DOTALL)
    return pattern.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), source)


def region(masked: str, opening_brace: int) -> tuple[int, int]:
    depth = 0
    for i in range(opening_brace, len(masked)):
        if masked[i] == "{":
            depth += 1
        elif masked[i] == "}":
            depth -= 1
            if depth == 0:
                return opening_brace, i + 1
    raise ValueError("Unbalanced C function body")


def line_at(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def selected_human_regions(task: dict) -> list[tuple[Path, int, int, str]]:
    app = ROOT / "subjects/upstream/zephyr" / task["human_app"]
    suite, test = task["human_case"].split(".")
    target = re.compile(r"\bZTEST(?:_USER)?\s*\(\s*" + re.escape(suite) +
                        r"\s*,\s*" + re.escape(test) + r"\s*\)\s*\{", re.DOTALL)
    sources = [(p, p.read_text(errors="replace")) for p in app.rglob("*") if p.suffix in (".c", ".h")]
    found = []
    functions = {}
    for path, source in sources:
        masked = mask_noncode(source)
        match = target.search(masked)
        if match:
            start, end = region(masked, match.end() - 1)
            found.append((path, start, end, "selected_case"))
        # Approximate top-level helper definitions; only reachable helpers are included.
        depth = 0
        top = [False] * len(masked)
        for i, ch in enumerate(masked):
            top[i] = depth == 0
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        for match in re.finditer(r"\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{", masked, re.DOTALL):
            if not top[match.start()] or match.group(1) in ("ZTEST", "ZTEST_USER", "if", "while", "for", "switch"):
                continue
            start, end = region(masked, match.end() - 1)
            functions[match.group(1)] = (path, start, end, "reachable_helper")
    if len(found) != 1:
        raise ValueError(f"Expected one source region for {task['human_case']}, found {len(found)}")
    regions = list(found)
    seen = set()
    queue = list(found)
    while queue:
        path, start, end, _ = queue.pop(0)
        body = mask_noncode(path.read_text(errors="replace"))[start:end]
        # Callback functions are often passed by name rather than called in the
        # selected case (for example, rtc_alarm_set_callback(..., callback)).
        for name in set(re.findall(r"\b[A-Za-z_]\w*\b", body)):
            if name in functions and name not in seen:
                seen.add(name)
                queue.append(functions[name])
                regions.append(functions[name])
    # Include timing constants defined outside the selected C bodies. Without
    # this, a K_MSEC() hidden behind a local macro biases the human scan low.
    referenced = set()
    for path, start, end, _ in regions:
        referenced.update(re.findall(r"\b[A-Za-z_]\w*\b", mask_noncode(path.read_text(errors="replace"))[start:end]))
    for path, source in sources:
        for match in re.finditer(r"^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)[^\n]*", source, re.MULTILINE):
            if match.group(1) in referenced:
                regions.append((path, match.start(), match.end(), "referenced_macro"))
    return regions


def scan_region(path: Path, start: int, end: int, scope: str) -> list[dict]:
    source = path.read_text(errors="replace")
    masked = mask_noncode(source)
    first_line = line_at(source, start)
    tags = []
    original_lines = source[start:end].splitlines()
    for offset, line in enumerate(masked[start:end].splitlines()):
        code = line.strip()
        categories = []
        if re.search(r"\b(?:k_sleep|k_msleep|k_usleep|k_busy_wait)\s*\(", code):
            categories.append("fixed_wait_candidate")
        if re.search(r"\bK_(?:MSEC|SECONDS|TICKS|USEC)\s*\(", code):
            categories.append("explicit_time_value_candidate")
        if (re.search(r"\b(?:elapsed|timeout|delay|wait|sleep|margin|settle)\w*\b\s*(?:<=|>=|<|>)\s*\d+", code, re.I)
                or re.search(r"^#[ \t]*define[ \t]+\w*(?:TIMEOUT|DELAY|WAIT|SLEEP|MARGIN|SETTLE)\w*[ \t]+\d+", code)):
            categories.append("numeric_time_bound_candidate")
        if re.search(r"\bwhile\s*\(", code) and not re.search(r"\b(?:elapsed|timeout|deadline|limit|count|index|remaining)\b", code, re.I):
            categories.append("possibly_unbounded_wait_candidate")
        if re.search(r"\bzassert_\w+\s*\(", code) and re.search(r"callback|fired|count|order|mask|flag", code, re.I):
            categories.append("ordering_or_shared_state_assertion_candidate")
        if (re.search(r"\b(?:zassert_\w+|TIMER_ASSERT|expect_\w+)\s*\(", code)
                and re.search(r"\b\w*(?:count|cnt|state|flag|mask|reported_id|expire_cnt)\w*\b", code, re.I)
                and not re.search(r"\b(?:atomic_get|atomic_test_bit|k_sem_take)\s*\(", code)):
            categories.append("unprotected_shared_read_candidate")
        if re.search(r"\b(?:atomic_get|atomic_test_bit|k_sem_take)\s*\(", code):
            categories.append("synchronization_observation")
        for category in categories:
            tags.append({"category": category, "path": str(path.relative_to(ROOT)),
                         "line": first_line + offset, "scope": scope,
                         "snippet": original_lines[offset].strip()[:240],
                         "adjudication": "pending_review"})
    return tags


def main() -> None:
    records = []
    for task in TASKS:
        regions = selected_human_regions(task)
        human_tags = []
        region_hashes = {}
        for path, start, end, scope in regions:
            human_tags.extend(scan_region(path, start, end, scope))
            region_hashes[str(path.relative_to(ROOT))] = sha256(path)
        records.append({"task_id": task["id"], "kind": "upstream", "case": task["human_case"],
                        "source_files_sha256": region_hashes, "regions_scanned": len(regions),
                        "tags": human_tags})
        for index in range(1, 6):
            run_id = f"{task['id']}-r{index:02d}"
            source = GENERATED / "suites" / task["id"] / f"r{index:02d}/test.c"
            if not source.exists():
                continue
            metadata = json.loads((source.parent / "metadata.json").read_text())
            if sha256(source) != metadata["source_sha256"]:
                raise ValueError(f"Generated source changed: {run_id}")
            records.append({"task_id": task["id"], "kind": "agent", "run_id": run_id,
                            "source_sha256": metadata["source_sha256"],
                            "tags": scan_region(source, 0, len(source.read_text(errors="replace")), "generated_suite")})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"method": "syntactic candidate scan; manual adjudication pending",
                               "records": records}, sort_keys=True, indent=2) + "\n")
    print(f"scanned {sum(r['kind'] == 'upstream' for r in records)} upstream cases and "
          f"{sum(r['kind'] == 'agent' for r in records)} generated suites")


if __name__ == "__main__":
    main()
