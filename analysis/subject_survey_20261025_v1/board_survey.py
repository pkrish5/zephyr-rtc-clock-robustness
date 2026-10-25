#!/usr/bin/env python3
"""Read-only STM32 board-DTS survey, not a firmware build or simulator run."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument('--zephyr',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
ap.add_argument('--work',type=Path,required=True)
ap.add_argument('--cpp',default='/Library/Developer/CommandLineTools/usr/bin/clang')
a=ap.parse_args();z=a.zephyr.resolve();a.out.mkdir(exist_ok=True);a.work.mkdir(exist_ok=True)
sys.path.insert(0,str(z/'scripts/dts/python-devicetree/src'))
from devicetree import dtlib
inc=[z/'dts',z/'dts/common',z/'dts/arm',z/'dts/arm64',z/'dts/riscv',z/'dts/vendor',z/'boards',z/'include',z/'include/zephyr',z.parent/'modules/hal/stm32/dts']
hashes={};memo={}
def text(p):
    b=p.read_bytes();hashes[str(p)]=hashlib.sha256(b).hexdigest();return b.decode(errors='replace')
def stm32_candidate(p,seen=None):
    p=p.resolve()
    if p in memo:return memo[p]
    seen=set() if seen is None else seen
    if p in seen:return False
    seen.add(p);s=text(p)
    for match in re.finditer(r'^\s*#\s*include\s*[<"]([^>"\n]+)',s,re.M):
        name=match[1]
        if re.search(r'stm32[^/]*\.(?:dtsi|h)$',name,re.I):memo[p]=True;return True
        q=next((q for q in [p.parent/name,*[d/name for d in inc]] if q.is_file()),None)
        if q and stm32_candidate(q,seen):memo[p]=True;return True
    memo[p]=False;return False
def enabled(n):
    while n is not None:
        if 'status' in n.props and n.props['status'].to_string() not in ('ok','okay'):return False
        n=n.parent
    return True
def compat(n):
    return n.props['compatible'].to_strings() if 'compatible' in n.props else []
def source(n,d):
    found=[];specs=[]
    for key in ('clocks','assigned-clock-parents'):
        prop=n.props.get(key)
        if not prop:continue
        raw=prop.value
        nums=[int.from_bytes(raw[i:i+4],'big') for i in range(0,len(raw),4)]
        i=0;decoded=[]
        while i<len(nums):
            provider=d.phandle2node.get(nums[i]);i+=1
            if provider is None:specs.append('unresolved phandle');break
            count=provider.props['#clock-cells'].to_num() if '#clock-cells' in provider.props else 0
            args=nums[i:i+count];i+=count
            specs.append(provider.path+':'+','.join(hex(v) for v in args))
            decoded.append((provider,count,args))
        # On this binding, clocks[0] gates the APB bus and clocks[1]
        # selects the RTC source. Do not mistake a bus ID for an oscillator.
        selected=decoded[1:] if key=='clocks' and len(decoded)>1 else decoded
        for provider,count,args in selected:
            labels=set(provider.labels)
            if 'clk_lsi' in labels or 'clk-lsi' in provider.name:found.append('LSI')
            elif 'clk_lse' in labels or 'clk-lse' in provider.name:found.append('LSE')
            elif count==2 and any('stm32' in c and 'rcc' in c for c in compat(provider)):
                # Pinned stm32_common_clocks.h defines LSI=0x003, LSE=0x002.
                if args and args[0] in (2,3):found.append({2:'LSE',3:'LSI'}[args[0]])
                elif args and args[0] in (4,5,6,7):found.append('other_clock_selector')
    return ('+'.join(sorted(set(found))) if found else 'unresolved_or_not_selected'),'; '.join(specs)
rows=[]
candidates=[p for p in sorted((z/'boards').rglob('*.dts')) if stm32_candidate(p)]
for idx,p in enumerate(candidates):
    rel=p.relative_to(z);target=str(rel.with_suffix(''));f=a.work/(str(idx)+'.dts')
    cmd=[a.cpp,'-E','-x','assembler-with-cpp','-nostdinc','-undef','-D__DTS__',*['-I'+str(d) for d in inc],str(p)]
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=30)
    row=dict(dts=str(rel),board_directory=str(rel.parent),target=p.stem,dts_sha256=hashes[str(p.resolve())],parse_status='unresolved',error='',
        rtc_nodes=0,rtc_enabled=0,rtc_source='unknown',rtc_active_source='none',rtc_clock_specs='',rtc_clock_evidence='',
        lsi_node_present=0,lsi_enabled=0,lse_enabled=0,iwdg_nodes=0,iwdg_enabled=0,iwdg_enabled_and_lsi_dt_enabled=0,
        iwdg_clock_note='IWDG hardware forces LSI when started; DTS clock-node status alone does not show runtime activation',
        scope='board DTS defaults; no application overlays or firmware build')
    if r.returncode:row['error']=r.stderr[-1500:]
    else:
        f.write_text(r.stdout)
        try:
            d=dtlib.DT(str(f));nodes=list(d.node_iter())
            if not any(any('st,stm32' in c for c in compat(n)) for n in nodes):
                row['parse_status']='not_stm32_after_resolution';rows.append(row);continue
            rtc=[n for n in nodes if any(c.startswith('st,stm32') and c.endswith('-rtc') for c in compat(n))]
            watchdog=[n for n in nodes if any(c in ('st,stm32-watchdog','st,stm32-iwdg') for c in compat(n))]
            lsi=[n for n in nodes if 'clk_lsi' in n.labels or n.name.startswith('clk-lsi')]
            lse=[n for n in nodes if 'clk_lse' in n.labels or n.name.startswith('clk-lse')]
            sources=[source(n,d)[0] for n in rtc]
            active=[source(n,d)[0] for n in rtc if enabled(n)]
            row.update(parse_status='resolved',rtc_nodes=len(rtc),rtc_enabled=sum(map(enabled,rtc)),
                rtc_source='|'.join(sources) if sources else 'no_rtc_node',rtc_active_source='|'.join(active) if active else 'none',
                rtc_clock_specs=' | '.join(source(n,d)[1] for n in rtc),
                rtc_clock_evidence='; '.join(str(n.props['clocks'].filename)+':'+str(n.props['clocks'].lineno) for n in rtc if 'clocks' in n.props),
                lsi_node_present=int(bool(lsi)),lsi_enabled=int(any(map(enabled,lsi))),lse_enabled=int(any(map(enabled,lse))),
                iwdg_nodes=len(watchdog),iwdg_enabled=sum(map(enabled,watchdog)),
                iwdg_enabled_and_lsi_dt_enabled=int(any(map(enabled,watchdog)) and any(map(enabled,lsi))))
            for loc in re.findall(r'^#\s+\d+\s+"([^"]+)"',r.stdout,re.M):
                q=Path(loc)
                if q.is_file() and str(q.resolve()).startswith(str(z.parent)):text(q.resolve())
        except (dtlib.DTError,ValueError,KeyError) as e:row['error']=str(e)
    rows.append(row)
    if idx%100==0:print(idx+1,'/',len(candidates),flush=True)
with (a.out/'board_targets.csv').open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
valid=[r for r in rows if r['parse_status']=='resolved']
summary=dict(unit='board DTS target, not sold board or physical-device prevalence',candidate_targets=len(rows),resolved_targets=len(valid),
    status=dict(Counter(r['parse_status'] for r in rows)),unique_board_directories=len({r['board_directory'] for r in valid}),
    all_rtc_source_selections=dict(Counter(r['rtc_source'] for r in valid)),active_rtc_sources=dict(Counter(r['rtc_active_source'] for r in valid)),
    targets_with_iwdg_enabled=sum(r['iwdg_enabled']>0 for r in valid),
    targets_with_iwdg_and_lsi_dt_enabled=sum(r['iwdg_enabled_and_lsi_dt_enabled'] for r in valid),
    targets_with_lsi_enabled=sum(r['lsi_enabled'] for r in valid),
    caveat='LSI may also feed RTC or other peripherals. Co-enabling LSI and IWDG does not establish exclusive intent; hardware starts LSI when IWDG starts.')
(a.out/'board_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(a.out/'board_input_hashes.json').write_text(json.dumps(hashes,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
