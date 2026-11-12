#!/usr/bin/env python3
"""Independently verify the returned bracket-control archive and its rate claims."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PATTERN = re.compile(r'BRACKET a0=(\d+) b0=(\d+) a1=(\d+) b1=(\d+) v0=(\d+) v1=(\d+) delta=(\d+)')
FREQUENCIES = (10000, 32000, 64000)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()

def read(path): return json.loads(Path(path).read_text())

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--returned', type=Path, required=True)
    ap.add_argument('--job', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    packet = HERE/'packet'
    ep = packet/'execution.json'
    assert sha(ep) == (packet/'execution.sha256').read_text().split()[0]
    e = read(ep)
    assert sha(packet/'plan.json') == e['plan_sha256']
    assert sha(HERE/'PROTOCOL.md') == e['protocol_sha256']
    for group in ('code_sha256','source_sha256'):
        for rel,digest in e[group].items(): assert sha(ROOT/rel) == digest, rel
    plan = read(packet/'plan.json')
    stem = args.job+'-bracket-control'
    receipt = read(args.returned/(stem+'.json'))
    archive = args.returned/(stem+'.tar.gz')
    manifest_file = args.returned/(stem+'.manifest.json.gz')
    assert receipt['slurm_job_id'] == args.job and receipt['account'].upper() == 'CCR26073'
    assert receipt['partition'] == 'development' and receipt['container_sha256'] == e['image_sha256']
    assert sha(archive) == receipt['archive_sha256'] == (args.returned/(stem+'.tar.gz.sha256')).read_text().split()[0]
    assert sha(manifest_file) == receipt['manifest_sha256']
    manifest = json.loads(gzip.decompress(manifest_file.read_bytes()))['files']
    spec = importlib.util.spec_from_file_location('archive_audit',ROOT/'harness/tacc_storage/archive.py')
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.verify(archive,manifest)
    args.out.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive) as tar:
        for item in tar:
            rel=PurePosixPath(item.name)
            assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0]=='output'
            target=args.out/item.name
            if item.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                assert item.isfile()
                target.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(item) as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
    out=args.out/'output'
    assert helper.inventory(out)==manifest
    assert sha(out/'job_metadata/plan.json')==e['plan_sha256']
    assert sha(out/'job_metadata/execution.json')==sha(ep)
    for rel,digest in e['source_sha256'].items():assert sha(out/'new_sources'/rel)==digest
    baseline=read(ROOT/'harness/tacc_s2_evidence/protected_inputs_20261024_v1/baseline.json')['hashes']
    for when in ('before','after'):
        proof=read(out/'job_metadata'/('protected_'+when+'.json'))
        assert proof['count']==len(baseline)==30067 and not proof['changed']
        assert set(proof['files'])==set(baseline)
        assert all(v['before_sha256']==v['after_sha256']==baseline[k] for k,v in proof['files'].items())
    build=read(out/'control/builds/f4-bracket-control/build_record.json')
    assert build['status']=='built' and build['source_commit']==plan['zephyr_commit']
    assert build['compiled_case_names']==['ref_counter_bracket.test_rate_window']
    assert build['plan_sha256']==e['plan_sha256']
    assert sha(out/'control/builds/f4-bracket-control/build/zephyr/zephyr.elf')==build['elf_sha256']
    assert sha(out/'control/builds/f4-bracket-control/build.log')==build['log_sha256']
    rows=[]
    for task in plan['tasks']:
        index=task['index'];f=task['frequency_hz']
        rid=f"f4-bracket-control-{task['condition']}-{index:03d}"
        record_path=out/'control/records'/(rid+'.json')
        uart_path=out/'control/uart'/(rid+'.log')
        process_path=out/'processes/run'/(str(index)+'.json')
        row=dict(index=index,frequency_hz=f,qualified=False,status='missing')
        if all(p.exists() for p in (record_path,uart_path,process_path)):
            r=read(record_path);process=read(process_path)
            row.update(status='failed',record_sha256=sha(record_path),uart_sha256=sha(uart_path),
                       cases=r.get('cases'),process_exit=process.get('exit_code'))
            basics=(process.get('exit_code')==0 and process.get('slurm_job_id')==args.job and
                    process.get('account','').upper()=='CCR26073' and
                    r.get('outcome')=='complete' and r.get('application_completed') is True and
                    r.get('error') is None and not r.get('missing_cases') and not r.get('duplicate_cases') and
                    r.get('cases')==[{'case':'ref_counter_bracket.test_rate_window','status':'pass'}] and
                    r.get('frequency_hz')==f and r.get('elf_sha256')==build['elf_sha256'] and
                    r.get('container_sha256')==e['image_sha256'] and
                    r.get('plan_sha256')==e['plan_sha256'] and
                    r.get('log_sha256',{}).get('uart')==sha(uart_path))
            platform=out/'control/platforms'/(rid+'.repl')
            basics=basics and platform.exists() and r.get('platform_sha256')==sha(platform)
            hits=PATTERN.findall(uart_path.read_text(errors='replace'))
            if basics and len(hits)==1:
                a0,b0,a1,b1,v0,v1,d=map(int,hits[0])
                if a0<=b0<=a1<=b1 and 9500<=a1-b0<=11500 and d==((v1-v0)&0xffffffff):
                    t_min=a1-b0-2;t_max=b1-a0+2
                    denominator=32000*1000
                    bands={str(hz):[hz*t_min//denominator,(hz*t_max+denominator-1)//denominator]
                           for hz in FREQUENCIES}
                    own=bands[str(f)]
                    qualified=own[0]<=d<=own[1] and all(not (low<=d<=high) for hz,(low,high)
                         in ((hz,bands[str(hz)]) for hz in FREQUENCIES if hz!=f))
                    row.update(status='qualified' if qualified else 'failed_band',qualified=qualified,
                               measurements=dict(a0=a0,b0=b0,a1=a1,b1=b1,v0=v0,v1=v1,delta=d),bands=bands)
        rows.append(row)
    summary=read(out/'control_summary.json')
    assert len(summary['rows'])==len(rows)==11
    for local,remote in zip(rows,summary['rows']):
        assert local['index']==remote['index'] and local['frequency_hz']==remote['frequency_hz']
        assert local['qualified']==(remote['status']=='qualified')
    result=dict(job_id=args.job,archive_sha256=sha(archive),output_state=receipt['output_state'],
                all_qualified=all(r['qualified'] for r in rows),qualified_count=sum(r['qualified'] for r in rows),
                rows=rows,old_18_ms_control_still_failed=True,primary_records_replaced=False)
    with (args.out/'verification.json').open('x') as stream:
        json.dump(result,stream,sort_keys=True,indent=2);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('job_id','output_state','all_qualified','qualified_count')},indent=2))

if __name__=='__main__':main()
