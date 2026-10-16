# Registered Phase 2 RTC context supplement

Registered 2026-09-29 **before the first supplement generation**. The user approved a separately labeled five-sample RTC supplement after the primary 55-run cohort left no RTC suite that both passed nominally and met its legal-bound oracle. Preserve all primary and Sol pilot outputs. This supplement is a context condition for the same selected upstream Zephyr RTC task, not a replacement or an additional independent firmware subject.

## Controlled context change

Use the same `gpt-6-luna` requested model, k = 5 fresh independent CLI sessions, [prompt template](../phase2/prompt_template.txt), [response schema](../phase2/response.schema.json), STM32F4 board, Zephyr commit, build config, feature specification, and three required oracles as the primary RTC task. The new [task manifest](../../subjects/phase2_rtc_bound_tasks.json) changes **only** `rtc_alarm_callback.api_hints` within the task. The exact hashes before generation are:

| Input | SHA-256 |
| --- | --- |
| Original task manifest | `4562d39e62cd6776b296422ab93748c30081a9b750d29d7c953e294745cd002a` |
| Supplement task manifest | `aa37a44fe226e00a0ea2e0bd741caddcffa565cbbe7863bc9e1a4cefbc4241dc` |
| Shared prompt template | `586f5df25ba8c33369d2d4e3605faa86851477e1b8f0bd47e0d2a194d2f0e67c` |
| Shared response schema | `8ebe4f68092ee33c6d7b00cd6b588447eac19935d4a923a8b1064605d9db353c` |

The added context quotes the pinned Zephyr v4.3.0 [RTC public API signatures](../../subjects/upstream/zephyr/include/zephyr/drivers/rtc.h), especially the `rtc_alarm_set_time(dev, id, mask, timeptr)` argument order and callback type. It states the [STM32F407 datasheet DS8626 Table 35](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf) LSI range of 17–47 kHz at VDD = 3 V over −40 to 105 °C, and the pinned Zephyr STM32 RTC driver's [128 × 250 LSI prescaler](../../subjects/upstream/zephyr/drivers/rtc/rtc_ll_stm32.c). Thus ten RTC calendar seconds require 320,000 LSI input cycles, taking about 18.824 s at 17 kHz and 6.809 s at 47 kHz. These are **calendar progression calculations**, not documented ISR latency bounds. The prompt supplies neither the original upstream test source nor prior generated outputs, Phase 1 verdicts, or a repair recipe.

## Capture and gates

Run each generation in an empty temporary working directory with read-only tools and no interactive repair. Save the exact prompt, date, requested model, CLI version, JSONL events, response, source hash, token usage, errors, and any unknown exact server snapshot. Do not replace a malformed, noncompiling, nominally failing, or otherwise unfavorable sample. The primary cohort and this supplement must be analyzed separately; the five supplement outputs must not be pooled into the original 55-run denominator.

Build each frozen `test.c` into its own Zephyr ELF with the same wrapper and RTC overlay as the primary RTC task. Record source, config, ELF, platform, simulator version, seed 0, UART/monitor trace, and nominal verdict. A compile failure remains in five-generation denominator. A nominal failure or timeout remains in the denominator but is not eligible for a later pass-to-fail rate. No varied-LSI run occurs in this supplement.

Before looking at any perturbed agent outcome, review the three unchanged required oracles. For the finite-bound oracle, a timeout that starts after setting the calendar must permit at least the computed 18.824 s slow-clock calendar progression; a later start can credit elapsed time only if the test observes and records its relation to RTC time. Any additional ISR/scheduler margin is a test policy, not a manufacturer guarantee. A timeout below the legal slow-clock arrival is inadequate. A longer timeout alone does not establish correct callbacks or preserve the premature-callback and alarm-ID assertions. Mark unclear timing or callback evidence `uncertain`; do not silently count it as adequate. Source-level timing tags use the same scanner and remain candidates pending adjudication.

Stop after generation, compilation, nominal runs, oracle review, and the supplement report. Await user review before Phase 3 legal timing schedules or any repair.
