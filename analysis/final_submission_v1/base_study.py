"""Reconcile original RTC data with A–B, preserving every missing verdict."""
from collections import Counter, defaultdict
from fractions import Fraction
import math
import re
from pathlib import Path

from common import fisher, sha, wilson


AB = 'artifacts/tacc_phase2_20261024_v1/returned-ab-complete/verified-bundle'


def build(inputs):
    old = inputs.json('analysis/rtc_factorial_v2_final_summary.json')
    roster = {r['suite_id']: r for r in old['suite_distribution']}
    assert len(roster) == 66
    human_ids = {'human-' + family for family in ('rtc_alarm_callback', 'rtc_alarm_pending', 'rtc_time_counting')}
    records = defaultdict(dict)
    paths = {}
    old_manifest = inputs.json('results/rtc_factorial_v2/manifest.json')
    old_manifest_sha = sha(inputs.use('results/rtc_factorial_v2/manifest.json'))
    schedule = inputs.json('subjects/phase3_rtc/plan.json')
    assert sha(inputs.use('subjects/phase3_rtc/plan.json')) == old_manifest['schedule_sha256']

    def add(path, study, versions, manifest_sha, schedule_sha):
        relative = str(path.relative_to(inputs.root))
        r = inputs.json(relative)
        sid = r['suite_id']
        if sid not in roster and sid not in human_ids:
            return
        assert sid in versions
        version = versions[sid]
        assert r['source_sha256'] == version['source_sha256'] and r['elf_sha256'] == version['elf_sha256']
        assert r['manifest_sha256'] == manifest_sha and r['schedule_sha256'] == schedule_sha
        assert r['condition'] in ('seeded', 'min', 'max')
        if r['condition'] == 'seeded':
            assert r['seed'] in range(100)
            expected_hz = schedule['seeded_frequencies_hz'][r['seed']]
        else:
            assert r['seed'] is None
            expected_hz = schedule['endpoints_hz'][r['condition']]
        assert r['lsi_frequency_hz'] == expected_hz
        assert r['cpu_performance_mips'] == 16 and r['systick_frequency_hz'] == 16000000
        assert r['quantum_ns'] == 1000
        key = (r['condition'], r['seed'])
        assert key not in records[sid], (sid, key)
        assert r['outcome'] in ('pass', 'fail', 'harness_error', 'timeout', 'unknown', 'skip')
        for kind in ('trace', 'uart', 'monitor'):
            if r.get(kind + '_sha256'):
                actual = inputs.use(str((study / r[kind + '_path']).relative_to(inputs.root)))
                assert sha(actual) == r[kind + '_sha256']
        records[sid][key] = r
        paths[sid, key] = relative

    for path in sorted((inputs.root / 'results/rtc_factorial_v2/records').glob('*.json')):
        add(path, inputs.root, old_manifest['versions'], old_manifest_sha, old_manifest['schedule_sha256'])
    before = {sid: dict(rr) for sid, rr in records.items()}
    ab_plan = inputs.json(AB + '/plan.json')
    assert ab_plan['phase'] == 'AB' and len(ab_plan['versions']) == 16
    ab_plan_sha = sha(inputs.use(AB + '/plan.json'))
    assert inputs.text(AB + '/plan.sha256').split()[0] == ab_plan_sha
    ab_proof = inputs.json('artifacts/tacc_phase2_20261024_v1/returned-ab-complete/local-verification.json')
    assert ab_proof['raw_report_agrees'] and ab_proof['report']['complete']
    assert ab_proof['report']['forecast_matches'] == 1600
    study = inputs.root / AB / 'study'
    ab_output = study / ab_plan['output_relative']
    for path in sorted((ab_output / 'records').glob('*.json')):
        add(path, study, ab_plan['versions'], ab_plan_sha, ab_plan['schedule_sha256'])
    assert set(records) == set(roster) | human_ids
    assert all(len(records[sid]) == 102 for sid in records)
    slow, fault_rows = {}, inputs.csv('analysis/rtc_quality_mutant_scores/rows.csv')
    fault_lookup = {}
    for row in fault_rows:
        if row['suite_id'] not in records:
            continue
        path = inputs.use(row['record_path'])
        assert sha(path) == row['record_sha256']
        r = inputs.json(row['record_path'])
        assert r['outcome'] == row['outcome']
        for kind in ('trace', 'uart', 'monitor'):
            if r.get(kind + '_sha256'):
                assert sha(inputs.use(r[kind + '_path'])) == r[kind + '_sha256']
        fault_lookup[row['suite_id'], row['operator']] = row
        if row['operator'] == 'late':
            slow[row['suite_id']] = row
    assert set(slow) == set(records)
    padding = {r['suite_id']: r for r in inputs.csv('analysis/rtc_padding_audit.csv')}
    forecast_rows = inputs.csv('analysis/rtc_threshold_sample_v2/forecast_table.csv')
    forecasts = {r['run_id']: r for r in forecast_rows if r['prediction_status'] == 'clock_only_prediction'}
    assert len(forecasts) == 30
    suite_rows = []
    for sid, rr in sorted(records.items()):
        seeded = [r for (condition, _), r in rr.items() if condition == 'seeded']
        endpoints = [r for (condition, _), r in rr.items() if condition != 'seeded']
        assert len(seeded) == 100 and len(endpoints) == 2
        counts = Counter(r['outcome'] for r in seeded)
        all_counts = Counter(r['outcome'] for r in rr.values())
        row = dict(suite_id=sid, scope='original_generated' if sid in roster else 'original_isolated_upstream',
                   model=roster[sid]['model'] if sid in roster else 'upstream',
                   prompt_condition=roster[sid]['prompt_condition'] if sid in roster else 'not_applicable',
                   family=roster[sid]['task_family'] if sid in roster else sid.removeprefix('human-'),
                   seeded_pass=counts['pass'], seeded_fail=counts['fail'],
                   seeded_missing=100 - counts['pass'] - counts['fail'],
                   endpoint_pass=sum(r['outcome'] == 'pass' for r in endpoints),
                   endpoint_fail=sum(r['outcome'] == 'fail' for r in endpoints),
                   endpoint_missing=sum(r['outcome'] not in ('pass', 'fail') for r in endpoints),
                   observed_clock_flip=all_counts['fail'] > 0,
                   confirmed_robust_100=counts['pass'] == 100,
                   optimistic_robust_100=counts['fail'] == 0,
                   confirmed_robust_102=all_counts['pass'] == 102,
                   clock_status=('observed_failure' if all_counts['fail'] else
                                 'survives_observed_schedule' if all_counts['pass'] == 102 else
                                 'unconfirmed_missing_verdicts'),
                   slow_outcome=slow[sid]['outcome'], slow_detected=slow[sid]['kill'] == 'yes',
                   slow_evaluable=slow[sid]['outcome'] in ('pass', 'fail'),
                   slow_record_path=slow[sid]['record_path'],
                   clock_record_paths=';'.join(paths[sid, key] for key in sorted(rr, key=str)))
        suite_rows.append(row)
    generated = [r for r in suite_rows if r['scope'] == 'original_generated']
    for row in generated:
        sid = row['suite_id']
        nonarrival = fault_lookup[sid, 'nonarrival']
        row['robust_and_two_detecting'] = (row['confirmed_robust_100'] and row['slow_detected']
                                         and nonarrival['kill'] == 'yes')
        row['quality_confirmed'] = row['robust_and_two_detecting'] and padding[sid]['over_padded'] == 'no'
    prompt_cells = {}
    for condition in ('range_absent', 'range_present'):
        group = [r for r in generated if r['prompt_condition'] == condition]
        prompt_cells[condition] = dict(suites=len(group), flips=sum(r['observed_clock_flip'] for r in group),
                                       seeded_pass=sum(r['seeded_pass'] for r in group),
                                       seeded_fail=sum(r['seeded_fail'] for r in group),
                                       seeded_missing=sum(r['seeded_missing'] for r in group))
    absent, present = prompt_cells['range_absent'], prompt_cells['range_present']
    prompt_fisher = fisher(absent['flips'], absent['suites'] - absent['flips'],
                           present['flips'], present['suites'] - present['flips'])
    complete_prompt = {}
    for condition in ('range_absent', 'range_present'):
        group = [r for r in generated if r['prompt_condition'] == condition and
                 r['seeded_missing'] == 0 and r['endpoint_missing'] == 0]
        complete_prompt[condition] = dict(suites=len(group), flips=sum(r['observed_clock_flip'] for r in group))
    ca, cp = complete_prompt['range_absent'], complete_prompt['range_present']
    yields = []
    for model in ('luna', 'sol', 'astra'):
        for condition in ('range_absent', 'range_present'):
            group = [r for r in generated if (r['model'], r['prompt_condition']) == (model, condition)]
            confirmed = sum(r['confirmed_robust_100'] for r in group)
            optimistic = sum(r['optimistic_robust_100'] for r in group)
            yields.append(dict(model=model, condition=condition, attempts=15, working=len(group),
                               confirmed_robust=confirmed, optimistic_robust_ceiling=optimistic,
                               confirmed_robust_wilson95=wilson(confirmed, 15),
                               robust_plus_two=sum(r['robust_and_two_detecting'] for r in group),
                               quality_confirmed=sum(r['quality_confirmed'] for r in group),
                               flips=sum(r['observed_clock_flip'] for r in group),
                               fail=sum(r['seeded_fail'] for r in group),
                               evaluable=sum(r['seeded_pass'] + r['seeded_fail'] for r in group),
                               missing=sum(r['seeded_missing'] for r in group)))
    predictable_matches = predictable_slots = nontrivial_failures = 0
    for sid, forecast in forecasts.items():
        failed_seeds = {int(s) for s in forecast['predicted_failure_seeds'].split(',') if s}
        for (condition, seed), r in records[sid].items():
            if condition != 'seeded':
                continue
            assert r['outcome'] in ('pass', 'fail')
            predictable_slots += 1
            predictable_matches += (r['outcome'] == 'fail') == (seed in failed_seeds)
            nontrivial_failures += r['outcome'] == 'fail'
    latency = {r['run_id']: r for r in inputs.csv('analysis/factorial_latency_assumptions.csv')}
    no_flip = [r for r in generated if not r['observed_clock_flip']]
    latency_counts = Counter(latency[r['suite_id']]['latency_category'] for r in no_flip)
    old_metric = dict(measured=sum(bool(before.get(sid)) for sid in roster),
                      confirmed_robust=sum(bool(before.get(sid)) and
                                           all(r['outcome'] == 'pass' for (cond, _), r in before[sid].items() if cond == 'seeded')
                                           for sid in roster))
    statistics = dict(
        generated_suites=66, measured_suites=len(generated), forecast_only=0,
        total_seed_slots=sum(r['seeded_pass'] + r['seeded_fail'] + r['seeded_missing'] for r in generated),
        seed_pass=sum(r['seeded_pass'] for r in generated), seed_fail=sum(r['seeded_fail'] for r in generated),
        seed_missing=sum(r['seeded_missing'] for r in generated), prompt_cells=prompt_cells,
        prompt_fisher=prompt_fisher, all_attempts=90,
        complete_case_prompt_cells=complete_prompt,
        complete_case_prompt_fisher=fisher(ca['flips'], ca['suites'] - ca['flips'], cp['flips'], cp['suites'] - cp['flips']),
        confirmed_robust=sum(r['confirmed_robust_100'] for r in generated),
        optimistic_robust_ceiling=sum(r['optimistic_robust_100'] for r in generated),
        robust_plus_two=sum(r['robust_and_two_detecting'] for r in generated),
        quality_confirmed=sum(r['quality_confirmed'] for r in generated),
        predictable_measured=len(forecasts), predictable_verdicts=predictable_slots,
        forecast_matches=predictable_matches, nontrivial_forecast_failures=nontrivial_failures,
        trivial_predictable_suites=sum(int(r['predicted_failure_count']) == 0 for r in forecasts.values()),
        no_observed_flip_suites=len(no_flip), no_flip_latency_counts=dict(latency_counts),
        previous_metrics=old_metric, yield_cells=yields)
    paired_rows = []
    for suite in generated:
        sid = suite['suite_id']
        human = records['human-' + suite['family']]
        up_only = generated_only = missing = 0
        for seed in range(100):
            a, b = human['seeded', seed], records[sid]['seeded', seed]
            if a['outcome'] not in ('pass', 'fail') or b['outcome'] not in ('pass', 'fail'):
                missing += 1
                continue
            up_only += a['outcome'] == 'fail' and b['outcome'] == 'pass'
            generated_only += a['outcome'] == 'pass' and b['outcome'] == 'fail'
        n = up_only + generated_only
        p = (min(Fraction(1), 2 * sum((Fraction(math.comb(n, k), 2 ** n)
                                     for k in range(min(up_only, generated_only) + 1)), Fraction(0)))
             if n else Fraction(1))
        paired_rows.append(dict(suite_id=sid, family=suite['family'], upstream_only_fail=up_only,
                                generated_only_fail=generated_only, missing_pairs=missing,
                                exact_p=float(p), exact_fraction=str(p)))
    task_contrasts, model_contrasts = [], []
    for model in ('luna', 'sol', 'astra'):
        model_tasks = []
        for family in ('rtc_alarm_callback', 'rtc_alarm_pending', 'rtc_time_counting'):
            absent_group = [r for r in generated if (r['model'], r['family'], r['prompt_condition']) == (model, family, 'range_absent')]
            present_group = [r for r in generated if (r['model'], r['family'], r['prompt_condition']) == (model, family, 'range_present')]
            if not absent_group or not present_group:
                continue
            def bounds(group):
                n = 100 * len(group)
                failed = sum(r['seeded_fail'] for r in group)
                missing = sum(r['seeded_missing'] for r in group)
                return Fraction(failed, n), Fraction(failed + missing, n)
            a, b = bounds(absent_group), bounds(present_group)
            low, high = b[0] - a[1], b[1] - a[0]
            task_contrasts.append(dict(model=model, task=family, low_percentage_points=100 * float(low), high_percentage_points=100 * float(high)))
            model_tasks.append((low, high))
        low = sum((r[0] for r in model_tasks), Fraction(0)) / len(model_tasks)
        high = sum((r[1] for r in model_tasks), Fraction(0)) / len(model_tasks)
        model_contrasts.append(dict(model=model, low_percentage_points=100 * float(low), high_percentage_points=100 * float(high)))
    statistics['registered_task_contrasts'] = task_contrasts
    statistics['registered_equal_task_by_model'] = model_contrasts
    statistics['registered_equal_model_contrast'] = dict(
        low_percentage_points=sum(r['low_percentage_points'] for r in model_contrasts) / 3,
        high_percentage_points=sum(r['high_percentage_points'] for r in model_contrasts) / 3)
    statistics['paired_by_task'] = [dict(
        family=family, suites=len([r for r in paired_rows if r['family'] == family]),
        significant=sum(r['exact_p'] < .05 for r in paired_rows if r['family'] == family),
        upstream_only_fail=sum(r['upstream_only_fail'] for r in paired_rows if r['family'] == family),
        generated_only_fail=sum(r['generated_only_fail'] for r in paired_rows if r['family'] == family),
        missing_pairs=sum(r['missing_pairs'] for r in paired_rows if r['family'] == family))
        for family in ('rtc_alarm_callback', 'rtc_alarm_pending', 'rtc_time_counting')]
    fault_cells = []
    groups = [('upstream', [r for r in suite_rows if r['scope'] == 'original_isolated_upstream']),
              ('all_generated', generated)]
    groups += [(model + '|' + condition,
                [r for r in generated if (r['model'], r['prompt_condition']) == (model, condition)])
               for model in ('luna', 'sol', 'astra') for condition in ('range_absent', 'range_present')]
    for group_name, members in groups:
        for operator, label in [('early', 'fast'), ('late', 'slow'), ('nonarrival', 'nonarrival')]:
            rr = [fault_lookup[r['suite_id'], operator] for r in members]
            n = sum(r['outcome'] in ('pass', 'fail') for r in rr)
            detected = sum(r['kill'] == 'yes' for r in rr)
            assert all(r['kill'] != 'yes' or r['outcome'] == 'fail' for r in rr)
            fault_cells.append(dict(group=group_name, operator=label, detected=detected, evaluable=n,
                                    missing=len(rr) - n, wilson95=wilson(detected, n)))
    offset_summary = inputs.json('results/rtc_alarm_offset_v1/analysis_summary.json')
    offset_manifest = inputs.json('results/rtc_alarm_offset_v1/manifest.json')
    offset_manifest_sha = sha(inputs.use('results/rtc_alarm_offset_v1/manifest.json'))
    pattern = re.compile(r'QUALITY_ALARM_OFFSET id=(\d+) sign=(-?\d+) requested=(-?\d+):(-?\d+):(-?\d+) '
                         r'programmed=(-?\d+):(-?\d+):(-?\d+) mask=(\d+)')
    offset_verified = []
    for score in offset_summary['rows']:
        if score['suite_id'] not in records or score['family'] == 'rtc_time_counting':
            continue
        path = 'results/rtc_alarm_offset_v1/records/' + score['run_id'] + '.json'
        assert sha(inputs.use(path)) == score['record_sha256']
        r = inputs.json(path)
        assert r['manifest_sha256'] == offset_manifest_sha
        suite = offset_manifest['suites'][score['suite_id']]
        assert r['source_sha256'] == suite['source_sha256']
        for kind in ('trace', 'uart', 'monitor'):
            if r.get(kind + '_sha256'):
                assert sha(inputs.use(r[kind + '_path'])) == r[kind + '_sha256']
        logs = pattern.findall(inputs.text(r['uart_path'])) if r.get('uart_sha256') else []
        sign = score['sign']
        valid = [log for log in logs if int(log[1]) == sign]
        for log in logs:
            requested = sum(int(x) * y for x, y in zip(log[2:5], (3600, 60, 1)))
            programmed = sum(int(x) * y for x, y in zip(log[5:8], (3600, 60, 1)))
            assert int(log[8]) != 7 or (programmed - requested) % 86400 == sign % 86400
        status = ('missing_verdict' if r['outcome'] in ('harness_error', 'timeout', 'unknown') else
                  'inactive' if not valid else
                  'kill' if r['outcome'] == 'fail' and any(c['status'] == 'fail' and
                    (not suite.get('selected_case') or c['case'] == suite['selected_case']) for c in r['cases']) else
                  'survive' if r['outcome'] == 'pass' else 'ambiguous')
        assert score['status'] == status and score['activation_logs'] == len(valid)
        offset_verified.append(score)
    offset_cells = []
    for family in ('rtc_alarm_callback', 'rtc_alarm_pending'):
        for kind in ('human', 'ai'):
            for sign in (-1, 1):
                rr = [r for r in offset_verified if (r['family'], r['kind'], r['sign']) == (family, kind, sign)]
                n = sum(r['status'] in ('kill', 'survive') for r in rr)
                detected = sum(r['status'] == 'kill' for r in rr)
                offset_cells.append(dict(family=family, kind=kind, sign=sign, detected=detected, evaluable=n,
                                         missing=len(rr) - n, wilson95=wilson(detected, n)))
    # User-supplied expectations are cross-checks only; every value is derived above.
    assert (absent['flips'], absent['suites'], present['flips'], present['suites']) == (3, 34, 0, 32)
    assert statistics['confirmed_robust'] == 55 and statistics['seed_missing'] == 12
    assert predictable_matches == predictable_slots == 3000
    return dict(statistics=statistics, suites=suite_rows, records=records,
                record_paths=paths, forecasts=forecasts, before=before, paired_per_suite=paired_rows,
                fault_cells=fault_cells, offset_cells=offset_cells)
