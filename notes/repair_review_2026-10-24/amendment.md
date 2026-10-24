

## 2026-10-24 E mechanical repair study: registration for approval, before variants

Status: protocol and six review-only example sources may be prepared now;
**no E compilation, simulation, or E2 model calls before explicit user approval**.
D must first disclose any disabled-control failures or missingness. A–B and D
remain separate new-data phases. This amendment is written before any repair
variant source is created and before any repair outcome is observed.

### Subjects and immutable V0

Include the 30 generated suites with a nonempty `clock_only_budget_s` in the
existing `analysis/rtc_padding_audit.csv`, plus the three selected upstream
RTC cases: **33 subjects (27 generated counting, three generated pending,
one upstream callback, one upstream pending, one upstream counting)**.
This is the pre-existing scalar-budget subset, not every source containing
a sleep. There is no eligible generated callback in this subset. The exact
roster, original source/ELF SHA-256 and budget expressions are sealed in
`notes/repair_review_2026-10-24/subjects.json`. V0 uses those unchanged source
and ELF bytes, with all new runs written separately; old results are preserved.

| Subject | Existing budget (s) |
|---|---:|
| `astra-range_absent-rtc_alarm_pending-r05` | 15 |
| `astra-range_absent-rtc_time_counting-r01` | 40 |
| `astra-range_absent-rtc_time_counting-r02` | 40 |
| `astra-range_absent-rtc_time_counting-r03` | 60 |
| `astra-range_absent-rtc_time_counting-r04` | 60 |
| `astra-range_absent-rtc_time_counting-r05` | 60 |
| `astra-range_present-rtc_time_counting-r01` | 20 |
| `astra-range_present-rtc_time_counting-r02` | 30 |
| `astra-range_present-rtc_time_counting-r03` | 20 |
| `astra-range_present-rtc_time_counting-r04` | 24 |
| `astra-range_present-rtc_time_counting-r05` | 20 |
| `luna-range_absent-rtc_time_counting-r01` | 20 |
| `luna-range_absent-rtc_time_counting-r02` | 30 |
| `luna-range_absent-rtc_time_counting-r03` | 20 |
| `luna-range_absent-rtc_time_counting-r05` | 30 |
| `luna-range_present-rtc_time_counting-r01` | 60 |
| `luna-range_present-rtc_time_counting-r02` | 60 |
| `luna-range_present-rtc_time_counting-r03` | 60 |
| `sol-range_absent-rtc_alarm_pending-r01` | 16 |
| `sol-range_absent-rtc_alarm_pending-r03` | 15 |
| `sol-range_absent-rtc_time_counting-r01` | 60 |
| `sol-range_absent-rtc_time_counting-r02` | 30 |
| `sol-range_absent-rtc_time_counting-r03` | 45 |
| `sol-range_absent-rtc_time_counting-r04` | 25 |
| `sol-range_absent-rtc_time_counting-r05` | 30 |
| `sol-range_present-rtc_time_counting-r01` | 40 |
| `sol-range_present-rtc_time_counting-r02` | 30 |
| `sol-range_present-rtc_time_counting-r03` | 30 |
| `sol-range_present-rtc_time_counting-r04` | 40 |
| `sol-range_present-rtc_time_counting-r05` | 30 |
| `human-rtc_alarm_callback` | 13 |
| `human-rtc_alarm_pending` | 13 |
| `human-rtc_time_counting` | 14.5 |

### Shared transformation rules

Use **20,824 ms = 18.824 s + 2 s** as the observation ceiling, measured by
kernel uptime from immediately before the successful `rtc_set_time` that
starts each target observation. Each reset/repetition gets its own ceiling.
This follows the requested ideal ten-RTC-second slow bound plus a fixed
experimental margin; it is not a measured bound on interrupt delivery.

V1 is a **deadline normalization**, not extension-only: an original wait over
20,824 ms is shortened. Thus normalization can remove over-padding as well as
extend brittle short waits. Record each original/new budget and direction.
Do not silently use max(original, new). This explicit interpretation and the
six examples require the user's approval before E execution.

Preserve all original target calendars, alarm channels, supported masks,
board/driver/clock configuration, setup, teardown, and non-time assertions.
Keep each original zassert invocation, except a timeout's numeric/loop-limit
expression may be redirected to the normalized deadline. Preserve original
success predicates, including any original exact equality, and record any
additional V3 predicate separately. A source with a poll counter retains its
counter variable for assertions but replaces the counter timeout with an
absolute uptime deadline. Clamp each sleep to nonnegative remaining time;
never add another full observation ceiling after a partial wait. Existing
pre-arrival checks stay at their original early observation points. For a
multi-stage calendar/pending path, its service stage uses min(original service
allowance, remaining common deadline); no fresh 3-second extension beyond
20,824 ms. No asserted failure is repaired again after outcomes are seen.

### V1: deadline normalization only

Replace the scalar timeout identified by the roster's existing budget
expression with the common ceiling. Retain the existing fixed-sleep versus
polling strategy and its original polling cadence, and retain original break
conditions. Where an upstream alarm uses 3 seconds plus 10 seconds, retain the
3-second early check and replace the second fixed sleep with the remaining
portion of the common ceiling. Timer anchors precede the initial/reset
rtc_set_time. A later pending service wait shares that deadline as above.
No new configuration or calendar assertions in V1.

### V2: event/state waiting with the same ceiling

Start from V1. Replace the final fixed observation sleep with waiting for the
existing completion predicate (all requested callback bits, pending state,
or the original calendar progress condition) under the same common ceiling.
Use the original protected callback flags, observed through 20-ms sleeps;
no unprotected callback state. Already state-polling tests retain their
predicate and switch to 20-ms polling. This may be only a cadence change for
some subjects; label it accordingly, not as a new event primitive. Retain all
original checks before and after the wait. A destructive pending read is
latched and substituted at the original consuming assertion so the observation
is not accidentally cleared twice. Do not add a new oracle in V2.

### V3: V2 plus the frozen task's required checks

For callbacks, read back configured supported alarm fields/mask, capture
RTC year/month/day/hour/minute/second in each callback before atomically
publishing completion, and check successful reads, configured channel identity,
not-before and exact requested calendar second in the test thread. Store
callback errors/invalid IDs without out-of-bounds indexing or ISR assertions.
Keep the original flags and assertions. Add only missing checks; already
present checks are not duplicated. Each repetition clears capture/error state
before enabling/observing the next event.

For pending, require successful configuration and readback of supported alarm
fields/mask; successful RTC reads bracketing the pending observation; no pending
state before target; and pending observed at/after target under the shared
ceiling. A pending event's recorded RTC calendar must be at/after target.
**Do not invent an exact/upper calendar bound for pending**: its frozen spec
requires eventual pending after target, not exact-second callback delivery.
For counting, require successful set and initial read, nondecreasing successive
calendar observations, and at least ten RTC seconds of progress crossing the
configured year boundary. Keep any stronger original equality unchanged.
Use full calendar comparison/epoch conversion, not tm_sec alone. Configuration
readback detects compare programming; callback timestamp equality also tests
delivery precision within this simulator. Neither supplies an independent
oscillator reference or guarantees detection of a fast oscillator.

Apply these rules only at the source sites identified by the existing budget
expressions. Before full generation, freeze a per-source patch-site ledger
and diff against V0. If a source cannot be transformed without changing
unrelated logic, retain it as not applicable and report why; do not improvise
a different repair. Example artifacts show one upstream callback and one
Sol base pending source for each V1, V2 and V3. They are source previews,
not compiled or validated experimental variants.

### Outcome measures and run policy (execution requires approval)

For each V0/V1/V2/V3 subject, report nominal/build status, legal-clock failure
counts and full per-setting vectors on the original 100 seeds plus both
endpoints, with missing outcomes separate. Reuse frozen V0 ELF bytes; build
new variant ELFs only in separate directories and record source/config/build
command/ELF hashes. Do not alter original forecasts or apply them to variants.
Each variant first clears a build and five-launch nominal gate; a failed
gate remains a failed repair attempt and does not get iterated until passing.

Challenge evaluable variants with fast/slow oscillator and driver-path
nonarrival operators, and signed one-RTC-second alarm offsets for alarm
subjects. Counting signed-offset challenges are non-activation controls,
outside the alarm denominator. A fault detection requires verified activation
and explicit selected-case failure. Gate losses are retained in all-attempt
repair yields. Use the same protected-input audits, separate disabled controls,
original selected-case parsing, assertion replay and task references as A–B.
Report virtual duration and host wall time separately; compare legal survival
and each fault separately, not a single pooled mutation score. Show results
per subject/task and variant, plus a survival versus slow-detection table.
All results are exploratory/post-result repairs, not prospective model evidence.

There are 33 x 4 x 102 = 13,464 planned legal-clock slots before any gate
attrition, 396 fast/slow/nonarrival slots, 40 activated-alarm-offset slots,
and 224 optional counting offset-control slots. Nominal gates, replays and
references are additional and must be included in a runtime/SU proposal before
submission. E2 remains deferred until the user approves E results. Phase 3
must show old/new numbers and their source files before any paper edit.
