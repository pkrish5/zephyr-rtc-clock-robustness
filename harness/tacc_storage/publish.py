#!/usr/bin/env python3
"""Publish one checked archive per job/subject to WORK; never delete sources.

Call only after all writers stop, including on the wrapper's signal path.
An interrupted archive preserves partial bytes without inventing verdicts.
"""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys

from archive import inventory, pack, sha, verify


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--label',required=True)
    ap.add_argument('--state',choices=('complete','interrupted','failed'),required=True)
    ap.add_argument('--source',type=Path)
    a=ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',a.label):raise RuntimeError('Invalid archive label')
    job=os.environ['SLURM_JOB_ID']
    repo=Path(os.environ['RTC_REPO']).resolve()
    repo.relative_to(Path(os.environ['WORK']).resolve())
    base=Path(os.environ['RTC_JOB_BASE']).resolve()
    base.relative_to(Path(os.environ['SCRATCH']).resolve())
    source=(a.source or Path(os.environ['RTC_JOB_OUTPUT'])).resolve();source.relative_to(base)
    dest=Path(os.environ['RTC_ARCHIVE_BASE']).resolve();dest.relative_to(repo/'tacc_work')
    # Final evidence contains no caches or build intermediates unless a caller
    # explicitly copied a kept ELF/log into its output before publication.
    original=inventory(source)
    stem=job+'-'+a.label
    temporary=base/(stem+'.tar.gz')
    pack(source,original,temporary);verify(temporary,original)
    if inventory(source)!=original:raise RuntimeError('Writers changed output while packing')
    digest=sha(temporary)
    provenance=dict(slurm_job_id=job,node_name=os.environ.get('SLURMD_NODENAME',socket.gethostname()),
        account=os.environ['SLURM_JOB_ACCOUNT'],partition=os.environ['SLURM_JOB_PARTITION'],
        container_sha256=os.environ['RTC_CONTAINER_SHA256'],
        apptainer_version=os.environ['RTC_APPTAINER_VERSION'],
        apptainer_module='tacc-apptainer/1.4.1',launcher_module='launcher/3.10',
        output_state=a.state,physical_loose_output=str(source),
        raw_bytes_unchanged=True,exact_archive_coverage=True,extracted_stream_hashes_match=True)
    if not re.fullmatch(r'[0-9a-f]{64}',provenance['container_sha256']):raise RuntimeError('Image identity missing')
    # Re-check just before WORK publication; a successful entry gate is not
    # evidence that headroom still exists after a long-running job.
    subprocess.run([sys.executable, str(repo/'harness/tacc_storage/check_headroom.py')],check=True)
    dest.mkdir(parents=True,exist_ok=True)
    archive=dest/(stem+'.tar.gz')
    with temporary.open('rb') as src,archive.open('xb') as dst:shutil.copyfileobj(src,dst)
    if sha(archive)!=digest:raise RuntimeError('WORK archive copy differs')
    manifest=dest/(stem+'.manifest.json.gz')
    with gzip.open(manifest,'xt') as f:json.dump(dict(files=original,provenance=provenance),f,sort_keys=True)
    with (dest/(stem+'.tar.gz.sha256')).open('x') as f:f.write(digest+'  '+archive.name+'\n')
    receipt=dict(archive=str(archive),archive_sha256=digest,manifest=str(manifest),manifest_sha256=sha(manifest),
        archive_entries=len(original),original_files_deleted=0,**provenance)
    with (dest/(stem+'.json')).open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
