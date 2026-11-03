#!/usr/bin/env python3
"""Inventory retained results/analysis files and release inputs with field schemas.

The catalogue describes stored structure, not scientific validity. Historical
files remain historical; the final reconciliation is the submission authority.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
from common import sha


def field_description(name):
    key = name.rsplit('.', 1)[-1].replace('[]', '')
    exact = {
        'outcome': ('categorical', 'Primary recorded verdict; pass/fail/harness_error/skip/timeout/unknown. Only explicit selected-case assertion failures count as fault detections.'),
        'status': ('categorical', 'Stored case, build or check status; its enclosing schema supplies the stage. Skips and missing outcomes are distinct from passes.'),
        'cases': ('array', 'Declared ztest cases and their individual statuses; application-level outcomes do not replace these.'),
        'condition': ('categorical', 'Seeded legal input or min/max endpoint; prompt condition uses a separate prompt field.'),
        'prompt_condition': ('categorical', 'range_absent is the base prompt; range_present is the prompt with clock ranges and the delivery reminder.'),
        'operator': ('categorical', 'Recorded legal-clock, fast/slow oscillator, nonarrival or early/late alarm-offset probe.'),
        'seed': ('integer index', 'Index into the frozen shared frequency schedule, not an independently replicated test task.'),
        'index': ('integer index', 'Registered evaluation/task index; provenance identifies the corresponding frozen task list.'),
        'virtual_ns': ('simulated ns', 'Renode virtual duration. Divide by 1e9 for simulated seconds; this is not callback-delivery latency.'),
        'wall_seconds': ('wall s', 'Elapsed real execution time; not Renode simulated time.'),
        'category': ('categorical', 'S2 a: single-boundary wait; b: phase-dependent wait; c: cleanup cascade; d: unresolved rate/accuracy contract. Blank means no observed failure.'),
        'final_category': ('categorical', 'Post-reference attribution; a failing reference remains firmware/simulator/contract investigation, not test brittleness.'),
        'board_role': ('categorical', 'Configuration identity; F767 is an F4 configuration replica and is not pooled as an independent hardware subject.'),
        'reference_outcomes': ('semicolon-separated categories', 'Outcomes of the reference cases listed in reference_cases, in the same order.'),
        'boundary_method': ('text', 'Source-only threshold, phase envelope, or explicitly labeled illustrative interpolation; unresolved contracts have no validated defect boundary.'),
        'confirmed_robust': ('suites', 'Eligible suites with all 100 original seeded verdicts observed passing; endpoints are reported separately.'),
        'optimistic_robust_ceiling': ('suites', 'No observed legal-clock failure, allowing missing outcomes to pass. This is a bound, not a confidence interval.'),
        'robust_plus_two': ('suites', 'Confirmed robust suites also explicitly detecting slow oscillator and nonarrival faults.'),
        'q': ('suites', 'Robust plus slow/nonarrival detection and a known budget no more than twice the legal slow bound; 2x is descriptive.'),
    }
    if key in exact:
        return exact[key]
    if 'sha256' in key or key.endswith('_hash'):
        return 'SHA256 hex', 'Integrity digest of the named artifact; not a test outcome.'
    if key.endswith('_hz') or key in ('frequency_hz', 'lsi_frequency_hz'):
        return 'Hz', 'Recorded oscillator frequency or source-derived frequency bound identified by the field name.'
    if 'khz' in key:
        return 'kHz', 'Frequency/boundary in kilohertz; a range denotes an envelope rather than an exact threshold.'
    if key.endswith('_ns'):
        return 'ns', 'Nanoseconds in the recorded clock domain; virtual fields use Renode simulated time.'
    if key.endswith('_ms'):
        return 'ms', 'Milliseconds; see the named measurement stage for simulated versus elapsed time.'
    if key.endswith('_seconds') or key.endswith('_seconds_low') or key.endswith('_seconds_high'):
        return 's', 'Seconds; virtual/simulated fields use Renode time, wall/elapsed fields use real time.'
    if 'percent' in key or key.endswith('_pct'):
        return '%', 'Percentage on a 0–100 scale; the associated denominator/scope is retained.'
    if 'conditional_legal' in key or 'untruncated' in key or key.endswith('_p') or key in ('p_value', 'p'):
        return 'unitless [0,1]', 'Probability/share under the named calculation. Distribution shares are illustrative assumptions, not measured device probabilities.'
    if 'wilson' in key or key.endswith('_ci'):
        return 'unitless interval', 'Descriptive 95% Wilson bounds; shared tasks/settings limit independence.'
    if key.endswith('_path') or key in ('path', 'source', 'record_path'):
        return 'path/reference', 'Saved artifact/source pointer; historical absolute paths are provenance and are not instructions to access that machine.'
    if key.endswith('_id') or key in ('model', 'family', 'unit_id', 'variant', 'case', 'task', 'sign'):
        return 'identifier/category', 'Stored identity/category; use with enclosing task, board and stage rather than pooling replicas.'
    if any(t in key for t in ('count', 'fail', 'pass', 'missing', 'skip', 'detected', 'evaluable', 'launches', 'suites', 'attempts', 'working')):
        return 'count or stored category', 'Named count/category at the enclosing row unit. Missing and skipped outcomes remain separate; evaluable denominators exclude them.'
    if key.endswith('_fraction') or 'fraction' in key:
        return 'ratio or exact rational text', 'Named numerator/denominator; preserve the explicit evaluable population.'
    if key.endswith('_bytes') or key == 'bytes':
        return 'bytes', 'Stored file or payload size.'
    return 'metadata (no physical unit)', 'Literal stored field named ' + name + '; structure/type is catalogued without assigning an undocumented physical unit. Consult its producer and dated protocol for interpretation.'


def structure(value, prefix='', depth=0):
    if isinstance(value, list):
        fields = set()
        for child in value[:20]:
            fields.update(structure(child, prefix + '[]', depth + 1))
        return fields or {(prefix + '[]', 'empty array')}
    if isinstance(value, dict):
        if depth >= 4:
            return {(prefix or '$', 'object (nested metadata)')}
        # Dynamic run-ID/path/hash dictionaries contain data keys, not columns.
        dynamic = len(value) > 100 or (value and sum('/' in k or len(k) == 64 for k in value) > len(value) / 2)
        if dynamic:
            return {(prefix + '{key}', 'map; keys are IDs/paths, values preserve stored metadata')}
        fields = set()
        for key, child in value.items():
            name = prefix + '.' + key if prefix else key
            fields.update(structure(child, name, depth + 1))
        return fields or {(prefix or '$', 'empty object')}
    return {(prefix or '$', 'null' if value is None else type(value).__name__)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--package', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    inputs = json.loads(a.inputs.read_text())
    tracked = subprocess.check_output(['git', 'ls-files', '-z', 'results', 'analysis'], cwd=repo).decode().split('\0')
    names = set(inputs) | {p for p in tracked if p}
    names |= {str(p.relative_to(repo)) for p in (repo / 'analysis/final_submission_v1').glob('*.py')}
    names |= {str(p.relative_to(repo)) for p in a.package.resolve().iterdir() if p.is_file()}
    schemas, rows = {}, []
    for relative in sorted(names):
        path = repo / relative
        if not path.is_file():
            continue
        schema = []
        meaning = 'One retained artifact; see producer/protocol. Historical snapshots are not additional experimental replication.'
        if path.suffix == '.csv':
            with path.open(newline='') as f:
                reader = csv.reader(f)
                header = next(reader, [])
            schema = sorted((c, 'CSV scalar; blank denotes unavailable/not applicable, not zero') for c in header)
            meaning = 'One row per stored ' + ('primary evaluation index' if 'repair_primary_index' in relative else
                      'suite/task' if 'per_suite' in relative or 'per_subject' in relative else
                      'board/application case' if 'per_case' in relative else
                      'model/prompt cell' if 'cells' in relative else
                      'named aggregation or saved assessment; identifiers/denominators are explicit columns') + '.'
        elif path.suffix == '.json':
            value = json.loads(path.read_text())
            schema = sorted(structure(value))
            meaning = ('One simulator run with per-case verdicts and provenance.' if '/records/' in relative else
                       'One parsed simulator trace.' if '/traces/' in relative else
                       'One structured manifest, analysis snapshot or integrity ledger; nested lists/maps retain their keys.')
        else:
            meaning = ('Raw UART/monitor/resource text for the associated run; preserve bytes for hash/replay checks.' if path.suffix in ('.log', '.time') else meaning)
        sid = hashlib.sha256(json.dumps(schema).encode()).hexdigest()[:20] if schema else ''
        if sid:
            schemas[sid] = schema
        rows.append(dict(path=relative, bytes=path.stat().st_size, sha256=inputs.get(relative) or sha(path),
                         role='final-analysis input' if relative in inputs else 'final derived output' if str(a.package) in relative else 'retained historical results/analysis',
                         row_or_file_meaning=meaning, schema_id=sid,
                         retrieval='release evidence archive' if relative in inputs else
                         'compressed Git snapshot at ' + relative + '.gz; also regenerated by offline analysis'
                         if path.name in ('input_hashes.json', 'output_hashes.json') and path.parent == a.package.resolve()
                         else 'Git repository'))
    a.out.mkdir(parents=True, exist_ok=True)
    def write_gzip(name, rows, fields):
        with (a.out / name).open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
    write_gzip('files.csv.gz', rows, list(rows[0]))
    fields = []
    for sid, schema in sorted(schemas.items()):
        for name, kind in schema:
            units, meaning = field_description(name)
            fields.append(dict(schema_id=sid, field=name, storage_type=kind, units=units, meaning=meaning))
    write_gzip('fields.csv.gz', fields, list(fields[0]))
    result = dict(files=len(rows), schemas=len(schemas), field_definitions=len(fields),
                  scope='Every Git-tracked results/analysis file, every final raw-analysis input, and every final-package output.',
                  nested_json_note='Arrays show [] and maps show {key}; map keys are data, not column names. Deep metadata objects remain objects. Null/blank is not numeric zero.')
    (a.out / 'catalogue.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
