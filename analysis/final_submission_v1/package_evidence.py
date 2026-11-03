#!/usr/bin/env python3
"""Create a new release archive from the exact offline-analysis input ledger.

Copies only explicitly hashed inputs; never prunes, edits or runs firmware.
Reads the archive back and verifies every member before declaring success.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
from common import sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--release-tag', required=True)
    a = p.parse_args()
    repo = Path(__file__).resolve().parents[2]
    hashes = json.loads(a.inputs.read_text())
    assert not any(k in hashes for k in ('paper/draft/main.tex', 'paper/draft/main.pdf'))
    assert not a.archive.exists() and not a.metadata.exists()
    files = {}
    for relative, expected in sorted(hashes.items()):
        path = repo / relative
        assert path.resolve().is_relative_to(repo) and not path.is_symlink()
        assert sha(path) == expected, relative
        files[relative] = dict(sha256=expected, bytes=path.stat().st_size)
    manifest = json.dumps(dict(format=1, files=files), sort_keys=True, separators=(',', ':')).encode()
    a.archive.parent.mkdir(parents=True, exist_ok=True)
    with a.archive.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w|') as tar:
            info = tarfile.TarInfo('.rtc-evidence-manifest.json')
            info.size = len(manifest)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(manifest))
            for relative in files:
                info = tar.gettarinfo(str(repo / relative), arcname=relative)
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.mode = 0o644
                with (repo / relative).open('rb') as stream:
                    tar.addfile(info, stream)
    seen = set()
    with tarfile.open(a.archive, 'r:gz') as tar:
        for member in tar:
            assert member.isfile()
            content = tar.extractfile(member)
            if member.name == '.rtc-evidence-manifest.json':
                assert content.read() == manifest
                continue
            assert member.name in files and member.name not in seen
            digest = hashlib.file_digest(content, 'sha256').hexdigest()
            assert digest == files[member.name]['sha256'], member.name
            assert member.size == files[member.name]['bytes']
            seen.add(member.name)
    assert seen == set(files)
    metadata = dict(format=1, filename=a.archive.name, sha256=sha(a.archive), bytes=a.archive.stat().st_size,
                    files=len(files), unpacked_bytes=sum(r['bytes'] for r in files.values()),
                    url='https://github.com/pkrish5/zephyr-rtc-clock-robustness/releases/download/' + a.release_tag + '/' + a.archive.name,
                    release_tag=a.release_tag, manifest_sha256=hashlib.sha256(manifest).hexdigest(),
                    source_input_ledger_sha256=sha(a.inputs), archive_readback_verified=True,
                    excludes='No SIF, full Zephyr checkout, caches or unrelated results; includes every input to the final offline analysis.')
    a.metadata.parent.mkdir(parents=True, exist_ok=True)
    a.metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    Path(str(a.archive) + '.sha256').write_text(metadata['sha256'] + '  ' + a.archive.name + '\n')
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
