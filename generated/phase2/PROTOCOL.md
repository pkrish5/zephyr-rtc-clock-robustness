# Phase 2 protocol: fixed-prompt agent test generation

Registered before the first counted generation call. The [task manifest](../../subjects/phase2_tasks.json) fixes 11 behavior objectives and their passing upstream Zephyr v4.3.0 comparison cases. Ten tasks belong to the earlier HSI corpus; the selected RTC callback task is a separate LSI pilot stratum. The `context` match uses its passing timed-sleep case because that application's interrupt-specific cases skipped at nominal timing. The upstream files are maintained test sources, not verified individually human-authored tests.

## Sampling and isolation

For each task, run **k = 5** fresh, independent Codex CLI sessions with the **identical rendered prompt** from [`prompt_template.txt`](prompt_template.txt). Use one fixed model/version for all 55 calls, locked in the generation manifest before the first counted call. The run index distinguishes repeated calls but is **not shown to the model**. The CLI does not expose a sampling seed or temperature for this route; record that limitation. Run in an isolated empty directory with no upstream tests available through the task context, with a read-only tool sandbox and no interactive repair. The prompt includes the written behavior, required checks, public API hints, and build configuration, but excludes the human test source, baseline verdicts, legal perturbation values, and Phase 1 flip result. Archive the exact rendered prompt, its hash, model response, JSONL event trace, model/CLI version, date, token usage, and errors for every invocation. Do not replace an unfavorable sample.

## Frozen suites and gates

Parse the model's structured `test_c` response into one C file verbatim, without fixing it. Preserve malformed or refused outputs as generation failures. A study-owned CMake wrapper and fixed config/overlay build each suite as its own ELF on `stm32f4_disco/stm32f407xx`. Hash the generated source, wrapper/config, and full ELF. A compile failure remains in the 55-attempt denominator. For a successfully built suite, run one nominal Renode execution and preserve the complete UART/monitor trace and verdict. A nominal failure remains in the denominator but is ineligible for Phase 3 pass-to-fail rates; do not silently discard it or repair it. Oracle adequacy is judged against the task's required checks before later timing outcomes are examined, with a reason recorded for inadequate tests. Phase 2 does **not** run perturbed schedules.

The full ELF is expected to differ between upstream and generated suites because ztest links test code into firmware. Freeze each generated test source and its ELF before Phase 3. Within one suite, the same full ELF must be used for nominal and every future timing schedule.

## Static timing-assumption pass

Tag candidate fixed sleeps/busy waits, explicit timeouts, callback/log ordering assertions, and reads of state shared with ISR or timer callbacks in the generated suites and the matched upstream cases. Keep source location and reason for each tag, distinguish *syntactic candidates* from adjudicated unjustified assumptions, and allow an explicit `unknown` judgment. The static tagging pass is blind to perturbation outcomes. Report per-task and per-suite tags, build/nominal/oracle attrition, and token counts. For ChatGPT-authenticated Codex CLI runs, dollar API cost may be unavailable; report it as unavailable rather than zero. Do not infer RQ1 prevalence from the selected RTC pilot alone.

Stop at the end of Phase 2 for user review before running Phase 3 schedules or attempting repair.

## Resource amendment before the primary cohort

The first counted `gpt-6-sol` sample (`rtc_alarm_callback-r01`) was generated, built, and passed nominally. Two tiny CLI connectivity pilots were also run. Codex account usage then reached 89% of its five-hour window, making 54 additional Sol generations impractical without repeated resets. The source and all raw logs of that sample remain frozen under `generated/phase2/` and `results/phase2/`; it is now an explicitly labeled **Sol feasibility pilot**, excluded from the planned primary 55-run model cohort for a resource reason, not because of its output. The generated RTC source contains a timing timeout candidate and passed nominally. Neither its code nor its result was used to revise the task manifest or prompt template.

The primary cohort uses the same frozen [task manifest](../../subjects/phase2_tasks.json), [prompt template](prompt_template.txt), response schema, k = 5, and gating rules with `gpt-6-luna` and separate roots `generated/phase2_luna/` and `results/phase2_luna/`. This model change is recorded here **before the first Luna task-generation call**. If Luna usage also limits completion, keep partial runs and resume only after reset; do not lower k, change the prompt, or silently omit tasks.
