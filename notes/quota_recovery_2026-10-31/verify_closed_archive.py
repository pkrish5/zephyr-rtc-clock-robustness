#!/usr/bin/env python3
"""Independently verify a returned closed-output archive without extracting it."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'manifest', 'receipt', 'out'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    source = Path(__file__).with_name('archive_closed_outputs.py')
    spec = importlib.util.spec_from_file_location('closed_archive_verifier', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    receipt = json.loads(a.receipt.read_text())
    with gzip.open(a.manifest, 'rt') as stream:
        manifest = json.load(stream)
    expected = receipt['archive_sha256']
    if module.sha(a.archive) != expected:
        raise RuntimeError('Transferred archive checksum differs')
    if module.sha(a.manifest) != receipt['verification_manifest_sha256']:
        raise RuntimeError('Transferred verification manifest differs')
    proof = manifest['predelete']
    if (proof['archive_sha256'] != expected or not proof['exact_archive_coverage']
            or not proof['extracted_stream_hashes_match']):
        raise RuntimeError('Pre-deletion verification is not complete')
    if proof['protected_intersections'] or proof['sealed_input_intersections']:
        raise RuntimeError('Protected or sealed input intersects prune roster')
    original = manifest['original']
    if len(original) != receipt['verified_entries']:
        raise RuntimeError('Original member count differs')
    if not set(proof['deletion_paths']) <= set(original):
        raise RuntimeError('Prune roster includes an unarchived original')
    # This compares every actual extracted regular-file stream with the
    # original SHA-256, plus exact directory/link types and link targets.
    module.verify(a.archive, original)
    value = dict(archive_sha256=expected, entries_verified=len(original),
                 regular_files_verified=sum(row['kind'] == 'file' for row in original.values()),
                 exact_member_coverage=True, extracted_stream_hashes_match=True,
                 archive_retained_on_work=receipt['archive_retained_on_work'],
                 protected_files_pruned=receipt['protected_files_pruned'],
                 sealed_inputs_pruned=receipt['sealed_inputs_pruned'],
                 remote_receipt_sha256=module.sha(a.receipt),
                 new_simulations=0, new_builds=0, local_files_deleted=0)
    if value['protected_files_pruned'] or value['sealed_inputs_pruned']:
        raise RuntimeError('Remote receipt indicates protected pruning')
    with a.out.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
