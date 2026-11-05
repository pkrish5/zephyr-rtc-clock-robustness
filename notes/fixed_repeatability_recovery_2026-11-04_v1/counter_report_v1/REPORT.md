# Verified f4-counter fixed-setting repeatability (partial study)

Job 3552870; 90 planned launches. Other application results are not included here.

|Fixed frequency, Hz|Pass|Fail|Skip|Missing|
|---:|---:|---:|---:|---:|
|29143|0|30|0|0|
|29352|30|0|0|0|
|32000|30|0|0|0|

All 30 verdicts agree in each of these three cells: **no observed same-setting flakiness in this application at these settings**. Rare flakiness is not ruled out.

## Evidence-linked timing observations

Kernel-reported case duration and sampled Renode UART exposure below are distinct measurements. Neither timestamps callback entry or subsecond phase. Full traces, UART and record hashes are listed per run.

|Frequency Hz|Kernel-reported case duration range, s|First sampled verdict exposure, virtual s|
|---:|---|---|
|29143|[3.002, 3.002]|[6.0, 6.0]|
|29352|[3.101, 3.101]|[323.0, 323.0]|
|32000|[3.101, 3.101]|[323.0, 323.0]|

Verified archived evidence: [verified-3552870-v1](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_recovery_2026-11-04_v1/verified-3552870-v1). Source/inference timeline remains in [TIMELINES.md](/Users/pranavkrishnan/Development/Flakey_Tests_Embeded/notes/fixed_repeatability_2026-11-04_v1/TIMELINES.md); it is not a direct event-time measurement.
Normalized trace differences can reflect UART visibility/rounding; they do not by themselves establish verdict flakiness.
