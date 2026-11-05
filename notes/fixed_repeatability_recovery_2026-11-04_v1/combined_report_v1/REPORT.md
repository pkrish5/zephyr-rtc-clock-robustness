# Fixed-setting repeatability results

|Case-frequency cell|Pass|Fail|Skip|Missing|
|---|---:|---:|---:|---:|
|f4-rtc-23673|0|30|0|0|
|f4-rtc-23847|30|0|0|0|
|f4-rtc-32000|30|0|0|0|
|f4-counter-29143|0|30|0|0|
|f4-counter-29352|30|0|0|0|
|f4-counter-32000|30|0|0|0|

All 30 fresh-process verdicts agree in every cell: **no observed same-setting flakiness** in these cells under this model. Rare flakiness is not ruled out.

Missing verdicts remain missing. Between-cell differences are timing sensitivity. Timelines are in TIMELINES.md; no callback-entry or phase timestamp was directly measured.

Both independent audit paths agree on all 180 selected verdicts. Every full-application case vector matches an archived vector at the same frequency. All capability skips and other case outcomes are retained in `all_case_verdicts.csv` and `all_case_counts.csv`. The two earlier preflight attempts launched zero processes and are separate from these 180 outcomes.
