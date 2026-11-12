#!/usr/bin/env python3
"""One sealed build, nominal gate, and six fault-input counter observations."""
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

PATTERN = re.compile(r'BRACKET a0=(\d+) b0=(\d+) a1=(\d+) b1=(\d+) v0=(\d+) v1=(\d+) delta=(\d+)')
FREQUENCIES = (10000, 32000, 64000)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()

def read(path): return json.loads(Path(path).read_text())

def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write('\n')

def band(f, low_ms, high_ms):
    denominator = 32000 * 1000
    return f * low_ms // denominator, (f * high_ms + denominator - 1) // denominator

def audit(task, out, plan, build):
    rid = f"f4-bracket-control-{task['condition']}-{task['index']:03d}"
    p = out / 'control/records' / (rid + '.json')
    uart = out / 'control/uart' / (rid + '.log')
    process = out / 'processes/run' / (str(task['index']) + '.json')
    row = dict(index=task['index'], frequency_hz=task['frequency_hz'], status='missing',
               record_sha256=sha(p) if p.exists() else None)
    if not (p.exists() and uart.exists() and process.exists()): return row
    r, pp = read(p), read(process)
    row.update(process_exit=pp['exit_code'], cases=r.get('cases'), error=r.get('error'),
               uart_sha256=sha(uart), outcome=r.get('outcome'), platform_sha256=r.get('platform_sha256'))
    checks = [pp['exit_code'] == 0, r.get('outcome') == 'complete', r.get('application_completed') is True,
              r.get('error') is None, r.get('missing_cases') == [], r.get('duplicate_cases') == [],
              r.get('cases') == [{'case':'ref_counter_bracket.test_rate_window','status':'pass'}],
              r.get('frequency_hz') == task['frequency_hz'], r.get('elf_sha256') == build['elf_sha256'],
              r.get('container_sha256') == plan['image_sha256'],
              r.get('log_sha256',{}).get('uart') == sha(uart),
              r.get('plan_sha256') == sha(out / 'job_metadata/plan.json')]
    platform = out / 'control/platforms' / (rid + '.repl')
    checks.append(platform.exists() and r.get('platform_sha256') == sha(platform))
    if not all(checks):
        row['status'] = 'failed_metadata_or_verdict'
        return row
    hits = PATTERN.findall(uart.read_text(errors='replace'))
    if len(hits) != 1:
        row['status'] = 'failed_uart_line'
        return row
    a0,b0,a1,b1,v0,v1,d = map(int,hits[0])
    row['measurement'] = dict(a0=a0,b0=b0,a1=a1,b1=b1,v0=v0,v1=v1,delta=d)
    if not (a0 <= b0 <= a1 <= b1 and 9500 <= a1-b0 <= 11500 and d == ((v1-v0) & 0xffffffff)):
        row['status'] = 'failed_timestamps_or_delta'
        return row
    lo,hi = a1-b0-2,b1-a0+2
    row['bands'] = {str(f): band(f,lo,hi) for f in FREQUENCIES}
    assigned = row['bands'][str(task['frequency_hz'])]
    row['status'] = ('qualified' if assigned[0] <= d <= assigned[1] and
                     all(not (lower <= d <= upper) for f,(lower,upper) in
                         ((f,row['bands'][str(f)]) for f in FREQUENCIES if f != task['frequency_hz']))
                     else 'failed_band')
    return row

def main():
    assert os.environ['SLURM_JOB_PARTITION'] == 'development'
    assert os.environ['SLURM_JOB_ACCOUNT'].upper() == 'CCR26073'
    repo = Path(os.environ['RTC_REPO'])
    packet = Path(os.environ['RTC_BRACKET_PACKET'])
    original = Path(os.environ['RTC_PRIMARY_BUNDLE'])
    image = Path(os.environ['RTC_IMAGE'])
    out = Path(os.environ['RTC_JOB_OUTPUT'])
    base = Path(os.environ['RTC_JOB_BASE'])
    ep = packet / 'execution.json'
    assert sha(ep) == (packet / 'execution.sha256').read_text().split()[0]
    e = read(ep)
    assert sha(packet/'plan.json') == e['plan_sha256']
    assert sha(packet.parent/'PROTOCOL.md') == e['protocol_sha256']
    assert sha(original/'plan.json') == e['original_counter_plan_sha256']
    assert sha(image) == e['image_sha256']
    for rel,digest in e['code_sha256'].items(): assert sha(repo/rel) == digest, rel
    for rel,digest in e['source_sha256'].items(): assert sha(repo/rel) == digest, rel
    plan = read(packet/'plan.json')
    assert len(plan['tasks']) == 11
    assert [t['frequency_hz'] for t in plan['tasks']] == [32000]*5+[10000]*3+[64000]*3
    bundle = base / 'bracket-bundle'
    bundle.mkdir()
    for rel,digest in plan['input_sha256'].items():
        src = original / rel
        assert sha(src) == digest, rel
        dest = bundle / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src,dest)
        assert sha(dest) == digest, rel
    shutil.copyfile(packet/'plan.json',bundle/'plan.json')
    shutil.copyfile(packet/'plan.sha256',bundle/'plan.sha256')
    (bundle/plan['output_relative']).mkdir(parents=True)
    shutil.copyfile(packet/'plan.json',out/'job_metadata/plan.json')
    shutil.copyfile(ep,out/'job_metadata/execution.json')
    for rel in e['source_sha256']:
        dest=out/'new_sources'/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(repo/rel,dest)
    env=dict(os.environ,RTC_REFERENCE_BUNDLE=str(bundle),RTC_REFERENCE_OUT_REL=plan['output_relative'],
             RTC_REFERENCE_PLAN_SHA256=e['plan_sha256'])
    task_script=repo/'harness/tacc_bracket_control/task.sh'
    phase_codes={}
    phases=[]
    try:
        phases.append('build')
        phase_codes['build']=subprocess.run(['bash',str(task_script),'build','f4-bracket-control'],env=env).returncode
        buildpath=out/'control/builds/f4-bracket-control/build_record.json'
        assert phase_codes['build']==0 and buildpath.exists(), 'build process failed'
        build=read(buildpath)
        assert build['status']=='built' and build['compiled_case_names']==['ref_counter_bracket.test_rate_window']
        def launch(phase,indices):
            folder=out/'launcher'/phase
            folder.mkdir(parents=True)
            jobfile=folder/'jobfile'
            with jobfile.open('x') as stream:
                for index in indices: stream.write(shlex.join(['bash',str(task_script),'run',str(index)])+'\n')
            launch_env=dict(env,LAUNCHER_PPN='32',LAUNCHER_NHOSTS='1',LAUNCHER_LOCALHOST='1',
                            LAUNCHER_SCHED='interleaved',LAUNCHER_BIND='1',LAUNCHER_WORKDIR=str(folder),
                            LAUNCHER_JOB_FILE=str(jobfile),LAUNCHER_LOGFILE=str(folder/'launcher.log'))
            for key in ('LAUNCHER_RMI','LAUNCHER_HOSTFILE','LAUNCHER_RMI_HOSTFILE'):launch_env.pop(key,None)
            phases.append(phase)
            phase_codes[phase]=subprocess.run([str(Path(env['LAUNCHER_DIR'])/'paramrun')],cwd=folder,env=launch_env).returncode
        launch('qualification',range(5))
        nominal=[audit(t,out,plan,build) for t in plan['tasks'][:5]]
        save(out/'qualification.json',dict(rows=nominal,all_qualified=all(r['status']=='qualified' for r in nominal)))
        assert phase_codes['qualification']==0 and all(r['status']=='qualified' for r in nominal), 'nominal gate failed'
        launch('evaluation',range(5,11))
    finally:
        buildpath=out/'control/builds/f4-bracket-control/build_record.json'
        build=read(buildpath) if buildpath.exists() else {}
        rows=[audit(t,out,plan,build) for t in plan['tasks']]
        save(out/'control_summary.json',dict(phases_started=phases,phase_exit_codes=phase_codes,
             rows=rows,all_qualified=all(r['status']=='qualified' for r in rows),
             old_control_replaced=False,primary_records_replaced=False))
        assert sha(image)==e['image_sha256']
        assert sha(original/'plan.json')==e['original_counter_plan_sha256']
        for rel,digest in e['code_sha256'].items(): assert sha(repo/rel)==digest, rel
        for rel,digest in e['source_sha256'].items(): assert sha(repo/rel)==digest, rel

if __name__=='__main__': main()
