#!/usr/bin/env python3
"""Package a checked six-page v4 manuscript and its new control evidence."""
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = ROOT/'submission_assets/course-paper-2026-11-11-v3'
OUT = ROOT/'submission_assets/course-paper-2026-11-12-v4'
JOB = '3578143'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())

def add_zip(path, files, extras=None):
    extras = extras or {}
    hashes = {}
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for file in sorted(set(files)):
            rel=str(file.relative_to(ROOT))
            data=file.read_bytes()
            hashes[rel]=hashlib.sha256(data).hexdigest()
            z.writestr(rel,data)
        for name,data in extras.items():z.writestr(name,data)
        z.writestr('SOURCE_SHA256.json',json.dumps(hashes,indent=2,sort_keys=True)+'\n')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(name)).hexdigest()==digest for name,digest in hashes.items())
    return hashes

def main():
    numbers=read(HERE/'manuscript_numbers_v4.json')
    control=read(HERE/f'verified-{JOB}-v1/verification.json')
    assert numbers['status']=='PASS' and numbers['original_table_hashes_match']==8
    assert numbers['citation_keys_resolve']==13 and numbers['counter_table_hash_matches']
    assert control['job_complete'] and control['all_qualified'] and control['qualified_count']==11
    tex=ROOT/'paper/draft/main.tex';pdf=ROOT/'paper/draft/main.pdf'
    assert numbers['manuscript_sha256']==sha(tex) and pdf.stat().st_mtime>=tex.stat().st_mtime
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    pages=int(re.search(r'^Pages:\s+(\d+)$',info,re.M).group(1))
    assert pages<=6 and pages>=1 and 'Page size:       612 x 792 pts (letter)' in info
    log=(ROOT/'paper/draft/main.log').read_text()
    assert not any(term in log for term in ('Overfull ','Undefined control sequence','Citation `','Reference `'))
    renders=[HERE/'rendered'/f'final-page-{i}.png' for i in range(1,pages+1)]
    assert all(p.is_file() for p in renders)
    validation=dict(status='PASS',date='2026-11-12',pdf_sha256=sha(pdf),tex_sha256=sha(tex),
                    pdf_pages_including_references=pages,all_pages_rendered_and_inspected=True,
                    overfull_boxes=0,unresolved_citation_or_reference_diagnostics=0,
                    original_tables_rebuilt_and_hash_matched=8,numeric_claims_checked=numbers['numeric_claims'],
                    counter_control_job=JOB,counter_control_qualified=True,
                    bracketed_processes=control['qualified_count'],historical_18_ms_control_still_failed=True)
    (HERE/'final_validation_v4.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
    OUT.mkdir(parents=True,exist_ok=False)
    old_zip=OLD/'clock-sensitive-waits-v3-source.zip'
    with zipfile.ZipFile(old_zip) as z:
        previous=[n for n in z.namelist() if n not in ('README-MANUSCRIPT.txt','SOURCE_SHA256.json')]
    files=[ROOT/n for n in previous]
    files += [tex,ROOT/'Makefile']
    for rel in ('harness/tacc_bracket_control','subjects/counter_bracket_20261112_v1'):
        files += [p for p in (ROOT/rel).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [HERE/n for n in ('PLAN.md','PROTOCOL.md','STATUS.md','CLAIM_AUDIT.md',
                               'verify_return.py','verify_manuscript_v4.py','package_release_v4.py',
                               'manuscript_numbers_v4.json','claim_to_evidence_v4.csv','final_validation_v4.json')]
    files += [p for p in (HERE/'packet').rglob('*') if p.is_file()]
    files += [p for p in (HERE/'submission-returned-v1').rglob('*') if p.is_file()]
    files += [HERE/f'sacct-{JOB}-terminal.json',HERE/f'verified-{JOB}-v1/verification.json']
    assert all(p.is_file() for p in files)
    readme=(f'# Course manuscript v4, 2026-11-12\n\nThe PDF has {pages} pages including references. '
            f'The preregistered 11-process bracketed control is archived under job {JOB}; '
            'the earlier 18-ms control violation remains in the record. '
            'The new control checks oscillator activation under the pinned simulator, not hardware or fault prevalence.\n\n'
            'To rebuild the original tables, obtain the unchanged v1 evidence archive and run '
            '`make course-tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz` '
            'from the tagged checkout after extracting this source ZIP. The supplemental ZIP holds raw job archives.\n')
    source_zip=OUT/'clock-sensitive-waits-v4-source.zip'
    source_hashes=add_zip(source_zip,files,{'README-MANUSCRIPT.txt':readme})
    with zipfile.ZipFile(OLD/'clock-sensitive-waits-v3-supplemental-evidence.zip') as z:
        prior={n:z.read(n) for n in z.namelist() if n!='SOURCE_SHA256.json'}
    raw=HERE/f'returned-{JOB}-v1'
    new_files=[raw/f'{JOB}-bracket-control{suffix}' for suffix in
               ('.tar.gz','.tar.gz.sha256','.manifest.json.gz','.json')]
    assert all(p.is_file() for p in new_files)
    supplement=OUT/'clock-sensitive-waits-v4-supplemental-evidence.zip'
    with zipfile.ZipFile(supplement,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in prior.items():z.writestr(name,data)
        for file in new_files:z.write(file,str(file.relative_to(ROOT)))
    with zipfile.ZipFile(supplement) as z:assert z.testzip() is None
    for src,name in ((pdf,'clock-sensitive-waits-v4.pdf'),(tex,'main-v4.tex'),
                     (HERE/'CLAIM_AUDIT.md','CLAIM_AUDIT.md'),
                     (HERE/'final_validation_v4.json','final_validation_v4.json')):
        shutil.copyfile(src,OUT/name)
    (OUT/'RELEASE_NOTES.md').write_text(
        '# Course paper v4: clock-sensitive wait repair\n\n'
        f'Five-page final report (six-page limit), with {numbers["numeric_claims"]} audited claims. '
        'The original six sensitive subjects pass all 102 tested legal settings after repair and retain measured slow-fault detection. '
        'A fourth upstream counter case also passes all 102 legal settings after three repairs.\n\n'
        'A new preregistered, 11-process bracketed rate control qualifies the modeled 10/32/64-kHz inputs. '
        'At the selected 10-kHz fault, naive extension accepts the fourth case while right-sizing and polling reject it. '
        'The earlier five-tick control still violates its stricter preregistered bound by 18 ms; its exact timing remains unexplained. '
        'The full counter application also retains downstream failures, and no same-setting flakiness is claimed.\n\n'
        'Assets include the PDF, TeX, source ZIP, supplemental raw evidence ZIP, claim audit, validation record and SHA256SUMS. '
        'The original evidence v1 and manuscript v3 releases remain unchanged.\n')
    assets=[p for p in OUT.iterdir() if p.is_file()]
    (OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(assets)))
    (HERE/'release_assets_v4.json').write_text(json.dumps(dict(status='PASS',
        source_entries_verified=len(source_hashes),supplemental_archives_verified=len(prior)+len(new_files),
        assets={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in assets}),indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(output=str(OUT),pages=pages,source_entries=len(source_hashes),assets=len(assets)+1),indent=2))

if __name__=='__main__':main()
