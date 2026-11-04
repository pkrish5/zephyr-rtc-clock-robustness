#!/usr/bin/env python3
"""Create only the new manuscript assets; never rewrite the evidence archive."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'submission_assets/course-paper-2026-11-04-v2';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
validated=json.loads((HERE/'final_validation.json').read_text())
assert sha(ROOT/'paper/draft/main.pdf')==validated['pdf_sha256']
assert sha(ROOT/'paper/draft/main.tex')==validated['tex_sha256']
assert sha(ROOT/'submission_assets/rtc-submission-evidence-v1.tar.gz')=='805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921'
files=[ROOT/'paper/draft/main.tex',ROOT/'paper/draft/refs.bib',ROOT/'DATA.md',ROOT/'Makefile']
files+=sorted((ROOT/'paper/draft/tables').glob('*.tex'))
for name in ['build_subject_tables.py','audit_paired_records.py','audit_hsi_context.py','verify_manuscript.py','CLAIM_AUDIT.md','claim_to_evidence.csv','manuscript_numbers_v2.json','paired_and_scope_audit.json','subject_table_audit.json','hsi_summary.json','citation_url_audit.json','final_validation.json','clean_clone_test.json','clean_clone_course_tables.txt']:
 files.append(HERE/name)
readme='''# Focused course manuscript v2, 2026-11-04

This bundle contains the current TeX, inline references, all table fragments
needed to typeset it, and its claim/reproduction audit. The PDF is a separate
asset named clock-sensitive-waits-v2.pdf. All units in the paper are virtual
seconds or specified oscillator Hz/kHz, not host wall time.

Typeset paper/draft/main.tex with acmart and a normal LaTeX compiler (tested with
Tectonic0.17.0). Relative table paths resolve from paper/draft/.

For complete data reproduction, clone the repository at tag
course-paper-2026-11-04-v2, obtain the unchanged evidence archive from
course-submission-2026-11-03-v1, and run:

make course-tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz

Repository: https://github.com/pkrish5/zephyr-rtc-clock-robustness
Current manuscript release: https://github.com/pkrish5/zephyr-rtc-clock-robustness/releases/tag/course-paper-2026-11-04-v2
Unchanged evidence release: https://github.com/pkrish5/zephyr-rtc-clock-robustness/releases/tag/course-submission-2026-11-03-v1
Evidence SHA256:805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921

The old evidence release contains an older PDF. It is not this manuscript.
The source ZIP is a typesetting/audit bundle, not a second copy of raw evidence.
'''
zip_path=OUT/'clock-sensitive-waits-v2-source.zip'
expected={str(p.relative_to(ROOT)):sha(p) for p in files}
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:
  info=zipfile.ZipInfo(str(p.relative_to(ROOT)),date_time=(2026,11,4,12,0,0)); info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
 z.writestr('README-MANUSCRIPT.txt',readme)
 z.writestr('SOURCE_SHA256.json',json.dumps(expected,indent=2,sort_keys=True)+'\n')
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for path,h in expected.items():assert hashlib.sha256(z.read(path)).hexdigest()==h
for src,name in [(ROOT/'paper/draft/main.pdf','clock-sensitive-waits-v2.pdf'),(ROOT/'paper/draft/main.tex','main-v2.tex'),(HERE/'CLAIM_AUDIT.md','CLAIM_AUDIT.md'),(HERE/'final_validation.json','final_validation.json'),(HERE/'clean_clone_test.json','clean_clone_test.json')]:shutil.copyfile(src,OUT/name)
assets=[zip_path]+[OUT/n for n in ['clock-sensitive-waits-v2.pdf','main-v2.tex','CLAIM_AUDIT.md','final_validation.json','clean_clone_test.json']]
(OUT/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(assets)))
(HERE/'release_assets.json').write_text(json.dumps(dict(assets={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in assets},source_entries_verified=len(expected),old_evidence_unchanged=True),indent=2)+'\n')
print(OUT)
