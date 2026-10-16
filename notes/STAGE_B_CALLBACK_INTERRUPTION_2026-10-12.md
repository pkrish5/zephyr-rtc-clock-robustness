# Stage B callback interruption audit, 2026-10-12

**Disposition, 2026-10-12:** Stage B is deferred by user direction. The proposed 12-call pilot will not run. The table remains an audit of saved infrastructure records, and its two finalized sources are excluded from all manuscript results.

Read-only audit of the locked 60-call exploratory round in `generated/stage_b_callback_v1`. Counts below are attempt records, except where explicitly called suites. A failed CLI or build attempt is an infrastructure event, not a failed generated test. No legal-clock or fault-probe run has started in this round.

| Prompt condition | Intended calls | Finalized sources | CLI sandbox failures | CLI timeouts | Built sources | SDK build failures before repair | Original nominal pass / history-access error / startup timeout | Separate access-retry pass | Suites excluded by 5/5 nominal rule |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Range present | 15 | 1 | 1 | 0 | 1 | 2 | 0 / 5 / 0 | 5 | 0 with registered access retry; 1 on originals alone |
| Loose spec | 15 | 1 | 0 | 1 | 1 | 0 | 4 / 0 / 1 | 0 | 1 |
| Range absent | 15 | 0 | 0 | 2 | 0 | 0 | 0 / 0 / 0 | 0 | 0 assessed |
| Reminder only | 15 | 0 | 0 | 0 | 0 | 0 | 0 / 0 / 0 | 0 | 0 assessed |
| **Total** | **60** | **2** | **1** | **3** | **2** | **2** | **4 / 5 / 1** | **5** | **1 excluded among 2 assessed** |

The first locked call, Astra range-present callback r01, succeeded on its second CLI attempt after a sandbox failure. Its initial two build attempts failed because the temporary SDK lacked CMake configuration and then `picolibc.specs`; the third build passed with the restored same-version SDK. All five original nominal records are virtual-time-zero history-file permission errors. The separate five-run access retry passed and qualifies under the 2026-10-08 design amendment; originals remain missing, not passes.

The pre-variation source review marked both finalized sources functionally adequate, with timing-bound adequacy unknown in both. There is no generated-source build failure or functional-gate failure among the two finalized calls.

The second call, Astra loose-spec callback r01, succeeded after one CLI timeout and built on the first attempt. Its nominal records are four passes and one Renode monitor startup timeout. The timeout is an infrastructure failure and excludes this suite under the frozen 5/5 nominal rule. It is not recoded as an assertion failure or replaced by a diagnostic. The third call, Astra range-absent callback r01, has two CLI timeout records and no finalized response. Calls 4--60 have not started. No generator or Renode process was active at this audit; an idle build watcher was stopped.

The revised full-round estimate is **14--22 more wall hours** if the model service remains responsive, with a longer tail if repeated timeouts recur. The full round is paused under the user's 12-hour stop rule. A reduced first-replicate pilot would use only the first 12 calls in the existing locked order, yielding one planned source per model and condition, while retaining both completed sources and all failed attempts. A balanced two-replicate pilot would use the first 24 calls, yielding two planned sources per cell. Either scope change needs a dated protocol amendment and user approval before new calls; no completed call should be regenerated. The first-replicate option is the lower-cost connectivity and gate check, but its cells are too small for a reliable model or prompt comparison.

Source records: `generated/stage_b_callback_v1/call_order.json`, suite `attempt.json` and `metadata.json` files, `results/stage_b_callback_v1/build_records`, `build_retry_records`, `nominal_records`, and `nominal_access_retry_records`. These raw files were not edited for this audit.
