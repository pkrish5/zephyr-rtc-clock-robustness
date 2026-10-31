# S2 attribution preparation, 2026-10-31

Draft only. No replay, reference build or reference execution has started.
Finalize exact sources, task lists, hashes and the dated registration after
primary archive verification, before reference builds/runs. Normal submission
still requires its concrete job/node/wall/SU approval.

## Unchanged full-application replays

Use the sealed primary ELF, platform input, frequency, unit, case roster,
monitor/RunFor function and quantum/step. One fresh-process full-application
replay covers every original failed case in that launch. Save independent
output and truthful new provenance. Compare per-case vectors, completion,
error, persisted observations/registers and raw trace hashes. A mismatch or
missing replay never overwrites the original. Keep skips separate.

Use SCRATCH output bound at the locked logical path, read-only original
bundle/builds, private node-local home/cache/tmp, and verified packed WORK
outputs. No source or ELF rebuild for replays. Primary records are never
counted twice or replaced by diagnostics.

## References and interpretation

- RTC alarm/pending/callback/counting: begin from the existing frozen reference
  implementations; qualify on each retained board with the exact RTC alias,
  configuration and pinned driver. Check matching premature/event/readback
  semantics with a justified conservative ceiling. Freeze any board adaptation
  as a new reference artifact. These are functional correctness controls,
  not a physical-silicon fidelity claim.
- RTC-backed counter all-channels: preserve channel capability handling,
  requested relative ticks, callback IDs/counts and cancellation. Use a
  clock-aware event ceiling that includes the driver's added relative tick
  and declared phase uncertainty; check callback-time count, not mere
  eventual occurrence. Do not silently treat the API's nominal reported
  frequency as the measured oscillator rate.
- Counter single-shot after an earlier failure: check alarm configuration and
  delivery from clean reference state. A passing reference does not by itself
  establish that the original later case has an independent waiting defect.
  Track the original -EBUSY/state-cascade explanation separately.
- Counter seconds-rate: retain the source's advertised rate contract in the
  interpretation. A longer-wait/eventual-progress reference can validate
  counter progress but cannot validate the original 1.2-second rate assertion.
  Do not use such a relaxed reference to label the original rate check brittle.
  Keep rate-contract versus oscillator/configuration attribution unresolved
  unless source/API/trace evidence establishes the contract under legal LSI.

Qualify references at nominal and both legal endpoints first. Use reference
checks at distinct failing settings per board/case or documented shared
reference, with every assertion failure linked to its replay/reference
artifacts. Failed or missing references block brittle-test attribution.

## Boundaries and result units

Derive scalar thresholds only where source and traces support a scalar model.
For phase-dependent counter checks, report the source-derived threshold band
and the measured failing/passing transitions, including nonmonotonicity if
present. Do not fit an exact scalar threshold after observing results and
present it as prospective. Distinguish no independent deadline in a cascade.

Report board/application/case outcomes; do not pool board replicas as
independent subjects. Separate nominal runnable, nominal capability-skipped,
runnable at any legal setting, dynamic skip transitions, and missing slots.
Keep observed primary failure distinct from replay-confirmed and reference-
attributed brittle behavior. The raw 100-setting schedule is a controlled
sensitivity intervention, not an observed distribution of devices.

## Replay infrastructure prepared while storage cleanup runs

`harness/tacc_s2_evidence/prepare_replay_plan.py` refuses a provisional
record-only audit and creates its roster only after the returned archive and
independent raw-log/ELF audit agree. It covers every primary assertion failure
with one replay of each affected full-application launch. The proposal is not
submission authorization.

`harness/tacc_s2_evidence/replay_worker.py` is a new outer adapter that checks
the proposal, original plan/input hashes, original record and trace, build
record and ELF, then calls the byte-identical S2 `run()` function. It uses
real new provenance. Mount `/primary` read only, identical original inputs at
`/bundle`, SCRATCH output at the original logical output path, original builds
read only, and `/renode` plus the sealed worker read only. Private cache/home
paths must be node-local. No replay has run and no normal submission is
authorized by these files. A checked job/subject archive must be published to
WORK before the new wrapper exits, including on interruption.

Provisional metadata suggested 274 affected application launches, covering
470 case failures, with 12,492.39 summed saved worker seconds. These are
planning inputs from the earlier record-only copy, not independently verified
S2 results. At 32 workers and a 1.5 allowance, the throughput component is
0.163 node-hours; registration, input audits, metadata contention, reference
qualification and packing require separate allowances. Freeze the actual
roster and reservation only after full evidence verification.
