#!/usr/bin/env python3
"""Freeze source sites, then emit approved mechanical repairs into new paths."""
import difflib
import re
from pathlib import Path
from support import read, save, sha, utc
from prepare_repair_review import assertions, replace_once

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'notes/repair_execution_20261024_v2'
REVIEW = ROOT / 'notes/repair_revision_2026-10-24'
OLD = ROOT / 'notes/repair_review_2026-10-24'

HEADER = '''/* Registered mechanical waiting adapter; original assertions remain below.
 * Original timeout messages may still describe V0's budget.
 */
#ifndef REPAIR_WAIT_H
#define REPAIR_WAIT_H
#include <zephyr/kernel.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/sys/util.h>
#include <stdint.h>
#include <stdbool.h>
static int64_t repair_deadline;
static int repair_set_time(const struct device *dev, const struct rtc_time *value)
{
    repair_deadline = k_uptime_get() + 20824;
    return rtc_set_time(dev, value);
}
static inline bool repair_expired(void)
{
    return k_uptime_get() >= repair_deadline;
}
static int32_t repair_sleep(k_timeout_t requested)
{
    int64_t wait_ms = k_ticks_to_ms_ceil64(requested.ticks);
    int64_t remaining = MAX(INT64_C(0), repair_deadline - k_uptime_get());
    if (REPAIR_EVENT_WAIT) {
        wait_ms = MIN(wait_ms, INT64_C(20));
    }
    return k_sleep(K_MSEC(MIN(wait_ms, remaining)));
}
static inline void repair_fixed_wait(void)
{
    k_sleep(K_MSEC(MAX(INT64_C(0), repair_deadline - k_uptime_get())));
}
#define rtc_set_time repair_set_time
#define k_sleep repair_sleep
#define k_msleep(ms) repair_sleep(K_MSEC(ms))
#endif
'''


def inject(text, event):
    lines = text.splitlines(True)
    last = max(i for i, line in enumerate(lines) if line.startswith('#include'))
    lines.insert(last + 1, f'\n#define REPAIR_EVENT_WAIT {int(event)}\n#include "repair_wait.h"\n')
    return ''.join(lines)


def sites(row, source):
    """All sites are chosen on frozen V0, before any new source is generated."""
    sid = row['suite_id']
    if sid in ('human-rtc_alarm_callback', 'sol-range_absent-rtc_alarm_pending-r03'):
        return dict(mode='approved_existing_preview', source_sites=['saved V1/V2/V3 example diffs'], replacements=[])
    pairs = []
    body = source[source.index('ZTEST('):]
    if row['family'] == 'rtc_time_counting':
        if sid == 'human-rtc_time_counting':
            pairs = [('i < RTC_TEST_TIME_COUNTING_POLL_LIMIT', '!repair_expired()')]
            assert source.count(pairs[0][0]) == 2  # loop bound and timeout assertion
        elif 'for (;;)' in body:
            pairs = [('k_uptime_get() - start <= OBSERVATION_MS', '!repair_expired()')]
        elif re.search(r'\bfor\s*\(', body):
            loop = re.search(r'for\s*\([^;]+;\s*([^;]+);', body)
            condition = loop.group(1)
            first = re.match(r'\w+\s*<\s*(?:\w+|\d+)', condition).group(0)
            pairs = [(first, '!repair_expired()')]
        elif re.search(r'deadline\s*=\s*k_uptime_get\(\)\s*\+', body):
            match = re.search(r'deadline\s*=\s*k_uptime_get\(\)\s*\+[^;]+;', body)
            pairs = [(match.group(0), 'deadline = repair_deadline;')]
        elif 'k_uptime_get() - started_ms < 40000' in body:
            pairs = [('k_uptime_get() - started_ms < 40000', '!repair_expired()')]
        elif 'elapsed_ms < OBSERVATION_BOUND_MS' in body:
            pairs = [('elapsed_ms < OBSERVATION_BOUND_MS', '!repair_expired()')]
        else:
            raise RuntimeError('Unmapped counting wait: ' + sid)
    elif sid == 'human-rtc_alarm_pending':
        pairs = [('k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_PENDING_DELAY));', 'repair_fixed_wait();')]
    else:
        match = re.search(r'deadline\s*=\s*k_uptime_get\(\)\s*\+\s*(15000|16000);', body)
        if not match:
            raise RuntimeError('Unmapped pending wait: ' + sid)
        pairs = [(match.group(0), 'deadline = repair_deadline;')]
    for before, after in pairs:
        if source.count(before) != (2 if sid == 'human-rtc_time_counting' else 1):
            raise RuntimeError('Patch site count differs: ' + sid + ': ' + before)
    return dict(mode='frozen_source_site_substitution', replacements=pairs,
                source_sites=[dict(text=a, lines=[i for i, s in enumerate(source.splitlines(), 1) if a in s])
                              for a, b in pairs])


def pending_wait(source, strict):
    helper = '''static int repair_pending[DT_PROP(DT_ALIAS(rtc), alarms_count)];
static void repair_wait_pending(void)
{
    for (uint16_t id = 0; id < alarms_count; ++id) {
        repair_pending[id] = 0;
    }
    while (!repair_expired()) {
        bool complete = true;
        for (uint16_t id = 0; id < alarms_count; ++id) {
            if (repair_pending[id] != 1) {
STRICT_BEFORE
                int status = rtc_alarm_is_pending(rtc, id);
STRICT_AFTER
                repair_pending[id] = status;
                if (status < 0) {
                    return;
                }
            }
            complete &= repair_pending[id] == 1;
        }
        if (complete) {
            return;
        }
        k_sleep(K_MSEC(20));
    }
}

'''
    before, after, comparison = '', '', ''
    if strict:
        before = '''                struct rtc_time repair_before, repair_after;
                zassert_ok(rtc_get_time(rtc, &repair_before));'''
        after = '''                zassert_ok(rtc_get_time(rtc, &repair_after));
                if (status > 0) {
                    zassert_true(repair_cmp(&repair_after, &test_alarm_time_set) >= 0,
                                 "Pending before configured RTC target");
                }'''
        comparison = '''static int repair_cmp(const struct rtc_time *a, const struct rtc_time *b)
{
    const int av[] = {a->tm_year,a->tm_mon,a->tm_mday,a->tm_hour,a->tm_min,a->tm_sec};
    const int bv[] = {b->tm_year,b->tm_mon,b->tm_mday,b->tm_hour,b->tm_min,b->tm_sec};
    for (size_t i=0; i<ARRAY_SIZE(av); ++i) {
        if (av[i] != bv[i]) { return av[i] < bv[i] ? -1 : 1; }
    }
    return 0;
}
'''
    helper = comparison + helper.replace('STRICT_BEFORE', before).replace('STRICT_AFTER', after)
    source = replace_once(source, 'ZTEST(rtc_api, test_alarm)', helper + 'ZTEST(rtc_api, test_alarm)')
    source = replace_once(source, 'repair_fixed_wait();', 'repair_wait_pending();')
    old = '''/* Validate alarm is pending */
		for (uint16_t i = 0; i < alarms_count; i++) {
			ret = rtc_alarm_is_pending(rtc, i);'''
    new = '''/* Validate alarm is pending; the state wait latched consuming reads. */
		for (uint16_t i = 0; i < alarms_count; i++) {
			ret = repair_pending[i];'''
    return replace_once(source, old, new)


def normalized(row, source, site, variant):
    sid = row['suite_id']
    if site['mode'] == 'approved_existing_preview':
        leaf = 'upstream_callback' if sid.startswith('human') else 'generated_sol_pending'
        old_variant = 'V1' if variant == 'V1b' else variant
        text = (OLD / 'examples' / leaf / old_variant / 'test.c').read_text()
        return text, None
    text = source
    for before, after in site['replacements']:
        text = text.replace(before, after)
    text = inject(text, variant in ('V2', 'V3'))
    if sid == 'human-rtc_alarm_pending' and variant in ('V2', 'V3'):
        text = pending_wait(text, variant == 'V3')
    if sid == 'astra-range_absent-rtc_alarm_pending-r05' and variant == 'V3':
        old = '\t\tstruct rtc_time now;\n\t\tint pending = rtc_alarm_is_pending(rtc, 0);'
        new = '''		struct rtc_time now;
		struct rtc_time repair_pending_before;
		zassert_ok(rtc_get_time(rtc, &repair_pending_before));
		int pending = rtc_alarm_is_pending(rtc, 0);'''
        text = replace_once(text, old, new)
    return text, HEADER


def main():
    revision = REVIEW / 'amendment.md'
    if sha(revision) != (REVIEW / 'amendment.sha256').read_text().split()[0]:
        raise RuntimeError('Revision seal differs')
    if revision.read_text() not in (ROOT / 'paper/DESIGN.md').read_text():
        raise RuntimeError('Revision not saved in DESIGN')
    roster = read(OLD / 'subjects.json')
    OUT.mkdir(exist_ok=False)
    site_rows = {}
    for row in roster:
        source = ROOT / row['source_path']
        if sha(source) != row['source_sha256']:
            raise RuntimeError('Frozen source differs')
        site_rows[row['suite_id']] = dict(source_sha256=row['source_sha256'],
            budget_seconds=row['budget_seconds'], **sites(row, source.read_text()))
    # Explicitly sealed before the first full-cohort variant is generated.
    save(OUT / 'patch_sites.json', dict(registered_utc=utc(), revision_sha256=sha(revision), subjects=site_rows))
    versions, examples = {}, []
    example_ids = ['human-rtc_alarm_callback', 'sol-range_absent-rtc_alarm_pending-r03', 'sol-range_absent-rtc_time_counting-r01']
    review = '# Approved V1 split: six updated diffs\n\nCreated before any repair compilation or run.\n\n'
    for row in roster:
        sid, original = row['suite_id'], (ROOT / row['source_path']).read_text()
        site = site_rows[sid]
        for variant in ('V0', 'V1', 'V1b', 'V2', 'V3'):
            header = None
            if variant == 'V0' or (variant == 'V1' and float(row['budget_seconds']) >= 20.824):
                text = original
            else:
                text, header = normalized(row, original, site, 'V1b' if variant == 'V1' else variant)
                if variant == 'V1' and sid == 'sol-range_absent-rtc_alarm_pending-r03':
                    text = text.replace('deadline = MIN(k_uptime_get() + 3000, repair_deadline);',
                                        'deadline = k_uptime_get() + 3000;')
                    text = text.replace('/* Preserve the service allowance, capped by the shared observation ceiling. */',
                                        '/* Naive extension preserves the original separate service allowance. */')
                if variant == 'V1':
                    # Expose the approved max rule at the two short example sites.
                    old_ms = int(float(row['budget_seconds']) * 1000)
                    if header is None:
                        text = text.replace('k_uptime_get() + 20824', f'k_uptime_get() + MAX(INT64_C({old_ms}), INT64_C(20824))')
            folder = OUT / 'sources' / sid / variant
            folder.mkdir(parents=True)
            path = folder / 'test.c'
            path.write_text(text)
            files = [path]
            if header:
                h = folder / 'repair_wait.h'
                h.write_text(header)
                files.append(h)
            diff = ''.join(difflib.unified_diff(original.splitlines(True), text.splitlines(True),
                fromfile='V0/' + row['source_path'], tofile=variant + '/' + row['source_path']))
            (folder / 'changes.diff').write_text(diff)
            # Changes to timeout-only assertions are listed explicitly, not hidden.
            original_asserts, new_asserts = assertions(original), assertions(text)
            altered = [s for s in original_asserts if new_asserts.count(s) < original_asserts.count(s)]
            allowed_timeout = {'human-rtc_time_counting': 'i < RTC_TEST_TIME_COUNTING_POLL_LIMIT',
                               'astra-range_present-rtc_time_counting-r02': 'k_uptime_get() - start <= OBSERVATION_MS'}
            if altered and sid not in allowed_timeout:
                raise RuntimeError('Non-timeout assertion changed: ' + sid)
            if altered and any(allowed_timeout[sid] not in s for s in altered):
                raise RuntimeError('Unexpected assertion alteration')
            vid = sid + '--' + variant
            versions[vid] = dict(**row, variant=variant, original_suite_id=sid,
                variant_source_path=str(path.relative_to(ROOT)), variant_source_sha256=sha(path),
                support_inputs={str(f.relative_to(ROOT)): sha(f) for f in files[1:]},
                unchanged_from_v0=text == original, original_budget_ms=int(float(row['budget_seconds']) * 1000),
                scalar_ceiling_ms=max(int(float(row['budget_seconds']) * 1000),20824) if variant == 'V1' else
                                  (int(float(row['budget_seconds']) * 1000) if variant == 'V0' else 20824),
                separate_service_ms=3000 if sid == 'sol-range_absent-rtc_alarm_pending-r03' and variant in ('V0','V1') else 0,
                original_assertions=len(original_asserts), added_assertions=len(new_asserts)-len(original_asserts),
                modified_timeout_assertions=altered, diff_sha256=sha(folder / 'changes.diff'))
            if sid in example_ids and variant in ('V1', 'V1b'):
                examples.append(dict(suite_id=sid, variant=variant, source_path=str(path.relative_to(ROOT)),
                    diff_path=str((folder / 'changes.diff').relative_to(ROOT)), unchanged=text == original))
                review += f'## {variant}: {sid}\n\n'
                if diff:
                    review += '```diff\n' + diff + '```\n\n'
                else:
                    review += '**No source changes:** the original 60-second wait is retained.\n\n'
                if header:
                    review += 'The added `repair_wait.h` anchors the deadline at calendar reset and clamps each sleep.\n\n'
    assert len(versions) == 165 and len(examples) == 6
    save(OUT / 'variants.json', dict(created_utc=utc(), patch_sites_sha256=sha(OUT / 'patch_sites.json'),
                                   revision_sha256=sha(revision), versions=versions))
    save(REVIEW / 'examples.json', examples)
    (REVIEW / 'example_diffs.md').write_text(review)
    print('Generated 165 source versions; six split examples saved; no builds or runs')


if __name__ == '__main__':
    main()
