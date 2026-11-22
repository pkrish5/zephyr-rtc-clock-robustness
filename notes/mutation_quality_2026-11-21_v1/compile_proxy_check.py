#!/usr/bin/env python3
"""Dry-run compile screen of generated mutants (proxy, not the production compiler).

Runs `clang -fsyntax-only` for every mutant under every recorded configuration
of the file (union: a mutant counts as compiling if it compiles in each
configuration in which its line is active; here: all configurations). The
production GCC 12 / Zephyr SDK 0.17.4 compile and Trivial Compiler Equivalence
(TCE) are separate, later steps inside the pinned container.

Local deviations, recorded in the output: Zephyr's minimal-libc headers stand in
for the SDK's picolibc headers, and `errno` is defined to an external int.

Usage: compile_proxy_check.py --mutants DIR   (writes DIR/compile_proxy.jsonl)
"""
import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import generate_mutants as g

LIBC = g.ZEPHYR / "lib/libc/minimal/include"


def check(text, src, flags, shim):
    with tempfile.NamedTemporaryFile("w", suffix=".c", delete=False, dir=shim.parent) as f:
        f.write(text)
        path = f.name
    try:
        cmd = ["clang", "-fsyntax-only", "-target", "arm-none-eabi", "-mcpu=cortex-m4", "-mthumb",
               "-ffreestanding", "-isystem", str(LIBC), "-include", str(shim), "-Derrno=rtcmut_errno",
               "-Wno-everything", "-Werror=implicit-int", "-Werror=implicit-function-declaration",
               "-iquote", str(src.parent), *flags, path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        errors = [l.split(path, 1)[-1] for l in r.stderr.splitlines() if " error: " in l]
        return r.returncode == 0, errors[:3]
    finally:
        os.unlink(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutants", required=True, type=Path)
    args = ap.parse_args()
    out_path = args.mutants / "compile_proxy.jsonl"
    cfgs = g.configurations()
    shim = Path(tempfile.mkdtemp(prefix="rtcmut-cc-")) / "shim.h"
    shim.write_text("extern int rtcmut_errno;\n")
    texts = {n: p.read_text() for n, p in g.TARGETS.items()}
    for name, src in g.TARGETS.items():
        for cfg, flags in cfgs[name].items():
            ok, err = check(texts[name], src, flags, shim)
            if not ok:
                raise SystemExit(f"baseline {name}/{cfg} does not pass the proxy: {err}")
    mutants = [json.loads(l) for l in (args.mutants / "mutants.jsonl").read_text().splitlines()]

    def run(m):
        src = g.TARGETS[m["file"]]
        text = g.apply(texts[m["file"]], m)
        res = {}
        for cfg, flags in cfgs[m["file"]].items():
            res[cfg] = check(text, src, flags, shim)
        ok = all(v[0] for v in res.values())
        return dict(id=m["id"], file=m["file"], operator=m["operator"], compiles_proxy=ok,
                    errors={c: v[1] for c, v in res.items() if not v[0]})

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
        results = list(ex.map(run, mutants))
    with out_path.open("x") as fh:
        for r in results:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    summary = {}
    for r in results:
        s = summary.setdefault(r["file"], {"mutants": 0, "compile_proxy_pass": 0, "compile_proxy_fail": 0,
                                           "by_operator": {}})
        s["mutants"] += 1
        key = "compile_proxy_pass" if r["compiles_proxy"] else "compile_proxy_fail"
        s[key] += 1
        o = s["by_operator"].setdefault(r["operator"], {"pass": 0, "fail": 0})
        o["pass" if r["compiles_proxy"] else "fail"] += 1
    summary["_proxy"] = dict(compiler=subprocess.run(["clang", "--version"], capture_output=True,
                                                      text=True).stdout.splitlines()[0],
                             libc_headers=str(LIBC.relative_to(g.ROOT)), errno_shim=True,
                             note="proxy screen only; production GCC compile and TCE pending")
    (args.mutants / "compile_proxy_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
