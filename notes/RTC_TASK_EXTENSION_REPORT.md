# RTC task extension and Luna gate report — 2026-09-29/30

Two upstream Zephyr RTC selected cases were screened **in order**, after their own protocols were registered. `rtc_api.test_time_counting` passed a separately numbered 5/5 nominal series at 32 kHz. Its first five launch attempts had failed at virtual time zero because Renode could not write its host command-history path in the initial sandbox; those records remain harness errors. `rtc_api.test_alarm` then passed its own 5/5 selected-case screen. Both selected ELFs, unchanged upstream source, build configuration, simulator/platform hashes, and traces are archived in [counting](../results/rtc_counting/qualification.json) and [alarm-pending](../results/rtc_alarm_pending/qualification.json). Each registered the pre-existing 100-frequency 17–47 kHz LSI list for later timing runs. Both observe RTC state rather than ISR callback delivery, so they are a correlated adjacent LSI stratum.

The separate [IWDG reset-state probe](IWDG_FIDELITY_RESULT.md) failed at nominal and both endpoints after a recorded configuration amendment. No reboot or `.noinit` retention was demonstrated; IWDG is excluded.

Using the unchanged Phase 2 template, schema, five-run count, task definitions, and gate rubrics, Luna generated ten frozen RTC extension sources. Two initial stdin-delivered CLI attempts for the first source stalled without model output; a [dated transport amendment](../generated/luna_rtc_extension/CLI_TRANSPORT_AMENDMENT.md) switched all successful new calls to direct-argument delivery of the same rendered prompt. No test source was repaired. The ten completed calls reported 139,126 input tokens (65,280 cached) and 8,080 output tokens; billed dollars and exact server snapshot are unavailable. All 65 old-and-new Luna prompt hashes match their definitions in the complete task manifest.

| Gate | RTC counting, 5 outputs | RTC alarm pending, 5 outputs | Combined, 10 outputs |
| --- | ---: | ---: | ---: |
| Generated | 5 | 5 | 10 |
| Built | 5 | 0 | 5 |
| One-run nominal pass | 4 | 0 | 4 |
| Original strict eligible | 0 | 0 | 0 |
| Amended functional eligible | 3 | 0 | 3 |

The five alarm-pending builds all fail at the pinned `rtc_alarm_get_time` signature, with additional signature errors in some outputs. Counting r04 fails nominal `rtc_set_time` because it supplies `tm_wday=-1`; the pinned STM32 driver explicitly rejects that value. Counting r05 passes nominal but never compares successive RTC observations, so its monotonicity oracle is inadequate. Counting r01–r03 pass nominal and are functionally adequate. Their source-level timing-bound judgments are retained in the first-reviewer ledger and withheld from this review packet until the independent RQ1 labels are submitted. Original strict source review has no adequate new suite; the amended functional filter admits the three. The complete 65-output primary Luna cohort is **34/65 original strict** versus **38/65 amended functional**. The separate five-output RTC bound-context supplement remains outside both denominators.

The [13-task manifest](../subjects/phase2_tasks_v2.json) and [v2 input lock](../generated/cross_model_v2/lock.json) are frozen. No seeded timing variation has yet run on the two new RTC cases, and no new Sol or Astra generation has started. The 100-MIPS HSI arm is registered for a later phase. The [blinded RQ1 packet](../analysis/blind_rq1/PACKET.md) contains 30 source items across all 13 tasks and awaits independent labels.

Audit the archived inputs and derived gates without new model or simulator runs:

```sh
python3 analysis/rtc_extension_qualification.py counting
python3 analysis/rtc_extension_qualification.py alarm_pending
PHASE2_COHORT=luna_rtc_extension python3 analysis/phase2_summary.py
python3 analysis/luna_rtc_extension_gates.py
python3 analysis/freeze_cross_model_v2.py
```
