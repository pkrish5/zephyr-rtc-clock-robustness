# RTC v2 not-predictable reason categories

Dated 2026-10-04. This is a **descriptive subcoding after varied execution began**. It does not change the frozen 66-suite forecast, 36 not-predictable decisions, sample, or outcome eligibility. The original reasons and frozen source hashes remain in the [row ledger](../analysis/rtc_threshold_sample_v2/not_predictable_categories.csv).

The categories identify the primary reason clock rate alone cannot predict a verdict. They are mutually exclusive but do not inventory every timing assumption in a suite: callback delivery/order covers IRQ delivery, callback service, and cross-context ordering; pending polling/service covers a pending-bit observation window whose verdict can depend on polling or peripheral service; multi-stage control flow requires distinct calendar and pending-delivery budgets or loops in the frozen source. The last two cases are Astra present r05 and Sol present r05. These labels are not measured failure causes.

| Model | Prompt | Eligible RTC suites | Callback delivery/order | Pending polling/service | Multi-stage control flow | Not predictable total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Luna | Range absent | 4 | 0 | 0 | 0 | 0 |
| Luna | Range present | 3 | 0 | 0 | 0 | 0 |
| Sol | Range absent | 15 | 5 | 3 | 0 | 8 |
| Sol | Range present | 15 | 5 | 4 | 1 | 10 |
| Astra | Range absent | 15 | 5 | 4 | 0 | 9 |
| Astra | Range present | 14 | 4 | 4 | 1 | 9 |

The range-present sources contain two explicit multi-stage pending tests versus zero in range-absent sources; Sol's not-predictable count is 10 versus 8 and Astra's is 9 in both conditions. These are small, eligibility-filtered cells and this finer category review was added after early outcomes were visible, so the differences are descriptive only. Luna's eligible RTC suites are counting tests, leaving no callback or pending comparison within Luna.
