#!/usr/bin/env python3
"""Repeat unchanged S2 full-application run(), with new output names only."""
import argparse,hashlib,importlib.util,json,os
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--index',type=int,required=True);a=ap.parse_args()
 packet=Path('/repeat-packet');new=json.loads((packet/'plan.json').read_text())
 assert sha(packet/'plan.json')==(packet/'plan.sha256').read_text().split()[0]
 assert os.environ['SLURM_JOB_PARTITION']=='development'
 assert os.environ['RTC_CONTAINER_SHA256']==new['image_sha256']
 t=next(t for t in new['tasks'] if t['index']==a.index)
 assert t['unit_id']==os.environ['RTC_REPEAT_UNIT']
 base=Path('/bundle');p=json.loads((base/'plan.json').read_text())
 assert sha(base/'plan.json')==new['base_plan_sha256']
 original=Path('/sealed-s2/worker.py');assert sha(original)==new['frozen_simulation_worker_sha256']
 b=base/p['output_relative']/'builds'/t['unit_id']/'build_record.json'
 info=new['unit_builds'][t['unit_id']]
 assert sha(b)==info['build_record_sha256'] and sha(base/info['elf_path'])==info['elf_sha256']
 assert t['frequency_hz'] in new['frequencies_hz'][t['unit_id']]
 spec=importlib.util.spec_from_file_location('unchanged_s2_runner',original)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 # index/condition identify only new output files; all simulation instructions
 # and the full application ELF/order remain the original implementation.
 m.run(base,p,t)
 rid=f"{t['unit_id']}-{t['condition']}-{t['index']:03d}"
 out=base/p['output_relative'];rp=out/'records'/(rid+'.json');r=json.loads(rp.read_text())
 assert r['elf_sha256']==info['elf_sha256'] and r['frequency_hz']==t['frequency_hz']
 meta=dict(index=t['index'],cell_id=t['cell_id'],repeat_index=t['repeat_index'],selected_case=t['selected_case'],primary_record_path=str(rp.relative_to(out)),primary_record_sha256=sha(rp),repeat_plan_sha256=sha(packet/'plan.json'),protocol_sha256=new['protocol_sha256'],cpu_mips=16,systick_hz=16000000,quantum_ns=p['quantum_ns'],step_ns=p['step_ns'],container_sha256=r['container_sha256'],apptainer_version=r['apptainer_version'],node_name=r['node_name'],slurm_job_id=r['slurm_job_id'])
 dst=out/'repeat_metadata'/f"{a.index:03d}.json";dst.parent.mkdir(exist_ok=True)
 with dst.open('x') as f:json.dump(meta,f,indent=2,sort_keys=True);f.write('\n')
if __name__=='__main__':main()
