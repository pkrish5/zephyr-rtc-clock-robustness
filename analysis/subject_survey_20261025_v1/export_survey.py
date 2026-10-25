#!/usr/bin/env python3
"""Export the reviewed S1 tables; no builds, simulations or old-record writes."""
import argparse,csv,hashlib,json,re,os
from collections import Counter
from pathlib import Path
SCRIPT=Path(__file__).parent;ROOT=SCRIPT.parents[1];Z=ROOT/'subjects/upstream/zephyr'
ap=argparse.ArgumentParser()
ap.add_argument('--out',type=Path,default=SCRIPT)
ap.add_argument('--renode-root',type=Path,default=Path(os.environ['RENODE_ROOT']) if os.environ.get('RENODE_ROOT') else None)
args=ap.parse_args();HERE=args.out
if args.renode_root is None:ap.error('provide --renode-root or RENODE_ROOT pointing to the calibrated package platform root')
def readcsv(p):
    with p.open() as f:return list(csv.DictReader(f))
def savecsv(name,rows):
    with (HERE/name).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def savejson(name,obj):
    with (HERE/name).open('x') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
boards=readcsv(HERE/'board_resolved_v3/board_targets.csv')
for r in boards:
    r['rtc_clock_evidence']=r['rtc_clock_evidence'].replace(str(Z.resolve())+'/','')
savecsv('stm32_board_targets.csv',boards)
summary=json.loads((HERE/'board_resolved_v3/board_summary.json').read_text())
summary.update(unique_board_directories_with_active_lsi_rtc=len({r['board_directory'] for r in boards if r['rtc_active_source']=='LSI'}),
    unique_board_directories_with_active_lse_rtc=len({r['board_directory'] for r in boards if r['rtc_active_source']=='LSE'}),
    unique_board_directories_with_iwdg_enabled=len({r['board_directory'] for r in boards if int(r['iwdg_enabled'])}),
    completeness_check='All board.yml directories naming an STM32 SoC checked; only omitted DTS was 96b_carbon_nrf51822, which targets the Nordic coprocessor, not STM32',
    preliminary_outputs='Root board_targets.csv and board_resolved_v2 are diagnostic passes, superseded by stm32_board_targets.csv after correcting APB gate/source distinction and include paths; no experiment records altered')
savejson('stm32_board_summary.json',summary)
cases=readcsv(HERE/'cases_reviewed_v2/case_inventory.csv')
for r in cases:
    cues=json.loads(r['timing_evidence']);unique={}
    for e in cues:unique.setdefault((e['file'],e['line']),e)
    r['timing_evidence']=json.dumps(list(unique.values()),separators=(',',':'))
    c=r['case'].split('.')[-1]
    r['visible_timing_assumption']='wait/timeout cue in case, callback or fixture; requires semantic review' if cues else 'no explicit wait found'
    if c=='test_set_get_time':r['visible_timing_assumption']='immediate readback constrained to requested calendar second or next second'
    if c=='test_09c_wdt_feed_stall':r['visible_timing_assumption']='five immediately repeated feeds expected to stall after first feed; implicit operation-latency premise'
    if c=='test_wdt':r['visible_timing_assumption']='watchdog windows, callback sleeps and reboot-dependent progression; prior fidelity probe failed'
    r['configuration_gate']='application default / board-dependent'
    if '/rtc_api' in r['app']:
        r['configuration_gate']={'test_alarm':'CONFIG_RTC_ALARM','test_alarm_callback':'CONFIG_RTC_ALARM',
            'test_update_callback':'CONFIG_RTC_UPDATE; STM32 API lacks implementation, expected skip',
            'test_set_get_calibration':'CONFIG_RTC_CALIBRATION; F4 model CALR fields are tags, not calibrated-rate behavior',
            'test_y2k':'compiled normally; STM32 rejects pre-2000 year, expected skip'}.get(c,'compiled normally')
    if '/counter_basic_api' in r['app']:r['configuration_gate']='RTC-only overlay and CONFIG_COUNTER_RTC_STM32; optional separately approved SUBSECONDS configuration repeats the same 11 cases'
    if '/counter_seconds' in r['app']:r['configuration_gate']='new rtc_0 alias/RTC-counter configuration; stock YAML does not select STM32'
savecsv('test_cases.csv',cases)
app_counts=Counter(r['app'] for r in cases if r['in_requested_inventory']=='yes')
savejson('case_counts.json',dict(requested_rows=sum(app_counts.values()),ztest_declarations=sum(r['case_kind']=='ztest' and r['in_requested_inventory']=='yes' for r in cases),
    console_behaviors=sum(r['case_kind']=='console' and r['in_requested_inventory']=='yes' for r in cases),by_application=dict(app_counts),
    prospective_non_watchdog_unique_cases=19,warning='Declarations and possible configurations, not confirmed build/run/evaluable subjects'))

platform_root=args.renode_root
platform_hashes={}
def expand(p,seen=None):
    p=p.resolve();seen=set() if seen is None else seen
    if p in seen:return ''
    seen.add(p);b=p.read_bytes();platform_hashes[str(p.relative_to(platform_root))]=hashlib.sha256(b).hexdigest();s=b.decode()
    for inc in re.findall(r'using\s+"([^"]+)"',s):
        q=p.parent/inc if inc.startswith('.') else platform_root/inc
        if q.is_file():s+='\n'+expand(q,seen)
    return s
platforms=[]
for p in sorted((platform_root/'platforms/boards').glob('*.repl')):
    s=expand(p)
    if 'STM32' not in s:continue
    platforms.append(dict(platform=str(p.relative_to(platform_root)),
        rtc_models=','.join(sorted(set(re.findall(r'rtc\w*:\s*(?:Timers\.)?(STM32\w*RTC)',s)))),
        iwdg_model_present='yes' if 'STM32_IndependentWatchdog' in s else 'no',
        evidence='static recursive using-closure; peripheral presence is not test compatibility or fidelity'))
savecsv('renode_platform_inventory.csv',platforms)
savejson('renode_platform_hashes.json',platform_hashes)
prefix='https://www.st.com/resource/en/datasheet/'
board_candidates=[
 dict(board='stm32f4_disco',platform='platforms/boards/stm32f4_discovery.repl',chip='STM32F407VG',lsi_min_khz=17,lsi_typ_khz=32,lsi_max_khz=47,conditions='VDD=3 V; TA=-40..105 C',document='DS8626 Rev 12, Table 35, p.105',url=prefix+'stm32f407vg.pdf',default_rtc='LSI',rtc_model='STM32F4_RTC',iwdg_model='present; prior fidelity failure',qualification='existing calibration for selected RTC cases only; expanded applications/configurations unverified'),
 dict(board='nucleo_f767zi',platform='platforms/boards/nucleo_f767zi.repl',chip='STM32F767ZI (platform inherits STM32F777 family model)',lsi_min_khz=17,lsi_typ_khz=32,lsi_max_khz=47,conditions='VDD=3 V; TA=-40..105 C',document='DS11532 Rev 9, Table 46, p.140',url=prefix+'stm32f767zi.pdf',default_rtc='LSI',rtc_model='STM32F4_RTC',iwdg_model='absent',qualification='priority candidate; existing Zephyr DTS and Renode board; build and timing calibration not run'),
 dict(board='stm32f746g_disco',platform='platforms/boards/stm32f7_discovery-bb.repl',chip='STM32F746NG',lsi_min_khz=17,lsi_typ_khz=32,lsi_max_khz=47,conditions='VDD=3 V; TA=-40..105 C',document='DS10916 Rev 5; LSI oscillator characteristics table (PDF/index pagination inconsistent, page omitted)',url=prefix+'stm32f746ng.pdf',default_rtc='LSI',rtc_model='STM32F4_RTC',iwdg_model='absent',qualification='priority candidate; build, console/platform matching and timing calibration not run'),
 dict(board='nucleo_h753zi',platform='platforms/boards/nucleo_h753zi.repl',chip='STM32H753ZI',lsi_min_khz=29.76,lsi_typ_khz=32,lsi_max_khz=33.60,conditions='VDD=1.62..3.6 V; TJ=-40..105 C common envelope of Tables38/135. Rev V specifies minimum29.4 at125 C; freeze revision/grade before S2.',document='DS12117 Rev 10, Tables 38/135, pp.129/233',url=prefix+'stm32h753zi.pdf',default_rtc='LSI',rtc_model='STM32F4_RTC',iwdg_model='present; not reset-qualified',qualification='priority narrower-range candidate; silicon revision and temperature envelope must be frozen before S2'),
 dict(board='stm32h747i_disco/stm32h747xx/m7',platform='platforms/boards/stm32h747-disco.repl',chip='STM32H747XI',lsi_min_khz=29.76,lsi_typ_khz=32,lsi_max_khz=33.60,conditions='TJ=-40..110 C; VDD=1.62..3.6 V; minimum29.4 at125 C',document='DS12930 Rev 3, Table 48, p.142',url=prefix+'stm32h747xi.pdf',default_rtc='disabled',rtc_model='STM32F4_RTC',iwdg_model='present; not reset-qualified',qualification='conditional; needs approved LSI/RTC overlay, single-core boot/console and peripheral qualification'),
 dict(board='stm32f072b_disco',platform='platforms/boards/stm32f072b_discovery.repl',chip='STM32F072RB',lsi_min_khz=30,lsi_typ_khz=40,lsi_max_khz=50,conditions='VDDA=3.3 V; TA=-40..105 C',document='DS9826 Rev 6, Table 44, p.74; verified PDF first page identifies F072 despite incorrect web metadata title',url=prefix+'stm32f072rb.pdf',default_rtc='disabled',rtc_model='STM32F4_RTC',iwdg_model='absent',qualification='conditional; needs approved RTC/LSI overlay and explicit divider policy for40-kHz nominal oscillator; do not transplant F4 thresholds'),
]
savecsv('board_candidates.csv',board_candidates)
estimates=[]
for b in board_candidates:
    for option,nconfig,caseconfig,est in [('three_apps_rtc_and_1Hz_counter',3,19,2.0),('plus_counter_subseconds',4,30,3.0)]:
        estimates.append(dict(board=b['board'],option=option,distinct_declared_cases=19,application_configurations=nconfig,
            schedule_launches=nconfig*102,nominal_launches=nconfig*5,primary_launches=nconfig*107,
            scheduled_case_configuration_slots=caseconfig*102,estimated_total_su=est,workers_provisional=32,
            scope='proposal only; no jobs authorized. Includes nominal/primary and provisional qualification/replay/reference allowance; skips/missing outcomes remain distinct',
            costing='Assumed wall seconds per full launch: RTC180, counter600, seconds60; optional subsecond counter600. /32 workers /3600; add30% overhead,0.25SU qualification and contingency. New application timing is unmeasured; recost after qualification.'))
savecsv('run_estimates.csv',estimates)
documents=[
 dict(number='AN5067',title='How to optimize STM32 MCUs internal RC oscillator accuracy',url='https://www.st.com/resource/en/application_note/dm00425536-how-to-optimize-stm32-mcus-internal-rc-oscillator-accuracy-stmicroelectronics.pdf',revision='Rev 1, March2018',evidence='Introduction and sections2/3 discuss assembly, thermal and mechanical effects. Figure1 measures HSI16 on500 STM32F767 boards, not LSI. Does not supply a usable F407 LSI population distribution.'),
 dict(number='AN5126',title='How to calibrate internal oscillators on STM32G0 MCUs',url='https://www.st.com/resource/en/application_note/dm00469014-using-xcuberccalib-software-to-calibrate-stm32g0-series-internal-rc-oscillator-stmicroelectronics.pdf',revision='Rev 2, April2023',evidence='Sections2/3/4 distinguish HSI trimming from LSI measurement, discuss process/temperature/voltage effects and timer capture. LSI is measured, not directly trimmed, on this family. No population probability model identified.'),
 dict(number='RM0090',title='STM32F405/415, STM32F407/417, STM32F427/437 and STM32F429/439 advanced Arm-based 32-bit MCUs',url='https://www.st.com/resource/en/reference_manual/dm00031020-stm32f10x-microcontrollers-stmicroelectronics.pdf',revision='Indexed Rev21 clock-measurement section6.2.11, pp160-161; current ST index advertises Rev22 separately',evidence='Verified ST-hosted indexed passage describes manufacturing deviation and TIM5 channel4 LSI measurement, then adjusting RTC prescaler/IWDG timeout. Full local PDF retrieval failed; do not claim an archived PDF or full-manual distribution search.'),
 dict(number='DS8626',title='STM32F405xx STM32F407xx datasheet',url=prefix+'stm32f407vg.pdf',revision='Rev12, Table35 and Figure34',evidence='17/32/47-kHz characterization limits plus min/average/max temperature curves. These are not a device-frequency probability distribution.'),
]
savejson('verified_st_documents.json',documents)

lines=['# S1 subject survey, 2026-10-25','',
'Read-only survey only. No builds, Renode runs, jobs or model generations were performed. E job3532543 was untouched; E2 and paper edits remain held. Stop here for S2 subject/board approval.','',
'## Pins and limits','',
'Zephyr commit: `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056`. Renode calibrated release source: `f1dd1b4af7838b45a925c17603cdfed0a583844a`; infrastructure submodule: `cd4b002aac2398994c4a61a34a8b31b5700facf2`. The model-source URLs and hashes are in `renode_model_sources.json`. S1 registration is the2026-10-25 amendment in `paper/DESIGN.md`.','',
'Build status is verified only where existing frozen records/configurations provide evidence. All new-board and new-config build/run claims remain unverified. Static model presence is insufficient for corpus admission.','',
'## Every case, including exclusions','',
'`test_cases.csv` has68 rows:45 ztest declarations plus one console behavior in the requested applications, and22 declarations in adjacent hardware-free/vendor-specific applications kept as explicit exclusions. The prospective non-watchdog cohort has19 distinct declarations across three applications, not19 independent programs. Conditional compilation, capability skips, build losses, nominal failures and harness errors must remain separate.','',
'| Application | Declarations | STM32F4 evidence and disposition |','|---|---:|---|',
'| rtc/rtc_api |7| Existing full-app build covers5 cases. Update and calibration were not enabled. Y2K is expected to skip because pre-2000 years are rejected; update callback is expected to skip because the STM32 API lacks that operation. Calibration fields are tagged in the model and do not establish oscillator-correction fidelity. |',
'| counter/counter_basic_api |11| Source supports STM32 RTC. Stock F4 overlay instead enables timer counters and disables RTC. A new RTC-only config is required; 1Hz and optional subsecond variants repeat the same cases. Capability skips are expected but not measured. |',
'| counter/counter_seconds |1| Source uses rtc_0 alias outside CMOS; stock YAML only selects x86/NXP. A new alias/config could target the STM32 RTC counter; no C changes or builds performed. |',
'| watchdog/wdt_basic_api |1| Existing configured build succeeds, but the prior five fidelity probes never demonstrate reboot and case completion. Exclude from production until independently qualified. |',
'| watchdog/wdt_basic_reset_none |2| Stock filter is not STM32; reset-none/callback capabilities do not match STM32 IWDG. |',
'| watchdog/wdt_error_cases |23| Stock platform list excludes STM32 and several required capabilities are unavailable. Inventory is exhaustive, not a claim of23 runnable STM32 subjects. |',
'| watchdog/wdt_variables |0 ztests;1 console behavior| Nordic-only platform list. Not an additional STM32 case. |','',
'The CSV records each case name, exact source span, build evidence, model status, source-reachable timing cues, configuration gate and caveats. Wait cues include callbacks/function-pointer helpers and fixtures; they are not a proof that every cue is an unjustified bound.','',
'### Prospective case names','']
for app in ['rtc_api','counter_basic_api','counter_seconds']:
    lines.append('- **'+app+'**: '+', '.join('`'+r['case']+'`' for r in cases if r['app'].endswith('/'+app))+'.')
lines+=['','## Board survey','',
'All233 STM32 DTS targets resolved, across210 board directories. `stm32_board_targets.csv` is the final full list; diagnostic passes are superseded. The survey preprocesses the include tree and resolves labels/phandles, distinguishes APB gate clocks from source selectors and honors peripheral/ancestor status. No application overlays or firmware configuration builds are applied. The only independent board.yml cross-check omission is the Nordic coprocessor target of96Boards Carbon, which is not an STM32 target.','',
'| Default board DTS state | Targets |','|---|---:|','| RTC enabled with LSI selection |106|','| RTC enabled with LSE selection |40|','| RTC enabled, source not selected/resolved |4|','| RTC disabled or absent |83|','| Total |233|','',
'The four enabled-but-unselected cases are Arduino Opta/Portenta H7 M4/M7 targets. Their DTS has an APB gate clock but no RTC source specifier; no LSI/LSE choice was inferred. LSI RTC targets span104 board directories; LSE targets span35, with variants counted separately above. This is repository-configuration prevalence, not deployed-board or physical-frequency prevalence.','',
'IWDG is DT-enabled on101 targets (96 board directories).55 of those also enable the LSI clock node;46 do not. This does not mean46 watchdogs lack a clock: the STM32 driver and hardware force LSI on when IWDG starts. The overlap cannot establish that LSI was enabled exclusively for IWDG rather than RTC or another peripheral.','',
'## Boards and verified oscillator bounds','',
'| Board | Default RTC | LSI kHz | Renode RTC / IWDG | Status |','|---|---|---|---|---|']
for b in board_candidates:lines.append('|'+b['board']+'|'+b['default_rtc']+'|'+str(b['lsi_min_khz'])+'–'+str(b['lsi_max_khz'])+'|'+b['rtc_model']+' / '+b['iwdg_model']+'|'+b['qualification']+'|')
lines+=['',
'The priority new-board candidates are F767ZI, F746G Discovery and H753ZI. H753 changes the clock-range stratum; F767/F746 retain the wider17–47-kHz range. These share the STM32 RTC driver family and often the same Renode RTC model, so they do not provide an independent simulator or a different-vendor replication. All need nominal and endpoint/reference qualification before production.','',
'H747 requires RTC/LSI enablement and core/boot qualification. F072 requires an explicit40-kHz divider policy: the RTC driver defaults to128×250 for an LSI source, so the F4 equation cannot simply be transplanted. Both are conditional proposals.','',
'Additional model-presence findings: `nucleo_wba52cg.repl` has no matching board definition in this Zephyr pin (WBA55 is a different target); `ramn.repl` also lacks a matching pinned board. RAMN uses STM32L_RTC, whose source supplies a1000-Hz guessed wakeup timer rather than a qualified calendar model. Do not admit them as ready-to-run boards. Their entries remain in `renode_platform_inventory.csv`.','',
'## Costed proposal, not submitted work','',
'Minimal option per approved board: three full applications,5 nominal launches plus100 settings and two endpoints each =321 firmware launches, with1,938 scheduled case-verdict slots before skips and95 nominal case slots. Optional subsecond counter adds107 launches, repeating11 cases:428 launches total,3,060 scheduled case/config slots. Neither option launches one Slurm task per case; each Launcher line executes one full application/configuration at one frequency.','',
'Planning costs use32 workers, assumed full-launch wall caps of180s for RTC,600s for generic counter and60s for seconds-rate; optional subsecond counter adds another600s. Nominal/primary ideal totals are0.78SU or1.34SU per board. After30% overhead, qualification minimum and a provisional replay/reference reserve, budget approximately2SU (minimal) or3SU (with subsecond) per board. These are unmeasured new-app estimates; the contingent replay/reference workload is not known. Recost and report exact node/wall/SU requests before any normal submission. New-app RSS must keep concurrency below80% of node memory.','',
'For existing F4 plus the three priority new boards:1,284 primary launches and7,752 scheduled case slots, about8SU under the minimal planning budget; optional subsecond configs give1,712 launches and12,240 scheduled case/config slots, about12SU. No S2 job is submitted or approved by S1. Missing, skipped and failed nominal outcomes must not be forced into timing-flip denominators.','',
'## ST documentation and distribution evidence','']
for d in documents:lines.append('- **'+d['number']+': '+d['title']+'** ('+d['revision']+'). '+d['evidence']+' [ST source]('+d['url']+').')
lines+=['',
'No F407 LSI population distribution was identified in the reviewed sources. ST documents manufacturing and environmental variability and measurement/compensation techniques. Datasheet envelopes and temperature curves do not justify treating uniform sampling as a measured share of devices. AN5067 does show a500-device HSI example; it is not an LSI distribution. Any normal distributions in S3 must remain explicitly illustrative. Full local ST PDF download attempts failed (TLS/transport); the titles/passages/tables above were verified through ST-hosted indexed PDF content. Do not claim locally archived ST PDFs.','',
'## Stop','',
'S1 is complete only as a survey. Approve subjects, board/configuration choices and qualification scope before S2; no distribution calculations, coverage runs, new generation specifications or model calls have been executed. E remains untouched and E2 remains held.']
report='\n'.join(lines)+'\n'
report=re.sub(r'\b(the|All|all|has|and|not|of|on|span|mean|requires|supplies|with|includes|covers|approximately|than|for|about|use|before|after|are|at|by|per|Figure|Table|Rev|sections|section|March|April|above|times|from|adds|repeating)(?=\d)',r'\1 ',report)
report=re.sub(r'(?<=\d)(SU|Hz|s)(?=\b)',r' \1',report)
(HERE/'REPORT.md').write_text(report)
print('Exported final S1 CSVs, document register and report')
