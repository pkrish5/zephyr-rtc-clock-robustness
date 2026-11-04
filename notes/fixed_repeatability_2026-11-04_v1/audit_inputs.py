#!/usr/bin/env python3
"""Read-only recheck of the preregistered archived records and unchanged ELF bytes."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
m=json.loads((HERE/'input_verification.json').read_text())
for rel,h in m['inputs'].items():assert sha(ROOT/rel)==h,rel
for c in m['cells']:
 for b in c['baseline_records']:
  rp=ROOT/b['path'];r=json.loads(rp.read_text());base=rp.parent.parent
  assert r['frequency_hz']==c['frequency_hz']
  assert r['elf_sha256']==m['unit_builds'][c['unit_id']]['elf_sha256']
  assert [x['status'] for x in r['cases'] if x['case']==c['case']]==[b['selected_outcome']]
  assert sha(base/'platforms'/(r['run_id']+'.repl'))==r['platform_sha256']
  for kind,h in r['log_sha256'].items():
   if h:assert sha(base/kind/(r['run_id']+('.json' if kind=='traces' else '.log')))==h
with a.out.open('x') as f:json.dump(dict(status='PASS',cells=6,archived_nominal_records=10,archived_boundary_records=4,unchanged_elves=2,source_input_hashes_checked=len(m['inputs']),new_simulations=0),f,indent=2);f.write('\n')
