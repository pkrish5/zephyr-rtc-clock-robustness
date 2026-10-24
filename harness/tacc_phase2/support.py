"""Append-only Phase 2 adapters; original simulation implementations stay frozen."""
import hashlib
import importlib.util
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

IMAGE_SHA = "94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write('\n')


def utc():
    return datetime.now(timezone.utc).isoformat()


def load_plan(bundle):
    bundle = Path(bundle)
    p = bundle / 'plan.json'
    if sha(p) != (bundle / 'plan.sha256').read_text().split()[0]:
        raise RuntimeError('Plan seal differs')
    return read(p)


def provenance(bundle):
    if not os.environ.get('SLURM_JOB_ID'):
        raise RuntimeError('A Slurm allocation is required')
    if os.environ['RTC_CONTAINER_SHA256'] != IMAGE_SHA:
        raise RuntimeError('Image differs from calibrated image')
    if os.environ['RTC_APPTAINER_VERSION'] not in ('apptainer version 1.4.1', 'apptainer version 1.4.1-1.el8'):
        raise RuntimeError('Apptainer 1.4.1 required')
    return dict(node_name=os.environ.get('RTC_NODE_NAME', socket.gethostname()),
                container_sha256=IMAGE_SHA, apptainer_version=os.environ['RTC_APPTAINER_VERSION'],
                slurm_job_id=os.environ['SLURM_JOB_ID'], slurm_partition=os.environ.get('SLURM_JOB_PARTITION'),
                apptainer_module='tacc-apptainer/1.4.1', launcher_module='launcher/3.10',
                phase2_plan_sha256=sha(Path(bundle) / 'plan.json'))


def original_module(name):
    path = Path('/opt/rtc-code/harness') / (name + '.py')
    spec = importlib.util.spec_from_file_location('frozen_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_inputs(bundle, repo=None):
    bundle = Path(bundle)
    plan = load_plan(bundle)
    for rel, digest in plan['input_sha256'].items():
        if sha(bundle / rel) != digest:
            raise RuntimeError('Input differs: ' + rel)
    if repo:
        for rel, digest in plan['code_sha256'].items():
            if sha(Path(repo) / rel) != digest:
                raise RuntimeError('Code differs: ' + rel)
    return plan
