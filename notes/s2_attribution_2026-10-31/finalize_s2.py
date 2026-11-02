#!/usr/bin/env python3
"""Read-only S2 analysis from verified primary/replay archives and frozen sources.

The output is source-supported attribution, not completed reference validation.
No simulation, build, replacement verdict, or source modification occurs here.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, sort_keys=True)
        stream.write('\n')


def csv_save(path, rows):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


CASES = {
    'rtc_api.test_alarm': dict(category='a', subtype='single-boundary waiting',
        source='tests/drivers/rtc/rtc_api/src/test_alarm.c', lines='14-15;177-204',
        excerpts=[(14, 15), (177, 204)], assertion_line=203, wait='3 + 10 host seconds',
        source_boundary='24.615 kHz, ideal zero-phase 320/13',
        explanation='First case in the application; the final alarm-pending assertion requires ten calendar seconds within thirteen host seconds. Its observed vector agrees with the isolated-case vector. The second source repetition is bypassed when the first assertion fails.'),
    'rtc_api.test_alarm_callback': dict(category='b', subtype='calendar-write phase',
        source='tests/drivers/rtc/rtc_api/src/test_alarm_callback.c', lines='13-14;119-141',
        excerpts=[(13, 14), (119, 141)], assertion_line=140, wait='3 + 10 host seconds',
        source_boundary='22.154--24.615 kHz phase envelope; no unique source-only threshold',
        explanation='The calendar write changes date/time but the Renode model retains the fractional ticker count. Prior cases therefore change the remaining ten-second calendar delay. The thirteen-second observation can expire before callback delivery. Phase is inferred from source and boundary shifts, not directly measured.'),
    'rtc_api.test_time_counting': dict(category='b', subtype='calendar-write phase',
        source='tests/drivers/rtc/rtc_api/src/test_time_incrementing.c', lines='15-17;35-59',
        excerpts=[(15, 17), (35, 59)], assertion_line=58, wait='30 polls every 500 ms; last observation about 14.5 s',
        source_boundary='19.862--22.069 kHz phase envelope; last-poll approximation',
        explanation='The calendar-write model preserves the tick phase left by preceding cases. The final calendar observation occurs before the final sleep and timeout assertion; the assertion duration is not the observation budget. The full-application boundary moves below the isolated-case boundary.'),
    'counter_basic.test_all_channels': dict(category='b', subtype='free-running relative-alarm phase',
        source='tests/drivers/counter/counter_basic_api/src/test_counter.c', lines='179-185;658-702',
        excerpts=[(179, 185), (658, 702)], assertion_line=695, wait='3 host seconds for a two-tick relative alarm',
        source_boundary='21.333--32.000 kHz phase envelope: (3-phi)*32/3',
        explanation='The RTC counter driver adds one tick to a relative alarm to compensate the partially started tick. Delivery can require two to three physical ticks, whereas the test waits three host seconds calculated from nominal reported frequency. This phase subtype is a free-running counter phase, not a calendar-write claim.'),
    'counter_basic.test_single_shot_alarm_notop': dict(category='c', subtype='shared-state cleanup cascade',
        source='tests/drivers/counter/counter_basic_api/src/test_counter.c', lines='225-249;473-478;692-701',
        excerpts=[(225, 249), (473, 478), (692, 701)], assertion_line=475, wait='none before observed setup failure',
        source_boundary='none: observed failure is -EBUSY before any wait',
        explanation='The earlier all-channels assertion bypasses alarm cancellation and teardown. This later case fails alarm setup with -16 (-EBUSY), and the driver rejects setup while a callback remains registered. It fails at exactly the earlier case settings. Retain the primary failure, but do not count another independent waiting defect; causality remains source-supported without isolation/reference intervention.'),
    'seconds_counter.test_seconds_rate': dict(category='d', subtype='unresolved clock-accuracy contract',
        source='tests/drivers/counter/counter_seconds/src/main.c', lines='10-12;20-42',
        excerpts=[(10, 12), (20, 42)], assertion_line=41, wait='1200 ms; require one to two integer ticks',
        source_boundary='26.667 kHz ideal zero-phase comparison; not a validated defect boundary',
        explanation='The case explicitly checks roughly 1 Hz and fails its minimum progress assertion. Its observed transition brackets the ideal 32000/1.2 comparison, but a legal-input sensitivity is not necessarily a spurious test failure. The intended clock-accuracy contract has not been established; a relaxed eventual-progress reference would not settle it.'),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    repo = a.repo.resolve()
    notes = repo / 'notes/s2_attribution_2026-10-31'
    evidence = notes / 'returned-3544535/verified/evidence'
    primary = evidence / 'bundle/results/s2_production_20261026_v1'
    plan_path = evidence / 'bundle/plan.json'
    plan = json.loads(plan_path.read_text())
    audit = json.loads((notes / 'returned-3544535/audit/report.json').read_text())
    replay = json.loads((notes / 'replay_comparison_20261102_v1/replay_summary.json').read_text())
    assert audit['raw_log_and_elf_hashes_verified'] and audit['records'] == 1122
    assert replay['status_counts'] == {'identical': 274} and replay['case_failures_in_identical_replays'] == 470
    assert not replay['differences'] and not replay['provenance_problems']
    inputs = {}

    def checked(path, expected=None):
        value = digest(path)
        if expected is not None:
            assert value == expected, path
        inputs[str(path.relative_to(repo))] = value
        return value

    checked(plan_path, audit['plan_sha256'])
    old_map = json.loads((notes / 'returned-3544535/audit/record_sha256.json').read_text())
    records = []
    for p in sorted((primary / 'records').glob('*.json')):
        # The audit's record ledger keys are primary run IDs.
        d = json.loads(p.read_text())
        expected = old_map.get(str(p.relative_to(evidence / 'bundle')))
        if isinstance(expected, dict):
            expected = expected.get('sha256')
        assert expected is not None, (p, list(old_map)[:3])
        checked(p, expected)
        for kind, value in d['log_sha256'].items():
            if value:
                suffix = '.json' if kind == 'traces' else '.log'
                checked(primary / kind / (d['run_id'] + suffix), value)
        records.append(d)
    assert len(records) == 1122
    units = {u['id']: u for u in plan['units']}
    a.out.mkdir(parents=True, exist_ok=False)
    case_rows, failure_rows, category_rows, app_rows = [], [], [], []
    for unit_id, unit in units.items():
        rs = [r for r in records if r['unit_id'] == unit_id]
        assert len(rs) == 102 and all(r['application_completed'] and r['error'] is None for r in rs)
        nominal_rows = list(csv.DictReader((evidence / 'nominal_cases.csv').open()))
        nominal = {r['case']: r['nominal_status'] for r in nominal_rows if r.get('unit_id') == unit_id}
        for case in unit['expected_declared_cases']:
            vals = [(r, next(c['status'] for c in r['cases'] if c['case'] == case)) for r in rs]
            counts = Counter(status for _, status in vals)
            fail = [r['frequency_hz'] for r, status in vals if status == 'fail']
            passes = [r['frequency_hz'] for r, status in vals if status == 'pass']
            skips = [r['frequency_hz'] for r, status in vals if status == 'skip']
            coded = CASES.get(case) if fail else None
            monotone = bool(fail and passes and max(fail) < min(passes))
            row = dict(board=plan['boards'][unit['board_id']]['board'], board_id=unit['board_id'],
                       unit_id=unit_id, case=case, nominal_status=nominal[case],
                       pass_count=counts['pass'], fail_count=counts['fail'], skip_count=counts['skip'], missing_count=0,
                       category=coded['category'] if coded else '', subtype=coded['subtype'] if coded else '',
                       minimum_failed_hz=min(fail) if fail else '', maximum_failed_hz=max(fail) if fail else '',
                       minimum_passed_hz=min(passes) if passes else '', maximum_passed_hz=max(passes) if passes else '',
                       observed_sample_single_transition=monotone,
                       source_boundary=coded['source_boundary'] if coded else '',
                       effective_wait=coded['wait'] if coded else '',
                       source=coded['source'] if coded else '', source_lines=coded['lines'] if coded else '',
                       reference_status='not run', attribution_status='source-supported; not reference-validated' if fail else 'no observed failure')
            case_rows.append(row)
            if coded:
                for r, status in vals:
                    if status != 'fail':
                        continue
                    text = (primary / 'uart' / (r['run_id'] + '.log')).read_text()
                    start = text.index('START - ' + case.split('.')[-1])
                    end = text.find('===================================================================', start)
                    block = text[start:end]
                    match = re.search(r'Assertion failed at (.*?):(\d+):', block)
                    assert match and int(match[2]) == coded['assertion_line'], (r['run_id'], case, block)
                    if coded['category'] == 'c':
                        assert 'err: -16' in block
                        assert any(c['case'] == 'counter_basic.test_all_channels' and c['status'] == 'fail' for c in r['cases'])
                    failure_rows.append(dict(run_id=r['run_id'], board_id=unit['board_id'], unit_id=unit_id,
                        case=case, frequency_hz=r['frequency_hz'], condition=r['condition'], category=coded['category'],
                        assertion_source=match[1], assertion_line=int(match[2]),
                        trace_sha256=r['log_sha256']['traces'], uart_sha256=r['log_sha256']['uart'],
                        replay='identical', reference='not run'))
        cr = [r for r in case_rows if r['unit_id'] == unit_id]
        app_rows.append(dict(board=plan['boards'][unit['board_id']]['board'], unit_id=unit_id,
            application=unit['app'], launches=102, declared_cases=len(cr),
            nominal_runnable=sum(r['nominal_status'] == 'pass' for r in cr),
            nominal_skipped=sum(r['nominal_status'] == 'skip' for r in cr),
            runnable_at_any_setting=sum(r['pass_count'] + r['fail_count'] > 0 for r in cr),
            always_skipped=sum(r['skip_count'] == 102 for r in cr),
            cases_with_any_failure=sum(r['fail_count'] > 0 for r in cr),
            pass_slots=sum(r['pass_count'] for r in cr), fail_slots=sum(r['fail_count'] for r in cr),
            skip_slots=sum(r['skip_count'] for r in cr), missing_slots=0))
    assert len(failure_rows) == 470
    for board_id in ('f4', 'f767', 'f746', 'h753'):
        cr = [r for r in case_rows if r['board_id'] == board_id]
        row = dict(board_id=board_id)
        for cat in 'abcd':
            row[cat + '_cases'] = sum(r['category'] == cat for r in cr)
            row[cat + '_failure_slots'] = sum(r['fail_count'] for r in cr if r['category'] == cat)
        category_rows.append(row)
    csv_save(a.out / 'per_case.csv', case_rows)
    csv_save(a.out / 'per_application.csv', app_rows)
    csv_save(a.out / 'per_board_categories.csv', category_rows)
    csv_save(a.out / 'failure_attribution.csv', failure_rows)

    # Verify board inclusion chains against the exact platform files sealed in the plan.
    platform_rows = []
    chains = {'f4': ['boards/stm32f4_discovery.repl', 'cpus/stm32f4.repl'],
              'f767': ['boards/nucleo_f767zi.repl', 'cpus/stm32f777.repl'],
              'f746': ['boards/stm32f7_discovery-bb.repl', 'cpus/stm32f746.repl'],
              'h753': ['boards/nucleo_h753zi.repl', 'cpus/stm32h753.repl', 'cpus/stm32h743.repl', 'cpus/stm32h7.repl']}
    for board, chain in chains.items():
        for i, relative in enumerate(chain):
            rel = 'platforms/' + relative
            p = evidence / 'bundle/renode' / rel
            value = checked(p, plan['input_sha256']['renode/' + rel])
            lines = p.read_text().splitlines()
            if i < len(chain) - 1:
                assert any('using ' in line and Path(chain[i + 1]).name in line for line in lines)
            else:
                assert any('rtc: Timers.STM32F4_RTC' in line for line in lines)
            platform_rows.append(dict(board_id=board, source=rel, sha256=value, original_platform_sha256=plan['original_platform_sha256'][rel],
                                      role='rtc: Timers.STM32F4_RTC' if i == len(chain) - 1 else 'include'))
    csv_save(a.out / 'platform_model_verification.csv', platform_rows)

    # Reconcile all 102 F4 frequencies for each matched historical isolated RTC case.
    reconciliation, differing = [], []
    families = {'rtc_alarm_pending': 'rtc_api.test_alarm', 'rtc_alarm_callback': 'rtc_api.test_alarm_callback',
                'rtc_time_counting': 'rtc_api.test_time_counting'}
    for family, case in families.items():
        old = [json.loads(p.read_text()) for p in sorted((repo / 'results/rtc_factorial_v2/records').glob('human-' + family + '-*.json'))]
        assert len(old) == 102
        mapping = {}
        for d in old:
            p = repo / 'results/rtc_factorial_v2/records' / (d['run_id'] + '.json')
            checked(p)
            for kind in ('uart', 'trace'):
                checked(repo / d[kind + '_path'], d[kind + '_sha256'])
            assert d['error'] is None and len(d['cases']) == 1
            key = (d['condition'], d['lsi_frequency_hz'])
            assert key not in mapping
            mapping[key] = d
        full = [r for r in records if r['unit_id'] == 'f4-rtc']
        matched = []
        for r in full:
            d = mapping[(r['condition'], r['frequency_hz'])]
            os = d['cases'][0]['status']
            fs = next(c['status'] for c in r['cases'] if c['case'] == case)
            matched.append((r['frequency_hz'], r['condition'], os, fs))
            if os != fs:
                differing.append(dict(case=case, frequency_hz=r['frequency_hz'], condition=r['condition'],
                    isolated=os, full_application=fs, isolated_run_id=d['run_id'], full_run_id=r['run_id']))
        of = [f for f, _, os, _ in matched if os == 'fail']
        op = [f for f, _, os, _ in matched if os == 'pass']
        ff = [f for f, _, _, fs in matched if fs == 'fail']
        fp = [f for f, _, _, fs in matched if fs == 'pass']
        reconciliation.append(dict(case=case, compared_settings=102,
            isolated_seed_failures=sum(os == 'fail' for _, c, os, _ in matched if c == 'seeded'),
            full_seed_failures=sum(fs == 'fail' for _, c, _, fs in matched if c == 'seeded'),
            isolated_all_failures=len(of), full_all_failures=len(ff),
            isolated_last_fail_hz=max(of), isolated_first_pass_hz=min(op),
            full_last_fail_hz=max(ff), full_first_pass_hz=min(fp),
            isolated_fail_full_pass=sum(os == 'fail' and fs == 'pass' for _, _, os, fs in matched),
            isolated_pass_full_fail=sum(os == 'pass' and fs == 'fail' for _, _, os, fs in matched)))
    csv_save(a.out / 'isolated_reconciliation.csv', reconciliation)
    csv_save(a.out / 'isolated_differing_settings.csv', differing)

    # Preserve the dynamic capability gate; do not infer unavailable hardware from a timing skip.
    h753 = [r for r in records if r['unit_id'] == 'h753-counter']
    dynamic = []
    for r in h753:
        status = next(c['status'] for c in r['cases'] if c['case'] == 'counter_basic.test_short_relative_alarm')
        text = (primary / 'uart' / (r['run_id'] + '.log')).read_text()
        start = text.index('START - test_short_relative_alarm')
        block = text[start:text.find('===================================================================', start)]
        assert ('Skipped for rtc@58004000' in block) == (status == 'skip')
        assert ('Testing rtc@58004000' in block) == (status == 'pass')
        dynamic.append(dict(run_id=r['run_id'], frequency_hz=r['frequency_hz'], condition=r['condition'], status=status))
    csv_save(a.out / 'h753_short_relative_capability.csv', dynamic)

    # Source explanations and noncontiguous excerpts with sealed upstream input hashes.
    excerpts = ['# S2 source explanations, 2026-11-02\n\nPost-result source review; reference validation is not complete.\n']
    for case, desc in CASES.items():
        p = repo / 'subjects/upstream/zephyr' / desc['source']
        checked(p, plan['upstream_input_sha256'][desc['source']])
        lines = p.read_text().splitlines()
        excerpts.append('\n## ' + case + '\n\n' + desc['explanation'] + '\n\n`' + desc['source'] + '`\n\n```c\n')
        for low, high in desc['excerpts']:
            excerpts.extend(str(i) + ': ' + lines[i - 1] + '\n' for i in range(low, high + 1))
        excerpts.append('```\n')
    for rel, spans in [('drivers/counter/counter_ll_stm32_rtc.c', [(517, 537), (689, 713)]),
                       ('drivers/rtc/rtc_ll_stm32.c', [(536, 623)]),
                       ('tests/drivers/counter/counter_basic_api/src/test_counter.c', [(979, 1036)])]:
        p = repo / 'subjects/upstream/zephyr' / rel
        checked(p, plan['upstream_input_sha256'][rel])
        lines = p.read_text().splitlines()
        excerpts.append('\n## ' + rel + '\n\n```c\n')
        for low, high in spans:
            excerpts.extend(str(i) + ': ' + lines[i - 1] + '\n' for i in range(low, high + 1))
        excerpts.append('```\n')
    (a.out / 'source_explanations.md').write_text(''.join(excerpts))
    csv_save(a.out / 'per_test_explanations.csv', [dict(case=k, **{f: v for f, v in d.items() if f != 'excerpts'}) for k, d in CASES.items()])
    summary = dict(primary_launches=len(records), primary_case_slots=dict(Counter(c['status'] for r in records for c in r['cases'])),
        replay_summary=replay, categories_by_board=category_rows,
        category_failure_slots={c: sum(r['category'] == c for r in failure_rows) for c in 'abcd'},
        source_supported_attribution_only=True, reference_runs=0, reference_validated_brittle_cases=0,
        no_new_experiments=True, original_records_changed=0,
        h753_short_relative_status_counts=dict(Counter(r['status'] for r in dynamic)))
    save(a.out / 'summary.json', summary)
    save(a.out / 'analysis_inputs_sha256.json', inputs)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
