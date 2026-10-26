#!/usr/bin/env python3
"""Normal-partition adapter around the byte-identical S2 simulation function."""
import argparse,hashlib,importlib.util,json,os
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--index',type=int,required=True)
a=ap.parse_args();p=json.loads((a.bundle/'plan.json').read_text())
assert sha(a.bundle/'plan.json')==(a.bundle/'plan.sha256').read_text().split()[0]
assert p['production_authorized'] is True and os.environ['SLURM_JOB_PARTITION']=='normal'
assert p['conditional_approval_evidence']['report']['all_15_accepted'] is True
assert os.environ['RTC_CONTAINER_SHA256']==p['image_sha256']
for rel,d in p['input_sha256'].items():assert sha(a.bundle/rel)==d,rel
original=Path('/sealed-s2/worker.py');assert sha(original)==p['conditional_approval_evidence']['unchanged_simulation_worker_sha256']
spec=importlib.util.spec_from_file_location('sealed_s2_worker',original);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
# Call the unchanged simulation function with real normal-partition metadata.
# The old development-only main()/verify() entrypoint is never spoofed.
module.run(a.bundle,p,p['tasks'][a.index])
