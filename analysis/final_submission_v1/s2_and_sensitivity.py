"""S2 attribution, exact quotations, and explicitly assumed distribution models."""
from collections import Counter, defaultdict
from pathlib import Path

from common import failure_share, markdown_table
import audit_s2_raw


S2 = 'notes/s2_attribution_2026-10-31/s2_report_20261102_v3'
REF = 'notes/s2_reference_2026-11-02_v1/verified-3547096-v1'


def s2_tables(inputs):
    cases = inputs.csv(S2 + '/per_case.csv')
    links = inputs.csv(REF + '/primary_failure_reference_links.csv')
    proof = inputs.json(REF + '/reference_validation_summary.json')
    assert len(links) == proof['linked_primary_failure_slots'] == 470
    raw_audit = audit_s2_raw.audit(inputs, cases, links)
    grouped = defaultdict(list)
    for link in links:
        grouped[link['unit_id'], link['primary_case']].append(link)
    updated = []
    for row in cases:
        row = dict(row)
        refs = grouped[row['unit_id'], row['case']]
        assert len(refs) == int(row['fail_count'])
        if refs:
            outcomes = Counter(r['reference_outcomes'] for r in refs)
            flags = Counter(r['flag'] for r in refs)
            row['reference_status'] = '; '.join('%s:%s' % (k, v) for k, v in sorted(outcomes.items()))
            row['attribution_status'] = '; '.join('%s:%s' % (k, v) for k, v in sorted(flags.items()))
            row['reference_record_hashes'] = ';'.join(sorted({r['reference_record_sha256'] for r in refs}))
            if any('firmware_or_simulator' in r['flag'] for r in refs):
                row['final_category'] = 'firmware_simulator_or_accuracy_contract_not_test_defect'
            elif row['category'] == 'c':
                row['final_category'] = 'cleanup_cascade_not_independent_waiting_defect'
            else:
                row['final_category'] = 'reference_supported_waiting_explanation_simulation_only'
        else:
            row['reference_status'] = 'no failing setting requiring attribution'
            row['attribution_status'] = 'no observed failure; skips remain skips'
            row['reference_record_hashes'] = ''
            row['final_category'] = 'no_observed_failure'
        row['effective_wait'] = row['effective_wait'].replace('host seconds', 'simulated seconds')
        if row['board_id'] == 'f767':
            row['board_role'] = 'F4 configuration replica (F767)'
        row['slow_fault_status'] = 'not_measured_in_full_application_context'
        row['clock_status'] = ('observed_failure' if int(row['fail_count']) else
                               'unconfirmed_missing_verdicts' if int(row['missing_count']) else
                               'not_applicable_capability_skipped' if int(row['pass_count']) == 0 else
                               'unconfirmed_some_settings_skipped' if int(row['skip_count']) else
                               'survives_observed_schedule')
        updated.append(row)
    boards = []
    for board in ('f4', 'f767', 'f746', 'h753'):
        rows = [r for r in updated if r['board_id'] == board]
        runnable = [r for r in rows if int(r['pass_count']) + int(r['fail_count']) > 0]
        flips = [r for r in rows if int(r['fail_count'])]
        boards.append(dict(board=board, board_role=proof['board_roles'][board], declared_cases=len(rows),
                           nominal_runnable=sum(r['nominal_status'] in ('pass', 'fail') for r in rows),
                           any_setting_runnable=len(runnable), always_skipped=sum(int(r['skip_count']) == 102 for r in rows),
                           any_observed_failure_cases=len(flips),
                           reference_supported_waiting_cases=sum(r['category'] in ('a', 'b') for r in flips),
                           cleanup_cascade_cases=sum(r['category'] == 'c' for r in flips),
                           firmware_simulator_or_contract_cases=sum(r['category'] == 'd' for r in flips),
                           missing_case_slots=sum(int(r['missing_count']) for r in rows)))
    return dict(cases=updated, boards=boards, reference_links=links, raw_audit=raw_audit,
                isolated_reconciliation=inputs.csv(S2 + '/isolated_reconciliation.csv'))


def examples(inputs, s2):
    by_case = {(r['board_id'], r['case']): r for r in s2['cases']}
    specs = [
        ('phase_dependent_F4_counting', 'rtc_api.test_time_counting',
         'RTC API, full application', [(15, 17), (35, 59)],
         'The test rewrites the RTC calendar, then polls every 500 ms, with its last observation about 14.5 simulated seconds after the write. '
         'Renode preserves the fractional count across the write, so phase carried from earlier cases can shift the failure boundary; that explanation is supported by source and reconciliation but was not directly measured.'),
        ('F4_counter_seconds_rate', 'seconds_counter.test_seconds_rate',
         'Counter seconds, RTC-only non-stock configuration', [(10, 12), (20, 42)],
         'The test samples the counter around a 1,200-ms sleep and requires a change of one or two ticks. '
         'At slow legal inputs its retained rate reference also fails while eventual progress passes, so these outcomes remain a firmware/simulator or accuracy-contract investigation rather than evidence of a faulty test.'),
        ('original_upstream_callback', 'rtc_api.test_alarm_callback',
         'RTC API; full-application and original isolated contexts', [(13, 14), (119, 141)],
         'The original callback test checks absence after three simulated seconds and eventual callback presence after another ten, without asserting equality to the requested calendar second. '
         'Its isolated and full-application contexts have different observed boundaries, consistent with a preserved phase explanation that has not been directly measured.')]
    result, markdown = [], '# Exact source examples\n\n'
    for name, case, app, spans, explanation in specs:
        row = by_case['f4', case]
        relative = 'subjects/upstream/zephyr/' + row['source']
        source = inputs.text(relative).splitlines()
        blocks = [dict(start=a, end=b, lines=[dict(line=i, text=source[i - 1]) for i in range(a, b + 1)])
                  for a, b in spans]
        record = dict(id=name, app=app, case=case, source=relative, quoted_blocks=blocks,
                      failing_frequency_hz=[int(row['minimum_failed_hz']), int(row['maximum_failed_hz'])],
                      passing_frequency_hz=[int(row['minimum_passed_hz']), int(row['maximum_passed_hz'])],
                      source_boundary=row['source_boundary'], reference_status=row['reference_status'],
                      two_sentence_explanation=explanation)
        result.append(record)
        markdown += '## %s\n\n**Application:** %s. **Case:** `%s`.\n\n' % (name, app, case)
        markdown += 'Observed failing band: %s–%s Hz; passing band: %s–%s Hz. Source boundary/band: %s.\n\n' % (
            *record['failing_frequency_hz'], *record['passing_frequency_hz'], row['source_boundary'])
        markdown += explanation + '\n\nSource: `%s`. Line labels below are metadata; code text is copied exactly.\n\n' % relative
        for block in blocks:
            markdown += 'Lines %s–%s:\n\n```c\n%s\n```\n\n' % (block['start'], block['end'], '\n'.join(r['text'] for r in block['lines']))
        if name == 'original_upstream_callback':
            comparison = next(r for r in s2['isolated_reconciliation'] if r['case'] == case)
            markdown += ('Original isolated context: %s/100 seeded failures; full application: %s/100. '
                         'The %s differences are isolated-fail/full-pass; no directly measured phase value is claimed.\n\n') % (
                             comparison['isolated_seed_failures'], comparison['full_seed_failures'],
                             comparison['isolated_fail_full_pass'])
    return result, markdown


def sensitivity(inputs, base, s2, repair):
    rows = []

    def add(scope, subject, family, board_role, fail_hz, pass_hz, bounds, method, source, caveat):
        row = dict(scope=scope, subject=subject, family=family, board_role=board_role,
                   observed_failure_band_hz='%s–%s' % (min(fail_hz), max(fail_hz)),
                   observed_pass_band_hz='%s–%s' % (min(pass_hz), max(pass_hz)) if pass_hz else 'not observed',
                   boundary_low_hz=bounds[0] if bounds else None,
                   boundary_high_hz=bounds[1] if bounds else None,
                   boundary_method=method, source=source, caveat=caveat,
                   distribution_status='assumed distributions; not measured device probabilities')
        for distribution in ('uniform', 'normal_3sigma', 'normal_2sigma'):
            for label, boundary in [('low', bounds[0] if bounds else None), ('high', bounds[1] if bounds else None)]:
                row[distribution + '_conditional_legal_' + label] = (failure_share(boundary, distribution) if boundary is not None else None)
                if distribution != 'uniform':
                    row[distribution + '_untruncated_' + label] = (failure_share(boundary, distribution, False) if boundary is not None else None)
        # A distinct optional diagnostic: interpolation from a finite monotone
        # sample is an assumption, not a source-proven exact boundary.
        monotone_compatible = bool(pass_hz and max(fail_hz) < min(pass_hz))
        row['observed_sample_monotone_compatible'] = monotone_compatible
        for distribution in ('uniform', 'normal_3sigma', 'normal_2sigma'):
            row['observed_monotone_interpolation_' + distribution + '_low'] = (failure_share(max(fail_hz), distribution) if monotone_compatible else None)
            row['observed_monotone_interpolation_' + distribution + '_high'] = (failure_share(min(pass_hz), distribution) if monotone_compatible else None)
        row['observed_interpolation_assumption'] = 'monotone single-threshold continuation beyond sampled points; not independently validated'
        rows.append(row)

    for suite in base['suites']:
        if not suite['observed_clock_flip']:
            continue
        sid = suite['suite_id']
        rs = list(base['records'][sid].values())
        failed = [r['lsi_frequency_hz'] for r in rs if r['outcome'] == 'fail']
        passed = [r['lsi_frequency_hz'] for r in rs if r['outcome'] == 'pass']
        if suite['scope'] == 'original_isolated_upstream':
            window = 14.5 if suite['family'] == 'rtc_time_counting' else 13.
            boundary = 320000. / window
            bounds, method = (boundary, boundary), 'manual source-derived ideal zero-phase threshold; counting last-poll approximation'
            source = 'subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/' + {
                'rtc_time_counting': 'test_time_incrementing.c', 'rtc_alarm_callback': 'test_alarm_callback.c',
                'rtc_alarm_pending': 'test_alarm.c'}[suite['family']]
        else:
            forecast = base['forecasts'][sid]
            boundary = 320000. / float(forecast['budget_seconds'])
            bounds, method = (boundary, boundary), 'frozen manually source-derived scalar threshold'
            source = 'analysis/rtc_threshold_sample_v2/forecast_table.csv: budget_seconds'
        add(suite['scope'], sid, suite['family'], 'original F4 isolated configuration',
            failed, passed, bounds, method, source,
            'clock-only approximation; delivery/service is not bounded by oscillator rate')
    for case in s2['cases']:
        if not int(case['fail_count']):
            continue
        kind = case['case']
        if kind == 'rtc_api.test_alarm':
            bounds = (320000. / 13, 320000. / 13)
            method = 'manual ideal first-case zero-phase threshold'
        elif kind == 'rtc_api.test_alarm_callback':
            bounds = (288000. / 13, 320000. / 13)
            method = 'source calendar-write phase envelope; phase not directly measured'
        elif kind == 'rtc_api.test_time_counting':
            bounds = (288000. / 14.5, 320000. / 14.5)
            method = 'source phase envelope with approximate last poll; phase not directly measured'
        elif kind == 'counter_basic.test_all_channels':
            bounds = (64000. / 3, 96000. / 3)
            method = 'free-running relative-alarm phase envelope; distinct from calendar-write phase'
        elif kind == 'seconds_counter.test_seconds_rate':
            bounds = None
            method = 'no validated source-only defect threshold; ideal zero-phase rate comparison is 32000/1.2 Hz'
        else:
            bounds = None
            method = 'cleanup cascade has no independent waiting boundary'
        add('S2_full_application', case['unit_id'] + '/' + kind, kind, case['board_role'],
            [int(case['minimum_failed_hz']), int(case['maximum_failed_hz'])],
            [int(case['minimum_passed_hz']), int(case['maximum_passed_hz'])],
            bounds, method, 'subjects/upstream/zephyr/' + case['source'] + ':' + case['source_lines'],
            case['final_category'] + '; bands are observed samples, not continuous failure intervals')
    # Repeated V0 contexts are explicit rows, not new independent discoveries.
    # Do not manufacture a scalar prediction for a repaired variant that fails
    # an added semantic assertion despite a sufficient waiting ceiling.
    repair_plan = inputs.json('notes/e_resume_2026-11-02_v1/packet/original-plan.json')
    repair_groups = defaultdict(list)
    for r in repair['primary']:
        if r['operator'] == 'legal':
            repair_groups[r['version_id']].append(r)
    base_models = {r['subject']: dict(r) for r in rows if r['scope'] != 'S2_full_application'}
    for vid, trials in repair_groups.items():
        failed = [r['frequency_hz'] for r in trials if r['outcome'] == 'fail']
        if not failed:
            continue
        passed = [r['frequency_hz'] for r in trials if r['outcome'] == 'pass']
        version = repair_plan['versions'][vid]
        prior = base_models.get(version['original_suite_id'])
        if version['variant'] == 'V0' and prior:
            bounds = (prior['boundary_low_hz'], prior['boundary_high_hz'])
            method = prior['boundary_method'] + '; repeated frozen V0 context'
        else:
            bounds = None
            method = 'repair semantic failure requires source review; no validated scalar threshold is assumed'
        add('E_repair_context', vid, version['family'], 'paired F4 repair context', failed, passed,
            bounds, method, version['source_path'],
            'separate experiment; never substitutes for an original missing verdict or adds an independent subject')
    assumptions = dict(
        legal_interval_hz=[17000, 47000], uniform='continuous uniform input interval',
        normal_3sigma=dict(mean_hz=32000, sigma_hz=5000,
                          mass_outside_legal=1 - (failure_share(47000, 'normal_3sigma', False) - failure_share(17000, 'normal_3sigma', False))),
        normal_2sigma=dict(mean_hz=32000, sigma_hz=7500,
                          mass_outside_legal=1 - (failure_share(47000, 'normal_2sigma', False) - failure_share(17000, 'normal_2sigma', False))),
        primary_normal_columns='conditional on the documented legal interval; untruncated CDF columns also supplied',
        interpretation='illustrative model sensitivity, not an empirical distribution of devices',
        phase_bands='model-implied bounds across unknown phase, not a fitted exact threshold',
        service_assumption='ideal clock model with normal software service; the oscillator range supplies no physical interrupt-delivery bound',
        unresolved_and_cascade='source-model CDF not identifiable; finite-sample monotone interpolation supplied separately and explicitly assumed')
    return rows, assumptions


def two_axes(base, s2):
    rows = []
    for suite in base['suites']:
        rows.append(dict(scope=suite['scope'], subject=suite['suite_id'], board_role='original isolated F4 configuration',
                         family=suite['family'], clock_status=suite['clock_status'],
                         slow_status='detected' if suite['slow_detected'] else 'survived_fault' if suite['slow_evaluable'] else 'missing_verdict',
                         slow_record_path=suite['slow_record_path'],
                         note='no missing verdict imputed; clock survival requires all 102 observed settings to pass'))
    for case in s2['cases']:
        rows.append(dict(scope='S2_full_application', subject=case['unit_id'] + '/' + case['case'],
                         board_role=case['board_role'], family=case['case'], clock_status=case['clock_status'],
                         slow_status='not_measured', slow_record_path='',
                         note='do not transfer isolated fault verdicts to full-application or board replicas; skips remain skips'))
    counts = Counter((r['scope'], r['clock_status'], r['slow_status']) for r in rows)
    summary = [dict(scope=scope, clock_status=clock, slow_status=slow, suites_or_cases=n)
               for (scope, clock, slow), n in sorted(counts.items())]
    return rows, summary
