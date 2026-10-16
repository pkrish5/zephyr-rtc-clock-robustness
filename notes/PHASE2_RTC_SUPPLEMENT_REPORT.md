# Phase 2 RTC bound-informed supplement

Date: 2026-09-29. **Stop point:** generation, build, nominal screening, and source-oracle review are complete. No agent timing perturbation or repair was run.

**Later amendment (2026-09-29):** The [split-gate reanalysis](PHASE2_GATE_AMENDMENT_REPORT.md) treats the nominally passing `r05` suite as functionally adequate and its immediate second-callback `K_NO_WAIT` as a timing-bound inadequacy. The original strict verdict below remains the historical Phase 2 result.

## Why this cohort exists

The primary 55-run Luna cohort left no RTC suite that both passed nominally and met the required legal-bound oracle. The user approved a separate, five-sample context supplement. Its [protocol](../generated/phase2_rtc_bound/PROTOCOL.md) was registered before generation. The only changed task field was `rtc_alarm_callback.api_hints` in the [supplement task manifest](../subjects/phase2_rtc_bound_tasks.json). It supplied the pinned public RTC API signatures, the documented STM32F407 LSI range of 17–47 kHz, the pinned driver's 128 × 250 prescaler, and the consequent 18.824 s maximum *calendar progression* time for ten RTC seconds at the slow endpoint. It explicitly distinguished that calculation from an ISR-to-thread latency guarantee. The feature specification, three required oracles, build configuration, board, prompt template, response schema, requested `gpt-6-luna` model, and k = 5 were unchanged. No prior generated suite, upstream test source, or Phase 1 verdict was supplied.

The [generation manifest](../generated/phase2_rtc_bound/generation_manifest.json) locks task, template, schema, model, CLI version, and per-run prompt hashes. Each fresh CLI call used the same rendered prompt and produced one frozen `test.c`. All five outputs are retained. The requested model slug was `gpt-6-luna` via `codex-cli 0.158.0-alpha.2.1`; the exact server snapshot, generation seed, and sampling temperature were not exposed.

## Gate outcomes

| Frozen suite | Build | Nominal Renode | Source-oracle review | Main reason |
| --- | --- | --- | --- | --- |
| [r01](../generated/phase2_rtc_bound/suites/rtc_alarm_callback/r01/test.c) | Fail | Not run | Inadequate | Adds two `k_timeout_t` values; the bound cannot compile. Its pre-alarm seconds check is also false for valid `55–59`. |
| [r02](../generated/phase2_rtc_bound/suites/rtc_alarm_callback/r02/test.c) | Fail | Not run | Inadequate | Leaves a `k_poll_signal_wait` placeholder and adds `k_timeout_t` to an integer deadline. |
| [r03](../generated/phase2_rtc_bound/suites/rtc_alarm_callback/r03/test.c) | Fail | Not run | Inadequate | Ends at an invalid `zassert_unreachable` assignment, before waiting for or asserting callback delivery. |
| [r04](../generated/phase2_rtc_bound/suites/rtc_alarm_callback/r04/test.c) | Pass | Fail | Inadequate overall | The 30 s event bound is source-adequate, but a pre-alarm check requires `now.tm_sec < 5` while the legitimate value is `55–59`; nominal assertion fails after 3.002 s. |
| [r05](../generated/phase2_rtc_bound/suites/rtc_alarm_callback/r05/test.c) | Pass | Pass | Inadequate | The first callback has a 24 s wait, but the second is required with `K_NO_WAIT` immediately afterward, without a documented zero-separation guarantee. |

Totals: **5/5 generated**, **2/5 built**, **1/5 nominally passed**, and **0/5 met both nominal and registered oracle gates**. The single nominal pass completed in 10.000 virtual seconds. The five individual source reviews and evidence are in [oracle decisions](../analysis/phase2_oracle_decisions_rtc_bound_supplement.json). Compiler output, nominal UART/monitor logs, exact configuration and hash-bearing traces are under [raw results](../results/phase2_rtc_bound/); [summary.json](../results/phase2_rtc_bound/summary.json) audits the attrition. The source review is by one reviewer and needs independent adjudication for a paper claim.

The added timing context did induce all five outputs to mention the approximately 18.824 s slow-clock arrival and choose a nominal 24 or 30 s main deadline. That is a descriptive observation for this **separate context condition**, not evidence of better timing robustness. Three attempts do not compile; one fails at nominal; the surviving pass encodes an unsupported immediate second-callback assumption. With zero eligible RTC agent suites, there is **no agent RTC flip-rate denominator** for this supplement. No confidence interval for an unmeasured flip rate is reported. The upstream selected RTC result remains 7/30 flips (95% Wilson 11.8–40.9%) in its separate Phase 1 stratum. The 34 primary HSI agent suites that passed nominal and oracle gates remain available for a later registered Phase 3 comparison; this supplement is not pooled with them or with the original 55.

The [static scan](../results/phase2_rtc_bound/static_candidates.json) records candidates in all five generated suites and the one matched upstream case. These are syntax tags, not adjudicated RQ1 prevalence. In particular, a tagged protected atomic read is not automatically an unsafe shared-state access, and the actual `K_NO_WAIT` issue requires line-level timing reasoning.

## Reproduce and audit

Use the pinned Zephyr v4.3.0 commit `3568e1b6d5cdd51a6b964a2a1d6d29200fea2056`, STM32F4 Discovery setup, and Renode 1.17.0 described in [Phase 1 setup](../harness/phase1/SETUP.md). The original collection commands were:

```sh
PHASE2_COHORT=rtc_bound_supplement python3 harness/phase2/generate.py --model gpt-6-luna
PHASE2_COHORT=rtc_bound_supplement python3 harness/phase2/build_nominal.py --skip-nominal
PHASE2_COHORT=rtc_bound_supplement python3 harness/phase2/build_nominal.py
PHASE2_COHORT=rtc_bound_supplement python3 analysis/phase2_static_scan.py
PHASE2_COHORT=rtc_bound_supplement python3 analysis/phase2_oracle_review.py --init
```

The existing artifacts can be checked without regenerating them:

```sh
PHASE2_COHORT=rtc_bound_supplement python3 analysis/phase2_summary.py
PHASE2_COHORT=rtc_bound_supplement python3 analysis/phase2_oracle_review.py
```

Generation and build scripts skip finalized IDs. The review checklist is an analysis judgment, distinct from machine-generated raw logs. The summary audit checks frozen prompt/source/build/ELF/platform/UART/trace hashes. The five calls reported **71,058 input tokens** (27,136 cached) and **6,579 output tokens**. Billed API dollars were unavailable through this authenticated CLI and are blank in [API_COSTS.csv](API_COSTS.csv), not zero.

## Assessment and review decision

This supplement did **not** recover an eligible RTC agent comparator. It does isolate a useful methodological point: giving the correct public signature and legal calendar bound addresses one failure mode, yet compile errors, a false pre-alarm predicate, and an unjustified zero wait still prevent a valid robustness comparison. The next study decision is whether Phase 3 should proceed with the 34 eligible primary HSI suites and the selected upstream RTC case reported separately, or whether a newly registered RTC generation condition is worth the extra model cost. Neither choice can be inferred from a perturbed agent result here; none has been collected. Stop for user review.
