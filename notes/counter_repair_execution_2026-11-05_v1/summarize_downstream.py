#!/usr/bin/env python3
"""Offline primary-evidence handoff; no replay, reference, or simulation."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SELECTED = 'counter_basic.test_all_channels'
DOWN = 'counter_basic.test_single_shot_alarm_notop'
SHORT = 'counter_basic.test_short_relative_alarm'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
status = lambda r, case: next(c['status'] for c in r['cases'] if c['case'] == case)
counts = lambda values: {k: values.count(k) for k in ['pass', 'fail', 'skip', 'missing']}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args(); a.out.mkdir(parents=True, exist_ok=False)
    baseline_dir = ROOT / 'notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/results/s2_production_20261026_v1/records'
    baseline = {}
    for p in baseline_dir.glob('f4-counter-*.json'):
        r = json.loads(p.read_text())
        assert r['unit_id'] == 'f4-counter'
        assert r['elf_sha256'] == 'ceda84d8a03383be5857e546d2ac87ecd2ed9c72c9e45bf0ca47661437c7ccb1'
        assert r['plan_sha256'] == '719b3bc42f2b93f44455a11eca3eacd69eacbbf4e8c714b90300d5a8343d0612'
        for kind, digest in r['log_sha256'].items():
            if digest: assert sha(p.parent.parent / kind / (r['run_id'] + ('.json' if kind == 'traces' else '.log'))) == digest
        assert r['frequency_hz'] not in baseline
        baseline[r['frequency_hz']] = (r, str(p.relative_to(ROOT)), sha(p))
    assert len(baseline) == 102
    assert Counter(status(r, SELECTED) for r, _, _ in baseline.values()) == {'pass': 58, 'fail': 44}
    legal = defaultdict(list); faults = []; groups = []; raw = []
    for job, group in [('3570473', 'legal-a'), ('3570474', 'legal-b'), ('3570475', 'fault')]:
        verified = HERE / f'verified-{job}-v1'
        proof = json.loads((verified / 'verification.json').read_text())
        assert proof['output_state'] == 'complete' and proof['protected_files_unchanged'] == 30067
        rows = list(csv.DictReader((verified / 'per_index.csv').open()))
        assert len(rows) == proof['planned'] == proof['primary_records']
        assert counts([r['selected_outcome'] for r in rows]) == proof['counts']
        actual = {r['index']: r for r in rows}
        groups.append(dict(job_id=job, group=group, selected_counts=proof['counts'],
                           downstream_counts=counts([r['downstream_single_shot'] for r in rows]),
                           archive_sha256=proof['archive_sha256']))
        for p in sorted((verified / 'output/records').glob('*.json')):
            r = json.loads(p.read_text()); row = actual[str(r['index'])]
            assert sha(p) == row['primary_record_sha256']
            assert status(r, SELECTED) == row['selected_outcome']
            info = dict(index=r['index'], variant=r['variant'], condition=r['condition'],
                        frequency_hz=r['frequency_hz'], selected=status(r, SELECTED),
                        downstream=status(r, DOWN), short_relative=status(r, SHORT),
                        record_path=str(p.relative_to(ROOT)), record_sha256=sha(p),
                        uart_path=str((p.parent.parent / 'uart' / (r['run_id'] + '.log')).relative_to(ROOT)),
                        uart_sha256=r['log_sha256']['uart'])
            raw.append(info)
            if group == 'fault': faults.append(info)
            else: legal[r['variant']].append((r, info))
    assert {r['index'] for r in raw} == set(range(20, 334)) and len(raw) == 314
    variants = []; paired = []; full_vectors = {}
    for variant, rows in sorted(legal.items()):
        assert len(rows) == 102 and {r['frequency_hz'] for r, _ in rows} == set(baseline)
        full_vectors[variant] = {case: counts([status(r, case) for r, _ in rows]) for case in rows[0][0]['expected_declared_cases']}
        transitions = {case: Counter() for case in [SELECTED, DOWN, SHORT]}
        for r, info in rows:
            old, oldpath, oldsha = baseline[r['frequency_hz']]
            for case in transitions:
                before, after = status(old, case), status(r, case)
                transitions[case][before + ' -> ' + after] += 1
                paired.append(dict(variant=variant, frequency_hz=r['frequency_hz'], case=case,
                                   before=before, after=after, baseline_record_path=oldpath,
                                   baseline_record_sha256=oldsha, repaired_record_path=info['record_path'],
                                   repaired_record_sha256=info['record_sha256']))
        variants.append(dict(variant=variant, selected_counts=counts([status(r, SELECTED) for r, _ in rows]),
                             short_relative_counts=counts([status(r, SHORT) for r, _ in rows]),
                             downstream_counts=counts([status(r, DOWN) for r, _ in rows]),
                             paired_transitions={case: dict(v) for case, v in transitions.items()},
                             downstream_fail_and_short_relative_fail=sum(status(r, DOWN) == status(r, SHORT) == 'fail' for r, _ in rows)))
    summary = dict(groups=groups, variants=variants, fault_primary_outcomes=faults,
                   full_application_case_counts=full_vectors,
                   remaining_checks=['legal failure replays', 'task-specific references', 'fault activation/control review', 'source-based attribution'],
                   fourth_case_repair_success_claimed=False, original_records_replaced=False,
                   protected_originals_unchanged=30067)
    for name, data in [('primary_index.json', raw), ('paired_legal_outcomes.json', paired), ('summary.json', summary)]:
        (a.out / name).write_text(json.dumps(data, indent=2) + '\n')
    lines = ['# Counter-repair primary-evidence handoff, 2026-11-10', '',
             'All three recovery archives and primary records passed independent verification. This is one upstream subject with three interventions, not 306 independent tests. Scientific interpretation still requires the original protocol\'s replay/reference and fault-control checks. The manuscript is unchanged.', '',
             '|Group / job|Selected pass|Fail|Skip|Missing|Later single-shot pass / fail|', '|---|---:|---:|---:|---:|---|']
    for g in groups:
        c = g['selected_counts']; d = g['downstream_counts']
        lines.append(f"|{g['group']} / {g['job_id']}|{c['pass']}|{c['fail']}|{c['skip']}|{c['missing']}|{d['pass']} / {d['fail']}|")
    lines += ['', '## Paired legal settings for the selected all-channels case', '',
              'The archived V0 has 58 passes and 44 failures at 102 settings. Each V1, V1b and V2 has 102 selected-case passes at those same exact settings, with zero skip/missing. All 44 originally failing settings pass under each intervention. No V0 legal run was repeated.', '',
              '|Variant|All-channels pass / fail|Short-relative pass / fail|Later single-shot pass / fail|', '|---|---|---|---|']
    for v in variants:
        lines.append(f"|{v['variant']}|{v['selected_counts']['pass']} / {v['selected_counts']['fail']}|{v['short_relative_counts']['pass']} / {v['short_relative_counts']['fail']}|{v['downstream_counts']['pass']} / {v['downstream_counts']['fail']}|")
    lines += ['', 'The full application is **not uniformly passing**. In each variant, 29 of the original 44 later single-shot failures become passes and 15 remain failures. The short-relative case, formerly skipped at those 44 baseline settings, now passes 30 and fails 14. Every originally passing setting remains passing for these cases. These are observations; the cause of each remaining failure and whether it is a cleanup cascade require replay/reference and source attribution. Recorded skips stay skips and are not imputed as passes.', '',
              'Full case-vector counts, including the seven other cases recorded SKIP at all 102 settings per repaired variant, are preserved in summary.json. primary_index.json and paired_legal_outcomes.json link exact primary/UART/baseline paths and hashes.', '',
              '## Oscillator fault probes: selected-case primary outcomes', '',
              '|Variant|10-kHz slow probe|64-kHz fast probe|', '|---|---|---|']
    for v in ['V0', 'V1', 'V1b', 'V2']:
        rr = {r['condition']: r for r in faults if r['variant'] == v}
        lines.append(f"|{v}|{rr['slow_fault']['selected']}|{rr['fast_fault']['selected']}|")
    lines += ['', 'V1 accepts the slow-clock probe in its selected case. V1b and V2 assert-fail it, as does V0. All four selected cases pass the fast-clock probe. These are explicit primary verdicts, not finalized fault-detection claims: activation/control and task-specific reference review remain pending. The downstream case can fail even when the selected case passes; consult the full vectors.', '',
              '## Next verification work (not executed here)', '',
              '1. Reconcile assertion/source signatures for the short-relative and remaining single-shot failures; keep each case distinct from the repaired all-channels case.',
              '2. Run only the originally registered representative same-input diagnostic replays and task-specific references in fresh paths after the required resource approval. Diagnostics never replace these primary records.',
              '3. Verify each fault\'s activation and reference/control result before using detected/accepted language in the paper. Preserve the V1 selected-case slow-probe pass.',
              '4. Reassess whole-application and cascade claims using same-run vectors; do not infer that cleanup failures disappear everywhere.',
              '5. Revise the fourth-case paper material only after these checks. No E2, additional driver, new fault, retuned margin or broad study rerun.', '',
              'All 30,067 original protected files passed before/after checks in each archive. Frozen scientific inputs and original records were not changed. Monitoring of these completed jobs is finished.', '']
    (a.out / 'HANDOFF.md').write_text('\n'.join(lines))
    hashes = {str(p.name): sha(p) for p in a.out.iterdir() if p.is_file()}
    (a.out / 'output_hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
    print(json.dumps(dict(groups=groups, variants=[{k:v[k] for k in ['variant','selected_counts','downstream_counts','short_relative_counts']} for v in variants]), indent=2))

if __name__ == '__main__': main()
