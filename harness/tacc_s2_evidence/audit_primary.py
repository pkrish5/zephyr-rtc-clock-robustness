#!/usr/bin/env python3
"""Audit copied S2 primary evidence locally; never run or alter a test.

Counts describe full-application execution. A failed case is not classified
as a brittle oracle before replay/reference attribution. Partial application
summaries remain missing for the primary complete-application comparison.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def write_csv(path, rows):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--sealed-plan', type=Path, required=True)
    parser.add_argument('--nominal-cases', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--records-only', action='store_true',
                        help='Explicitly provisional metadata accounting; do not claim log/ELF verification')
    args = parser.parse_args()
    bundle, dest = args.bundle, args.out
    plan_path = args.sealed_plan if args.records_only else bundle / 'plan.json'
    plan = json.loads(plan_path.read_text())
    digest = sha(plan_path)
    assert digest == sha(args.sealed_plan)
    if not args.records_only:
        assert digest == (bundle / 'plan.sha256').read_text().split()[0]
        for relative, expected in plan['input_sha256'].items():
            assert sha(bundle / relative) == expected, relative
    for relative, expected in plan['code_sha256'].items():
        assert sha(args.repo / relative) == expected, relative
    assert sha(args.repo / 'paper/DESIGN.md') == plan['design_sha256']
    out = bundle / plan['output_relative']
    units = {u['id']: u for u in plan['units']}
    tasks = {t['index']: t for t in plan['tasks']}
    nominal = {(r['unit_id'], r['case']): r['nominal_status'] for r in
               csv.DictReader(args.nominal_cases.open())}
    builds = {}
    for uid in units:
        if args.records_only:
            continue
        root = out / 'builds' / uid
        p = root / 'build_record.json'
        r = json.loads(p.read_text())
        assert r['status'] == 'built'
        assert sha(root / 'build.log') == r['log_sha256'], uid
        assert sha(bundle / r['elf_path']) == r['elf_sha256'], uid
        for relative, expected in r['build_products_sha256'].items():
            assert sha(root / 'build' / relative) == expected, (uid, relative)
        builds[uid] = (r, sha(p))
    setup = {} if args.records_only else json.loads((out / 'setup_audit.json').read_text())
    if not args.records_only:
        assert setup['new_builds'] == 0 and setup['scientific_inputs_changed'] == []
    for r in setup.get('builds', []):
        build, bdigest = builds[r['unit_id']]
        assert r['byte_identical'] is True
        assert r['elf_sha256'] == build['elf_sha256']
        assert r['build_record_sha256'] == bdigest

    records, record_files, processes = {}, {}, {}
    case_pattern = re.compile(r'-\s+(PASS|FAIL|SKIP)\s+-\s+\[([^\]]+)\]')
    for path in sorted((out / 'records').glob('*.json')):
        r = json.loads(path.read_text())
        index = r['index']
        assert index in tasks and index not in records, path
        for key, value in tasks[index].items():
            assert r[key] == value, (index, key)
        uid, rid = r['unit_id'], r['run_id']
        build, bdigest = builds.get(uid, ({}, None))
        assert rid == f"{uid}-{r['condition']}-{index:03d}"
        assert r['plan_sha256'] == digest
        assert r['container_sha256'] == plan['image_sha256']
        assert r['renode_version'] == plan['renode_version']
        assert r['apptainer_module'] == 'tacc-apptainer/1.4.1'
        assert r['launcher_module'] == 'launcher/3.10'
        assert r['apptainer_version'] in ('apptainer version 1.4.1', 'apptainer version 1.4.1-1.el8')
        assert str(r['slurm_job_id']) == '3535524'
        assert r['slurm_partition'] == 'normal' and r['node_name']
        assert r['expected_declared_cases'] == units[uid]['expected_declared_cases']
        assert Counter(c['case'] for c in r['cases']) == Counter(r['expected_declared_cases']), rid
        if args.records_only:
            records[index] = r
            record_files[str(path.relative_to(bundle))] = sha(path)
            continue
        assert r['elf_sha256'] == build['elf_sha256']
        assert r['build_record_sha256'] == bdigest
        assert sha(out / 'platforms' / (rid + '.repl')) == r['platform_sha256']
        for kind, expected in r['log_sha256'].items():
            if expected:
                suffix = '.json' if kind == 'traces' else '.log'
                assert sha(out / kind / (rid + suffix)) == expected, (rid, kind)
        trace = json.loads((out / 'traces' / (rid + '.json')).read_text())
        for key in ('run_id', 'cases', 'application_completed', 'outcome', 'error'):
            assert trace[key] == r[key], (rid, key)
        uart = (out / 'uart' / (rid + '.log')).read_text(errors='replace')
        parsed = [dict(case=case, status=status.lower()) for status, case in case_pattern.findall(uart)]
        assert parsed == r['cases'], rid
        assert r['application_completed'] == any(x in uart for x in
            ('PROJECT EXECUTION SUCCESSFUL', 'PROJECT EXECUTION FAILED')), rid
        for c in r['cases']:
            assert c['case'] in units[uid]['expected_declared_cases']
            assert c['status'] in ('pass', 'fail', 'skip')
        proc = json.loads((out / 'processes/run' / f'{index}.json').read_text())
        assert proc['index'] == index and str(proc['slurm_job_id']) == str(r['slurm_job_id'])
        processes[index] = proc
        records[index] = r
        record_files[str(path.relative_to(bundle))] = sha(path)

    cells = []
    failed = []
    for uid, unit in units.items():
        unit_records = [r for r in records.values() if r['unit_id'] == uid]
        for case in unit['expected_declared_cases']:
            counts = defaultdict(Counter)
            frequencies = []
            for r in unit_records:
                values = [c['status'] for c in r['cases'] if c['case'] == case]
                complete = (r['outcome'] == 'complete' and r['application_completed']
                            and not r['error'] and not r['missing_cases'] and not r['duplicate_cases'])
                status = values[0] if complete and len(values) == 1 else 'missing'
                counts[r['condition']][status] += 1
                if status == 'fail':
                    frequencies.append(r['frequency_hz'])
                    failed.append(dict(unit_id=uid, case=case, frequency_hz=r['frequency_hz'],
                        condition=r['condition'], seed=r.get('seed'), run_id=r['run_id'],
                        record_sha256=record_files[f"{plan['output_relative']}/records/{r['run_id']}.json"],
                        attribution='unattributed primary failure; replay/reference pending'))
            # Entirely absent tasks count as missing, independently of partial logs.
            absent = [t for i, t in tasks.items() if t['unit_id'] == uid and i not in records]
            for t in absent:
                counts[t['condition']]['missing'] += 1
            row = dict(board=plan['boards'][unit['board_id']]['board'], unit_id=uid, case=case,
                       nominal_status=nominal[(uid, case)])
            for cond in ('seeded', 'min', 'max'):
                for status in ('pass', 'fail', 'skip', 'missing'):
                    row[f'{cond}_{status}'] = counts[cond][status]
            row.update(any_failure=bool(frequencies), nominal_pass_to_fail=bool(frequencies) and row['nominal_status'] == 'pass',
                       minimum_failed_hz=min(frequencies) if frequencies else '',
                       maximum_failed_hz=max(frequencies) if frequencies else '')
            cells.append(row)

    boards = []
    for bid in plan['boards']:
        uids = {uid for uid, u in units.items() if u['board_id'] == bid}
        if not uids:
            continue
        rows = [r for r in cells if r['unit_id'] in uids]
        boards.append(dict(board_id=bid, board=plan['boards'][bid]['board'],
            applications=len(uids), launches=sum(r['unit_id'] in uids for r in records.values()),
            declared_cases=len(rows), nominal_runnable=sum(r['nominal_status'] == 'pass' for r in rows),
            nominal_capability_skipped=sum(r['nominal_status'] == 'skip' for r in rows),
            nominal_pass_cases_with_primary_failure=sum(r['nominal_pass_to_fail'] for r in rows),
            cases_with_any_primary_failure=sum(r['any_failure'] for r in rows),
            runnable_at_any_legal_setting=sum(any(r[f'{c}_{s}'] for c in ('seeded','min','max') for s in ('pass','fail')) for r in rows),
            always_skipped_cases=sum(sum(r[f'{c}_skip'] for c in ('seeded','min','max')) == 102 for r in rows),
            missing_case_slots=sum(r[f'{c}_missing'] for r in rows for c in ('seeded','min','max'))))
    report = dict(plan_sha256=digest, expected_launches=len(tasks), records=len(records),
        verification_level='provisional record metadata only' if args.records_only else 'logs, trace contents, inputs and reused ELFs verified',
        raw_log_and_elf_hashes_verified=not args.records_only,
        missing_indices=sorted(set(tasks) - set(records)),
        outcome_counts=dict(Counter(r['outcome'] for r in records.values())),
        process_exit_counts=dict(Counter(str(p['exit_code']) for p in processes.values())),
        records_with_error=[r['run_id'] for r in records.values() if r['error']],
        records_with_missing_cases=[r['run_id'] for r in records.values() if r['missing_cases']],
        records_with_duplicate_cases=[r['run_id'] for r in records.values() if r['duplicate_cases']],
        observed_partial_summaries_unscored=sum(len(r['cases']) for r in records.values() if r['outcome'] != 'complete'),
        declared_case_slots=sum(len(units[t['unit_id']]['expected_declared_cases']) for t in tasks.values()),
        case_slot_counts={s: sum(r[f'{c}_{s}'] for r in cells for c in ('seeded', 'min', 'max')) for s in ('pass', 'fail', 'skip', 'missing')},
        nodes=sorted({r['node_name'] for r in records.values()}),
        slurm_job_ids=sorted({r['slurm_job_id'] for r in records.values()}),
        container_sha256=plan['image_sha256'], audit_sha256=sha(Path(__file__)),
        new_builds=0, new_simulations=0, replay_reference_attribution_complete=False,
        board_replicas_are_independent_subjects=False, boards=boards,
        nominal_case_source_sha256=sha(args.nominal_cases))
    assert sum(report['case_slot_counts'].values()) == report['declared_case_slots']
    dest.mkdir(parents=True, exist_ok=False)
    save(dest / 'report.json', report)
    save(dest / 'record_sha256.json', record_files)
    write_csv(dest / 'per_case.csv', cells)
    write_csv(dest / 'per_board.csv', boards)
    if failed:
        write_csv(dest / 'primary_failures.csv', failed)
    print(json.dumps({k: report[k] for k in ('records','missing_indices','outcome_counts','case_slot_counts','boards')}, indent=2))


if __name__ == '__main__':
    main()
