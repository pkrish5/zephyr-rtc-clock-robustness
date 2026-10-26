#!/usr/bin/env python3
"""One-time recovery; execute only after explicit user approval of this exception."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
root=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
assert Path.cwd().resolve()==root
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
incoming=subprocess.check_output(['git','rev-parse','origin/main'],text=True).strip()
assert head=='eedb8b1e95f5bc81d994096aebfbcd11a99923bf'
assert incoming=='abff0ced99983e9b3f60dc35ee5209c8a065f831'
tracked=set(subprocess.check_output(['git','ls-files'],text=True).splitlines())
changed=subprocess.check_output(['git','diff','--name-only','HEAD..origin/main'],text=True).splitlines()
tracked_targets=['notes/s2_qualification_2026-10-25/STATUS.md','paper/DESIGN.md']
paths=tracked_targets+[p for p in changed if p not in tracked and Path(p).is_file()]
assert len(paths)==28
h=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
for rel in paths:
    p=root/rel;p.resolve().relative_to(root)
    actual=p.read_bytes();wanted=subprocess.check_output(['git','show','origin/main:'+rel])
    assert actual==wanted,rel
    rows.append(dict(path=rel,sha256=h(actual),size_bytes=len(actual),tracked=rel in tracked))
core=['harness/tacc_s2/worker.py','harness/tacc_s2/task.sh','harness/tacc_s2/control.py']
core_before={p:h((root/p).read_bytes()) for p in core}
backup=root/'tacc_work/20261026-git-checkout-recovery-v1'
backup.mkdir(parents=True,exist_ok=False)
def save(name,x):
    with (backup/name).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
save('before.json',dict(head=head,incoming=incoming,files=rows,core_sha256=core_before))
for r in rows:
    src=root/r['path'];dst=backup/'preserved'/r['path'];dst.parent.mkdir(parents=True,exist_ok=True)
    if r['tracked']:shutil.copy2(src,dst)
    else:src.rename(dst)
    assert h(dst.read_bytes())==r['sha256']
# Explicit user-approved exception, two paths only, after byte-verified backups.
restore=subprocess.run(['git','restore','--source=HEAD','--worktree','--',*tracked_targets],capture_output=True,text=True)
save('restore.json',dict(returncode=restore.returncode,stdout=restore.stdout,stderr=restore.stderr))
assert restore.returncode==0
pull=subprocess.run(['git','pull','--ff-only'],capture_output=True,text=True)
save('pull.json',dict(returncode=pull.returncode,stdout=pull.stdout,stderr=pull.stderr))
if pull.returncode:
    raise SystemExit('STOP: pull failed; all backed-up bytes retained; no tests/jobs launched')
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==incoming
for r in rows:assert h((root/r['path']).read_bytes())==r['sha256'],r['path']
core_after={p:h((root/p).read_bytes()) for p in core};assert core_after==core_before
save('after.json',dict(head=incoming,all_28_files_match=True,core_sha256=core_after,
    scientific_files_changed=[],new_jobs_submitted=0,backup=str(backup)))
print(json.dumps(dict(recovered=True,head=incoming,files_preserved=28,core_unchanged=True,backup=str(backup))))
