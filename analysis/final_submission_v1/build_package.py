#!/usr/bin/env python3
"""Build the Phase 3 review package from verified records, without Renode.

All Phase A evidence must be complete before analysis executes. The open
manuscript is read for proposed changes and never written or compiled.
"""
import argparse
from pathlib import Path

from common import Inputs, csv_save, failure_share, markdown_table, save, sha, wilson
import base_study
import number_changes
import repair_study
import s2_and_sensitivity


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument('--original-e-verified', required=True)
    ap.add_argument('--chunk-verified', nargs=7, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    inputs = Inputs(a.repo)
    if a.out.exists():
        raise RuntimeError('New output directory required; do not overwrite a review package')
    manuscript_before = {name: sha(inputs.path(name)) for name in ('paper/draft/main.tex', 'paper/draft/main.pdf')}
    # Phase A gate first. Missing archives or failed replay checks stop here,
    # before Phase B and before creating any output directory.
    repair = repair_study.build(inputs, a.original_e_verified, a.chunk_verified)
    s2 = s2_and_sensitivity.s2_tables(inputs)
    base = base_study.build(inputs)
    examples, example_text = s2_and_sensitivity.examples(inputs, s2)
    sensitivity, assumptions = s2_and_sensitivity.sensitivity(inputs, base, s2, repair)
    axes, axis_counts = s2_and_sensitivity.two_axes(base, s2)
    changes, unchanged = number_changes.build(inputs, base, s2, repair)
    statistics = base['statistics']
    statistics['confirmed_robust_wilson95'] = wilson(statistics['confirmed_robust'], 90)
    statistics['optimistic_ceiling_is_not_a_confidence_interval'] = True
    statistics['wilson_interpretation'] = 'descriptive cohort/schedule intervals; clustered settings and shared tasks limit inference'
    board_rows = inputs.csv('analysis/subject_survey_20261025_v1/board_targets.csv')
    active = [r for r in board_rows if r['rtc_enabled'] == '1']
    board_survey = dict(unit='board DTS target, not devices or independent experimental subjects',
                        rtc_enabled_targets=len(active),
                        lsi=sum('LSI' in r['rtc_active_source'] for r in active),
                        lse=sum('LSE' in r['rtc_active_source'] for r in active))
    assert board_survey['lsi'] == 106 and board_survey['lse'] == 40
    board_survey['other_or_unresolved'] = len(active) - board_survey['lsi'] - board_survey['lse']
    st_documents = inputs.json('analysis/subject_survey_20261025_v1/verified_st_documents.json')
    for row in repair['per_variant']:
        row['legal_failures'] = '%s/3300 seeded; %s/66 endpoints' % (row['seeded_fail'], row['endpoint_fail'])
        row['legal_missing'] = '%s seeded; %s endpoints' % (row['seeded_missing'], row['endpoint_missing'])
        for op in ('fast', 'slow', 'nonarrival', 'offset_early', 'offset_late'):
            row[op + '_fraction'] = '%s/%s' % (row[op + '_detected'], row[op + '_evaluable'])
    for row in sensitivity:
        lo_hz, hi_hz = row['boundary_low_hz'], row['boundary_high_hz']
        row['boundary_display_khz'] = ('not source-identified' if lo_hz is None else
                                        '%.3f' % (lo_hz / 1000) if lo_hz == hi_hz else
                                        '%.3f–%.3f' % (lo_hz / 1000, hi_hz / 1000))
        for model in ('uniform', 'normal_3sigma', 'normal_2sigma'):
            lo, hi = row[model + '_conditional_legal_low'], row[model + '_conditional_legal_high']
            row[model + '_display_percent'] = ('not identifiable from a source-only threshold' if lo is None else
                                               ('%.3f%%' % (100 * lo) if lo == hi else '%.3f–%.3f%%' % (100 * lo, 100 * hi)))
    # No inputs may change during derivation, including the author's open draft.
    input_hashes = inputs.finish()
    assert all(sha(inputs.path(p)) == digest for p, digest in manuscript_before.items())
    a.out.mkdir(parents=True, exist_ok=False)
    csv_save(a.out / 'repair_per_variant.csv', repair['per_variant'])
    csv_save(a.out / 'repair_per_subject.csv', repair['per_subject'])
    csv_save(a.out / 'repair_primary_index.csv', repair['primary'])
    save(a.out / 'repair_replays.json', repair['replay_checks'])
    save(a.out / 'repair_references.json', repair['reference_checks'])
    save(a.out / 'repair_scope.json', {k: v for k, v in repair.items() if k not in
                                      ('per_variant', 'per_subject', 'primary', 'replay_checks', 'reference_checks')})
    csv_save(a.out / 's2_per_case_with_references.csv', s2['cases'])
    csv_save(a.out / 's2_by_board.csv', s2['boards'])
    csv_save(a.out / 'isolated_reconciliation.csv', s2['isolated_reconciliation'])
    save(a.out / 'examples.json', examples)
    (a.out / 'EXAMPLES.md').write_text(example_text)
    csv_save(a.out / 'sensitivity.csv', sensitivity)
    save(a.out / 'distribution_assumptions.json', assumptions)
    csv_save(a.out / 'two_axis_per_subject.csv', axes)
    csv_save(a.out / 'two_axis_counts.csv', axis_counts)
    csv_save(a.out / 'per_suite.csv', base['suites'])
    csv_save(a.out / 'yield_cells.csv', statistics['yield_cells'])
    csv_save(a.out / 'paired_per_suite.csv', base['paired_per_suite'])
    csv_save(a.out / 'original_fault_cells.csv', base['fault_cells'])
    csv_save(a.out / 'original_alarm_offset_cells.csv', base['offset_cells'])
    save(a.out / 'statistics.json', statistics)
    csv_save(a.out / 'before_after_numbers.csv', changes)
    save(a.out / 'unchanged_numbers.json', unchanged)
    save(a.out / 'board_survey.json', board_survey)
    save(a.out / 'verified_st_documents.json', st_documents)
    save(a.out / 'input_hashes.json', input_hashes)
    save(a.out / 'manuscript_untouched.json', manuscript_before)
    text = '# Phase 3 evidence package — verify before paper edits\n\n'
    text += 'All registered E evaluations and S2 references have been reconciled. This package derives existing data only; it runs no Renode, changes no raw record and does not edit the manuscript. E2 remains held.\n\n'
    text += '## E repair study\n\n'
    text += markdown_table(repair['per_variant'], [
        ('variant', 'Variant'), ('legal_failures', 'Legal failures'), ('legal_missing', 'Missing legal verdicts'),
        ('fast_fraction', 'Fast detected'), ('slow_fraction', 'Slow detected'), ('nonarrival_fraction', 'Nonarrival detected'),
        ('offset_early_fraction', 'Early offset detected'), ('offset_late_fraction', 'Late offset detected'),
        ('median_seeded_virtual_seconds', 'Median simulated s')])
    text += '\nDuration is the median Renode virtual duration among evaluable seeded legal-clock primary runs, excluding endpoints, faults, diagnostics and harness errors; it is not callback latency. See repair_per_subject.csv for paired subject/family detail and repair_primary_index.csv for every primary index and source path. Finalized missing outcomes remain missing.\n\n'
    text += '## Expanded upstream cases and reference attribution\n\n'
    text += markdown_table(s2['boards'], [('board_role', 'Board role'), ('any_setting_runnable', 'Runnable cases'),
                                             ('always_skipped', 'Always skipped'), ('any_observed_failure_cases', 'Any failure'),
                                             ('reference_supported_waiting_cases', 'Reference-supported waits'),
                                             ('cleanup_cascade_cases', 'Cascades'), ('firmware_simulator_or_contract_cases', 'Firmware/simulator/contract')])
    text += '\nAll 470 original failure slots have reference outcomes. A failed seconds-rate reference is a firmware/simulator or accuracy-contract investigation, not a test defect; a passing progress check does not replace that property. F767 is an F4 configuration replica, and board replicas are not pooled as independent tests. Full per-case/skipped/missing/reference data are in s2_per_case_with_references.csv.\n\n'
    text += markdown_table(s2['isolated_reconciliation'], [('case', 'Case'), ('isolated_seed_failures', 'Isolated failures /100'),
                                                           ('full_seed_failures', 'Full-app failures /100'),
                                                           ('isolated_fail_full_pass', 'Isolated-fail/full-pass'),
                                                           ('isolated_pass_full_fail', 'Reverse differences')])
    text += '\nThe phase explanation is source-supported but not directly measured. Exact source quotations and two-sentence examples are in EXAMPLES.md.\n\n'
    text += '## Final statistics on the original generated cohort\n\n'
    p = statistics['prompt_fisher']['two_sided_p']
    text += 'Observed flip contrast: **3/34 base versus 0/32 with clock ranges**, two-sided Fisher p=%.6f. Confirmed robust yield: **%s/90**; optimistic missing-outcome ceiling **%s/90**, which is not a confidence interval.\n\n' % (p, statistics['confirmed_robust'], statistics['optimistic_robust_ceiling'])
    text += markdown_table(statistics['yield_cells'], [('model', 'Model'), ('condition', 'Prompt'), ('working', 'Working /15'),
                                                      ('confirmed_robust', 'Confirmed robust /15'), ('optimistic_robust_ceiling', 'Optimistic ceiling /15'),
                                                      ('robust_plus_two', 'Robust + two detections /15')])
    text += '\nAll 66 eligible suites are measured; 12 original seed verdicts remain missing. E V0 reruns never replace them. The manual source-derived forecast applies to 30/66 suites; all 3,000 predictable verdicts are now measured. Most predictable vectors are zero-failure checks; the three nontrivial vectors remain separately reported. Statistics, descriptive Wilson intervals, exact paired tests and source hashes are in the accompanying ledgers.\n\n'
    text += '## Distribution sensitivity\n\n'
    text += 'The primary normal columns condition on the documented legal interval; sigma is 5 kHz for ±3 sigma and 7.5 kHz for ±2 sigma, centered on 32 kHz. Untruncated CDFs and out-of-range mass are supplied separately. These are illustrative assumptions, not measured distributions of devices. Phase-envelope results are bounds, not fitted exact thresholds. For cascades and unresolved rate contracts, source-only shares are not identifiable; separately labeled observed monotone-step interpolation is available in sensitivity.csv and must not be presented as measured device risk.\n\n'
    text += markdown_table(sensitivity, [('subject', 'Case/suite'), ('boundary_display_khz', 'Source boundary/band, kHz'), ('boundary_method', 'Boundary model'),
                                        ('uniform_display_percent', 'Uniform'), ('normal_3sigma_display_percent', 'Normal ±3σ, legal'),
                                        ('normal_2sigma_display_percent', 'Normal ±2σ, legal')])
    text += '\n## Two axes: legal-clock survival and slow-fault detection\n\n'
    text += markdown_table(axis_counts, [('scope', 'Context'), ('clock_status', 'Clock status'),
                                         ('slow_status', 'Slow-fault status'), ('suites_or_cases', 'Count')])
    text += '\nUnknown verdicts and capability skips are not passes. Expanded full-application S2 cases have no measured slow-fault result; their unknown axis is retained in two_axis_per_subject.csv rather than inferred from isolated cases or legal-clock results.\n\n'
    text += '## Before/after number approval\n\nSee before_after_numbers.csv for every proposed replacement/table-row change, manuscript line locations and source paths, and unchanged_numbers.json for preserved original counts. Secondary paired, timing and similarity material is to move into the repository after approval. No replacements have been applied by this evidence builder.\n\n'
    text += '## Evidence checkpoint and authorized continuation\n\n**The human removed the Phase 3 approval stop on 2026-11-02.** Internally verify this complete evidence package, then continue directly to Phase C with verified values and framing, compile within six pages including the inline bibliography, and perform the Phase D artifact/data dictionary, clean-clone reproduction and tagged-release work. Do not proceed on unresolved integrity inconsistencies. E2 remains held; the automation cannot submit normal-queue jobs.\n'
    (a.out / 'PHASE3_PACKAGE.md').write_text(text)
    outputs = {str(p.relative_to(a.out)): sha(p) for p in sorted(a.out.iterdir()) if p.is_file()}
    save(a.out / 'output_hashes.json', outputs)
    print(str(a.out / 'PHASE3_PACKAGE.md'))


if __name__ == '__main__':
    main()
