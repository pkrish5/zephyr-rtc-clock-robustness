#!/usr/bin/env python3
"""Compute-only coordinator and container-binding fixture; no simulation/build."""
import hashlib,json,os,subprocess,signal,time
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

if os.environ['SLURM_JOB_PARTITION']!='development':raise RuntimeError('Development required')
repo=Path(os.environ['WORK']).resolve()/'zephyr-rtc-clock-robustness'
out=Path(os.environ['RTC_RECOVERY_REPORT']).resolve();out.relative_to(Path(os.environ['SCRATCH']).resolve());out.mkdir(exist_ok=False)
EXPECTED = {'harness/tacc_storage/runtime.sh': '94824b806985ec216e3c0b41968ce876a3588eaf73a6fb526d54279b2a933202', 'harness/tacc_storage/run_packed.sh': 'f7b6b6adad43724523834c5dcb7bedad2653a9a6475fb7ca751273b98f373f29', 'harness/tacc_storage/check_headroom.py': '654e8303c0c70e85d651b6d68019ae67349001679ffe6f7607c974f4609ca5a3', 'harness/tacc_storage/protected_check.py': '43989e19b5b5e37771082c1ffb3f2ec7d41c62b7c7b77a18739a1f9733aaa150', 'harness/tacc_storage/publish.py': 'a9945300ba607cd649135ceadcbc5d667391288300ea8d757f270b0dda7ac3b5', 'harness/tacc_storage/archive.py': '35170da78ae6a0d7c0f863ba204f286a0fa2e1a1f8e914effad92a1adf181b6a'}
for rel,digest in EXPECTED.items():
    if sha(repo/rel)!=digest:raise RuntimeError('Infrastructure code differs: '+rel)
image=repo/'tacc_work/20261023-v10/images/rtc-ls6-v1.sif'
digest=sha(image)
if digest!='94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1':raise RuntimeError('Calibrated image differs')
primary=repo/'tacc_work/20261026-s2-primary-v1/bundle'
if sha(primary/'plan.json')!='719b3bc42f2b93f44455a11eca3eacd69eacbbf4e8c714b90300d5a8343d0612':raise RuntimeError('Primary plan differs')
relative=json.loads((primary/'plan.json').read_text())['output_relative']
fixture=out/'fixture.py'
with fixture.open('x') as f:f.write('import json,os,hashlib\nfrom pathlib import Path\nchecks={"primary":bool(os.statvfs("/primary").f_flag & os.ST_RDONLY),"builds":bool(os.statvfs(os.environ["RTC_FIXTURE_BUILDS"]).f_flag & os.ST_RDONLY),"new_output":not bool(os.statvfs(os.environ["RTC_FIXTURE_OUTPUT"]).f_flag & os.ST_RDONLY)}\nif not all(checks.values()):raise RuntimeError("Incorrect read-only/writable storage bindings: "+repr(checks))\nplan=Path("/primary/plan.json").read_bytes()\nif hashlib.sha256(plan).hexdigest()!="719b3bc42f2b93f44455a11eca3eacd69eacbbf4e8c714b90300d5a8343d0612":raise RuntimeError("Primary plan differs")\nout=Path(os.environ["RTC_FIXTURE_OUTPUT"])/"fixture.json"\nwith out.open("x") as f:json.dump(dict(dataset_role="infrastructure fixture only",new_firmware_executions=0,node=os.environ["RTC_NODE_NAME"],job_id=os.environ["SLURM_JOB_ID"],container_sha256=os.environ["RTC_CONTAINER_SHA256"],apptainer_version=os.environ["RTC_APPTAINER_VERSION"],bindings=checks,primary_plan_sha256=hashlib.sha256(plan).hexdigest()),f,indent=2)\nprint("Container binding fixture written; no firmware execution.",flush=True)\n(Path(os.environ["RTC_FIXTURE_OUTPUT"])/"fixture.ready").write_text("ready\\n")\nimport time\nwhile True:\n    with (Path(os.environ["RTC_FIXTURE_OUTPUT"])/"heartbeat.bin").open("ab") as f:f.write(b"tick\\n")\n    time.sleep(0.2)\n')
env=dict(os.environ,RTC_REPO=str(repo),RTC_CONTAINER_SHA256=digest,RTC_IMAGE=str(image),
         RTC_STORAGE_PRIMARY_BUNDLE=str(primary),RTC_STORAGE_FIXTURE_SCRIPT=str(fixture),
         RTC_FIXTURE_OUTPUT='/bundle/'+relative,RTC_FIXTURE_BUILDS='/bundle/'+relative+'/builds',RTC_FIXTURE_REL=relative)
command=['bash','-l',str(repo/'harness/tacc_storage/run_packed.sh'),'storage-smoke','bash','-l','-c','set -euo pipefail\nprivate="$RTC_NODE_BASE/storage-fixture"\nmkdir -p "$private/home" "$private/tmp" "$private/work" "$RTC_JOB_OUTPUT/builds"\nexec apptainer exec --cleanenv --containall --home "$private/home:/home/rtc" --pwd /bundle \\\n --bind "$RTC_STORAGE_PRIMARY_BUNDLE:/primary:ro" --bind "$RTC_STORAGE_PRIMARY_BUNDLE:/bundle:ro" \\\n --bind "$RTC_JOB_OUTPUT:$RTC_FIXTURE_OUTPUT:rw" \\\n --bind "$RTC_STORAGE_PRIMARY_BUNDLE/$RTC_FIXTURE_REL/builds:$RTC_FIXTURE_BUILDS:ro" \\\n --bind "$RTC_STORAGE_FIXTURE_SCRIPT:/fixture.py:ro" \\\n --bind "$private/tmp:/tmp:rw" --bind "$private/work:/var/tmp:rw" \\\n --env "RTC_FIXTURE_OUTPUT=$RTC_FIXTURE_OUTPUT" --env "RTC_FIXTURE_BUILDS=$RTC_FIXTURE_BUILDS" \\\n --env "RTC_NODE_NAME=$SLURMD_NODENAME" --env "SLURM_JOB_ID=$SLURM_JOB_ID" \\\n --env "RTC_CONTAINER_SHA256=$RTC_CONTAINER_SHA256" --env "RTC_APPTAINER_VERSION=$RTC_APPTAINER_VERSION" \\\n "$RTC_IMAGE" /opt/rtc-python/bin/python /fixture.py\n']
proc=subprocess.Popen(command,env=env)
physical=Path(os.environ['SCRATCH'])/'zephyr-rtc-clock-robustness/jobs'/os.environ['SLURM_JOB_ID']/'output'
deadline=time.monotonic()+900
while not (physical/'fixture.ready').exists():
    if proc.poll() is not None:raise RuntimeError('Coordinator exited before binding fixture was ready')
    if time.monotonic()>deadline:raise RuntimeError('Storage fixture preflight exceeded limit')
    time.sleep(0.2)
if not all(json.loads((physical/'fixture.json').read_text())['bindings'].values()):raise RuntimeError('Binding fixture failed')
proc.send_signal(signal.SIGUSR1)
status=proc.wait(timeout=900)
if status!=124:raise RuntimeError('Expected controlled interrupted exit124, got '+str(status))
size=(physical/'heartbeat.bin').stat().st_size
time.sleep(3)
if (physical/'heartbeat.bin').stat().st_size!=size:raise RuntimeError('A detached writer survived publication')
job=os.environ['SLURM_JOB_ID']
receipt=repo/'tacc_work/packed-results'/(job+'-storage-smoke.json')
r=json.loads(receipt.read_text())
if r['output_state']!='interrupted' or not r['exact_archive_coverage'] or not r['extracted_stream_hashes_match']:
    raise RuntimeError('Coordinator publication failed')
verification=dict(job_id=job,receipt=str(receipt),archive_sha256=r['archive_sha256'],controlled_interrupt_preserved=True,writer_stopped=True,new_firmware_executions=0,new_builds=0,coordinator_code_sha256=EXPECTED)
for dest in (out/'complete.json',receipt.with_name(job+'-storage-smoke.verification.json')):
    with dest.open('x') as f:json.dump(verification,f,indent=2);f.write('\n')
print(json.dumps(dict(job_id=job,receipt=str(receipt),new_firmware_executions=0)))
