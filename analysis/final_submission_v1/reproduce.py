#!/usr/bin/env python3
"""Verify archived evidence, reconcile records, and rebuild all manuscript tables.

Python 3.11+ standard library only. No Renode, Zephyr, network (with a cached
archive), compiler, account credentials, or TACC allocation is required.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from common import sha


def restore(repo, archive, metadata):
    assert sha(archive) == metadata['sha256'], 'Evidence archive SHA256 mismatch'
    with tarfile.open(archive, 'r:gz') as tar:
        member = tar.next()
        assert member.name == '.rtc-evidence-manifest.json' and member.isfile()
        data = tar.extractfile(member).read()
        assert hashlib.sha256(data).hexdigest() == metadata['manifest_sha256']
        files = json.loads(data)['files']
    assert len(files) == metadata['files']
    # Preflight every path and existing destination before writing anything.
    for relative, record in files.items():
        pure = PurePosixPath(relative)
        assert not pure.is_absolute() and '..' not in pure.parts
        path = repo / relative
        assert path.resolve().is_relative_to(repo) and not path.is_symlink()
        if path.exists():
            assert path.is_file() and sha(path) == record['sha256'], 'Refusing to replace different input: ' + relative
    seen = set()
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            if member.name == '.rtc-evidence-manifest.json':
                continue
            assert member.isfile() and member.name in files and member.name not in seen
            record = files[member.name]
            assert member.size == record['bytes']
            path = repo / member.name
            source = tar.extractfile(member)
            digest = hashlib.sha256()
            if path.exists():
                for block in iter(lambda: source.read(1048576), b''):
                    digest.update(block)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as output:
                    for block in iter(lambda: source.read(1048576), b''):
                        output.write(block)
                        digest.update(block)
            assert digest.hexdigest() == record['sha256'], member.name
            seen.add(member.name)
    assert seen == set(files)
    return len(seen)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, help='Cached release asset; omitted means download the pinned asset')
    a = p.parse_args()
    assert sys.version_info >= (3, 11), 'Python 3.11+ required'
    repo = Path(__file__).resolve().parents[2]
    metadata = json.loads((repo / 'reproduction/evidence.json').read_text())
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='rtc-tables-') as temp:
        temp = Path(temp)
        archive = a.archive.resolve() if a.archive else temp / metadata['filename']
        if not a.archive:
            urllib.request.urlretrieve(metadata['url'], archive)
        count = restore(repo, archive, metadata)
        output = temp / 'analysis'
        notes = 'notes/final_submission_2026-11-02_v1'
        command = [sys.executable, '-B', 'analysis/final_submission_v1/build_package.py', '--repo', str(repo),
                   '--original-e-verified', notes + '/verified-original-e-3549010-v1', '--chunk-verified']
        command += ['notes/e_resume_2026-11-02_v1/verified-%s-v1' % job for job in range(3547925, 3547932)]
        command += ['--comparison-manuscript', notes + '/main_before_phaseC.tex', '--out', str(output)]
        subprocess.run(command, cwd=repo, check=True)
        subprocess.run([sys.executable, '-B', 'analysis/final_submission_v1/render_tables.py', '--package', str(output),
                        '--out', 'paper/draft/tables'], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        manifest = json.loads((repo / 'paper/draft/tables/manifest.json').read_text())
        expected = json.loads((repo / 'reproduction/expected_tables.json').read_text())
        assert manifest['fragments'] == expected, 'Rebuilt tables differ from the submission'
        result = dict(status='PASS', evidence_files_verified=count, evidence_sha256=metadata['sha256'],
                      rebuilt_tables=len(expected), all_table_hashes_match=True,
                      renode_runs=0, seconds=round(time.monotonic() - start, 3),
                      python=sys.version.split()[0])
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
