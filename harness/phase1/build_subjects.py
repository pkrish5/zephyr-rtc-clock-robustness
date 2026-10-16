#!/usr/bin/env python3
"""Build pinned, unchanged upstream ztest applications for the Phase 1 pilot."""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "subjects" / "phase1_zephyr"
UPSTREAM = ROOT / "subjects" / "upstream" / "zephyr"
RESULTS = ROOT / "results" / "phase1"
MANIFEST = json.loads((CONFIG_DIR / "candidates.json").read_text())
HSI_OVERLAY = CONFIG_DIR / "config" / "stm32f4_hsi.overlay"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*")
    args = parser.parse_args()
    expected = MANIFEST["zephyr_commit"]
    actual = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if actual != expected:
        raise SystemExit(f"Zephyr commit mismatch: {actual} != {expected}")
    selection = set(args.ids) if args.ids else {item["id"] for item in MANIFEST["subjects"]}
    unknown = selection - {item["id"] for item in MANIFEST["subjects"]}
    if unknown:
        raise SystemExit(f"Unknown subject IDs: {sorted(unknown)}")
    sdk = Path(os.environ.get("ZEPHYR_SDK_INSTALL_DIR", "/private/tmp/phase1-zephyr-sdk"))
    west = ROOT / ".venv" / "bin" / "west"
    env = dict(os.environ)
    env["ZEPHYR_SDK_INSTALL_DIR"] = str(sdk)
    env["PATH"] = f"{west.parent}:{env['PATH']}"
    RESULTS.mkdir(parents=True, exist_ok=True)
    log_dir = RESULTS / "build_logs"
    log_dir.mkdir(exist_ok=True)
    records = RESULTS / "builds.jsonl"
    done = {json.loads(line)["subject_id"] for line in records.read_text().splitlines()} if records.exists() else set()
    for subject in MANIFEST["subjects"]:
        ident = subject["id"]
        if ident not in selection or ident in done:
            continue
        source = UPSTREAM / subject["path"]
        build = CONFIG_DIR / "build" / ident
        elf = build / "zephyr" / "zephyr.elf"
        log_path = log_dir / f"{ident}.log"
        if log_path.exists():
            raise RuntimeError(f"Refusing to overwrite raw build log: {log_path}")
        overlays = [HSI_OVERLAY] + [UPSTREAM / path for path in subject.get("overlays", [])]
        command = [str(west), "build", "-p", "always", "-b", "stm32f4_disco", str(source), "-d", str(build), "--", "-DDTC_OVERLAY_FILE=" + ";".join(map(str, overlays))] + subject.get("cmake_args", [])
        with log_path.open("w") as log:
            result = subprocess.run(command, cwd=UPSTREAM, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        record = {
            "subject_id": ident,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "upstream_commit": actual,
            "source_path": str(source.relative_to(ROOT)),
            "source_tree_sha256": source_sha256(source),
            "board": MANIFEST["board"],
            "overlay_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in overlays},
            "sdk_version": (sdk / "sdk_version").read_text().strip(),
            "command": command,
            "exit_code": result.returncode,
            "elf_path": str(elf.relative_to(ROOT)) if elf.exists() else None,
            "elf_sha256": sha256(elf) if elf.exists() else None,
            "log_path": str(log_path.relative_to(ROOT)),
        }
        with records.open("a") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
        print(f"{ident}: {'built' if result.returncode == 0 else 'FAILED'}", flush=True)


if __name__ == "__main__":
    main()
