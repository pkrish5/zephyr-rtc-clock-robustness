"""Proposed semantic number changes, with manuscript locations and evidence."""
from collections import Counter


def build(inputs, base, s2, repair):
    source = inputs.text('paper/draft/main.tex')
    lines = source.splitlines()
    stats = base['statistics']
    old = inputs.json('analysis/rtc_factorial_v2_final_summary.json')
    stage = inputs.json('analysis/rtc_all_attempts.json')
    changes = []

    def table_rows(label):
        start = source.index('\\label{' + label + '}')
        block = source[start:source.index('\\end{table}', start)]
        return [line.strip() for line in block.splitlines() if ' & ' in line and
                line.lstrip().startswith(('Luna ', 'Sol ', 'Astra '))]

    old_yield_rows = table_rows('tab:yield')
    old_clock_rows = table_rows('tab:agent')

    def add(metric, before, after, evidence, search, action='replace by meaning, not global numeric substitution'):
        locations = [str(i) for i, line in enumerate(lines, 1) if any(token in line for token in search)]
        changes.append(dict(metric=metric, old_value=str(before), proposed_value=str(after),
                            source_files=evidence, manuscript_lines=';'.join(locations),
                            search_literals=' | '.join(search), action=action))

    absent, present = stats['prompt_cells']['range_absent'], stats['prompt_cells']['range_present']
    add('measured generated suites', 50, stats['measured_suites'],
        'analysis/rtc_factorial_v2_final_summary.json; artifacts/tacc_phase2_20261024_v1/returned-ab-complete/ab-derived-comparison.json; per_suite.csv', ['50 suites', '14 of the 30'])
    add('unrun forecast-only suites', 16, stats['forecast_only'], 'per_suite.csv; original and A–B primary records',
        ['16 remain forecast', '16 frozen forecasts', 'Sixteen generated', 'other 16 predictable'])
    add('all measured suites including original isolated upstream', 53, stats['measured_suites'] + 3,
        'per_suite.csv; original and A–B primary records', ['53 measured suites'])
    add('seeded slots including original isolated upstream', '5,300', stats['total_seed_slots'] + 300,
        'per_suite.csv; original and A–B primary records', ['5,300'])
    add('passes including original isolated upstream', '5,182', stats['seed_pass'] + sum(r['seeded_pass'] for r in base['suites'] if r['scope'] == 'original_isolated_upstream'),
        'per_suite.csv; original and A–B primary records', ['5,182'])
    add('base-prompt observed flip suites', '3/24', '%s/%s' % (absent['flips'], absent['suites']),
        'per_suite.csv; statistics.json', ['3/24'])
    add('clock-range-prompt observed flip suites', '0/26', '%s/%s' % (present['flips'], present['suites']),
        'per_suite.csv; statistics.json', ['0/26'])
    add('suite-level two-sided Fisher p', '0.103', '%.6f' % stats['prompt_fisher']['two_sided_p'],
        'statistics.json: prompt_fisher, exact fixed-margin enumeration', ['0.103'])
    add('base-prompt seeded slots', '2,400', 100 * absent['suites'], 'statistics.json: prompt_cells', ['2,400'])
    add('clock-range-prompt seeded slots', '2,600', 100 * present['suites'], 'statistics.json: prompt_cells', ['2,600'])
    add('predictable suites measured', '14/30', '%s/30' % stats['predictable_measured'],
        'analysis/rtc_threshold_sample_v2/forecast_table.csv; statistics.json', ['sample of 14', 'Eleven of 14'])
    add('zero-failure predictable vectors measured', '11/14', '%s/%s' % (stats['trivial_predictable_suites'], stats['predictable_measured']),
        'analysis/rtc_threshold_sample_v2/forecast_table.csv; all measured predictable raw records', ['Eleven of 14'])
    add('exact predictable verdict matches', '1,400/1,400', '%s/%s' % (stats['forecast_matches'], stats['predictable_verdicts']),
        'statistics.json; original and A–B predictable primary records', ['1,400/1,400'])
    add('confirmed robust all-attempt yield', '39/90', '%s/90' % stats['confirmed_robust'],
        'per_suite.csv; yield_cells.csv; statistics.json', ['Thirty-nine', '39/90'])
    add('optimistic robust all-attempt ceiling', 'not shown', '%s/90' % stats['optimistic_robust_ceiling'],
        'per_suite.csv; yield_cells.csv; statistics.json', ['tab:yield'], 'add ceiling column; missing outcomes are not observed passes')
    add('confirmed robust plus slow/nonarrival detection yield', '29/90', '%s/90' % stats['robust_plus_two'],
        'analysis/rtc_quality_mutant_scores/rows.csv; per_suite.csv; statistics.json', ['29 also', 'Robust+2'])
    add('descriptive non-padding combined Q yield', '5/90', '%s/90' % stats['quality_confirmed'],
        'analysis/rtc_padding_audit.csv; analysis/rtc_quality_mutant_scores/rows.csv; per_suite.csv', ['5/90'])
    add('measured suites without an observed clock flip', 47, stats['no_observed_flip_suites'],
        'per_suite.csv; analysis/factorial_latency_assumptions.csv', ['47 measured'])
    counts = stats['no_flip_latency_counts']
    add('latency labels within measured no-flip subgroup', '21 definite; 23 unknown', str(counts),
        'analysis/factorial_latency_assumptions.csv; per_suite.csv', ['21 had a definite', '23 were unknown'])
    for row in stats['yield_cells']:
        old_cell = next(r for r in stage['cells'] if (r['model'], r['prompt_condition']) == (row['model'], row['condition']))
        model = row['model'].title()
        prompt = 'Base' if row['condition'] == 'range_absent' else 'Ranges'
        old_yield = next(line for line in old_yield_rows if line.startswith(model + ' & ' + prompt + ' &'))
        old_clock = next(line for line in old_clock_rows if line.startswith(model + ' & ' + prompt + ' &'))
        add('confirmed robust table cell: ' + row['model'] + '/' + row['condition'],
            '%s/15' % old_cell['clock_complete_pass_suites'], '%s/15' % row['confirmed_robust'],
            'analysis/rtc_all_attempts.json; yield_cells.csv; original and A–B primary records', [model + ' &'])
        add('complete clock table row: ' + row['model'] + '/' + row['condition'], old_clock,
            '%s & %s & %s & %s & %s/%s' % (model, prompt, row['working'], row['working'], row['fail'], row['evaluable']),
            'per_suite.csv; yield_cells.csv', [old_clock])
        add('complete all-attempt yield table row: ' + row['model'] + '/' + row['condition'], old_yield,
            '%s & %s & %s/15 & %s/15 & %s/15; optimistic robust ceiling %s/15' %
            (model, prompt, row['working'], row['confirmed_robust'], row['robust_plus_two'], row['optimistic_robust_ceiling']),
            'per_suite.csv; yield_cells.csv; analysis/rtc_quality_mutant_scores/rows.csv', [old_yield])
    for row in stats['paired_by_task']:
        old_values = {'rtc_alarm_callback': '19/19; 492; 0', 'rtc_alarm_pending': '20/20; 480; 0',
                      'rtc_time_counting': '11/11; 187; 0'}[row['family']]
        add('paired McNemar secondary table: ' + row['family'], old_values,
            '%s/%s; %s; %s' % (row['significant'], row['suites'], row['upstream_only_fail'], row['generated_only_fail']),
            'paired_per_suite.csv; statistics.json: paired_by_task', ['tab:paired'],
            'move table into repository; retain one-sentence main-body pointer')
    # Expanded results supplement the original isolated baseline; do not replace
    # the earlier 26/26/17 sampled failures with full-application counts.
    for row in s2['boards']:
        add('expanded cohort, ' + row['board_role'], 'not reported',
            '%s/%s observed flips; %s reference-supported waiting cases; %s cascade; %s firmware/simulator/contract' %
            (row['any_observed_failure_cases'], row['any_setting_runnable'], row['reference_supported_waiting_cases'],
             row['cleanup_cascade_cases'], row['firmware_simulator_or_contract_cases']),
            's2_by_board.csv; s2_per_case_with_references.csv; S2 primary and reference archives',
            ['three purposively', 'three upstream cases'], 'add expanded context; retain original isolated results side by side')
    for row in repair['per_variant']:
        add('mechanical repair results ' + row['variant'], 'not reported',
            'seed failures=%s, endpoint failures=%s, median simulated seconds=%s' %
            (row['seeded_fail'], row['endpoint_fail'], row['median_seeded_virtual_seconds']),
            'repair_per_variant.csv; repair_primary_index.csv; verified original/recovery archives',
            ['two-sided repair study', 'repair'], 'add paired mechanical-variant results, not new model generations')
    # Preserve original values whose sample scope has not changed.
    unchanged = dict(original_generation_attempts=390, original_RTC_attempts=90,
                     eligible_RTC_generated=66, original_seeded_assertion_failures=stats['seed_fail'],
                     original_missing_seed_verdicts=stats['seed_missing'],
                     original_isolated_upstream_seed_failures={r['suite_id']: r['seeded_fail'] for r in base['suites'] if r['scope'] == 'original_isolated_upstream'},
                     assertion='S2 full-application context and E reruns never replace original missing verdicts or isolated results')
    return changes, unchanged
