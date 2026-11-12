#!/usr/bin/env python3
"""Numerical, paired-record, citation and table audit for course manuscript v4."""
import csv, hashlib, json, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; HERE=ROOT/'notes/course_counter_2026-11-11_v1'; OUT=Path(__file__).resolve().parent
V2=ROOT/'notes/course_subjects_2026-11-04_v1'
P=ROOT/'notes/final_submission_2026-11-02_v1/phase3_package_v2'
tex=(ROOT/'paper/draft/main.tex').read_text()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
e=json.loads((V2/'paired_and_scope_audit.json').read_text()); stats=json.loads((P/'statistics.json').read_text())
rows=read(P/'repair_primary_index.csv'); sub=lambda r:r['version_id'].rsplit('--',1)[0]
checks=[]
def check(claim,actual,expected,tokens,paths):
 assert actual==expected,(claim,actual,expected)
 assert all(t in tex for t in tokens),(claim,tokens)
 checks.append(dict(claim=claim,value=actual,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in paths},manuscript_tokens=tokens))
R=P/'repair_primary_index.csv'; S=P/'s2_per_case_with_references.csv'
v={r['variant']:r for r in e['variants']}; pairs=e['adjacent_variant_pairs']
check('Six subjects, three upstream and three generated', [len(e['sensitive_subjects']),sum(s.startswith('human-') for s in e['sensitive_subjects'])],[6,3],['six subjects','three upstream subjects'],[R])
subject_view=json.loads((V2/'subject_table_audit.json').read_text())
check('Individual original seeded failures', [r['original_seed_fail'] for r in subject_view['subjects']],[26,26,17,11,13,13],['Table~\\ref{tab:subjects}'],[R])
check('Individual endpoint failures', [r['original_endpoint_fail'] for r in subject_view['subjects']],[1]*6,['two endpoints'],[R])
check('Each repaired sensitive subject passes 102/102, no missing, slow detection retained',[[r['repaired_pass_per_variant'],r['missing_per_variant'],r['slow_all_variants']] for r in subject_view['subjects']],[[102,0,'detected']]*6,['passes all 102 legal settings','zero missing verdicts','does \\emph{not} weaken slow-fault detection'],[R])
check('Supporting 612 pairs are six subjects', [v['V0']['six_sensitive_subjects_legal_outcomes']]+[v[k]['six_sensitive_subjects_legal_outcomes'] for k in ['V1','V1b','V2','V3']],[{'pass':500,'fail':112}]+[{'pass':612}]*4,['612 shared subject-setting pairs','500 passes and 112 failures','six subjects, not 612 independent tests'],[R])
check('Full roster and generated task composition',[len({sub(r) for r in rows}),len({sub(r) for r in rows if not sub(r).startswith('human-') and r['family']=='rtc_time_counting'}),len({sub(r) for r in rows if not sub(r).startswith('human-') and r['family']=='rtc_alarm_pending'})],[33,27,3],['30 generated scalar-budget suites (27 counting, three pending)','no generated callback suite'],[R])
check('Seeded failures and retained missing per variant',[[v[k]['seeded_fail'],v[k]['seeded_missing']] for k in v],[[106,9],[0,7],[0,5],[0,3],[0,2]],['106 seeded','7/5/3/2 missing'],[R])
check('Endpoint failures/missing',[[v[k]['endpoint_fail'],v[k]['endpoint_missing']] for k in v],[[6,0]]+[[0,0]]*4,['six endpoint failures','all 66 endpoints are observed passing'],[R])
check('Slow fault denominators',[[v[k]['slow']['detected'],v[k]['slow']['evaluable']] for k in v],[[21,33],[21,33],[32,32],[33,33],[33,33]],['21/33','32/32','33/33'],[R])
gain=next(x for x in pairs if (x['before'],x['after'],x['operator'])==('V1','V1b','slow'))
check('Right sizing common pairs', [gain['common_evaluable'],gain['retained'],len(gain['gained']),len(gain['lost'])],[32,21,11,0],['retain 21 detections, gain 11 and lose none'],[R])
for s in gain['gained']:
 rr=[r for r in rows if sub(r)==s and r['variant']=='V0' and r['operator']=='legal']
 assert s not in e['sensitive_subjects'] and 'rtc_time_counting' in s and len(rr)==102 and all(r['outcome']=='pass' for r in rr)
check('Eleven gains are different already tolerant counting subjects',len(gain['gained']),11,['All 11 gains are generated counting subjects with 102 V0 legal passes and no missing legal verdicts'],[R])
manifest_path=ROOT/'notes/repair_execution_20261024_v2/variants.json'
manifest=json.loads(manifest_path.read_text())['versions']
for sid in gain['gained']:
 a,b=[manifest[sid+'--'+k] for k in ['V1','V1b']]
 assert a['scalar_ceiling_ms']==a['original_budget_ms']>20824 and a['unchanged_from_v0'] is True
 assert b['scalar_ceiling_ms']==20824 and b['added_assertions']==0
 for k in ['V1','V1b']:
  m=manifest[sid+'--'+k]
  assert sha(ROOT/m['variant_source_path'])==m['variant_source_sha256']
check('Counting gains change overlong ceilings without added assertions',len(gain['gained']),11,['They correct over-padding'],[manifest_path])
poll=next(x for x in pairs if (x['before'],x['after'],x['operator'])==('V1b','V2','slow'))
check('Polling common pairs',[poll['common_evaluable'],poll['retained'],len(poll['gained'])],[32,32,0],['all 32 common V1b/V2 pairs already detect it'],[R])
check('Adjacent common-evaluable detection losses',sum(len(x['lost']) for x in pairs),0,['no detected fault becomes accepted on common-evaluable subject pairs'],[R])
check('Early and late detection each variant',[[v[k][op]['detected'],v[k][op]['evaluable']] for k in v for op in ['offset_early','offset_late']],[[4,5]]*8+[[5,5]]*2,['4/5 applicable subjects','V3 reaches 5/5'],[R])
for op in ['offset_early','offset_late']:
 assert next(x['gained'] for x in pairs if (x['before'],x['after'],x['operator'])==('V2','V3',op))==['human-rtc_alarm_callback']
check('Fast fault not detected',[[v[k]['fast']['detected'],v[k]['fast']['evaluable']] for k in v],[[0,33],[0,33],[0,32],[0,33],[0,33]],['0/32 for V1b, 0/33 otherwise'],[R])
check('Nonarrival detections and denominators',[[v[k]['nonarrival']['detected'],v[k]['nonarrival']['evaluable']] for k in v],[[32,32]]+[[33,33]]*4,['32/32 evaluable V0 subjects and 33/33 after repair'],[R])
check('Duration, whole-test not latency',[e['upstream_callback_median_simulated_seconds'][k] for k in ['V1b','V2']]+[v[k]['median_simulated_seconds'] for k in v],[42,20.75,11,11,11,11,11],['42.0 s (V1b) to 20.75 s (V2)','pooled median is 11.0 s','whole-test time is not callback latency'],[R])
replay=json.loads((P/'repair_replays.json').read_text());refs=json.loads((P/'repair_references.json').read_text())
assert all(r['persisted_fields_match'] and r['raw_trace_hash_matches'] for r in replay)
assert all(r['outcome']=='pass' for r in refs)
check('Replay, reference and missing evidence',[len(replay),len(refs),e['primary_outcomes']['harness_error']],[458,112,29],['All 458 primary assertion failures replay exactly','112 original failing slots have passing task-specific references','29 finalized missing outcomes'],[P/'repair_replays.json',P/'repair_references.json',R])
s2=read(S)
check('Declared, runnable and waiting-sensitive names',[e['expanded_declared_distinct_case_names'],len(e['expanded_runnable_distinct_case_names']),sum(len(e['expanded_categories_by_distinct_name'][c]) for c in 'ab')],[19,10,4],['10 distinct runnable upstream case names','19 declared names','Four distinct names have waiting-sensitive failures'],[S])
check('Distinct runnable applications',[len({r['case'] for r in s2 if r['case'].startswith(x+'.') and int(r['pass_count'])+int(r['fail_count'])}) for x in ['rtc_api','counter_basic','seconds_counter']],[5,4,1],['five runnable RTC API cases, four counter basic cases and one counter seconds case'],[S])
by_board=[]
for bid in ['f4','f767','f746','h753']:
 rr=[r for r in s2 if r['board_id']==bid]
 runnable={r['case'] for r in rr if int(r['pass_count'])+int(r['fail_count'])}
 waiting={r['case'] for r in rr if r['category'] in 'ab' and int(r['fail_count'])}
 by_board.append([len(runnable),len({r['case'] for r in rr}-runnable),len(waiting)])
check('Per-board runnable/skipped and waiting names',by_board,[[10,9,4],[10,9,4],[6,2,3],[10,9,0]],['4/10 runnable names on F4 and its F767 replica, 3/6 on F746, and 0/10 on H753'],[S])
check('Launch/case-slot accounting',[len({r['unit_id'] for r in s2}),len({r['unit_id'] for r in s2})*102]+[sum(int(r[k+'_count']) for r in s2) for k in ['pass','fail','skip','missing']],[11,1122,3022,470,3138,0],['11 application/configuration combinations','1,122 launches','3,022 passing, 470 failing and 3,138 capability-skipped','no missing primary case verdicts'],[S])
linked=read(ROOT/'notes/s2_reference_2026-11-02_v1/verified-3547096-v1/primary_failure_reference_links.csv')
check('S2 reference categories',sorted(Counter(r['flag'] for r in linked).values()),[88,105,277],['277 waiting references pass','88 clean-state cascade references pass','105 rate references fail'],[S,ROOT/'notes/s2_reference_2026-11-02_v1/verified-3547096-v1/primary_failure_reference_links.csv'])
rec=read(P/'isolated_reconciliation.csv')
check('Full vs isolated',[ [int(r['full_seed_failures']),int(r['isolated_seed_failures'])] for r in rec],[[26,26],[22,26],[12,17]],['pending 26/26, callback 22/26 and counting 12/17','not directly measured phase'],[P/'isolated_reconciliation.csv'])
f4={r['case']:r for r in s2 if r['board_id']=='f4'}
check('Observed full-application bands',[[int(f4[n][k]) for k in ['minimum_failed_hz','maximum_failed_hz','minimum_passed_hz','maximum_passed_hz']] for n in ['rtc_api.test_alarm_callback','rtc_api.test_time_counting','seconds_counter.test_seconds_rate']],[[17000,23673,23847,47000],[17000,20500,20701,47000],[17000,26168,27086,47000]],['17.000--23.673','23.847--47.000','17.000--20.500','20.701--47.000','17.000--26.168','27.086--47.000'],[S])
check('Phase envelope all channels',[round(2*32/3,3),round(3*32/3,3)],[21.333,32.0],['21.333--32.000 kHz'],[ROOT/'notes/s2_attribution_2026-10-31/finalize_s2.py'])
h=[r for r in s2 if r['board_id']=='h753' and int(r['pass_count'])]
check('H753 range and failures',[min(int(r['minimum_passed_hz']) for r in h),max(int(r['maximum_passed_hz']) for r in h),sum(int(r['fail_count']) for r in h)],[29760,33600,0],['29.760--33.600','H753 has no observed failures'],[S])
check('Secondary cohort and prompt contrast',[stats['all_attempts'],stats['generated_suites'],stats['prompt_cells']['range_absent']['flips'],stats['prompt_cells']['range_absent']['suites'],stats['prompt_cells']['range_present']['flips'],stats['prompt_cells']['range_present']['suites'],round(stats['prompt_fisher']['two_sided_p'],3),stats['seed_missing']],[90,66,3,34,0,32,.239,12],['90 attempts, 66','3/34 base versus 0/32','Fisher $p=0.239$','12 original seeded verdicts remain missing'],[P/'statistics.json'])
hsi=json.loads((V2/'hsi_summary.json').read_text());hp=ROOT/'subjects/phase3_hsi_100mips/plan.json'; plan=json.loads(hp.read_text())
c={k:Counter() for k in ['upstream','agent']}
for r in hsi['versions'].values():
 if r['nominal_5_of_5']:c[r['kind']].update(r['seeded_statuses'])
check('Pinned HSI evaluable results',[c['upstream']['pass'],c['agent']['pass'],c['upstream']['fail']+c['agent']['fail'],c['upstream']['harness_error']+c['agent']['harness_error']],[943,3270,0,87],['943 upstream and 3,270 generated evaluable seeded runs','87 seeded outcomes were not evaluable'],[hp,V2/'hsi_summary.json'])
check('HSI interval and mapping',[plan['hsi_bound_hz'],sorted(set(plan['seeded_cpu_mips']))],[[15840000,16160000],[99,100,101]],['15.84--16.16 MHz','99--101-MIPS'],[hp])
board=json.loads((P/'board_survey.json').read_text())
check('Context board survey',[board['lsi'],board['lse']],[106,40],['106 LSI versus 40 LSE'],[P/'board_survey.json'])
scan=read(ROOT/'analysis/rtc_stage_a_upstream_patterns.csv')
check('Delivery-bound scoped source scan',[len(scan),sum(r['explicit_delivery_latency_pattern']=='True' for r in scan)],[33,0],['no explicit interrupt-to-callback latency bound was found in 33 scanned files'],[ROOT/'analysis/rtc_stage_a_upstream_patterns.csv'])
check('Clock arithmetic and experimental ceiling',[round(320000/17000,3),round(320/13,3),320000/10000],[18.824,24.615,32],['18.824','24.615','20.824','two seconds of unvalidated experimental allowance','32 s'],[ROOT/'paper/DESIGN.md'])
protocol=(ROOT/'paper/DESIGN.md').read_text();assert '23.824 seconds' in protocol and '20,824 ms' in protocol
assert '23.824 s' in tex and '20-ms state polling' in tex
source=ROOT/'subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c'
ss=source.read_text().splitlines()
assert 'RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY' in ss[119] and 'RTC_TEST_ALARM_TEST_CALLED_DELAY' in ss[131] and 'zassert_equal(callback_called_status, true' in ss[139]
check('Source timeline exact sleep constants',[next(l.strip() for l in ss if l.startswith('#define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY')),next(l.strip() for l in ss if l.startswith('#define RTC_TEST_ALARM_TEST_CALLED_DELAY'))],['#define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)','#define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)'],['lines 120 and 132','lines 126--129','lines 140--141'],[source])
expected=json.loads((ROOT/'reproduction/expected_tables.json').read_text());assert len(expected)==8
assert {n:sha(ROOT/'paper/draft/tables'/n) for n in expected}==expected
assert sorted(re.findall(r'\\input\{tables/([^}]+)\}',tex))==sorted(list(subject_view['table_sha256'])+['counter_course_v3.tex'])
assert all(sha(ROOT/'paper/draft/tables'/n)==h for n,h in subject_view['table_sha256'].items())
counter=json.loads((HERE/'counter_table_audit.json').read_text())
assert counter['status']=='PASS' and sha(ROOT/'paper/draft/tables/counter_course_v3.tex')==counter['table_sha256']
cc=counter['counts'];allcase='counter_basic.test_all_channels';short='counter_basic.test_short_relative_alarm';single='counter_basic.test_single_shot_alarm_notop'
check('Fourth upstream case legal pairing',[[cc[k][allcase][s] for s in ['pass','fail','skip']] for k in ['V0','V1','V1b','V2']],[[58,44,0]]+[[102,0,0]]*3,['44 of 102 tested legal frequencies','each pass the same 102 settings','one additional upstream case'],[HERE/'counter_table_audit.json'])
check('Residual short relative and single shot outcomes',[[cc[k][short]['fail'],cc[k][single]['fail']] for k in ['V1','V1b','V2']],[[14,15]]*3,['short-relative fails at 14 settings','fails at 15 settings after repair','29 original failures disappear'],[HERE/'counter_table_audit.json'])
check('Counter matched replays and functional references',[counter['diagnostic_replays_matched'],counter['functional_reference_case_passes'],counter['functional_reference_failures_covered']],[17,51,87],['Seventeen representative full-application replays','Three clean-state functional references pass at 17 legal settings each','all 87 residual failing case slots'],[HERE/'counter_table_audit.json'])
diagnostic=ROOT/'notes/counter_verification_2026-11-11_v1/report-3575326-v1/summary.json';diag=json.loads(diagnostic.read_text())
slow=next(x for x in diag['activation_controls'] if x['frequency_hz']==10000)
check('Historical five-tick control bound remains failed',[slow['elapsed_ms'],slow['upper_ms'],slow['over_upper_ms'],diag['activation_qualified']],[16040,16022.0,18,False],['16.040 s','18 ms above its preregistered 16.022-s bound','the exact five-tick timing remain unresolved'],[diagnostic,ROOT/'notes/counter_verification_2026-11-11_v1/OBSERVER_AUDIT.md'])
control_path=OUT/'verified-3578143-v1/verification.json';control=json.loads(control_path.read_text())
assert control['job_complete'] and control['all_qualified'] and len(control['rows'])==11
by_freq={f:[r for r in control['rows'] if r['frequency_hz']==f] for f in (10000,32000,64000)}
assert all(r['qualified'] for rows_for_freq in by_freq.values() for r in rows_for_freq)
check('Preregistered bracketed rate activation',
      [control['qualified_count']]+[len(by_freq[f]) for f in (32000,10000,64000)]+[[r['measurements']['delta'] for r in by_freq[f]] for f in (32000,10000,64000)],
      [11,5,3,3,[10]*5,[3]*3,[20]*3],
      ['All five nominal, three slow and three fast fresh processes','10, 3 and 20 ticks','three injected rates'],
      [control_path,OUT/'PROTOCOL.md',OUT/'packet/plan.json'])
faults=counter['raw_fault_selected_verdicts']
check('Fourth selected-case slow-fault response',
      [faults[k]['slow_fault'] for k in ('V0','V1','V1b','V2')],
      ['fail','pass','fail','fail'],
      ['V1 loses detection, while V1b/V2 retain it'],
      [HERE/'counter_table_audit.json',control_path])
repeat_path=ROOT/'notes/fixed_repeatability_recovery_2026-11-04_v1/combined_report_v1/summary.json';repeat=json.loads(repeat_path.read_text())
check('Six fixed-setting repeatability cells',[repeat['planned_launches'],len(repeat['cells']),sum(x['fail_count'] for x in repeat['cells']),sum(x['pass_count'] for x in repeat['cells']),len(repeat['observed_mixed_pass_fail_cells'])],[180,6,60,120,0],['180 outcomes','30/30 at 23.673 kHz','30/30 at 29.143 kHz','no mixed verdict within these six cells'],[repeat_path])
keys=re.findall(r'\\bibitem\{([^}]+)\}',tex);cites={k for g in re.findall(r'\\cite\{([^}]+)\}',tex) for k in g.split(',')}
assert len(keys)==len(set(keys))==13 and set(keys)==cites
assert 'E2' not in tex and '\\scriptsize' not in tex and '\\tiny' not in tex
assert 'no same-setting flakiness' in tex and 'not observed nondeterminism at one setting' in tex
result=dict(status='PASS',numeric_claims=len(checks),checks=checks,original_table_hashes_match=8,readable_table_hashes_match=3,counter_table_hash_matches=True,citation_keys_resolve=13,manuscript_sha256=sha(ROOT/'paper/draft/main.tex'),raw_records_mutated=False,renode_runs=11)
(OUT/'manuscript_numbers_v4.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
with (OUT/'claim_to_evidence_v4.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['claim','value','manuscript_tokens','sources'])
 for r in checks:w.writerow([r['claim'],json.dumps(r['value']),'; '.join(r['manuscript_tokens']),'; '.join(r['source_sha256'])])
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
