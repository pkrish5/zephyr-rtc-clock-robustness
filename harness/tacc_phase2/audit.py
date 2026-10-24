#!/usr/bin/env python3
"""Seal/check all Phase 1 protected bytes plus the final packaging bytes."""
import argparse
from pathlib import Path
from support import read, save, sha, utc

ap = argparse.ArgumentParser()
ap.add_argument('command', choices=['baseline', 'check'])
ap.add_argument('--root', type=Path, required=True)
ap.add_argument('--snapshot', type=Path, required=True)
ap.add_argument('--out', type=Path)
a = ap.parse_args()
if a.command == 'baseline':
    old = read(a.root / 'artifacts/tacc_phase1_20261023_v10/hash_audit.json')
    hashes = {rel: d['after_sha256'] for rel, d in old['protected_files'].items()}
    # Protect the finalized packaging, too; Phase 2 has no packaging exemption.
    for p in (a.root / 'harness').rglob('*'):
        if p.is_file() and 'tacc_phase2' not in p.parts and '__pycache__' not in p.parts:
            hashes[str(p.relative_to(a.root))] = sha(p)
    changed = [rel for rel, digest in hashes.items() if sha(a.root / rel) != digest]
    if changed:
        raise RuntimeError('Protected inputs already differ: ' + str(changed))
    save(a.snapshot, dict(timestamp_utc=utc(), hashes=hashes, protected_count=len(hashes)))
    print(len(hashes), sha(a.snapshot))
else:
    base = read(a.snapshot)
    rows = {rel: dict(before_sha256=digest, after_sha256=sha(a.root / rel)) for rel, digest in base['hashes'].items()}
    changed = [rel for rel, d in rows.items() if d['before_sha256'] != d['after_sha256']]
    save(a.out, dict(timestamp_utc=utc(), snapshot_sha256=sha(a.snapshot), count=len(rows), changed=changed, files=rows))
    print(len(rows), 'changed:', changed, 'audit:', sha(a.out))
    if changed:
        raise SystemExit(2)
