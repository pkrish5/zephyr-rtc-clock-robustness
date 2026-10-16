# Phase 2 report: frozen agent suites and nominal validity gates

Date: 2026-09-28 local / 2026-09-29 UTC. Phase 2 ended before any perturbed agent run or repair.

**Later amendment (2026-09-29):** The original strict oracle counts in this historical report are preserved. The [split-gate reanalysis](PHASE2_GATE_AMENDMENT_REPORT.md) separately scores functional and timing-bound adequacy and reports both original and amended attrition.

## Scope and protocol

The [registered protocol](../generated/phase2/PROTOCOL.md) fixes five independent generations for each of [11 tasks](../subjects/phase2_tasks.json). Ten tasks match nominally passing upstream Zephyr v4.3.0 HSI test cases; the selected RTC callback case remains a separate LSI stratum. These are upstream-maintained tests, not verified individually human-authored tests. The prompt supplies behavior, required oracles, public API hints, and build configuration; it does not supply the upstream test source or prior timing outcomes. Exact task, prompt-template, and response-schema hashes are locked in the [generation manifest](../generated/phase2_luna/generation_manifest.json).

One `gpt-6-sol` RTC suite was generated, built, and run nominally as a retained feasibility pilot. Before the Luna primary cohort began, a resource amendment separated that Sol sample from the planned 55-run denominator. The primary cohort requested `gpt-6-luna` using `codex-cli 0.158.0-alpha.2.1` in fresh read-only, empty-workspace CLI processes. All 55 model outputs were captured in one attempt each, with zero tool-use events. Raw prompts, JSONL events, responses, dates, source hashes, and usage records are saved under [generated/phase2_luna](../generated/phase2_luna/) and [results/phase2_luna](../results/phase2_luna/). The CLI did not disclose an exact server snapshot, sampling seed, or temperature; the requested slug and CLI version are recorded, and exact server version is **unverified**.

Each generated `test.c` is unchanged after capture. A study-owned wrapper builds it into a separate full Zephyr ELF. Each built ELF is unchanged between its nominal run and any future legal schedules. Human and generated ztests link into different full ELFs; the same-binary invariant applies within each suite, not across suites. Every nominal run records source/ELF/platform hashes, Renode version, virtual-time configuration, UART output, and trace. Build and runtime failures remain in the generation denominator.

## Results

All **55/55** Luna generations produced a nonempty source file. **50/55** built; five failed at compile or link time. The failed builds were `sleep-r03` (`k_thread_is_sleeping` unresolved), `pending-r01` (wrong `k_thread_state_str` call), `pending-r04` (using `k_sem_give` as a value), `pending-r05` (wrong `K_TIMER_DEFINE` arity), and `rtc_alarm_callback-r05` (C syntax error). Their compiler logs are preserved.

Of the **50 compiled suites**, **38 passed** nominally, **9 failed** their ztest assertion, and **3 timed out** after 90 virtual seconds without a verdict. The 90-second timeout cases were `timer_api-r02`, `sleep-r04`, and `pending-r03`; their partial UART and full monitor traces remain in the raw results. Thus **38/55 generated suites** passed both generation and nominal execution gates. The per-suite source review found **34/55** meeting all registered oracle requirements and the feature-path gate, **19 inadequate**, and **2 uncertain**. All 34 adequate suites also passed nominally. The two uncertain cases are nominally passing context tests with incomplete evidence that the worker actually entered sleep and that their lower timing bound represents the requested duration.

| Task | Build pass / 5 | Nominal pass / 5 | Oracle adequate / 5 |
| --- | ---: | ---: | ---: |
| Periodic timer | 5 | 4 | 4 |
| Semaphore ISR | 5 | 5 | 5 |
| FIFO ISR | 5 | 5 | 5 |
| LIFO ISR | 5 | 5 | 5 |
| Message queue ISR | 5 | 5 | 5 |
| Delayed work | 5 | 2 | 2 |
| Queue ISR | 5 | 5 | 5 |
| Sleep/wakeup | 4 | 3 | 3 |
| Timed-sleep context | 5 | 3 | 0 |
| Pending timer | 2 | 0 | 0 |
| RTC callback (selected LSI stratum) | 4 | 1 | 0 |

The nominal and oracle-review totals are generated in [summary.json](../results/phase2_luna/summary.json), with per-suite judgments and evidence in [phase2_oracle_decisions_luna_primary.json](../analysis/phase2_oracle_decisions_luna_primary.json). A source can compile and pass nominally yet still fail a required oracle. The review was performed against registered requirements before any perturbed agent result was observed; a second independent reviewer remains a paper-stage requirement.

The [static scan](../results/phase2_luna/static_candidates.json) records source locations for fixed waits, explicit bounds, ordering/shared-state assertions, possible unprotected reads, and synchronization observations in all 55 agent suites and 11 matched upstream cases. It found at least one non-synchronization candidate in **37/55 agent suites** and **7/11 matched upstream cases**. These are **syntactic candidates**, not an RQ1 prevalence estimate: the scanner also marks waits that implement the behavior being tested and justified immediate reads. For example, it flags a semaphore-count assertion after `irq_offload`, but that call returns after the ISR handler, so the immediate count read can be justified. [Selected manual judgments](../analysis/phase2_timing_examples.json) include the upstream RTC fixed wait, an agent RTC deadline below the legal slow-clock arrival time, and uncertain shared-state reads. Exhaustive adjudication and reviewer agreement remain to be done before claiming RQ1 rates.

The most consequential limit is the RTC task context. Its prompt omitted both the registered 17–47 kHz LSI range and the `rtc_alarm_set_time` parameter signature. Two generated RTC suites passed compilation but swapped the API arguments and failed nominally; another failed a stale-calendar assertion; one failed compilation. The sole nominally passing RTC suite imposes a 15 s deadline on a ten-RTC-second interval that takes about **18.8 s at the registered 17 kHz endpoint** with the nominal-32-kHz prescaler. Its deadline therefore does not satisfy the predeclared justified-bound oracle. The original outputs are retained; no Phase 3 flip has been measured for them.

The earlier upstream baseline remains **0 flips / 299 evaluable HSI runs**, with one unresolved harness error among 300 planned, and **7/30** flips for the separately selected RTC LSI pilot. Those results are not an agent-versus-upstream effectiveness comparison. Phase 2 ran agent suites at nominal timing only, so it cannot answer whether agents improve timing robustness or whether repair works.

## Token and cost record

The 55 Luna calls reported **762,788 input tokens** (including **574,464 cached input tokens**) and **31,035 output tokens**. The one Sol feasibility sample reported 14,139 input and 3,186 output tokens; two tiny CLI connectivity pilots are listed separately in [API_COSTS.csv](API_COSTS.csv). This ChatGPT-authenticated CLI route did not expose billed API dollars, so the dollar field is blank rather than zero. The account's five-hour usage display reached 100% during the batch, but all 55 already-running generation calls completed without a recorded infrastructure retry.

## Reproduce and audit

Use the pinned Zephyr/toolchain/Renode setup in [harness/phase1/SETUP.md](../harness/phase1/SETUP.md). The existing frozen outputs can be audited without regenerating them:

```sh
PHASE2_COHORT=luna_primary python3 analysis/phase2_summary.py
PHASE2_COHORT=luna_primary python3 analysis/phase2_static_scan.py
PHASE2_COHORT=luna_primary python3 analysis/phase2_oracle_review.py
```

The original collection commands were:

```sh
PHASE2_COHORT=luna_primary python3 harness/phase2/generate.py --model gpt-6-luna
PHASE2_COHORT=luna_primary python3 harness/phase2/build_nominal.py --skip-nominal
PHASE2_COHORT=luna_primary python3 harness/phase2/build_nominal.py
```

The generation command skips already finalized IDs and must not be used to replace any frozen output. The build command likewise skips recorded builds and nominal runs. Source-level review decisions are separate from machine-generated raw logs. The latest audit checks hashes of prompts, source, wrapper, overlays, build log, ELF, platform, UART, and trace.

## Assessment and next decision

The fixed-prompt, five-sample generation method is feasible and yields **34 nominally passing, oracle-adequate HSI suites**, while exposing meaningful build, nominal, and oracle attrition. The current primary cohort has no RTC suite that both passes nominally and meets the registered legal-bound oracle. A separately registered RTC supplement could provide the public `rtc_alarm_set_time` signature and legal LSI bound, then generate five new samples without modifying or dropping the original 55. The alternative is to proceed with the current cohort and report that the primary RTC agent comparison has no eligible suite. This choice belongs to the user at the Phase 2 review gate. No Phase 3 schedules or repairs have been run.

**2026-09-29 follow-up:** The user approved that separate five-sample context supplement. It completed with 2/5 builds, 1/5 nominal passes, and 0/5 nominal-and-oracle-adequate suites; see [the supplement report](PHASE2_RTC_SUPPLEMENT_REPORT.md). The original primary outcomes above remain unchanged. No Phase 3 agent timing run or repair has occurred.
