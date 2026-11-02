# S2 results for Progress Report 2

Verified November 2, 2026. This report adds analysis of existing evidence only.
No new experiments, builds, reference runs, E/E2 work, or manuscript edits were
performed in this handoff continuation. Primary records are unchanged.

## 1. What is complete

The expanded upstream cohort includes **all declared cases in 11 qualified
board/application configurations**, with 100 registered sampled settings plus
both documented endpoints for each configuration: **1,122 launches**. The primary
archive passed independent log, trace, input, and ELF checks on the Mac.
There were **3,022 passing, 470 failing, 3,138 skipped, and zero missing case
slots**. These are case outcomes, not 6,630 independently sampled tests.

Replay job **3546149 completed, exit 0:0, in 00:12:26**, on node c304-015.
All **274/274 full-application replays** matched the primaries, covering all
**470/470 assertion failures**. Every compared case vector, selected trace
field, UART hash, and trace hash matched. No replay was missing, outside the
frozen roster, or associated with an incorrect job/partition. Replays are
repeatability evidence, not a second sample or proof of causal attribution.

The replay archive has SHA-256
`9247f19e878b94370e8d9ed85717dfacc787184654ab90f68d661ff1bb56dfb2`.
Its **2,214 entries** match the manifest, extracted file hashes, and types.
Its receipt says `output_state: complete`. Protected-before and protected-after
receipts each verify **30,067 unchanged files** against the original ledger.
New output was packed on SCRATCH and published as an archive on WORK.
The final Mac audit also confirms 30,067 unchanged protected files, and the
user's main.tex and main.pdf hashes are unchanged; the compact receipt is
`protected_and_manuscript_check.json`. Monitor log bytes also match in all
274 replay comparisons.

**Reference-based attribution is not complete.** No S2 reference jobs have
run. The categories below are post-result, source-supported explanations with
matching replay evidence; they must not be described as reference-validated
counts of brittle tests. Reference protocols and any normal-queue submissions
still require registration and approval.

Evidence:

- Primary audit: `../returned-3544535/audit/report.json` and
  `return_verification.json`; archive SHA-256
  `0de8c18ebabe0dd8e91b4df43072dbd1aa5843e1455f455831afbf00d951d85e`.
- Replay audit: `../returned-replays-3546149-20261102/local_archive_verification.json`.
- Exact comparison: `../replay_comparison_20261102_v1/replay_summary.json` and
  `replay_comparison.csv`; comparator
  `harness/tacc_s2_evidence/compare_replays.py`.
- Reproducible source analysis: `../finalize_s2.py`; all read input hashes are
  retained in `analysis_inputs_sha256.json` in this directory.

## 2. Cohort, runnable cases, and observed flips

Every configuration has 102 production launches. RTC = complete RTC API
application; counter = complete counter basic API application under the approved
**non-stock RTC-only configuration**, without optional subsecond mode; seconds =
complete counter-seconds application under that RTC-only configuration.
Capability skips remain skips.

| Board | Application | Declared cases | Nominal runnable / skipped | Runnable at any setting / always skipped | Cases with any failure |
|---|---|---:|---:|---:|---:|
| STM32F4 Discovery | RTC | 7 | 5 / 2 | 5 / 2 | 3 |
| STM32F4 Discovery | Counter basic | 11 | 4 / 7 | 4 / 7 | 2 |
| STM32F4 Discovery | Counter seconds | 1 | 1 / 0 | 1 / 0 | 1 |
| Nucleo-F767ZI (F4 configuration replica) | RTC | 7 | 5 / 2 | 5 / 2 | 3 |
| Nucleo-F767ZI (F4 configuration replica) | Counter basic | 11 | 4 / 7 | 4 / 7 | 2 |
| Nucleo-F767ZI (F4 configuration replica) | Counter seconds | 1 | 1 / 0 | 1 / 0 | 1 |
| STM32F746G Discovery | RTC | 7 | 5 / 2 | 5 / 2 | 3 |
| STM32F746G Discovery | Counter seconds | 1 | 1 / 0 | 1 / 0 | 1 |
| Nucleo-H753ZI | RTC | 7 | 5 / 2 | 5 / 2 | 0 |
| Nucleo-H753ZI | Counter basic | 11 | 3 / 8 | 4 / 7 | 0 |
| Nucleo-H753ZI | Counter seconds | 1 | 1 / 0 | 1 / 0 | 0 |

| Board | Declared cases | Nominal runnable / skipped | Runnable at any legal setting | Observed flip cases / runnable at any setting | Always skipped | Missing slots |
|---|---:|---:|---:|---:|---:|---:|
| STM32F4 Discovery | 19 | 10 / 9 | 10 | 6/10 | 9 | 0 |
| Nucleo-F767ZI (F4 configuration replica) | 19 | 10 / 9 | 10 | 6/10 | 9 | 0 |
| STM32F746G Discovery | 8 | 6 / 2 | 6 | 4/6 | 2 | 0 |
| Nucleo-H753ZI | 19 | 9 / 10 | 10 | 0/10 | 9 | 0 |

These raw flip numerators include the cascade and unresolved rate case, so
they must not be relabeled as independent waiting-defect counts. On H753 the
nominal-runnable numerator/denominator is also 0/9; the any-setting denominator
is 10 because one capability-gated case runs at some sampled settings.
All per-case and per-application pass/fail/skip counts are in `per_case.csv`
and `per_application.csv`.

F746 counter remains excluded for its qualification MPU fault. F072 remains
excluded for no test output; no divider claim is inferred. Watchdog remains
excluded for no demonstrated reboot/completion. No excluded application is
counted as a skip or a passing case.

## 3. Four attribution categories, reported per board

Each cell is **distinct failing case names (failing case slots)**. Board
replicas share sources, driver, and simulator and are not independent subjects.

| Board | (a) Single-boundary wait | (b) Phase-dependent | (c) Cleanup cascade | (d) Unresolved rate contract |
|---|---:|---:|---:|---:|
| STM32F4 Discovery | 1 (27) | 3 (80) | 1 (44) | 1 (35) |
| Nucleo-F767ZI (F4 configuration replica) | 1 (27) | 3 (80) | 1 (44) | 1 (35) |
| STM32F746G Discovery | 1 (27) | 2 (36) | 0 (0) | 1 (35) |
| Nucleo-H753ZI | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

Across the stored case slots these categories account for 81 + 196 + 88 + 105
= 470 failures. Summing slots is bookkeeping, not statistical independence.
Categories (a) and (b) identify four candidate timing-sensitive case types
where counter basic is present, and three on F746; category (c) adds no
independent waiting defect. Category (d) remains unresolved.

The counter all-channels case is included in (b) with an explicit
**free-running relative-alarm phase** subtype. It does not use the
calendar-write explanation of the two RTC cases. This makes the scope of (b)
explicit rather than attributing every phase effect to calendar writes.

Source and per-failure evidence: `per_test_explanations.csv`,
`source_explanations.md`, `failure_attribution.csv`, and
`per_board_categories.csv`.

## 4. Source boundaries and observed frequency bands

The following observations apply separately and identically to F4 and F767;
the RTC and seconds observations also apply to F746. F746 has no admitted
counter-basic configuration. Counts below include the lower endpoint in addition
to the 100 sampled settings. The higher endpoint passes for these cases.
Bands describe the tested settings only; no outcomes were measured in the gaps.

| Case | Source-derived boundary or envelope | Observed failing band, kHz | Observed passing band, kHz | Failures per applicable board | Category |
|---|---|---|---|---:|---|
| `rtc_api.test_alarm` | Ideal zero-phase 320/13 = 24.615 kHz | 17.000–24.428 | 24.734–47.000 | 27/102 | a |
| `rtc_api.test_alarm_callback` | Phase envelope 22.154–24.615 kHz | 17.000–23.673 | 23.847–47.000 | 23/102 | b |
| `rtc_api.test_time_counting` | Last-poll phase envelope 19.862–22.069 kHz | 17.000–20.500 | 20.701–47.000 | 13/102 | b |
| `counter_basic.test_all_channels` | Relative-tick phase envelope 21.333–32.000 kHz | 17.000–29.143 | 29.352–47.000 | 44/102 | b |
| `counter_basic.test_single_shot_alarm_notop` | No independent wait boundary: setup returns -EBUSY | 17.000–29.143 | 29.352–47.000 | 44/102 | c |
| `seconds_counter.test_seconds_rate` | Ideal zero-phase rate comparison 32/1.2 = 26.667 kHz; contract unresolved | 17.000–26.168 | 27.086–47.000 | 35/102 | d |

Each measured case vector has one fail-to-pass transition when sorted by
frequency; this observation does not establish a unique physical threshold or
exclude nonmonotone behavior at unmeasured settings. The phase envelopes are
post-result source explanations, not newly validated prospective forecasts.

### Why each fails

- **Alarm pending, (a):** `test_alarm.c:177–204` sets a target ten calendar
  seconds ahead, sleeps three plus ten host seconds, then asserts pending at
  line 203. The ideal thirteen-second threshold brackets the sampled transition.
  This is the first application case and matches the isolated-case vector.
- **Callback, (b):** `test_alarm_callback.c:119–141` uses the same waits and
  asserts callback presence at line 140. Earlier cases leave a fractional
  RTC-second phase. In the Renode model, writing calendar fields preserves that
  subsecond count, changing the remaining arrival time.
- **Calendar counting, (b):** `test_time_incrementing.c:35–59` polls every
  500 ms. The last observation is around 14.5 seconds, although the failure is
  asserted after the following sleep. The same preserved calendar phase changes
  the remaining ten-calendar-second delay.
- **All channels, (b):** `test_counter.c:658–702` waits three host seconds for
  a two-tick relative alarm and fails callback-count equality at line 695.
  `counter_ll_stm32_rtc.c:529–537` adds one tick to accommodate the partially
  started tick. The target can need between two and three physical ticks. This
  explains why nominal reported frequency is insufficient to justify the wait.
- **Single shot, (c):** `test_counter.c:475` fails setup with `err: -16` before
  waiting, at exactly the all-channels failing settings. The earlier assertion
  at line 695 bypasses cancellation at line 701 and teardown in
  `test_all_instances`. The driver rejects setup while a callback remains
  registered (`counter_ll_stm32_rtc.c:520–523`). This is a source-supported
  cascade explanation, not another independently established wait defect.
- **Seconds rate, (d):** `counter_seconds/src/main.c:10–12,20–42` explicitly
  checks roughly 1 Hz, sleeps 1.2 seconds, and requires one to two ticks. It
  fails the minimum assertion at line 41. Whether that rate is the intended
  contract under legal LSI variation is unresolved; changing it to eventual
  progress would weaken the original property.

## 5. Reconciliation with earlier isolated RTC cases

The reconciliation verifies every historical record, UART, and trace hash and
matches the same **102 frequencies per case on F4**, including endpoints.
Old raw records and old forecasts remain unchanged.

| Same case name | Earlier isolated failures / 100 seeds | Full-application failures / 100 seeds | Isolated last fail / first pass, Hz | Full last fail / first pass, Hz | Isolated fail → full pass |
|---|---:|---:|---|---|---:|
| `rtc_api.test_alarm` | 26 | 26 | 24,428 / 24,734 | 24,428 / 24,734 | 0 |
| `rtc_api.test_alarm_callback` | 26 | 22 | 24,428 / 24,734 | 23,673 / 23,847 | 4 |
| `rtc_api.test_time_counting` | 17 | 12 | 21,782 / 22,405 | 20,500 / 20,701 | 5 |

Callback differences occur at 23,847; 23,876; 24,346; and 24,428 Hz. Counting
differences occur at 20,701; 21,402; 21,742; 21,762; and 21,782 Hz. There are no
differences in the reverse direction. With endpoints included, isolated/full
failure counts are 27/27, 27/23, and 18/13, respectively.

The source-supported explanation is execution context: these later cases run
after other cases in the full application, and RTC calendar writes in this
Renode model preserve the fractional ticker count. A ten-calendar-second
transition can therefore require less host time than in an isolated fresh
process. Earlier assertion aborts can also alter later state and ordering.
The trace records do not directly measure the fractional phase, so this
mechanism is supported but not experimentally isolated. The comparisons also
use different full-application versus selected-case binaries and platform
packages; the earlier cross-platform calibration supports compatibility but
does not remove every possible execution-context difference.

All sealed platform include chains were checked against the **packaged input
hashes** in the S2 plan. F4, F767, F746, and H753 each instantiate
`Timers.STM32F4_RTC`; see `platform_model_verification.csv`. The packaged files
contain the registered relocated include paths, so their hashes are distinct
from the original package-path hashes also retained in the plan.
The exact release model and timer sources are identified in
`../FULL_APPLICATION_PHASE.md` and `../model_source/provenance.json`:
`STM32F4_RTC.cs:242–250,641–695` and `LimitTimer.cs:272–285` support phase
preservation during calendar writes. This does not establish silicon behavior.

There is **no earlier isolated baseline for counter basic or counter seconds**;
their reconciliation is "no baseline", not agreement. New isolation experiments
require a separately registered protocol and approval.

Machine-readable results: `isolated_reconciliation.csv` and
`isolated_differing_settings.csv`.

## 6. H753: narrower clock envelope and dynamic skips

The H753 schedule uses **29,760–33,600 Hz**, frozen from **DS12117 Rev10,
silicon revision V, VDD 1.62–3.6 V, TJ −40 to 105 C**. F4, F767, and F746 use
their verified 17–47 kHz envelopes. H753's lower endpoint is above the largest
observed failure frequency elsewhere (29,143 Hz). Its zero failures therefore
do not demonstrate a stronger test oracle or an independent replication with
the same oscillator envelope.

`counter_basic.test_short_relative_alarm` is skipped at nominal. In production
it passes at **10 sampled settings** and is skipped at **90 sampled settings
and both endpoints**. The source's `short_relative_capable` predicate
(`test_counter.c:979–1036`) actively programs an alarm and checks one callback
after a ten-reported-tick busy wait. Failure of that operational predicate
causes a skip through `test_all_instances`; it is not a static board capability
flag. Saved UART confirms "Testing" for all 10 passes and "Skipped" for all
92 skips. The exact internal false-return branch and callback/phase history
are not logged, so the underlying reason for those changes remains unresolved.
This prevents treating a skip as a pass or silently fixing the denominator at
the nominal case count. Every setting is listed in
`h753_short_relative_capability.csv`.

## 7. Remaining limits and next decision

- No S2 reference validation has run; final brittle-test attribution remains
  open. Replays alone do not prove the correctness of firmware or simulator.
- Category assignments, phase explanations, and observed transition brackets
  are post-result analyses. Phase is not directly observed.
- Identical vectors across shared F4/F767/F746 settings reflect common
  source/driver/model structure. Do not pool board copies as independent tests.
- The uniform settings are controlled interventions, not measured device
  distributions. Physical-board and distribution sensitivity work remain separate.
- E, E2, new generation, and paper edits remain held. No additional job was
  submitted or resubmitted during this continuation. The watcher is paused
  because its target job is complete.

The next scientific step is to freeze the source-preserving reference protocol
and resolve the seconds-rate contract, then present concrete job, node count,
wall time, and SU estimates for approval. This report is ready now for Progress
Report 2 without waiting for E.
