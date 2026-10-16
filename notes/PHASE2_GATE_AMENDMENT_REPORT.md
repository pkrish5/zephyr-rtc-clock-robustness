# Phase 2 oracle-gate reanalysis — 2026-09-29

The [dated amendment](../paper/DESIGN.md) separates **functional adequacy**, which filters a suite for a meaningful RQ2 comparison, from **timing-bound adequacy**, which is a measured outcome. The original source-oracle gate excluded a nominally passing RTC suite because its 15-second deadline was too short for the documented slow LSI. That excluded the timing defect this study seeks to observe. The [split protocol](../analysis/PHASE2_SPLIT_GATE_PROTOCOL.md) preserves all original decisions, source files, builds, and nominal results. This recoding is **retrospective and unblinded**: the reviewer knew the Phase 1 upstream RTC result and early Phase 3 RTC outcomes. It is not an independent validation of oracle quality.

| Cohort and gate | Generated | Built | Nominal pass | Source status after nominal pass | Eligible for pass-to-fail schedules |
| --- | ---: | ---: | ---: | --- | ---: |
| Primary Luna, **original strict** | 55 | 50 | 38 | 34 adequate, 2 uncertain, 2 inadequate | **34/55** |
| Primary Luna, **amended functional** | 55 | 50 | 38 | 35 met, 2 unknown, 1 not met | **35/55** |
| RTC bound-context supplement, **original strict** | 5 | 2 | 1 | 1 inadequate | **0/5** |
| RTC bound-context supplement, **amended functional** | 5 | 2 | 1 | 1 met | **1/5** |

The primary Luna generation also had five build failures, nine nominal assertion failures, and three nominal timeouts. Under the amended review these 17 sources are `not_evaluable` for executable functional behavior; none disappears from the 55-attempt denominator. Across all 55 sources, the timing source review records six `inadequate`, 32 `no_issue_found`, and 17 `unknown`. Among the **35 amended eligible** primary suites, the timing counts are **1 inadequate, 28 no issue found, 6 unknown**. “No issue found” is a source-review result, not proof of robustness under timing variation.

The extra primary eligible source is [`rtc_alarm_callback-r04`](../generated/phase2_luna/suites/rtc_alarm_callback/r04/test.c): it checks two configured callbacks, their IDs, and pre-alarm absence, but its 15-second calendar-arrival cap conflicts with the approximately 18.824 seconds possible at 17 kHz LSI under the configured prescaler. The 34 eligible HSI suites are unchanged by this gate amendment; they require a fresh **100 MIPS nominal** screen before the new HSI arm. The separate supplement's [`rtc_alarm_callback-r05`](../generated/phase2_rtc_bound/suites/rtc_alarm_callback/r05/test.c) checks both callback IDs and calendar state, but asserts the second callback with `K_NO_WAIT` immediately after the first. That is a timing-bound issue, not a functional failure. It remains a separate context condition and is **not pooled** with the 55 primary model samples.

The original strict gate yields no oracle-adequate RTC agent comparator. The amended gate makes the primary Luna `r04` RTC result a primary *timing-brittleness* measurement for that selected task. This change of eligibility was made after some RTC schedules had run, so report both gates and do not present its observed flip rate as a preregistered oracle-adequate success. A passing timing schedule also does not validate an unjustified assertion. The earlier single Sol feasibility sample is excluded from both denominators and all future cross-model comparisons.

The separate [amended decision ledger](../analysis/phase2_split_gate_decisions.json) stores frozen source hashes, old oracle status, build/nominal outcomes, functional and timing judgments, evidence, and review provenance. The [analysis script](../analysis/phase2_split_gate.py) audits it and regenerates [machine-readable counts](../results/phase2_split_gate_summary.json):

```sh
python3 analysis/phase2_split_gate.py
```
