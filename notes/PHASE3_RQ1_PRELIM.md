# Preliminary RQ1 source review

Date: 2026-09-29. This is a **single-reviewer, unblinded exploratory source coding**, completed while Phase 3 RTC schedule runs were in progress. Early RTC outcomes and the Phase 1 RTC result were already visible to the reviewer. It is not a final prevalence estimate or an agent-versus-human quality conclusion.

The [registered coding rubric](../analysis/PHASE3_RQ1_CODING.md) separates a supported unjustified timing premise from a justified operation and an unresolved source judgment. The [decision ledger](../analysis/phase3_rq1_decisions.json) covers all 55 frozen primary Luna test sources and the 11 matched selected upstream Zephyr cases, with source hashes and line-level evidence for each confirmed issue. The [audit/summary script](../analysis/phase3_rq1_review.py) checks that inventory and emits [machine-readable counts](../results/phase3_rq1_summary.json). The separate five-sample RTC context supplement is not pooled into the primary 55.

| Source group | Confirmed unjustified | None found | Unknown | Registered units |
| --- | ---: | ---: | ---: | ---: |
| Primary agent suites | 6 | 32 | 17 | 55 |
| Matched upstream cases | 4 | 5 | 2 | 11 |

The descriptive confirmed fractions are 6/55 = 10.9% (95% suite-level Wilson 5.1–21.8%) and 4/11 = 36.4% (15.2–64.6%). **Do not interpret their difference as an agent advantage.** The 17 and 2 unknowns are retained, agent outputs cluster five per task, upstream files are not verified individually human-authored, and the task sample is selected from one repository/board. The Wilson intervals are conditional descriptive calculations across units, not uncertainty intervals for a population of embedded tests. A second blinded reviewer and task-level uncertainty analysis are required for a paper claim.

If every unknown were ultimately coded unjustified, the counts could rise to 23/55 agent suites (41.8%) and 6/11 upstream cases (54.5%). These are sensitivity bounds, not confidence intervals. They show why the observed confirmed fractions alone cannot answer which source group has more timing assumptions.

At the task level, confirmed issues occur in agent suites for **3/11 tasks** (pending, RTC alarm callback, sleep) and in upstream cases for **4/11 tasks** (RTC alarm callback, sleep, timer API, work queue). The five agent generations within a task are related observations, so their 55 suite labels should not be read as 55 independent firmware subjects. The two task sets also retain unresolved source judgments; this task-level inventory is descriptive, not a paired superiority test.

Concrete confirmed cases include the upstream RTC fixed wait (already flipped under legal LSI in Phase 1), the primary agent RTC 15-second cap below the 18.824-second slow-clock arrival, agent yield loops that can starve lower-priority workers, and upstream assertions that a periodic timer or delayed work must be observed within an exact short scheduling window. In contrast, most ISR-offload queue/semaphore assertions follow synchronous `irq_offload()` return, so immediate `K_NO_WAIT` checks there are not coded as timing defects. Plain callback counts, worker-ready sleeps, and marginal ordering checks remain unknown where the source contract is unclear.

This coding does not use Phase 3 flips as a substitute for source judgment. Final RQ2 results and the four-way flip ledger will be reported separately after the registered runs and replays finish.
