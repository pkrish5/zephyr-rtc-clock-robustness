#!/usr/bin/env python3
"""Case declarations, source call-graph wait cues and explicit survey limits."""
import csv,hashlib,json,re,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
Z=ROOT/'subjects/upstream/zephyr';OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
OUT.mkdir(exist_ok=True)
def masked(s):
    return re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',lambda m:''.join('\n' if c=='\n' else ' ' for c in m[0]),s,flags=re.S)
def block_end(s,start):
    level=0
    for i in range(start,len(s)):
        if s[i]=='{':level+=1
        elif s[i]=='}':
            level-=1
            if not level:return i+1
    raise ValueError('Unbalanced source')
rows=[];hashes={}
for area in ('rtc','watchdog','counter'):
 for yaml in sorted((Z/'tests/drivers'/area).rglob('testcase.yaml')):
    app=yaml.parent;name=app.name;functions={};cases=[];fixtures=[];sources={}
    for f in sorted((app/'src').glob('*.c')):
        original=f.read_text();s=masked(original);rel=str(f.relative_to(ROOT));sources[rel]=original
        hashes[rel]=hashlib.sha256(f.read_bytes()).hexdigest()
        for m in re.finditer(r'^\s*(?:(?:static|inline|const|struct|unsigned|signed|volatile)\s+)*(?:void|int|bool|size_t|uint\w*|int\w*|char|[A-Za-z_]\w*\s*\*)\b\s*\**\s*(\w+)\s*\([^;{}]*\)\s*\{',s,re.M):
            begin=s.index('{',m.start(),m.end());end=block_end(s,begin)
            functions[m[1]]=(rel,m.start(),end,s[m.start():end])
        for m in re.finditer(r'ZTEST(?:_USER|_F)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)\s*\{',s):
            end=block_end(s,s.index('{',m.start(),m.end()))
            cases.append((m[1],m[2],rel,m.start(),end,s[m.start():end]))
        for m in re.finditer(r'ZTEST_SUITE\s*\(([^;]+)\)\s*;',s):
            args=[x.strip() for x in m[1].split(',')]
            fixtures.extend(x for x in args[2:] if x!='NULL')
    if name=='wdt_variables' and not cases:
        f=app/'src/main.c';rel=str(f.relative_to(ROOT));s=masked(f.read_text())
        cases=[('console','main (console behavior, not a ztest case)',rel,0,len(s),s)]
    for suite,case,rel,start,end,body in cases:
        # Helpers and callbacks are also passed as function-pointer arguments.
        reachable={'case':(rel,start,end,body)};todo=re.findall(r'\b[A-Za-z_]\w*\b',body)+fixtures
        while todo:
            n=todo.pop()
            if n in reachable or n not in functions:continue
            reachable[n]=functions[n];todo+=re.findall(r'\b[A-Za-z_]\w*\b',functions[n][3])
        cues=[]
        for fn,(f,b,e,code) in reachable.items():
            for m in re.finditer(r'\b(k_sleep|k_msleep|k_usleep|k_busy_wait|k_sem_take|k_poll|WAIT_FOR|Z_SPIN_DELAY)\s*\(',code):
                line=sources[f].count('\n',0,b+m.start())+1
                cues.append(dict(function=fn,file=f,line=line,source=sources[f].splitlines()[line-1].strip()))
        selected=(area=='rtc' and name=='rtc_api') or area=='watchdog' or (area=='counter' and name in ('counter_basic_api','counter_seconds'))
        build='not built in S1';basis='Static source/configuration review only';model='not applicable';status='outside LSI hardware scope'
        note='Hardware-free RTC helper/shell or vendor-specific counter; not an STM32 LSI timing subject'
        if area=='rtc' and name=='rtc_api':
            model='RTC model present; individual API support differs';status='candidate; full application required'
            build='existing STM32F4 full-app build' if case not in ('test_set_get_calibration','test_update_callback') else 'conditional source; no existing enabled-feature build verified'
            basis='results/phase1_lsi_rtc/build.json and saved zephyr/.config; CONFIG_RTC_ALARM=y, UPDATE/CALIBRATION disabled'
            note={'test_alarm_callback':'Fixed 3 s absence + 10 s presence windows; existing selected-case clock records',
                  'test_alarm':'Fixed 3 s + 10 s pending windows and programmed-field readback; existing selected-case records',
                  'test_time_counting':'500 ms polling, finite 30-count limit; existing selected-case records',
                  'test_set_get_time':'Immediate readback within target or target+1 RTC second; no explicit host wait',
                  'test_y2k':'2 s wait, but STM32 driver rejects years before 2000 and case skips on -EINVAL',
                  'test_update_callback':'5 s disabled + 10 s enabled; require 9..11 callbacks; STM32 RTC API has no update callback and skips on -ENOSYS',
                  'test_set_get_calibration':'CONFIG_RTC_CALIBRATION source gate; API/calibration-range loops, not a clock-arrival assertion; model calibration behavior unvalidated'}[case]
        elif area=='watchdog':
            model='IWDG model present; reset/reboot fidelity NOT qualified on this platform'
            status='blocked or excluded; do not schedule as qualified'
            if name=='wdt_basic_api':
                build='existing STM32F4 IWDG build; manual configuration'
                basis='results/iwdg_fidelity_configured/build.json; notes/IWDG_FIDELITY_RESULT.md'
                note='One registered ZTEST contains several reboot-dependent scenarios. Stock stm32iwdg Twister allow-list omits STM32F4 Discovery. Existing five configured probes did not reboot/finish; no timing verdict.'
            elif name=='wdt_error_cases':note='Stock Twister platforms exclude STM32; many API/error cases depend on disable, pause or callback capabilities absent in STM32 IWDG'
            elif name=='wdt_basic_reset_none':note='Stock filter accepts NXP/Renesas/Silabs watchdogs; STM32 IWDG only supports RESET_SOC, not reset-none callback operation'
            else:note='Nordic-only console application; no ZTEST declarations and no STM32 implementation evidence'
        elif area=='counter' and name=='counter_basic_api':
            model='RTC peripheral model present; RTC-counter API, prescaler/subsecond and alarm behavior unvalidated'
            status='candidate only after new RTC-only overlay qualification'
            note='Stock stm32f4_disco overlay disables RTC and enables timer counters. Source enumerates st_stm32_rtc under CONFIG_COUNTER_RTC_STM32. No C changes needed; do not mix timer devices into the LSI denominator. Capability-dependent skips must be retained.'
        elif area=='counter' and name=='counter_seconds':
            model='RTC peripheral model present; RTC-counter port unvalidated'
            status='candidate only after new RTC alias/configuration qualification'
            note='Stock YAML only lists x86 CMOS and NXP SNVS. Non-CMOS source selects rtc_0 alias: a new STM32 RTC-counter overlay could supply it. 1.2 s sleep requires counter delta 1..2 at nominal 1 Hz.'
        rows.append(dict(app=str(app.relative_to(ROOT)),case=suite+'.'+case,case_kind='console' if suite=='console' else 'ztest',
            source=rel,start_line=sources[rel].count('\n',0,start)+1,end_line=sources[rel].count('\n',0,end)+1,
            in_requested_inventory='yes' if selected else 'excluded_non_lsi_hardware',stm32f4_build=build,build_evidence=basis,
            required_peripheral='IWDG' if area=='watchdog' else ('RTC counter' if area=='counter' else 'RTC'),
            renode_support=model,visible_wait='yes' if cues else 'no_explicit_wait_found',timing_evidence=json.dumps(cues,separators=(',',':')),
            candidate_status=status,notes=note))
with (OUT/'case_inventory.csv').open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'case_source_hashes.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
summary=dict(all_declared_rows=len(rows),requested_inventory_rows=sum(r['in_requested_inventory']=='yes' for r in rows),
    by_application=dict(Counter(r['app'] for r in rows if r['in_requested_inventory']=='yes')),
    caveat='Source declarations, not measured runnable/evaluable cases. Existing build evidence is explicit; no S1 builds/runs. Conditional skips and unsupported configurations are not successes.')
(OUT/'case_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
