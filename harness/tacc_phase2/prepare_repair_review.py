#!/usr/bin/env python3
"""Create six review-only diffs after verifying the saved E amendment seal.

Does not compile, execute, generate full repair cohorts, or invoke an LLM.
"""
import difflib
import re
from pathlib import Path
from support import read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'notes/repair_review_2026-10-24'


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Patch site is not unique: ' + old)
    return text.replace(old, new)


def assertions(text):
    """Extract balanced assertion invocations, including strings, for retention."""
    found = []
    for m in re.finditer(r'\bzassert_\w+\s*\(', text):
        start = m.start()
        depth, quoted, escape = 1, None, False
        i = m.end()
        while depth:
            c = text[i]
            if quoted:
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == quoted:
                    quoted = None
            elif c in ('"', "'"):
                quoted = c
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            i += 1
        found.append(text[start:i])
    return found


def upstream_variants(source):
    v1 = replace_once(source, '#include <zephyr/sys/atomic.h>',
        '#include <zephyr/sys/atomic.h>\n#include <zephyr/kernel.h>\n#include <zephyr/sys/util.h>\n#include <stdint.h>')
    v1 = replace_once(v1, '\tbool callback_called_status;',
        '\tbool callback_called_status;\n\tint64_t repair_deadline;')
    line = 'ret = rtc_set_time(rtc, &test_rtc_time_set);'
    assert v1.count(line) == 2
    v1 = v1.replace(line, 'repair_deadline = k_uptime_get() + 20824;\n\t' + line)
    # The reset is nested one level further than the first set.
    v1 = v1.replace('\t\trepair_deadline = k_uptime_get() + 20824;\n\tret =',
                    '\t\trepair_deadline = k_uptime_get() + 20824;\n\t\tret =')
    fixed = 'k_sleep(K_MSEC(MAX(INT64_C(0), repair_deadline - k_uptime_get())));'
    v1 = replace_once(v1, 'k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));', fixed)
    helper = '''static bool repair_all_called(void)
{
	for (uint16_t id = 0; id < alarms_count; ++id) {
		bool called = (id % 2) ? atomic_test_bit(&callback_called_mask_odd, id)
				       : atomic_test_bit(&callback_called_mask_even, id);
		if (!called) {
			return false;
		}
	}
	return true;
}

'''
    v2 = replace_once(v1, 'ZTEST(rtc_api, test_alarm_callback)', helper + 'ZTEST(rtc_api, test_alarm_callback)')
    v2 = replace_once(v2, fixed, '''while (!repair_all_called() && k_uptime_get() < repair_deadline) {
			int64_t repair_remaining = repair_deadline - k_uptime_get();
			if (repair_remaining <= 0) {
				break;
			}
			k_sleep(K_MSEC(MIN(INT64_C(20), repair_remaining)));
		}''')
    capture = '''static struct rtc_time repair_callback_time[DT_PROP(DT_ALIAS(rtc), alarms_count)];
static int repair_callback_read_rc[DT_PROP(DT_ALIAS(rtc), alarms_count)];
static atomic_t repair_bad_id;

static bool repair_capture(const struct device *dev, uint16_t id, uint16_t parity)
{
	if (dev != rtc || id >= alarms_count || (id % 2) != parity) {
		atomic_set(&repair_bad_id, 1);
		return false;
	}
	repair_callback_read_rc[id] = rtc_get_time(dev, &repair_callback_time[id]);
	return true;
}

static int repair_calendar_cmp(const struct rtc_time *a, const struct rtc_time *b)
{
	const int av[] = {a->tm_year, a->tm_mon, a->tm_mday, a->tm_hour, a->tm_min, a->tm_sec};
	const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday, b->tm_hour, b->tm_min, b->tm_sec};
	for (size_t i = 0; i < ARRAY_SIZE(av); ++i) {
		if (av[i] != bv[i]) {
			return (av[i] < bv[i]) ? -1 : 1;
		}
	}
	return 0;
}

'''
    v3 = replace_once(v2, 'static void test_rtc_alarm_callback_handler_odd', capture + 'static void test_rtc_alarm_callback_handler_odd')
    for parity, name in [(1, 'odd'), (0, 'even')]:
        old = '\tatomic_set_bit(&callback_called_mask_' + name + ', id);'
        v3 = replace_once(v3, old, f'\tif (!repair_capture(dev, id, {parity})) {{\n\t\treturn;\n\t}}\n' + old)
    v3 = replace_once(v3, '\tint64_t repair_deadline;',
        '\tint64_t repair_deadline;\n\tstruct rtc_time repair_alarm_readback;\n\tuint16_t repair_alarm_mask;')
    old = '\t\tzassert_ok(ret, "Failed to set alarm %d time", i);'
    v3 = replace_once(v3, old, old + '''
		zassert_ok(rtc_alarm_get_time(rtc, i, &repair_alarm_mask, &repair_alarm_readback));
		zassert_equal(repair_alarm_mask, test_alarm_time_mask_set);
		zassert_equal(repair_alarm_readback.tm_hour, test_alarm_time_set.tm_hour);
		zassert_equal(repair_alarm_readback.tm_min, test_alarm_time_set.tm_min);
		zassert_equal(repair_alarm_readback.tm_sec, test_alarm_time_set.tm_sec);''')
    old = '\t\t/* Clear callback called atomics */'
    v3 = replace_once(v3, old, '''		atomic_set(&repair_bad_id, 0);
		for (uint16_t id = 0; id < alarms_count; ++id) {
			repair_callback_read_rc[id] = -EAGAIN;
		}
''' + old)
    old = '\t\t/* Validate alarm callback called */'
    v3 = replace_once(v3, old, '\t\tzassert_equal(atomic_get(&repair_bad_id), 0, "Unexpected callback device/ID");\n' + old)
    old = '''			zassert_equal(callback_called_status, true,
				      "Alarm %d callback should have been called", j);'''
    v3 = replace_once(v3, old, old + '''
			zassert_ok(repair_callback_read_rc[j], "Failed to capture callback RTC calendar");
			zassert_true(repair_calendar_cmp(&repair_callback_time[j], &test_alarm_time_set) >= 0,
				     "Callback before target calendar");
			zassert_equal(repair_calendar_cmp(&repair_callback_time[j], &test_alarm_time_set), 0,
				      "Callback outside target RTC second");''')
    return dict(V1=v1, V2=v2, V3=v3)


def generated_variants(source):
    v1 = replace_once(source, '    zassert_ok(rtc_set_time(rtc, &start));',
        '    const int64_t repair_deadline = k_uptime_get() + 20824;\n    zassert_ok(rtc_set_time(rtc, &start));')
    v1 = replace_once(v1, '/* The alarm is ten RTC seconds away; allow 15 wall-clock seconds. */',
        '/* Share one 20,824-ms observation ceiling from the calendar reset. */')
    v1 = replace_once(v1, 'deadline = k_uptime_get() + 15000;', 'deadline = repair_deadline;')
    v1 = replace_once(v1, '/* Allow three more seconds for the alarm status to become visible. */',
        '/* Preserve the service allowance, capped by the shared observation ceiling. */')
    v1 = replace_once(v1, 'deadline = k_uptime_get() + 3000;',
        'deadline = MIN(k_uptime_get() + 3000, repair_deadline);')
    # V1 retains cadence; clamp sleeps only to the remaining time.
    assert v1.count('k_sleep(K_MSEC(50));') == 2
    v1 = v1.replace('k_sleep(K_MSEC(50));',
        'k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));')
    v1 = replace_once(v1, '#include <zephyr/kernel.h>',
        '#include <zephyr/kernel.h>\n#include <zephyr/sys/util.h>')
    v2 = v1.replace('MIN(INT64_C(50), deadline', 'MIN(INT64_C(20), deadline')
    v3 = replace_once(v2, '    struct rtc_time now;',
        '    struct rtc_time now;\n    struct rtc_time repair_pending_before;\n    struct rtc_time repair_pending_after;')
    old = '''    while (!saw_after && k_uptime_get() < deadline) {
        pending = rtc_alarm_is_pending(rtc, 0);
        zassert_true(pending >= 0);
        saw_after = pending > 0;'''
    new = '''    while (!saw_after && k_uptime_get() < deadline) {
        zassert_ok(rtc_get_time(rtc, &repair_pending_before));
        pending = rtc_alarm_is_pending(rtc, 0);
        zassert_true(pending >= 0);
        zassert_ok(rtc_get_time(rtc, &repair_pending_after));
        if (pending > 0) {
            zassert_false(before_time(&repair_pending_after, &alarm),
                          "pending observed before configured calendar target");
        }
        saw_after = pending > 0;'''
    v3 = replace_once(v3, old, new)
    return dict(V1=v1, V2=v2, V3=v3)


def main():
    seal = (OUT / 'amendment.sha256').read_text().split()[0]
    if sha(OUT / 'amendment.md') != seal or (OUT / 'amendment.md').read_text() not in (ROOT / 'paper/DESIGN.md').read_text():
        raise RuntimeError('The pre-variant amendment is not saved and sealed')
    roster = {r['suite_id']: r for r in read(OUT / 'subjects.json')}
    examples = [('human-rtc_alarm_callback', 'upstream_callback', upstream_variants),
                ('sol-range_absent-rtc_alarm_pending-r03', 'generated_sol_pending', generated_variants)]
    manifest = dict(created_utc=utc(), amendment_sha256=seal, roster_sha256=sha(OUT / 'subjects.json'),
                    status='REVIEW_ONLY_NOT_BUILT_OR_RUN', examples=[])
    review = '# E repair examples for approval\n\nNo variants were built or run. Each diff is against the frozen V0 source.\n\n'
    for sid, label, transform in examples:
        r = roster[sid]
        source = ROOT / r['source_path']
        if sha(source) != r['source_sha256']:
            raise RuntimeError('Original example source differs')
        original = source.read_text()
        variants = transform(original)
        for name, text in variants.items():
            originals, added = assertions(original), assertions(text)
            if any(added.count(s) < originals.count(s) for s in originals):
                raise RuntimeError('An original assertion was deleted/changed')
            leaf = OUT / 'examples' / label / name
            leaf.mkdir(parents=True, exist_ok=False)
            (leaf / 'test.c').write_text(text)
            diff = ''.join(difflib.unified_diff(original.splitlines(True), text.splitlines(True),
                fromfile='V0/' + r['source_path'], tofile=name + '/' + r['source_path']))
            (leaf / 'changes.diff').write_text(diff)
            review += f'## {name}: {label}\n\n```diff\n{diff}```\n\n'
            manifest['examples'].append(dict(suite_id=sid, variant=name,
                original_source_path=r['source_path'], original_sha256=r['source_sha256'],
                preview_path=str((leaf / 'test.c').relative_to(ROOT)), preview_sha256=sha(leaf / 'test.c'),
                diff_path=str((leaf / 'changes.diff').relative_to(ROOT)), diff_sha256=sha(leaf / 'changes.diff'),
                original_assertion_invocations=len(originals), all_original_assertions_retained=True,
                preview_assertion_invocations=len(added)))
    save(OUT / 'manifest.json', manifest)
    (OUT / 'example_diffs.md').write_text(review)
    print('Saved six review-only sources/diffs; all original assertions retained; no builds or runs')


if __name__ == '__main__':
    main()
