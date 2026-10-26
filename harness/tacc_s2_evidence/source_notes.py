#!/usr/bin/env python3
"""Extract source-verified preliminary explanations, without executing tests."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('--plan', type=Path, required=True)
ap.add_argument('--zephyr', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args()
plan = json.loads(a.plan.read_text())
rows = [
 dict(case='rtc_api.test_alarm',source='tests/drivers/rtc/rtc_api/src/test_alarm.c',lines='14-15;177-204',effective_wait='3 + 10 host seconds',boundary_khz='320/13 = 24.615 (ideal fixed-divider boundary)',explanation='Ten RTC seconds must elapse before the final pending assertion. Two repetitions are in the source; a first failure aborts later checks.',attribution='candidate brittle bound; production replay/reference triage pending',ranges=[(14,15),(177,204)]),
 dict(case='rtc_api.test_alarm_callback',source='tests/drivers/rtc/rtc_api/src/test_alarm_callback.c',lines='13-14;119-141',effective_wait='3 + 10 host seconds',boundary_khz='320/13 = 24.615 (ideal fixed-divider boundary)',explanation='Callback presence is required after a fixed thirteen-second observation; slower legal input can delay the target RTC second beyond it.',attribution='candidate brittle bound; production replay/reference triage pending',ranges=[(13,14),(119,141)]),
 dict(case='rtc_api.test_time_counting',source='tests/drivers/rtc/rtc_api/src/test_time_incrementing.c',lines='15-17;35-59',effective_wait='30 polls; 500 ms sleeps; final observation about 14.5 seconds',boundary_khz='320/14.5 = 22.069 (last-poll approximation)',explanation='The final unsuccessful poll is followed by another sleep before the timeout assertion; assertion duration is not the observation deadline.',attribution='candidate brittle polling bound; production replay/reference triage pending',ranges=[(15,17),(35,59)]),
 dict(case='counter_basic.test_all_channels',source='tests/drivers/counter/counter_basic_api/src/test_counter.c',lines='179-185;658-702',effective_wait='1.5 * 2 reported counter seconds = 3 host seconds',boundary_khz='phase-dependent: (3 - phi)*32/3, between 21.333 and 32 for phi in [0,1); no single fitted boundary',explanation='The driver adds one tick for a relative alarm. A two-tick request can need between two and three physical ticks. The three-second busy wait assumes nominal counter rate. Exact phase and conversions require trace/reference validation.',attribution='candidate timing failure; not a validated scalar threshold',ranges=[(179,185),(658,702)]),
 dict(case='counter_basic.test_single_shot_alarm_notop',source='tests/drivers/counter/counter_basic_api/src/test_counter.c',lines='473-478',effective_wait='none before the observed alarm-setup failure',boundary_khz='not assigned; possible earlier-test state cascade',explanation='Observed -EBUSY is at alarm setup, before this case waits. An earlier all-channels failure bypasses cancellation; the driver rejects an alarm while a callback is registered. This is not an independently demonstrated waiting-bound defect.',attribution='possible shared-state cascade; isolation/reference evidence pending',ranges=[(473,478)]),
 dict(case='seconds_counter.test_seconds_rate',source='tests/drivers/counter/counter_seconds/src/main.c',lines='20-42',effective_wait='1200 ms',boundary_khz='32/1.2 = 26.667 in ideal zero-phase model; actual boundary is phase-dependent',explanation='At least one counter tick is required after a fixed 1.2-second sleep. Slower legal input can leave the elapsed count at zero. Read phase affects the observed transition.',attribution='candidate rate-oracle failure; production replay/reference triage pending',ranges=[(20,42)]),
]
excerpts=['# Qualification failure source excerpts\n\nSource hashes match the sealed S2 upstream-input ledger. These are preliminary\nexplanations, not completed production attribution. Phase-dependent expressions\nassume divider 32000; phi is the fractional tick at alarm programming.\n']
extra=[('drivers/counter/counter_ll_stm32_rtc.c',[(517,537)])]
for r in rows:
 p=a.zephyr/r['source'];digest=hashlib.sha256(p.read_bytes()).hexdigest()
 assert digest==plan['upstream_input_sha256'][r['source']],r['source']
 r['source_sha256']=digest
 excerpts.append('\n## '+r['case']+'\n\n`'+r['source']+'`\n\n```c\n')
 lines=p.read_text().splitlines()
 for lo,hi in r.pop('ranges'):
  assert 1 <= lo <= hi <= len(lines)
  excerpts.extend(f'{i}: {lines[i-1]}\n' for i in range(lo,hi+1))
  excerpts.append('\n')
 excerpts.append('```\n')
for rel,ranges in extra:
 p=a.zephyr/rel;assert hashlib.sha256(p.read_bytes()).hexdigest()==plan['upstream_input_sha256'][rel]
 excerpts.append('\n## Driver relative-alarm offset and busy guard\n\n`'+rel+'`\n\n```c\n')
 lines=p.read_text().splitlines()
 for lo,hi in ranges:excerpts.extend(f'{i}: {lines[i-1]}\n' for i in range(lo,hi+1))
 excerpts.append('```\n')
with (a.out/'preliminary_failure_explanations.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (a.out/'source_excerpts.md').open('x') as f:f.write(''.join(excerpts))
