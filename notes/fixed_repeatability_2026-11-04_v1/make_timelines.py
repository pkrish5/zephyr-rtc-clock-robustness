#!/usr/bin/env python3
"""Existing-evidence timelines: distinguish observed logs from source arithmetic."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
m=json.loads((HERE/'input_verification.json').read_text())
lines=['# Evidence-linked timing timelines (archived baseline, no new run)','',
'These timelines deliberately distinguish three clocks/claims: kernel-reported case duration in UART; Renode virtual time when buffered UART verdicts become visible to the harness; and source-derived ideal RTC timing. They are not interchangeable. No callback-entry or subsecond-phase timestamp was measured. The new repeatability study leaves the ELFs and instrumentation unchanged.','']
for unit,case,source,body in [
 ('f4-rtc','rtc_api.test_alarm_callback','subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c',[
  '**Source inference:** each callback iteration sleeps3s, checks no premature callback, sleeps10s, then requires callback status (lines120-141). The loop has two iterations and resets RTC calendar time (lines113-147). A complete26s test duration is compatible with reaching the second window; the UART does not directly log the loop index or callback timestamp.',
  '**Clock arithmetic, not measured event time:** at input f, one RTC tick ideally takes32000/f virtual seconds. An alarm ten calendar ticks ahead can need nine to ten ticks depending on preserved subsecond phase. Thus the13s wait is phase-sensitive. The relevant phase is not recorded; pass/fail boundaries alone cannot measure it.',
  '**Measured evidence limit:** the trace records UART exposure only at sampling points. A completion observed at52.5s or53s is the harness seeing buffered output, not proof that the callback/assertion occurred then. UART durations are separately labeled kernel-reported, not converted to Renode timestamps.']),
 ('f4-counter','counter_basic.test_all_channels','subjects/upstream/zephyr/tests/drivers/counter/counter_basic_api/src/test_counter.c',[
  '**Source inference:** the test requests a two-tick relative alarm and busy-waits1.5 times counter_ticks_to_us(ticks), then asserts cnt==nchan (lines661-701; failure site695). On the nominal1Hz RTC counter, the source wait expression is3000000us. Successful cleanup follows the assertion; a failure skips that cleanup.',
  '**Source inference:** counter_ll_stm32_rtc.c adds one compensating tick for a partially started tick. The physical interval can therefore span two to three RTC ticks. The fixed3s wait yields a phase envelope21.333-32.000kHz; this is a source-derived envelope, not a directly measured phase or universal threshold.',
  '**Measured ordering:** at29143Hz the archived UART reports all_channels FAIL, then later single_shot_alarm_notop FAIL with err:-16. At29352Hz both explicitly PASS in the same application. This supports the cleanup-cascade explanation; no callback-entry timestamp was recorded. A long final application observation time does not locate the selected callback.'])]:
 lines+=['## '+case,'',f'Source: [{source}]({ROOT/source}).','']+sum(([s,''] for s in body),[])
 lines+=['| Input Hz | Archived verdict | UART case duration (kernel-reported s) | First trace observation containing verdict (Renode virtual s) | Evidence |','|---:|---|---:|---:|---|']
 for c in m['cells']:
  if c['unit_id']!=unit:continue
  b=c['baseline_records'][0];uart=ROOT/b['uart_path'];text=uart.read_text();tail=case.split('.')[-1]
  dur=re.search(r'\b(?:PASS|FAIL|SKIP) - '+re.escape(tail)+r' in ([0-9.]+) seconds',text)
  trace=json.loads((ROOT/b['trace_path']).read_text());obs=next(o['virtual_ns']/1e9 for o in trace['observations'] if any(x['case']==case for x in o['cases']))
  assert hashlib.sha256(uart.read_bytes()).hexdigest()==b['uart_sha256']
  lines.append(f"|{c['frequency_hz']}|{b['selected_outcome']}|{dur[1]}|{obs:g}|[UART]({uart}), [trace]({ROOT/b['trace_path']}), [record]({ROOT/b['path']})|")
 lines+=['','The32000Hz row displays the first of five archived nominal runs, not a new repeatability outcome. All five input hashes and outcomes are in input_verification.json.','']
(HERE/'TIMELINES.md').write_text('\n'.join(lines)+'\n')
