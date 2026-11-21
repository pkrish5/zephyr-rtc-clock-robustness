#!/usr/bin/env python3
"""Package the checked six-page v5 manuscript and the counter sweep evidence.

Derived from notes/course_improvement_2026-11-12_v1/package_release_v4.py.
Writes submission_assets/course-paper-2026-11-21-v5/ (refuses to overwrite).
"""
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = ROOT/'submission_assets/course-paper-2026-11-12-v4'
OUT = ROOT/'submission_assets/course-paper-2026-11-21-v5'
TAG = 'course-paper-2026-11-21-v5'
NOTES = ['notes/counter_phase_qualification_2026-11-17_v1', 'notes/counter_natural_sweep_2026-11-19_v1',
         'notes/counter_natural_recovery_2026-11-20_v1', 'notes/manuscript_v5_2026-11-21_v1']
RAW = [('notes/counter_phase_qualification_2026-11-17_v1/returned-3589708-v1', '3589708-phase-qualification'),
       ('notes/counter_natural_sweep_2026-11-19_v1/returned-3596807-v1', '3596807-natural-sweep'),
       ('notes/counter_natural_recovery_2026-11-20_v1/returned-3598828-v1', '3598828-natural-recovery')]


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def add_zip(path, files, extras=None):
    extras = extras or {}
    hashes = {}
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for file in sorted(set(files)):
            rel = str(file.relative_to(ROOT))
            data = file.read_bytes()
            hashes[rel] = hashlib.sha256(data).hexdigest()
            z.writestr(rel, data)
        for name, data in extras.items():
            z.writestr(name, data)
        z.writestr('SOURCE_SHA256.json', json.dumps(hashes, indent=2, sort_keys=True)+'\n')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(name)).hexdigest() == digest for name, digest in hashes.items())
    return hashes


def tracked(rel):
    out = subprocess.check_output(['git', 'ls-files', rel], cwd=ROOT, text=True).split()
    return [ROOT/p for p in out]


def main():
    numbers = read(HERE/'manuscript_numbers_v5.json')
    assert numbers['status'] == 'PASS' and numbers['original_table_hashes_match'] == 8
    assert numbers['citation_keys_resolve'] == 17 and numbers['counter_table_hash_matches'] and numbers['sweep_table_rebuilt']
    tex = ROOT/'paper/draft/main.tex'; pdf = ROOT/'paper/draft/main.pdf'
    assert numbers['manuscript_sha256'] == sha(tex) and pdf.stat().st_mtime >= tex.stat().st_mtime
    assert TAG in tex.read_text()
    log = (ROOT/'paper/draft/main.log').read_text()
    pages = int(re.search(r'Output written on main\.pdf \((\d+) pages', log).group(1))
    assert 1 <= pages <= 6
    assert not any(term in log for term in ('Overfull ', 'Undefined control sequence', 'Citation `', 'Reference `'))
    renders = [HERE/'rendered'/f'final-page-{i}.png' for i in range(1, pages+1)]
    assert all(p.is_file() for p in renders)
    sweep = read(ROOT/'notes/counter_natural_recovery_2026-11-20_v1/report-3598828-v1/summary.json')
    assert sweep['verified_complete'] and sweep['counts']['primary']['selected'] == {'pass': 38, 'fail': 60}
    validation = dict(status='PASS', date='2026-11-21', tag=TAG, pdf_sha256=sha(pdf), tex_sha256=sha(tex),
                      pdf_pages_including_references=pages, all_pages_rendered_and_inspected=True,
                      overfull_boxes=0, unresolved_citation_or_reference_diagnostics=0,
                      original_tables_rebuilt_and_hash_matched=8, numeric_claims_checked=numbers['numeric_claims'],
                      sweep_job='3598828', sweep_primary_selected={'pass': 38, 'fail': 60, 'missing': 0},
                      failed_phase_qualification_job='3589708', failed_metadata_attempt_job='3596807',
                      historical_18_ms_control_still_failed=True,
                      page_size_points_ghostscript=[612, 792])
    (HERE/'final_validation_v5.json').write_text(json.dumps(validation, indent=2, sort_keys=True)+'\n')

    OUT.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(OLD/'clock-sensitive-waits-v4-source.zip') as z:
        previous = [n for n in z.namelist() if n not in ('README-MANUSCRIPT.txt', 'SOURCE_SHA256.json')]
    files = [ROOT/n for n in previous if (ROOT/n).is_file()]
    dropped = [n for n in previous if not (ROOT/n).is_file()]
    files += [tex, ROOT/'Makefile', ROOT/'DATA.md', ROOT/'README.md']
    files += tracked('paper/draft/tables')
    for rel in NOTES:
        files += [p for p in tracked(rel) if p.is_file()]
    files += [HERE/'final_validation_v5.json'] + renders
    assert all(p.is_file() for p in files)
    readme = (f'# Course manuscript v5, 2026-11-21\n\nThe PDF has {pages} pages including references. '
              'It adds a prespecified natural-phase counter deadline sweep (job 3598828: seven waits x 14 rates, '
              '98 primary runs, 38 pass / 60 fail, 0 missing). The failed controlled-phase qualification (3589708) '
              'and the failed metadata attempt (3596807) are retained. Phase was not measured.\n\n'
              'To rebuild every table and rerun the 52-claim audit, obtain the unchanged v1 evidence archive and run '
              '`make course-tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz` '
              f'from the `{TAG}` checkout. `make counter-sweep` checks the sweep table alone. '
              'The supplemental ZIP holds raw job archives.\n')
    source_zip = OUT/'clock-sensitive-waits-v5-source.zip'
    source_hashes = add_zip(source_zip, files, {'README-MANUSCRIPT.txt': readme})

    with zipfile.ZipFile(OLD/'clock-sensitive-waits-v4-supplemental-evidence.zip') as z:
        prior = {n: z.read(n) for n in z.namelist() if n != 'SOURCE_SHA256.json'}
    new_files = []
    for rel, stem in RAW:
        group = [ROOT/rel/f'{stem}{s}' for s in ('.tar.gz', '.tar.gz.sha256', '.manifest.json.gz', '.json')]
        assert all(p.is_file() for p in group)
        expected = (ROOT/rel/f'{stem}.tar.gz.sha256').read_text().split()[0]
        assert sha(group[0]) == expected, f'{stem} archive hash mismatch'
        new_files += group
    supplement = OUT/'clock-sensitive-waits-v5-supplemental-evidence.zip'
    with zipfile.ZipFile(supplement, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in prior.items():
            z.writestr(name, data)
        for file in new_files:
            z.write(file, str(file.relative_to(ROOT)))
    with zipfile.ZipFile(supplement) as z:
        assert z.testzip() is None

    for src, name in ((pdf, 'clock-sensitive-waits-v5.pdf'), (tex, 'main-v5.tex'),
                      (HERE/'CLAIM_AUDIT.md', 'CLAIM_AUDIT.md'),
                      (HERE/'final_validation_v5.json', 'final_validation_v5.json')):
        shutil.copyfile(src, OUT/name)
    (OUT/'RELEASE_NOTES.md').write_text(
        '# Course paper v5: clock-sensitive wait repair\n\n'
        f'Six-page report (including references), with {numbers["numeric_claims"]} audited numeric claims.\n\n'
        'New in v5: a prespecified natural-phase deadline sweep of the full F4 counter application (job 3598828). '
        'Seven waits (original 3 s; fixed 6, 8, 10, 13 s; right-sized 7.648 s fixed and polling) each ran at 14 clock rates '
        '(4-14 kHz, 16, 17, 32 kHz): 98 primary runs, 38 pass / 60 fail, 0 missing; 35 nominal gates pass and 7 replays agree. '
        'All 76 cells predicted to be all-accept or all-reject match; all 22 phase-dependent cells reject. '
        'Longer waits accept 0, 1, 3, 3, 4, 6 and 8 of 12 out-of-envelope slow rates; right-sizing still accepts 13, 14 and 16 kHz. '
        'Phase was not measured, so these brackets are likely optimistic for other phases.\n\n'
        'Retained negative results: the controlled-phase qualification (3589708) failed with 9 of 42 late arrivals, '
        'so no controlled-phase sweep ran; a first sweep attempt (3596807) lost its records to a metadata defect and remains missing. '
        'The earlier 18-ms control violation remains unexplained.\n\n'
        'Assets: PDF, TeX, source ZIP, supplemental raw evidence ZIP (v4 contents plus the three new job archives), '
        'claim audit, validation record and SHA256SUMS. Earlier releases are unchanged.\n')
    assets = [p for p in OUT.iterdir() if p.is_file()]
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(assets)))
    (HERE/'release_assets_v5.json').write_text(json.dumps(dict(status='PASS', tag=TAG,
        source_entries_verified=len(source_hashes), v4_source_entries_no_longer_present=dropped,
        supplemental_entries=len(prior)+len(new_files),
        assets={p.name: dict(bytes=p.stat().st_size, sha256=sha(p)) for p in assets}), indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(output=str(OUT.relative_to(ROOT)), pages=pages, source_entries=len(source_hashes),
                          dropped=dropped, assets=len(assets)+1), indent=2))


if __name__ == '__main__':
    main()
