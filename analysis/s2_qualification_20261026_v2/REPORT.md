# S2 qualification checkpoint, 2026-10-26

**STOP before production. Qualification is incomplete.** No normal-queue job,
new generated test, manuscript edit, E query or E2 action was performed.

## Evidence and integrity

Development job 3533596 timed out at 01:30:04 on c306-005, after nominal runs
and part of calibration. Audit-only job 3535059 completed 0:0 in 54 seconds.
The returned archive is `results/s2_qualification_20261025_v1/evidence_v1.tar.gz`,
SHA-256 `be4c26e901f65bddfb0319bca2d0f94c380d76c9b74f84bf81749ce5feaa85f2`.
Its 1,583 file hashes were independently verified locally. All 17 builds passed;
all copied ELFs/build products and finalized run-log hashes match their records.
All 30,067 historically protected files remain unchanged. S2 execution code and
scientific inputs retain the v4 plan seal
`cbde1752ce2435a980cbce88a94829ae1bfc322368b1ef15c9bc54803753efbb`.

The collector ran the original sealed reporter on a separate snapshot. It did
not create reports in, or modify, the original qualification output directory.
The local summary's first CSV preparation failed on optional seed columns;
that partial output was preserved as v1, and corrected v2 is this report.
This local reporting error involved no firmware or experimental data changes.

## Per-application checkpoint

P/S/M are nominal working, explicit capability-skipped, and unconfirmed case
counts, respectively. Working requires all five complete nominal launches.
Calibration counts include complete applications even when an assertion failed.
Those failures are experimental observations, not infrastructure failures.
The full per-case ledger is `per_case_qualification.csv`.

| Board | Application | Nominal P/S/M | Complete calibration / 7 | Qualification |
|---|---|---:|---:|---|
| F4 Discovery | RTC API | 5/2/0 | 7 | Ready for review |
| F4 Discovery | RTC-only counter basic | 4/7/0 | 4 | Three interrupted calibration launches |
| F4 Discovery | Counter seconds | 1/0/0 | 7 | Ready for review |
| Nucleo-F767ZI | RTC API | 5/2/0 | 7 | Ready for review |
| Nucleo-F767ZI | RTC-only counter basic | 4/7/0 | 4 | Three interrupted calibration launches |
| Nucleo-F767ZI | Counter seconds | 1/0/0 | 5 | Two unstarted calibration launches |
| F746G Discovery | RTC API | 5/2/0 | 6 | One unstarted calibration launch |
| F746G Discovery | RTC-only counter basic | 0/0/11 | 0 | MPU fault; incomplete application in all five nominal runs |
| F746G Discovery | Counter seconds | 1/0/0 | 7 | Ready for review |
| Nucleo-H753ZI | RTC API | 5/2/0 | 5 | Two unstarted calibration launches |
| Nucleo-H753ZI | RTC-only counter basic | 3/8/0 | 6 | One unstarted calibration launch |
| Nucleo-H753ZI | Counter seconds | 1/0/0 | 4 | Three unstarted calibration launches |
| F072B Discovery | RTC API | 0/0/7 | 0 | No UART completion; conditional board not qualified |
| F072B Discovery | RTC-only counter basic | 0/0/11 | 0 | No UART completion; conditional board not qualified |
| F072B Discovery | Counter seconds | 0/0/1 | 0 | No UART completion; conditional board not qualified |

RTC update callback and Y2K are explicit skips on the four otherwise working
boards. Counter capability skips are retained, including the clock-dependent
short-relative capability gate. The counter configuration is non-stock,
RTC-only, with subsecond support disabled. Every compiled case remains present.
Board replicas are not independent subjects.

### Missingness and exclusions

Of 182 planned launches, 139 have finalized records: 117 complete applications,
15 harness wall-ceiling outcomes, and seven incomplete applications (five F072
seconds, two watchdog). Twenty-eight calibration launches were omitted because
nominal applications lacked complete verdicts: F746 counter basic (seven) and
all three F072 applications (21). Fifteen other calibration launches lack final
records: six started but were interrupted by the Slurm limit, and nine never
started. These categories total 182 and are not converted into passes or fails.
`unfinished_calibration.csv` identifies all fifteen settings exactly.

Both watchdog probes reached 120 simulated seconds, printed one reset request,
and showed neither reboot nor explicit case completion. No infrastructure
error was reported. Exclude F4/H753 watchdog from production under the approved
bounded qualification rule; do not repeat to obtain a pass.

F746 counter UART shows individual case outcomes followed by an MPU data-access
fault in the second ztest suite at `test_set_top_value_without_alarm`.
All five nominal applications remain incomplete, so none qualifies as five
complete nominal passes. The first UART also reports no free partition slots.
This is a configuration/firmware/emulator issue requiring investigation, not
an oscillator-induced assertion failure. Changing MPU/userspace settings or
test configuration requires a separately approved and frozen change.

F072's generated DTS resolves nominal LSI to 40,000 Hz. Source defaults predict
RTC API divider 32,000 and RTC-counter divider 39,936, but runtime reads stayed
at the uninitialized/model divider 32,768 with no UART output. The required
runtime divider confirmation therefore failed. Static policy resolution is
insufficient to admit this conditional board. No compensating divider was added.

## What calibration already shows

These are seven-setting qualification observations, not final 100-setting
failure rates or completed reference-based attribution:

- RTC API: the alarm, callback and counting cases fail at 17 kHz on F4/F767/F746;
  alarm and callback also fail at 21,402 Hz. All received H753 RTC settings pass
  its five runnable cases; two settings remain unstarted.
- Counter seconds: explicit lower-bound assertion failures occur at slow legal
  F4/F767/F746 settings. This adds a different, rate-checking upstream oracle.
- Counter basic on F4/F767: `test_all_channels` fails its callback-count assertion
  at the four completed slow calibration settings. The later single-shot case
  then fails alarm setup with -EBUSY. The failed all-channels assertion precedes
  alarm cancellation, and the driver rejects a new alarm while its callback is
  still registered. Treat the second failure as a possible shared-state cascade,
  not independent evidence of another brittle waiting window. Replay/reference
  checks and any isolation diagnostic need their own approved protocol.

No general field failure probability, complete schedule flip fraction, physical
silicon validation or independent board replication is inferred from calibration.

## Resource evidence and production planning

The first resource probe measured 300.625 wall seconds and 327.082 MiB RSS.
The largest finalized application record's measured RSS is 365.828 MiB. A cap
of 32 workers remains well below 80% of the measured available node memory,
including a 1.5 safety multiplier. Long counter basic nominal launches on F4
and F767 take about 1,190–1,232 seconds; their 100 repeated three-second busy
waits explain why the original RTC-only runtime allowance was insufficient.
The job's sequential stages and static interleaving left some calibration tasks
unstarted when the 90-minute allocation expired.

`production_cost_scenarios.json` gives reproducible **conditional** primary-run
estimates, not a production submission or final whole-study cost:

| Scope | Full-application launches | Case-verdict slots, including skips | Primary SU estimate |
|---|---:|---:|---:|
| Four currently ready configurations | 408 | 1,632 | 0.66 |
| Eleven nominal-ready configurations, if remaining calibration succeeds | 1,122 | 6,630 | 4.48 |

Each configuration uses 100 saved frequencies plus both endpoints. The estimate
is sum(102 × maximum measured wall seconds)/(32 × 3600) × 1.5, at one SU per
node-hour. It excludes builds, replays, reference checks, whole-node reservation
rounding and extra diagnostic work. Full production counts/costs cannot be
finalized while seven configurations lack calibration. Do not silently reduce
the approved scope to the four already ready configurations.

## Required decisions before further experiments

1. Complete the exact fifteen interrupted/unstarted calibration settings in a
   fresh output namespace. Preserve all original missing slots and distinguish
   new attempts; use the same sources, ELFs, frequencies, per-run limits and
   sealed worker. Splitting calibration into its own development allocation
   addresses the Slurm allocation limit without changing test semantics.
2. Exclude or separately qualify F746 counter basic after a documented MPU/
   configuration investigation. Do not change its configuration as an
   infrastructure-only correction without approval.
3. Exclude conditional F072 and both watchdogs on current evidence, or propose
   a separately frozen qualification investigation. No firmware/source fixes
   were made here.
4. After qualification is complete, freeze production packing, replay/reference
   counts and SUs, then obtain approval before any normal-queue submission.

No further job has been submitted after evidence collection. The paper remains
unchanged. S1's 106 LSI / 40 LSE RTC-enabled target counts and verified AN5067,
AN5126 and RM0090 documentation remain available for later manuscript revision.
