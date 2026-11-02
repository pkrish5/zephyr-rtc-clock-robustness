#!/usr/bin/env python3
"""Freeze new task-specific references and complete S2 failure coverage; no runs."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--packet', type=Path, required=True)
    a = ap.parse_args()
    repo = a.repo.resolve()
    source = repo / 'notes/s2_attribution_2026-10-31/returned-3544535/verified/evidence/bundle/plan.json'
    old = json.loads(source.read_text())
    proposal_path = repo / 'notes/s2_attribution_2026-10-31/replay_plan_20261101_v1/replay_proposal.json'
    proposal = json.loads(proposal_path.read_text())
    comparison = repo / 'notes/s2_attribution_2026-10-31/replay_comparison_20261102_v1/replay_summary.json'
    replay = json.loads(comparison.read_text())
    assert replay['status_counts'] == {'identical': 274} and replay['case_failures_in_identical_replays'] == 470
    app = repo / 'subjects/s2_references_20261102_v1'
    app_sha = {str(p.relative_to(app)): sha(p) for p in sorted(app.rglob('*')) if p.is_file()}
    expected = {'rtc': ['ref_rtc.test_a_alarm_pending', 'ref_rtc.test_b_alarm_callback', 'ref_rtc.test_c_time_counting'],
                'counter': ['ref_counter.test_all_channels', 'ref_counter.test_single_shot_alarm_notop'],
                'seconds': ['ref_seconds.test_a_rate_contract', 'ref_seconds.test_b_legal_clock_progress']}
    mapping = {'rtc_api.test_alarm': ['ref_rtc.test_a_alarm_pending'],
               'rtc_api.test_alarm_callback': ['ref_rtc.test_b_alarm_callback'],
               'rtc_api.test_time_counting': ['ref_rtc.test_c_time_counting'],
               'counter_basic.test_all_channels': ['ref_counter.test_all_channels'],
               'counter_basic.test_single_shot_alarm_notop': ['ref_counter.test_single_shot_alarm_notop'],
               'seconds_counter.test_seconds_rate': ['ref_seconds.test_a_rate_contract', 'ref_seconds.test_b_legal_clock_progress']}
    a.packet.mkdir(parents=True, exist_ok=False)
    config = a.packet / 'inputs/configs/reference-rtc.conf'
    config.parent.mkdir(parents=True)
    config.write_text('CONFIG_RTC_ALARM=y\nCONFIG_RTC_UPDATE=y\nCONFIG_RTC_CALIBRATION=y\n')
    inputs = dict(old['input_sha256'])
    inputs['configs/reference-rtc.conf'] = sha(config)
    plan = {key: copy.deepcopy(old[key]) for key in
            ('boards', 'image_sha256', 'original_platform_sha256', 'upstream_input_sha256',
             'renode_version', 'original_local_renode_version', 'zephyr_commit', 'quantum_ns', 'step_ns')}
    plan.update(phase='S2 task-specific reference validation', registered_date='2026-11-02',
        source_primary_plan_sha256=sha(source), source_primary_replay_proposal_sha256=sha(proposal_path),
        verified_replay_summary_sha256=sha(comparison), design_sha256=sha(repo / 'paper/DESIGN.md'),
        output_relative='results/s2_references_20261102_v1',
        frozen_s2_worker_sha256=sha(repo / 'harness/tacc_s2/worker.py'),
        reference_sources_sha256=app_sha, input_sha256=inputs,
        production_authorized=False, execution_authorization='User requested complete reference validation on development or normal as needed; this job is development only.',
        node_count=1, walltime='02:00:00', maximum_workers=32, compiler_parallelism=2,
        build_timeout_seconds=1800, primary_failure_slots_covered=470,
        normal_queue_submission_authorized=False, development_reservation_su_ceiling=2.0,
        reference_case_mapping=mapping,
        board_roles={'f4': 'F4 configuration', 'f767': 'F4 configuration replica (F767)',
                     'f746': 'F746 configuration', 'h753': 'H753 configuration, narrower legal range'},
        reference_interpretation=dict(reference_failure='firmware_or_simulator_flag_not_test_brittleness',
            rate_contract='Retain original 1200-ms one-to-two-tick check; report alongside separate legal-clock progress check. The accuracy contract remains unresolved.',
            cascade='A passing clean-state reference does not turn the original cascade into an independent waiting defect.',
            phase='Supported by source and reconciliation, not directly measured.',
            reference_scope='Task-specific functional controls, not coverage-equivalent copies of every upstream API assertion.'))
    plan['units'] = []
    tasks = []
    for u in old['units']:
        v = copy.deepcopy(u)
        v['app'] = '/reference-app/' + u['family']
        v['config'] = 'configs/reference-rtc.conf' if u['family'] == 'rtc' else u['config']
        v['expected_declared_cases'] = expected[u['family']]
        v['max_virtual_seconds'] = {'rtc': 180, 'counter': 60, 'seconds': 30}[u['family']]
        v['wall_timeout_seconds'] = 900
        plan['units'].append(v)
        board = old['boards'][u['board_id']]
        settings = [('nominal', board['nominal'])] * 5 + [('min', board['minimum']), ('max', board['maximum'])]
        for repeat, (condition, hz) in enumerate(settings):
            tasks.append(dict(index=len(tasks), unit_id=u['id'], frequency_hz=hz, condition=condition,
                              phase='qualification', qualification_repeat=repeat))
    assert len(tasks) == 77
    for item in proposal['tasks']:
        t = copy.deepcopy(item['primary_task'])
        t.update(index=len(tasks), phase='evaluation', primary_run_id=item['primary_run_id'],
                 primary_task_index=item['primary_task']['index'],
                 primary_record_sha256=item['primary_record_sha256'], failed_cases=item['failed_cases'])
        assert all(case in mapping for case in t['failed_cases'])
        tasks.append(t)
    assert len(tasks) == 351 and sum(len(t.get('failed_cases', [])) for t in tasks) == 470
    plan['tasks'] = tasks
    save(a.packet / 'plan.json', plan)
    (a.packet / 'plan.sha256').write_text(sha(a.packet / 'plan.json') + '  plan.json\n')
    paths = [p for root in ('harness/tacc_s2_references', 'harness/tacc_storage', 'subjects/s2_references_20261102_v1')
             for p in (repo / root).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [repo / 'harness/tacc_s2/worker.py']
    save(a.packet / 'code.sha256.json', {str(p.relative_to(repo)): sha(p) for p in sorted(paths)})
    save(a.packet / 'packet_receipt.json', dict(plan_sha256=sha(a.packet / 'plan.json'),
        code_sha256_manifest=sha(a.packet / 'code.sha256.json'), design_sha256=plan['design_sha256'],
        new_reference_builds=11, qualification_launches=77, evaluation_launches=274,
        original_failure_slots_covered=470, reference_sources=len(app_sha), new_experiments_run=0,
        queue='development', nodes=1, walltime='02:00:00', reservation_su_ceiling=2.0))
    print((a.packet / 'packet_receipt.json').read_text())


if __name__ == '__main__':
    main()
