#!/usr/bin/env python3
"""Selection/provenance guard, then exec the unchanged sealed E evaluator."""
import json
import os
from pathlib import Path
import sys
from setup_fixture import read, sha
from setup_resume import record_relative


index, chunk_id = map(int, sys.argv[1:])
assert os.environ['SLURM_JOB_PARTITION'] == 'normal'
packet = Path('/recovery-packet')
plan = read(packet / 'resume_plan.json')
assert sha(packet / 'resume_plan.json') == os.environ['RTC_E_RESUME_PLAN_SHA256']
selection = read(packet / 'selection.json')
assert sha(packet / 'selection.json') == plan['selection_sha256']
assert index in plan['chunks'][chunk_id]['indices']
assert str(index) not in selection['completed_record_sha256']
old_plan = read(Path('/bundle/plan.json'))
assert sha(Path('/bundle/plan.json')) == plan['original_plan_sha256']
out = Path('/study') / old_plan['output_relative']
assert not (out / 'STOP.json').exists()
assert sha(out / 'execution.json') == plan['execution_sha256']
assert sha(out / 'tasks-evaluate.json') == plan['tasks_sha256']
task = read(out / 'tasks-evaluate.json')[index]
assert task['index'] == index
old_record = Path('/original/study') / old_plan['output_relative'] / record_relative(task)
if old_record.exists():
    try:
        read(old_record)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    else:
        raise RuntimeError('A finalized original cannot be retried')
assert not (out / record_relative(task)).exists()
assert (Path('/original/study') / old_plan['output_relative'] / 'STOP.json').is_file()
# Do not import, monkey-patch or change the original scientific worker.
os.execv(sys.executable, [sys.executable, '/phase2/worker_e.py',
                        '--bundle', '/bundle', '--stage', 'evaluate', '--index', str(index)])
