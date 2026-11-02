# S2 task-specific reference validation, 2026-11-02

Registered before reference builds or execution. This is a new reference
experiment; original upstream/generated sources, forecasts, primary records,
and replay records are read only. E, E2, and manuscript edits remain held.

## Cohort and coverage

Use the eleven qualified S2 board/application configurations and the exact
primary overlays, simulator platform files, fixed-divider driver, Linux Renode
1.17.0/.NET 8.0.21 image, CPU/SysTick settings, 500-ms RunFor sampling, and
simulation body. Label **F767 as an F4 configuration replica in every table**.
Boards are separate configurations, not independent developer subjects.

Build three new reference applications, from
`subjects/s2_references_20261102_v1/`, for the admitted board/family pairs:

| Board role | RTC reference | RTC-only counter reference | Seconds reference |
|---|---|---|---|
| F4 | yes | yes | yes |
| F4 configuration replica (F767) | yes | yes | yes |
| F746 | yes | excluded as before | yes |
| H753, narrower legal envelope | yes | yes | yes |

Five nominal launches and both legal endpoints per configuration give **77
qualification launches**. Five nominal repetitions must produce every expected
reference case with passing outcomes, no skips, and no harness errors. At the
endpoints the deliberately retained seconds-rate contract may pass or fail;
report its observed status without treating that failure as infrastructure.
Every other qualification reference must pass. An unexpected failure stops
later evaluation, preserves its evidence, and is reported before any change.

After qualification, one reference launch per verified failing primary
application setting gives **274 evaluation launches**, with an explicit link
to every one of the **470 failing primary case slots**. These are not 470
independent tests. Shared reference launches cover multiple failing cases;
H753 has no evaluation launches because its primaries have no assertion
failures. The reference plan retains each original frequency and primary run ID.

## Task-specific checks

| Original case | Reference case(s) | Preserved failing property and added checks |
|---|---|---|
| `rtc_api.test_alarm` | `ref_rtc.test_a_alarm_pending` | Both alarm channels, second/minute/hour mask and compare readback, two reset-and-delivery repetitions, pending not before target, bounded arrival |
| `rtc_api.test_alarm_callback` | `ref_rtc.test_b_alarm_callback` | Both IDs and per-channel protected counts, two calendar resets, calendar captured in callback, independent-time early check, bounded arrival |
| `rtc_api.test_time_counting` | `ref_rtc.test_c_time_counting` | Original 2025/2026 date and exact ten-second target, monotone calendar reads, independent-time premature check, bounded polling |
| `counter_basic.test_all_channels` | `ref_counter.test_all_channels` | One supported RTC channel and unsupported-channel errors, same two-tick relative request, callback ID/data/ISR context, callback counter read, no premature callback, bounded arrival and cancellation |
| `counter_basic.test_single_shot_alarm_notop` | `ref_counter.test_single_shot_alarm_notop` | Explicitly clean callback state, same two-tick request, ID/data/counter checks, bounded arrival, original three-second extra no-repeat observation and cancellation |
| `seconds_counter.test_seconds_rate` | `ref_seconds.test_a_rate_contract` plus `ref_seconds.test_b_legal_clock_progress` | Retain the original 1200-ms, one-to-two-tick assertion first; separately check monotone ten-tick progress, premature progress and a legal-clock ceiling |

References are task-specific functional controls. They are not claimed to
preserve coverage of every invalid-argument or unrelated API assertion in the
full upstream applications. The original sources and original scores are
unchanged. The RTC references execute pending, callback, then counting; the
counter reference runs all-channels before a clean-state single-shot. The
seconds rate check runs before the progress check, avoiding a deliberately
introduced prior-progress phase shift. Reference phase is not asserted equal
to original full-application phase.

## Ceilings and premature-event checks

The shared conservative reference envelope is the full cohort envelope,
17–47 kHz with fixed divider 32,000. H753's actual approved range is narrower;
using the broader envelope does not make its primary sample wider.

- Ten calendar/counter ticks: experimental ceiling
  `ceil(11 * 32000 / 17000 + 5) = 26` host seconds. The additional tick covers
  phase/observation uncertainty; five seconds is an explicit experimental
  delivery margin, not a datasheet ISR-latency guarantee.
- Ten-tick earliest transition: `9 * 32000 / 47000`, minus 2 ms uptime
  quantization, gives **6125 ms**. Callback checks use the calendar read
  inside the callback as well as the independent SysTick-derived uptime.
- Two-tick relative counter alarm: the driver's compensating extra tick gives
  a two-to-three physical-tick arrival. One further uncertainty tick plus the
  five-second margin gives `ceil(4 * 32000 / 17000 + 5) = 13` seconds.
  The independent earliest check is **1360 ms**, just below
  `2 * 32000 / 47000`. Callback-time counter progress must also be at least
  the requested two ticks.
- Polling interval is **20 ms**. The deadline is checked before accepting
  completion. These checks are simulator controls and do not establish
  physical-board timing or a certified scheduling bound.

The 1.2-second rate assertion is retained separately because extending its
wait would change the property. If it fails while legal-clock progress passes,
flag firmware/simulator or accuracy-contract investigation; do not call that
a brittle waiting test. A passing rate reference also does not resolve the
original phase-dependent rate contract by itself.

## Interpretation and reconciliation

Every primary failing case gets reference status, reference record/log hashes,
the matching task and case names, and its attribution category. Reference
failure is flagged **firmware/simulator investigation, not test brittleness**.
An infrastructure error or missing reference remains missing and blocks a
reference-supported brittleness claim. A reference failure alone does not
establish which implementation or contract is wrong.

For categories (a) and (b), passing references may strengthen the source and
replay-supported waiting explanation. Keep the single-boundary and two phase
subtypes separate. For (c), clean-state reference success supports functional
delivery but does not count the original cleanup cascade as an independent
waiting defect. For (d), preserve the unresolved accuracy contract and report
the two reference properties separately.

Keep full-application and earlier isolated F4 results side by side for the
three original RTC cases. Seeded failures are pending 26/26, callback 22/26,
and counting 12/17 (full/isolated); endpoint-inclusive counts and exact changed
frequencies remain in the verified reconciliation table. The preserved-phase
explanation is **supported but not directly measured**. Never overwrite the
earlier forecasts or isolated-case counts with the expanded cohort's results.

## Execution, storage, protection, and cost

Planned job: **development, TRA25006, one node, two-hour limit, at most 2 SUs**,
four parallel builds (two compiler workers each), then 32 local Launcher
workers. Qualification and evaluation have separate jobfiles, with the
qualification audit blocking evaluation on anomalies. No arrays and no
automatic requeue. The existing 32-worker memory qualification applies to the
same Renode executable; collect peak RSS and wall time for every new build/run.

This is a small bounded reference follow-up using the development queue as
the user allowed. No normal submission is authorized by this packet. If the
job cannot fit, report concrete normal-queue nodes, wall time, and SUs before
submission and obtain any approval required by the standing rules. Do not
resubmit ambiguous or failed work automatically.

Use `tacc-apptainer/1.4.1` and `launcher/3.10`. Container SHA-256 is
`94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.
Run new builds, bundle copies, and loose records on SCRATCH; use private
node-local homes/caches/tmp. Kept reference ELFs, build logs, configurations,
metadata and hashes go into the job archive; regenerable intermediates remain
on SCRATCH. Pack and verify before publishing to WORK, including interruptions,
with a fresh headroom check immediately before publication. Preserve all
originals and verify all 30,067 protected hashes before and after the job.

The frozen original S2 build/run body is imported unchanged; new outer adapters
stage the new reference sources and truthful provenance. The source/plan/code
seals and DESIGN snapshot are frozen before execution. No LS6 edits or pushes;
code reaches LS6 by git pull after commit/push on the Mac. Always use
`ssh -o BatchMode=yes`; stop on authentication failures, MFA requests or drops.

E audit/resumption starts only after the reference step is complete, with its
own dated quota-interruption amendment and exact rerun index list. E2 and
manuscript edits remain on hold.
