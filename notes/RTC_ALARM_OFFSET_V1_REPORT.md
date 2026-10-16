# Nominal-clock RTC alarm-offset quality probe — 2026-10-08 UTC

## Registration and scope

The user approved this separate quality arm on 2026-10-07. The [dated preregistration](RTC_FIRMWARE_ALARM_OFFSET_PROPOSAL.md) and immutable [manifest](../results/rtc_alarm_offset_v1/manifest.json) (SHA-256 `8cb29f03c2d2bf604846508fc2149ac96b88953b6ce6594ed0b1e98afaf4fdea`) preceded all builds and runs. Two isolated STM32 RTC driver variants programmed the requested alarm compare one RTC calendar second early or late at nominal 32-kHz LSI. The RTC calendar clock, CPU setting, test sources, source hashes, and task-specific selected-case rule remained fixed within each variant. These are deliberately faulty rebuilt ELFs, not datasheet-legal oscillator schedules. The registered score covers 39 eligible LLM-generated alarm suites and two upstream (human) alarm cases; 27 LLM-generated counting suites and one upstream (human) counting case are non-activation controls.

Both callback and pending reference tests passed on the nominal driver. Under either offset, their programmed-alarm readback assertion failed with a UART line showing requested `00:00:05`, programmed `00:00:04` or `00:00:06`, and full second/minute/hour mask `7`. The counting reference passed at nominal and under both variants without alarm activation. The [activation audit](../results/rtc_alarm_offset_v1/activation_audit.json) records all nine checks. Five first reference attempts failed at virtual time zero because the sandbox denied Renode access to its history file. Those originals remain untouched; the successful activation runs are separately saved under `replays/` with the same built ELFs. No suite scoring started until that access-retry activation audit passed.

## Scores

A kill requires a signed activation log and an explicit failing selected ztest case. Pass means survival. Monitor or startup errors remain missing. Counting controls never enter alarm kill denominators. The [machine-readable audit](../results/rtc_alarm_offset_v1/analysis_summary.json) verifies all 138/138 original suite records, source/ELF/trace hashes, and the activated selected-case rule.

| Cohort | Early compare (−1 RTC s) | Late compare (+1 RTC s) |
|---|---:|---:|
| Astra, range absent | 10/10 killed | 10/10 killed |
| Astra, range present | 9/9 | 9/9 |
| Sol, range absent | 9/9, 1 missing | 7/9, 1 missing |
| Sol, range present | 10/10 | 8/10 |
| **All LLM-generated alarm suites** | **38/38, 1 missing** | **34/38, 1 missing** |
| Upstream (human) callback | 0/1 | 0/1 |
| Upstream (human) pending | missing, 0/1 evaluable | 1/1 |

Luna has no functionally eligible alarm suite in this factorial. The 20 LLM-generated pending cases killed each sign. In callback, LLM-generated suites killed the early compare in 18/18 evaluable runs (one missing) and the late compare in 14/18 (one missing). Four callback suites survived the late compare: Sol range-absent r01/r02 and Sol range-present r01/r05. Their source assertions accept a callback after the requested calendar time. The upstream (human) callback test also survived both signs; its 13-second observation window accepts both 9- and 11-second nominal transitions. The upstream (human) pending test killed the late offset by alarm readback. Its original early run has no verdict; a separately labeled diagnostic run failed the same readback assertion, but this is **not** substituted for the missing original.

All 56/56 counting-control originals passed without any active alarm log (54 LLM-generated and two upstream (human) runs). Across the 82 planned alarm-fault runs, there were 73 kills, six survivors, and three missing originals. Every one of the 73 kills reproduced in a fresh process with identical selected-case verdict, error field, and signed programming logs. Diagnostic reruns for the three missing originals yielded failure for upstream (human) pending early and Sol absent callback r04 early, and a pass for Sol absent callback r03 late; the primary scores remain missing. The 138 originals ran from 2026-10-07 23:36 to 2026-10-08 00:57 UTC; summed simulator wall time was 0.94 hours across three workers, excluding builds and replay.

These faults answer a different oracle question from the earlier out-of-spec 64-kHz/10-kHz oscillator probes. In the offset arm, a test can compare the alarm register or callback calendar with the requested RTC time while the oscillator stays nominal. The high offset kill rate therefore does not imply independent host-time validation or robustness to callback-delivery latency. The small and selected upstream baseline, three missing verdicts, one board/driver/model, and handpicked ±1-second operators limit generalization. The range-present and range-absent alarm cells have similar offset performance: early 19/19 evaluable in each condition and late 17/19 in each; the range-absent condition has one missing original per sign.

## Reproduction and immutable data

On a fresh configured checkout with the pinned Zephyr SDK and Renode version, run `python3 harness/rtc_alarm_offset_v1.py --register`, `python3 harness/rtc_alarm_offset_v1.py --references`, `python3 harness/rtc_alarm_offset_v1.py --audit-activation`, `python3 harness/rtc_alarm_offset_v1.py --workers`, `python3 analysis/rtc_alarm_offset_v1_replay.py`, and `python3 analysis/rtc_alarm_offset_v1_summary.py` in order. The first command creates records exclusively; do not rerun it in the existing results directory. Renode needs normal access to its user history file. In this checkout the initial sandbox-denied reference records and later access-retry activation namespace are both retained. Read-only analysis can be reproduced now with `python3 analysis/rtc_alarm_offset_v1_summary.py`; original records live in `results/rtc_alarm_offset_v1/records/` with corresponding UART, monitor, and trace files. The driver copy, builder, runner, manifest, activation audit, reference sources, and derived summary are separately hash-auditable.

## 2026-10-08 assertion-level audit and separately labeled diagnostic

I coded the **first failing assertion** in each of the 73 original scored kills using its persisted UART line and frozen source, recording one row per kill in [the assertion ledger](../analysis/rtc_alarm_offset_v1_assertion_audit.csv) and category totals in [the audit summary](../analysis/rtc_alarm_offset_v1_assertion_audit.json). This is a single-reviewer source audit, not independently rated. The breakdown is:

| First failing assertion | Early kills | Late kills | What it proves |
|---|---:|---:|---|
| `rtc_alarm_get_time` programmed-second readback differs from request | 20 | 21 | The alarm compare is misprogrammed; this is a calendar-relative **configuration** check, not evidence of actual callback timing. This includes all 40 scored LLM-generated pending kills and the upstream (human) pending late kill. |
| Callback observed before the RTC target, or captured callback calendar before target | 18 | 0 | The one-second-early callback violates a guard tied to RTC calendar progress. None is a standalone timeout or unguarded count failure. |
| Callback or observation calendar differs from the requested second | 0 | 13 | The one-second-late callback violates an exact RTC calendar assertion. Astra range-present callback r04 reports error bit 8, which the frozen source assigns specifically to callback calendar later than target. |
| Combined ID, RTC-read, or callback-calendar error flag | 0 | 1 | Sol range-present callback r03 late fails a combined flag. The saved trace cannot identify which branch set it, so its calendar cause remains **ambiguous** despite the activated offset and identical replay. |

Thus 72/73 scored kills have a source-backed alarm readback or calendar-relative first assertion. The remaining kill is explicit and replayed, but its immediate assertion is composite. **41/73 are register-readback checks**, so the measured score must not be described as 73 direct firing-time checks. No first failure is a bare timeout or an unguarded callback-count assertion.

The four LLM-generated late-offset survivors are all Sol callback suites; none has a scalar clock-only padding classification in [the earlier padding ledger](../analysis/rtc_padding_audit.csv), because callback delivery makes such a bound non-scalar. Source reasons are:

| Suite | Source-backed reason for surviving +1 RTC second |
|---|---|
| `sol-range_absent-rtc_alarm_callback-r01` | Accepts `now.tm_sec >= 5 && now.tm_sec <= 6` after callbacks; it explicitly allows the next RTC second. Its 30-second deadline is a permissive observation ceiling, not the decisive missing assertion. |
| `sol-range_absent-rtc_alarm_callback-r02` | Also accepts RTC seconds 5 or 6 after callback delivery, with a 20-second calendar deadline and 1-second callback grace. The accepted range includes the faulty +1 second. |
| `sol-range_present-rtc_alarm_callback-r01` | Rejects callbacks before target but finally checks counts and ID only. It has no upper calendar-second assertion; a callback at second 6 passes within its 30-second deadline. |
| `sol-range_present-rtc_alarm_callback-r05` | Rejects callbacks before target and checks counts, but has no exact or upper calendar-second assertion. Its 60-second deadline adds substantial slack, yet the immediate reason for survival is the missing late-calendar check. |

The user requested one fresh diagnostic rerun of upstream (human) pending under the early offset. The new [diagnostic record](../results/rtc_alarm_offset_v1/diagnostics_20261008/records/human-rtc_alarm_pending__early__diagnostic_20261008.json) is saved in its own namespace, using the same mutant ELF hash as the missing original. It failed at the alarm-second readback: requested `00:00:05`, programmed `00:00:04`. The **original remains a harness error and remains unscored**. This diagnostic is additional to the earlier separately saved access-retry run and replaces no raw verdict.
