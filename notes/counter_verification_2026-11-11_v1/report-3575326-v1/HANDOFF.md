# Counter diagnostic handoff, 2026-11-11

Job **3575326** completed **0:0**, elapsed **00:56:50**, development / CCR26073.
Its 506-entry archive, every member and extracted byte passed the offline audit.
Archive SHA256: `e7b18ff6518d97e319d657e4b30a82ea345dd7fb429a4013007d31c22d567787`.
All 30,067 protected originals, 764 active input seals and four reused ELFs
passed before/after guards. No original outcome was replaced. No paper edit.

## Verified outcomes

| Stage | Processes | Explicit case pass / fail / skip / missing |
| --- | ---: | --- |
| Nominal qualification, two reference ELFs | 10 | 20 / 0 / 0 / 0 |
| Same-input full-application replays | 17 | 48 / 17 / 122 / 0 |
| Functional legal references, three cases at 17 settings | 17 | 51 / 0 / 0 / 0 |
| Extra 10/64-kHz progress controls | 2 | 2 / 0 / 0 / 0 |

All 46 processes have complete outcomes. All 17 replay case vectors, UART hashes
and normalized trace hashes match their primaries. Reproduced failures remain
failures, and capability skips remain skips. Functional references cover all
**87** residual primary failing case slots: 42 short-relative and 45 single-shot,
shared across V1/V1b/V2. These are clean-state functional controls, not identical
application phase/order or 87 independent experiments.

## Blocking control result: do not finalize slow-fault attribution

The progress cases themselves all passed their 20-second safety ceiling, but
activation qualification also requires the separate preregistered timing band.
Uptime measurements below are diagnostic-firmware observations, not callback
entry timestamps or directly measured primary application phase.

| Clock | Five-tick elapsed uptime | Registered tolerated band | Band result |
| --- | ---: | ---: | --- |
| 32 kHz, each of five nominal launches | 5,012 ms | 3,998–5,022 ms | Pass |
| 10 kHz, one control | **16,040 ms** | **12,798–16,022 ms** | **Fail: 18 ms above ceiling** |
| 64 kHz, one control | 2,516 ms | 1,998–2,522 ms | Pass |

The measured ordering is consistent with slow/nominal/fast clock progress,
but that does not override the registered control failure. Keep its bound and
outcome unchanged. No tolerance expansion, source tuning, replacement record
or automatic rerun. The overall activation qualification is **unresolved**.
This is not an archive-integrity failure or a missing verdict.

Raw logs: `../verified-3575326-v1/output/references/uart/`:
`f4-progress-control-slow_progress_control-027.log`,
`f4-progress-control-fast_progress_control-028.log`, and nominal-005 through -009.
The source is `subjects/counter_verification_20261111_v1/progress.c`; the band
arithmetic is frozen in PROTOCOL.md and independently applied by verify_job.py.
The initial sampled RTC divider is 32,000. The terminal sample follows the
control's counter_stop and reads PRER=0; it is not a changed active divider.
The inherited read-only `nvic SystickFrequency` query is unsupported in this
model and its exact errors are retained. SysTick 16 MHz is established by the
sealed platform file, not by a successful property readback.

## Primary repair results retained, with limits

Each V1/V1b/V2 all-channels subject passes all 102 paired legal settings,
including the 44 archived V0 failures. This remains one upstream subject.
Each repaired full application still has 14 short-relative and 15 later
single-shot failures; only 29 of the original 44 later failures disappear.
The new passing references corroborate a bounded functional alternative,
without directly measuring the original application's phase.

The selected primary 10-kHz outcomes are V0 fail, V1 pass, V1b fail, V2 fail;
all four 64-kHz selected probes pass. Replays corroborate these raw outcomes.
Do not promote them to finalized slow-fault detections/acceptance while the
independent slow-clock control fails its registered observer bound. The
64-kHz control satisfies its registered band, but no pooled fault score is
justified. No alarm-offset or callback-nonarrival operator was added here.
The previous six-cell repeatability pilot still supports only no observed
same-setting flakiness there; rare flakiness is not ruled out.

## Next main-workflow step and reproduction

The completed job watcher has been removed; no further automatic checks or
remote work are scheduled by it. Report this control discrepancy. An offline audit of the
counter-progress observer and model/timebase can diagnose the discrepancy.
Any revised observer, tolerance or fresh control experiment needs a separately
registered justification and authorization before execution; it cannot erase
this outcome. Keep primary records, frozen sources, and manuscript unchanged.
No new job or paper revision was performed by this watcher.

Run from the repository root, using new output directories each time:

    python3 -B notes/counter_verification_2026-11-11_v1/verify_job.py \
      --returned notes/counter_verification_2026-11-11_v1/returned-3575326-20261111T205259Z \
      --job 3575326 \
      --sacct-json notes/counter_verification_2026-11-11_v1/sacct-3575326-20261111T205259Z.json \
      --out <fresh-verified-directory>
    python3 -B notes/counter_verification_2026-11-11_v1/summarize_job.py \
      --verified <fresh-verified-directory> --out <fresh-report-directory>

Machine-readable evidence: `summary.json`, `../verified-3575326-v1/verification.json`,
`processes.csv`, `case_verdicts.csv` and `reference_coverage.json` in that verified
directory. The raw archive remains unchanged and is not staged in Git.
