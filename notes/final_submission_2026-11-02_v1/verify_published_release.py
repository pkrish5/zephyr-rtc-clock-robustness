#!/usr/bin/env python3
"""Read-only public release/download verification; no GitHub credential used."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--clone', type=Path, required=True)
    a = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    # This script lives in notes/<dated namespace>.
    assert (repo / 'reproduction/evidence.json').is_file()
    a.out.mkdir(parents=True, exist_ok=False)
    tag = 'course-submission-2026-11-03-v1'
    commit = '67ecb3d90e93895d5c5073ca6e8b78e9c8d1a05d'
    api = 'https://api.github.com/repos/pkrish5/zephyr-rtc-clock-robustness/releases/tags/' + tag
    def get(url):
        return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'rtc-submission-verifier',
                                      'Accept': 'application/vnd.github+json'}), timeout=45)
    with get(api) as stream:
        release = json.load(stream)
    assert release['tag_name'] == tag and not release['draft'] and not release['prerelease']
    expected = {'main.pdf': 'paper/draft/main.pdf',
                'clean-clone-test.json': 'submission_assets/clean-clone-test.json',
                'rtc-submission-evidence-v1.tar.gz.sha256': 'submission_assets/rtc-submission-evidence-v1.tar.gz.sha256'}
    checks = []
    for asset in release['assets']:
        if asset['name'] not in expected:
            continue
        target = a.out / asset['name']
        with get(asset['browser_download_url']) as stream, target.open('xb') as output:
            while block := stream.read(1048576):
                output.write(block)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        assert digest == hashlib.sha256((repo / expected[asset['name']]).read_bytes()).hexdigest()
        assert asset['digest'] == 'sha256:' + digest
        checks.append(dict(name=asset['name'], bytes=target.stat().st_size, sha256=digest,
                           public_download_matches_local=True))
    assert len(checks) == 3
    metadata = json.loads((repo / 'reproduction/evidence.json').read_text())
    asset = next(r for r in release['assets'] if r['name'] == metadata['filename'])
    assert asset['size'] == metadata['bytes'] and asset['digest'] == 'sha256:' + metadata['sha256']
    result = dict(release_url=release['html_url'], tag=tag, release_id=release['id'],
                  published_at=release['published_at'], draft=False,
                  assets=[{k: r[k] for k in ('name', 'size', 'digest', 'browser_download_url')} for r in release['assets']],
                  public_download_checks=checks, authentication_used_for_downloads=False,
                  tls_certificate_verification=True)
    (a.out / 'release_verification.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('Published release and three small public downloads verified.', flush=True)
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.clone, text=True).strip() == commit
    with (a.out / 'network_make_tables.txt').open('x') as output:
        proc = subprocess.run(['make', 'tables', 'PYTHON=' + sys.executable], cwd=a.clone,
                              env=os.environ.copy(), stdout=output, stderr=subprocess.STDOUT)
    log = (a.out / 'network_make_tables.txt').read_text()
    print(log[-2000:], flush=True)
    assert proc.returncode == 0, 'Public-download table rebuild failed; see log'
    changes = subprocess.check_output(['git', 'diff', '--name-only'], cwd=a.clone, text=True).splitlines()
    # Full-precision illustrative CDF CSV bytes may differ between Python math
    # runtimes. The manuscript fragments must still match exactly; preserve the
    # newly derived manifest rather than hiding that provenance difference.
    assert set(changes) <= {'paper/draft/tables/manifest.json'}, changes
    provenance_difference = None
    if changes:
        name = changes[0]
        before = json.loads(subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=a.clone, text=True))
        after = json.loads((a.clone / name).read_text())
        assert all(before[k] == after[k] for k in before if k != 'source_sha256')
        changed_sources = [k for k in before['source_sha256'] if before['source_sha256'][k] != after['source_sha256'][k]]
        assert changed_sources == ['sensitivity.csv'], changed_sources
        provenance_difference = dict(file=name, changed_derived_csv_sha256=changed_sources,
                                     table_fragment_hashes_unchanged=True)
    rebuild = json.loads(log[log.index('{'):])
    rebuild.update(submission_commit=commit, release_url=release['html_url'], cached_archive_supplied=False,
                   authentication_used=False, tracked_clone_changed_files=changes,
                   derived_provenance_difference=provenance_difference,
                   tls_certificate_verification=True, ca_bundle=os.environ.get('SSL_CERT_FILE', 'runtime default'))
    (a.out / 'network_make_tables.json').write_text(json.dumps(rebuild, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
