#!/usr/bin/env python3
"""Compute-node build-copy audit and Launcher packing; no compilation."""
import argparse,hashlib,json,os,shlex,shutil
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--image',type=Path,required=True)
a=ap.parse_args();p=json.loads((a.bundle/'plan.json').read_text());old=json.loads((a.previous/'plan.json').read_text())
assert os.environ['SLURM_JOB_PARTITION']=='normal' and p['production_authorized']
assert sha(a.bundle/'plan.json')==(a.bundle/'plan.sha256').read_text().split()[0]
assert p['conditional_approval_evidence']['report']['all_15_accepted'] is True
assert sha(a.image)==p['image_sha256']
assert sha(a.previous/'plan.json')==p['conditional_approval_evidence']['qualification_plan_sha256']
assert sha(a.repo/'paper/DESIGN.md')==p['design_sha256']
for rel,d in p['input_sha256'].items():assert sha(a.bundle/rel)==d,rel
for rel,d in p['code_sha256'].items():assert sha(a.repo/rel)==d,rel
out=a.bundle/p['output_relative'];oldout=a.previous/old['output_relative'];audits=[]
for u in p['units']:
    assert u==next(x for x in old['units'] if x['id']==u['id'])
    assert p['boards'][u['board_id']]==old['boards'][u['board_id']]
    src=oldout/'builds'/u['id'];dst=out/'builds'/u['id'];r=json.loads((src/'build_record.json').read_text())
    assert r['status']=='built' and sha(src/'build.log')==r['log_sha256']
    files=['build_record.json','build.log']
    for rel,d in r['build_products_sha256'].items():assert sha(src/'build'/rel)==d;files.append('build/'+rel)
    for rel in files:
        target=dst/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();shutil.copyfile(src/rel,target);assert sha(src/rel)==sha(target)
    # Retain the byte-identical build record's ELF pointer in the new bundle.
    elf=a.previous/r['elf_path'];assert sha(elf)==r['elf_sha256']
    target=a.bundle/r['elf_path'];target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();shutil.copyfile(elf,target);assert sha(target)==r['elf_sha256']
    audits.append(dict(unit_id=u['id'],elf_sha256=r['elf_sha256'],build_record_sha256=sha(src/'build_record.json'),original_build_job=r['slurm_job_id'],byte_identical=True))
jobfile=out/'launcher/primary/jobfile';jobfile.parent.mkdir(parents=True,exist_ok=True)
with jobfile.open('x') as f:
    for t in p['tasks']:f.write(shlex.join(['bash','-l',str(a.repo/'harness/tacc_s2_production/task.sh'),str(t['index'])])+'\n')
save(out/'setup_audit.json',dict(builds=audits,scientific_inputs_changed=[],new_builds=0,actual_partition=os.environ['SLURM_JOB_PARTITION'],slurm_job_id=os.environ['SLURM_JOB_ID'],image_sha256=sha(a.image),plan_sha256=sha(a.bundle/'plan.json'),launcher_lines=len(p['tasks'])))
print('Verified reused scientific inputs; production packing ready.')
