#!/usr/bin/env python3
"""Render every manuscript table from the raw-reconciled package ledgers.

Only generated TeX fragments and their manifest may be overwritten. Raw
records, verification outputs and the existing manuscript are never modified.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(package, output):
    used = {}

    def rows(name):
        p = package / name
        used[name] = sha(p)
        with p.open(newline='') as f:
            return list(csv.DictReader(f))

    def tabular(columns, header, data):
        lines = [r'\begin{tabular}{@{}' + columns + r'@{}}\toprule',
                 ' & '.join(header) + r'\\\midrule']
        lines += [' & '.join(map(str, row)) + r'\\' for row in data]
        return '\n'.join(lines + [r'\bottomrule\end{tabular}', ''])

    def percentage(v, precision=1):
        value = 100 * float(v)
        if abs(value) < 1e-8:
            return '0'
        if abs(value - 100) < 1e-8:
            return '100'
        return ('%.' + str(precision) + 'f') % value

    def score(r, interval=True, missing=False):
        n = int(r['evaluable'])
        if not n:
            return 'missing'
        s = '%s/%s' % (r['detected'], n)
        if interval:
            lo, hi = json.loads(r['wilson95'])
            s += ' [%s,%s]\\%%' % (percentage(lo), percentage(hi))
        if missing and int(r['missing']):
            s += ' +%s missing' % r['missing']
        return s

    suites = rows('per_suite.csv')
    sensitivity = rows('sensitivity.csv')
    primary_human = {r['family']: r for r in suites if r['scope'] == 'original_isolated_upstream'}
    human_cdf = {r['family']: r for r in sensitivity if r['scope'] == 'original_isolated_upstream'}
    human = []
    for family, title in [('rtc_alarm_callback', 'Callback'), ('rtc_time_counting', 'Counting'), ('rtc_alarm_pending', 'Pending')]:
        r, c = primary_human[family], human_cdf[family]
        human.append([title, '%.3f' % (float(c['boundary_low_hz']) / 1000), r['seeded_fail'] + '/100',
                      '%.2f' % (100 * float(c['uniform_conditional_legal_low'])),
                      '%.2f' % (100 * float(c['normal_3sigma_conditional_legal_low'])),
                      '%.2f' % (100 * float(c['normal_2sigma_conditional_legal_low']))])
    tables = {'human': tabular('lrrrrr', ['Case', 'Boundary', 'Fail', 'U', 'N3', 'N2'], human)}
    yields = rows('yield_cells.csv')
    names = {'luna': 'Luna', 'sol': 'Sol', 'astra': 'Astra'}
    def prompt(r):
        return 'B' if r['condition'] == 'range_absent' else 'R'
    tables['agent'] = tabular('llrrr', ['Model', 'Prompt', 'Eligible', 'Measured', 'Fail/evaluable'],
        [[names[r['model']], prompt(r), r['working'], r['working'], r['fail'] + '/' + r['evaluable']] for r in yields])
    tables['yield'] = tabular('llrrrr', ['Model', 'Prompt', 'W', 'R', 'U', '+2'],
        [[names[r['model']], prompt(r)] + [r[k] + '/15' for k in
          ('working', 'confirmed_robust', 'optimistic_robust_ceiling', 'robust_plus_two')] for r in yields])
    boards = rows('s2_by_board.csv')
    cases = rows('s2_per_case_with_references.csv')
    expanded = []
    for board in boards:
        rr = [r for r in cases if r['board_id'] == board['board']]
        cat = [sum(r['category'] == c and int(r['fail_count']) > 0 for r in rr) for c in 'abcd']
        name = 'F767 (F4 replica)' if board['board'] == 'f767' else board['board'].upper()
        expanded.append([name, board['any_setting_runnable'], board['always_skipped'], board['any_observed_failure_cases'],
                         board['any_observed_failure_cases'] + '/' + board['any_setting_runnable'], '/'.join(map(str, cat))])
    tables['expanded'] = tabular('lrrrrl', ['Configuration', 'Run', 'Skip', 'F', 'F/Run', 'A/B/C/D'], expanded)
    faults = {(r['group'], r['operator']): r for r in rows('original_fault_cells.csv')}
    groups = [('upstream', 'Upstream', 'n/a')] + [(r['model'] + '|' + r['condition'], names[r['model']], prompt(r)) for r in yields] + [('all_generated', 'All generated', 'both')]
    tables['faults'] = tabular('llrrr', ['Model', 'Prompt', 'Fast oscillator', 'Slow oscillator', 'Nonarrival'],
        [[model, cond] + [score(faults[group, op], missing=True) for op in ('fast', 'slow', 'nonarrival')]
         for group, model, cond in groups])
    offsets = {(r['family'], r['kind'], r['sign']): r for r in rows('original_alarm_offset_cells.csv')}
    tables['offset'] = tabular('lrr', ['Case', '$-1$ RTC s', '$+1$ RTC s'],
        [[name + ' ' + task] + [score(offsets['rtc_alarm_' + family, kind, sign], interval=kind == 'ai') for sign in ('-1', '1')]
         for family, task in [('callback', 'callback'), ('pending', 'pending')]
         for kind, name in [('human', 'Upstream'), ('ai', 'Generated')]])
    repairs = rows('repair_per_variant.csv')
    tables['repair'] = tabular('lrrrrrrrr', ['Variant', 'Seed F', 'M', 'Fast', 'Slow', 'Nonarrival', 'Early', 'Late', 'Median s'],
        [[r['variant'], r['seeded_fail'], r['seeded_missing']] + [r[op + '_detected'] + '/' + r[op + '_evaluable'] for op in
          ('fast', 'slow', 'nonarrival', 'offset_early', 'offset_late')] + ['%.1f' % float(r['median_seeded_virtual_seconds'])] for r in repairs])
    axes = {(r['scope'], r['clock_status'], r['slow_status']): r['suites_or_cases'] for r in rows('two_axis_counts.csv')}
    arows = []
    for scope, name, statuses in [('original_generated', 'Generated', [('survives_observed_schedule', '100 passes'), ('observed_failure', 'Observed flip'), ('unconfirmed_missing_verdicts', 'Unknown')]),
                                  ('original_isolated_upstream', 'Isolated upstream', [('observed_failure', 'Observed flip')])]:
        for i, (status, title) in enumerate(statuses):
            arows.append([name if not i else '', title, axes.get((scope, status, 'detected'), '0'), axes.get((scope, status, 'survived_fault'), '0')])
    tables['axes'] = tabular('llrr', ['Cohort', 'Clock result', 'Detect slow', 'Accept slow'], arows)
    output.mkdir(parents=True, exist_ok=True)
    for name, content in tables.items():
        (output / (name + '.tex')).write_text('% Generated from verified archived records. Do not edit by hand.\n' + content)
    manifest = dict(source_package='verified raw-record reconciliation (build_package.py)', source_sha256=used,
                    fragments={name + '.tex': sha(output / (name + '.tex')) for name in tables},
                    experiment_execution=False, tables=len(tables))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(render(a.package, a.out), indent=2, sort_keys=True))
