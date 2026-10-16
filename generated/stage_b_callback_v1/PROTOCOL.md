# Stage B callback exploratory round, approved and frozen 2026-10-08

This is a new, separate cohort. The dated approval amendment is in
[`paper/DESIGN.md`](../../paper/DESIGN.md). No historical source, build,
schedule, or raw verdict is changed. All comparisons in this round are
exploratory.

## Generation lock

Generate five independent complete C ztest sources for each of three
requested model IDs (`gpt-6-luna`, `gpt-6-sol`, `gpt-6-astra`) and four
callback prompt conditions (`range_absent`, `range_present`, `loose_spec`,
`reminder_only`): 60 intended calls. The first two are fresh copies of the
original factorial prompts. The latter two are the exact approved Stage B
proposal texts. `lock.json` hashes every prompt, the original source prompt
or proposal, response schema, call order, and generation runner. The order
is a seeded interleaving of model and condition within each of five rounds.
The generation command must validate this lock before every call. Store all
raw CLI events, stderr, response, source, hashes, usage, and failed attempts.
Do not rewrite a generated source. A failed infrastructure call may be
retried unchanged, with its first attempt retained. A malformed model
response remains one failed intended attempt.

## Gates and clocks

Build in the pinned Zephyr v4.3.0 board configuration and original RTC alias
overlay. Review source functionality against its assigned prompt, and code
timing-bound adequacy separately. The looser callback prompt does not require
an exact calendar check or alarm readback. For built functionally adequate
sources, run five fresh nominal 32-kHz LSI/16-MIPS launches. An original
nonpass or harness error disqualifies the suite; diagnostic retries do not
replace originals.

Each eligible suite receives the 17- and 47-kHz legal endpoints. Before
varied-clock outcomes, record whether a defensible clock-only prediction can
be frozen for all 100 existing schedule frequencies. A predictable suite is
selected for validation on the same seed vector if it wins the presaved
per-cell SHA-256 rank; the same rank selects one not-predictable suite if no
predictable one is lower. Thus at most one eligible suite per model ×
condition receives the full vector. No unrun not-predictable suite is called
robust. Exact vector disagreement for a sampled prediction stops further
clock work for review. All original failures are replayed and classified
with persisted traces; original verdicts remain authoritative.

## Fault challenges

At nominal RTC clock, challenge every eligible callback suite with the
validated 10-kHz slow oscillator, driver-path nonarrival, and driver-programmed
alarm compare offsets of −1 and +1 RTC calendar second. Run reference
activation controls before suite scoring. Rebuild each new suite with the
isolated operator driver in a new result namespace. A kill requires a logged
active fault and explicit selected-case assertion failure. Pass is survival;
ambiguous/startup/monitor errors are missing; absent activation is unscored.
The fast 64-kHz out-of-spec oscillator is optional and separately labeled.
No fault verdict is a legal-clock failure.

Report all 60 attempts, gate losses, measured seed verdicts, endpoint
verdicts, predictions, and missing results separately. Contrast task-matched
callback suites only, by requested model ID and prompt condition. There is
one task cluster, so statistical comparisons are descriptive. The model IDs
do not identify immutable backend snapshots.
