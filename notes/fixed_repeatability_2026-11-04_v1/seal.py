#!/usr/bin/env python3
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
verification=json.loads((HERE/'input_verification.json').read_text());counter=json.loads((HERE/'remote_counter_seal.json').read_text())
for rel,h in verification['inputs'].items():assert sha(ROOT/rel)==h,rel
for rel,h in json.loads((HERE/'counter_inputs_before.json').read_text()).items():assert sha(ROOT/rel)==h,rel
protocol=sha(HERE/'PROTOCOL.md');(HERE/'PROTOCOL.sha256').write_text(protocol+'  PROTOCOL.md\n')
section=f'''
## 2026-11-04 Separate fixed-setting F4 repeatability study (pre-execution)

The user authorized exactly30 fresh-process repeats in each of six cells:
rtc_api.test_alarm_callback at23673,23847,32000Hz and
counter_basic.test_all_channels at29143,29352,32000Hz. Run unchanged archived
F4 full-application ELFs and unchanged S2 simulation instructions; no rebuild,
source instrumentation, isolation, clock resampling, new driver or fault. The
nominal32000Hz cells are verified against archived qualification, not the seeded
production schedule. Both qualification and production use exactly the same
ELFs. Boundary and nominal records, linked logs, input hashes and resource
measurements were checked before sealing.

Protocol: notes/fixed_repeatability_2026-11-04_v1/PROTOCOL.md, SHA256
{protocol}.
COST.json freezes two independent development/TRA25006 jobs, one node and32
Launcher workers each,90 launches per job: RTC01:30:00 ceiling1.5SU; counter
02:00:00 ceiling2SU. Estimated total2.441906SU, reservation ceiling3.5SU, excluding
queue wait. Uses tacc-apptainer/1.4.1, launcher/3.10 and the existing calibrated
SIF. Original CPU16MIPS, SysTick16MHz, quantum1000ns, observation step0.5virtual
seconds, per-app timeouts, full application order and ELF bytes remain fixed.

Keep all180 planned indices; report pass/fail/skip/missing separately per cell.
Only complete error-free unambiguous application records supply primary selected
verdicts. Missing/harness outcomes are retained, never replaced. Mixed explicit
pass/fail within a cell supports observed same-setting flakiness in that cell;
concordance means no observed same-setting flakiness, not exclusion of rare
flakiness. No outcome-dependent repeats or stopping. Timelines distinguish UART
kernel-reported duration, sampled simulator observation and source inference;
callback-entry and subsecond-phase timestamps are not directly measured.

New namespace only, SCRATCH/node-local runtime and per-job verified packed WORK
archives with fresh headroom gates and before/after protected audits. Archived
ELFs and active counter-repair inputs stay read only; no git clean, pruning,
resubmission or alteration of3552460-3552463. No fourth-case manuscript result
before that chain is collected and verified. An exact user-supplied follow-up
prompt is retained for delivery after all four existing jobs finish. No normal
queue repeatability job is covered by this development-only plan.
'''
design=ROOT/'paper/DESIGN.md'
with design.open('a') as f:f.write(section)
packet=HERE/'packet';packet.mkdir(exist_ok=False)
for n in ['PROTOCOL.md','PROTOCOL.sha256','COST.json','input_verification.json']:
 shutil.copyfile(HERE/n,packet/n)
tasks=[]
for unit,case,freqs in [('f4-rtc','rtc_api.test_alarm_callback',[23673,23847,32000]),('f4-counter','counter_basic.test_all_channels',[29143,29352,32000])]:
 for repeat in range(30):
  for freq in freqs:tasks.append(dict(index=len(tasks),unit_id=unit,condition='repeatability',frequency_hz=freq,cell_id=unit+'-'+str(freq),repeat_index=repeat,selected_case=case))
remote='tacc_work/20261104-counter-repair-v1/bundle'
counter_inputs={**counter['code_sha256'],**{remote+'/'+k:v for k,v in counter['input_sha256'].items()},remote+'/plan.json':'c5d2f7f515a59f2d45bcad665ab649b251051904704a1c96186610d08141ea8d'}
code=[p for p in (ROOT/'harness/tacc_fixed_repeatability').glob('*') if p.is_file()]
code += [ROOT/('harness/tacc_storage/'+s) for s in ['runtime.sh','run_packed.sh','protected_check.py','check_headroom.py','publish.py','archive.py']]
code += [ROOT/'harness/tacc_s2/worker.py']
plan=dict(schema=1,study='fixed-setting F4 full-application repeatability v1',registered_date='2026-11-04',tasks=tasks,frequencies_hz={'f4-rtc':[23673,23847,32000],'f4-counter':[29143,29352,32000]},unit_builds=verification['unit_builds'],image_sha256=verification['image_sha256'],base_plan_sha256=verification['base_plan_sha256'],frozen_simulation_worker_sha256=verification['frozen_simulation_worker_sha256'],protocol_sha256=protocol,cost_sha256=sha(HERE/'COST.json'),input_verification_sha256=sha(HERE/'input_verification.json'),code_sha256={str(p.relative_to(ROOT)):sha(p) for p in code},counter_inputs_sha256=counter_inputs,design_amendment_sha256=hashlib.sha256(section.encode()).hexdigest(),cpu_mips=16,systick_hz=16000000,quantum_ns=1000,step_ns=500000000,maximum_workers=32,account='TRA25006',partition='development',jobs=json.loads((HERE/'COST.json').read_text())['jobs'],normal_queue_authorized=False)
with (packet/'plan.json').open('x') as f:json.dump(plan,f,indent=2,sort_keys=True);f.write('\n')
(packet/'plan.sha256').write_text(sha(packet/'plan.json')+'  plan.json\n')
print(json.dumps(dict(protocol_sha256=protocol,plan_sha256=sha(packet/'plan.json'),tasks=len(tasks),counter_active_input_files=len(counter_inputs),code_files=len(code)),indent=2))
