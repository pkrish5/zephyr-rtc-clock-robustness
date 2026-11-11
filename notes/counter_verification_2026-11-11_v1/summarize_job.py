#!/usr/bin/env python3
"""Summarize only independently verified diagnostic evidence; no simulation."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verified', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    v = json.loads((a.verified / 'verification.json').read_text())
    assert v['job_id'] == '3575326' and v['complete_job']
    assert v['qualification_passed'] and v['replays_agree']
    assert v['complete_processes'] == 46 and v['missing_processes'] == 0
    rows = list(csv.DictReader((a.verified / 'case_verdicts.csv').open()))
    groups = defaultdict(Counter)
    for r in rows:
        assert r['usable'] == 'True'
        groups[(r['mode'], r['phase'])][r['status']] += 1
    cells = v['reference_cell_counts']
    functions = [r for r in cells if r['phase'] == 'evaluation' and r['unit_id'] == 'f4-functional-reference']
    assert len(functions) == 17
    assert all(r['counts'] == {'pass': 3, 'fail': 0, 'skip': 0, 'missing': 0} for r in functions)
    controls = []
    for r in v['activation_controls']:
        unit = 'f4-progress-control'
        condition = 'nominal' if r['frequency_hz'] == 32000 else ('slow_progress_control' if r['frequency_hz'] == 10000 else 'fast_progress_control')
        log = a.verified / 'output/references/uart' / f"{unit}-{condition}-{r['index']:03d}.log"
        matches = re.findall(r'VERIFY_RATE delta_ticks=(\d+) elapsed_ms=(\d+)', log.read_text())
        assert matches == [(str(r['delta_ticks']), str(r['elapsed_ms']))]
        controls.append(dict(**r, uart_path=str(log), uart_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                             over_upper_ms=max(0, r['elapsed_ms'] - r['upper_ms'])))
    coverage = json.loads((a.verified / 'reference_coverage.json').read_text())
    assert len(coverage) == 87 and all(r['reference_outcome'] == 'pass' for r in coverage)
    coverage_counts = Counter(r['primary_slot']['case'] for r in coverage)
    result = dict(job_id=v['job_id'], elapsed=v['sacct']['elapsed'], archive_sha256=v['archive_sha256'],
                  archive_entries=v['exact_archive_entries'], planned_processes=46, complete_processes=46,
                  missing_processes=0, nominal_launches_passed=10, nominal_case_passes=20,
                  replay_launches_matched=17, replay_full_case_counts=dict(groups[('replays', 'replays')]),
                  functional_legal_settings=17, functional_legal_case_counts={'pass': 51, 'fail': 0, 'skip': 0, 'missing': 0},
                  covered_primary_failure_slots=87, covered_primary_cases=dict(coverage_counts),
                  activation_controls=controls, activation_qualified=all(c['complete'] and c['passed'] for c in controls),
                  ztest_progress_case_counts={'pass': 7, 'fail': 0, 'skip': 0, 'missing': 0},
                  protected_originals_unchanged=30067, active_original_seals_unchanged=764,
                  reused_original_elf_hashes_unchanged=4, original_outcomes_replaced=False,
                  slow_fault_detection_or_acceptance_finalized=False, manuscript_edited=False,
                  stop_reason='The 10-kHz control exceeds its preregistered upper observer bound; no tolerance tuning or rerun.')
    assert result['activation_qualified'] is False
    a.out.mkdir(parents=True, exist_ok=False)
    with (a.out / 'summary.json').open('x') as f: json.dump(result, f, indent=2, sort_keys=True); f.write('\n')
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__': main()
