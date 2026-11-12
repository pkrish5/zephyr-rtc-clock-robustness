# Course manuscript v3: claim and evidence audit

Date: 2026-11-11. Manuscript: `paper/draft/main.tex` and `main.pdf`.
The 2026-11-03 evidence release and 2026-11-04 manuscript v2 remain historical
snapshots. This revision uses completed counter-repair, diagnostic and
fixed-setting repeatability runs. It starts no new Renode or TACC work.

## What the evidence establishes

The original six sensitive subjects comprise three purposively chosen upstream
cases and three generated pending suites. Each of four repairs passes the same
102 legal clock settings per subject with no missing verdict and retains the
measured 10-kHz slow-fault assertion. These are six subjects, not 612 independent
tests. Separately, right-sizing overlong waits adds 11 slow-fault detections in
other generated counting subjects; polling adds none on common-evaluable pairs.
The original cohort has 29 finalized missing legal/fault outcomes, never scored
as passes. The expanded upstream survey has 10 distinct ever-runnable case names
from 19 declared names, with four waiting-sensitive names. It is a purposive,
shared-model case study, not a developer-test prevalence estimate.

The fourth upstream case is `counter_basic.test_all_channels` in the full F4
counter application. The table below reports 102 *paired settings* per variant,
with pass/fail/skip counts for three distinct case names. Only the all-channels
wait was edited; V1, V1b and V2 are three variants of the same subject.

| Variant | All channels | Short relative | Single shot |
| --- | ---: | ---: | ---: |
| V0 | 58/44/0 | 58/0/44 | 58/44/0 |
| V1 | 102/0/0 | 88/14/0 | 87/15/0 |
| V1b | 102/0/0 | 88/14/0 | 87/15/0 |
| V2 | 102/0/0 | 88/14/0 | 87/15/0 |

All 44 original all-channels failures change to passes under each repair.
The original failure skipped short-relative at 44 settings; repair exposes 14
failures there. Single-shot has 29 fail-to-pass and 15 fail-to-fail paired
transitions. These later failures are residual full-application observations,
not additional repaired tests. All 17 representative full-application replay
vectors, UART hashes and normalized traces match their primaries. Three
clean-state functional references pass at 17 legal settings each, covering all
87 residual failing case slots across variants (42 short-relative and 45
single-shot). Those references do not recreate the full application's phase or
order, so they cannot by themselves assign every residual failure to cleanup.

The selected 10-kHz raw verdicts are V0 fail, V1 pass, V1b fail and V2 fail;
all four 64-kHz raw verdicts pass. The independent progress control measures
16,040 ms for five 10-kHz ticks, 18 ms beyond its preregistered 16,022-ms
upper bound. Five nominal 32-kHz controls measure 5,012 ms each and the 64-kHz
control measures 2,516 ms, within their respective bounds. Source inspection
shows uptime begins before the first counter read and the loop polls every
20 ms; saved traces only sample every 0.5 virtual seconds. That can plausibly
contribute observer delay but cannot quantify or explain the extra 18 ms.
The failed bound remains unchanged. **Slow-fault activation and preservation
for the fourth case are unresolved.** Raw verdicts are observations, not a
finalized fault-detection score. See
`notes/counter_verification_2026-11-11_v1/OBSERVER_AUDIT.md` and the diagnostic
`report-3575326-v1/HANDOFF.md`.

The repeatability pilot has six frozen test-frequency cells, 30 fresh processes
per cell. F4 callback: 23,673 Hz fails 30/30; 23,847 and 32,000 Hz pass 30/30.
F4 counter all-channels: 29,143 Hz fails 30/30; 29,352 and 32,000 Hz pass
30/30. All 180 explicit outcomes agree within cells. This supports observed
cross-setting sensitivity and no *observed* same-setting mixed verdict in these
cells; it neither estimates a population flakiness rate nor rules out rare
within-setting nondeterminism.

## Reproduction and manuscript checks

`make tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz`
verifies all 113,433 original archived inputs and rebuilds all eight original
table hashes without Renode. The archive SHA256 is
`805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921`.
`audit_paired_records.py` checks hashes and parsed outcomes for 17,375 original
repair primary records. `build_counter_table.py` independently pairs the 102
V0 and 306 repaired full-application records by condition, seed and frequency,
checks eight fault records, the 17 replay matches, the 51 functional reference
passes and the six-cell pilot. Its `counter_table_audit.json` stores every
record hash. `verify_manuscript_v3.py` checks 40 numerical and textual claims,
the eight original table hashes, three readable table hashes, the new counter
table hash and all 13 unique citation keys. The citation metadata and canonical
URLs were audited for v2 and are unchanged here; the v3 release link must be
checked after publication. The TeX compiles to five letter-size pages including
references, with zero overfull boxes or unresolved references/citations; every
page was rendered and visually inspected. The final PDF/source hashes and release
asset checksums are recorded separately after packaging.

To reproduce the full v3 audit from a clean checkout, obtain the unchanged v1
evidence archive and extract the v3 source bundle into the checkout, preserving
paths. Then run `make course-tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz`.
The source bundle includes the 102 original and 314 new counter records, diagnostic and pilot
summaries, scripts and table fragments. No TACC access or new experiment is
needed for these checks.

## Limits and next experiment

All four board labels are Renode configurations using the same existing STM32F4
RTC model; they are not physical-board replication. Counter cases use a non-stock
RTC-only configuration. The clock schedule samples a datasheet interval, not a
measured population frequency distribution. Source-derived phase explanations
are not direct phase measurements. The original three upstream cases were
selected for visible waits; no same-spec developer-written baseline supports
an LLM superiority claim. Fast-fault probes remain undetected. The original
two-second delivery allowance has not been validated as a general bound.

A stronger slow-fault preservation claim for the fourth case needs a *new,
preregistered* progress-control protocol that fixes the observer definition
and timing bound before execution. One focused control is enough to test that
qualification; the 102-setting legal repair schedule need not be rerun.
