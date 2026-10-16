# Stage B proposals, 2026-10-08

**Status: proposed only. No model generation, simulation, recruitment, build, or
fault run has started.** Existing frozen prompts, sources, ELFs, schedules, and
raw records remain unchanged. The proposal responds to the model and
specification fairness questions after the read-only Stage A re-analysis.

## B1 and B2: one combined RTC generation round

### Conditions and exact proposed text

The six complete proposed prompt files and SHA-256 values are in
[`STAGE_B_PROPOSED_PROMPTS/manifest.json`](STAGE_B_PROPOSED_PROMPTS/manifest.json).
They remain drafts. All unchanged preamble, board, Kconfig, JSON schema,
read-only/no-tools instruction, and output text are copied byte-for-byte from
the frozen range-absent prompt.

**B1, `loose_spec`:** Replace only the `Behavior to test` and
`Required observable checks` blocks, plus remove `rtc_get_time` from the
callback API hint and `rtc_get_time`/`rtc_alarm_get_time` from the pending
API hint. The exact replacements are:

| Task | Replacement `Behavior to test` |
|---|---|
| Callback | Exercise the STM32F407 RTC alarm callbacks using the board's RTC alias. The RTC uses the independent LSI oscillator. Set calendar time to 2024-12-31 23:59:55 and alarm time to 2025-01-01 00:00:05 for both alarm channels. Use supported second, minute, and hour alarm fields (mask 7). Verify that both alarm callbacks are called after the alarms are programmed. Each callback must identify its configured alarm channel. |
| Pending | Exercise the STM32F407 RTC alarm-pending state through the board's RTC alias. Set the calendar to 2024-12-31 23:59:55 and an alarm to 2025-01-01 00:00:05. Use supported second, minute, and hour alarm fields (mask 7). Verify that the alarm-pending state becomes set after the alarm is configured. No alarm callback is required. |
| Counting | Exercise STM32F407 RTC calendar counting through the board's RTC alias. The RTC uses an independent LSI oscillator. Set a calendar time near a year boundary, then verify that the observed calendar advances across that boundary. Compare RTC calendar values rather than relying only on host uptime. |

| Task | Replacement `Required observable checks` |
|---|---|
| Callback | Both callbacks are eventually observed after their alarms are configured. Each callback reports its expected alarm ID. The test uses a finite observation window and checks callbacks through observable events or protected state. |
| Pending | The test configures a supported RTC alarm successfully. The alarm is initially not pending and is eventually observed pending. The test uses a finite observation window. |
| Counting | Setting and subsequently reading the initial RTC calendar succeeds. A later observed calendar value is after the initial value and crosses the year boundary. The test uses a finite observation window. |

The full proposed files preserve the bullet formatting. B1 deliberately
does not require firing at the exact target RTC calendar second or reading
back the programmed alarm. The setup still gives a target alarm time so a
model may choose either check. Counting is an analogous looser task and
serves as a non-alarm control. This condition changes the requested
functional contract. Judge working-test yield against its own looser
contract, and score exact-time/readback strength as separate outcomes. Never
exclude a B1 source merely for omitting a check B1 did not request.

**B2, `reminder_only`:** Keep each frozen range-absent task specification
byte-for-byte and insert this exact **52-word** paragraph immediately before
`Return a JSON object`, the same location and whitespace as the 52-word
numeric range paragraph:

> Documented hardware timing reminder: The RTC and processor timing can vary across operating conditions. A test should remain valid when clock speed, scheduling, and callback service differ from nominal timing. Choose observation bounds from the behavior and API guarantees. A clock-rate argument alone does not establish when a callback reaches a thread.

The paragraph gives no oscillator frequency, prescaler, numerical deadline,
or device tolerance. Its length matches the frozen numeric paragraph by
space-separated words, not tokenizer tokens. B2 versus a contemporaneous
numeric-range control probes whether numerical information adds anything
beyond the generic reminder. B1 versus a contemporaneous range-absent
control probes whether exact alarm checks come from the specification.

### Sample size and controls

**Recommended pilot:** two independently generated sources for each of
three RTC tasks × three requested model IDs × four conditions
(`loose_spec`, `reminder_only`, fresh `range_absent`, fresh
`range_present`) = **72 calls**. The two new conditions account for 36
calls and the contemporaneous controls for 36. Interleave task, model, and
condition in a fixed seeded order. Save every response, failed call/retry,
exact prompt bytes, model ID/version information if exposed, token usage,
and source hash. The controls are necessary because the historical October
3--4 model IDs have no backend version snapshots. Two per cell makes this
an exploratory pilot; a later confirmation would need a larger independent
sample. Three per cell would be 108 calls, about 50% more generation and
test work.

### Gates, runs, and scoring

1. Freeze all prompts, call order, random seed, source-review rubric, and
   analysis plan before the first generation. Use the source-only no-tool
   route and original build configuration. Do not repair outputs.
2. For all 72 attempts, preserve generation/schema outcome, build outcome,
   functional source review, and timing-bound adequacy separately. For built
   functionally adequate tests, run five fresh nominal launches. B1 uses
   its own stated functional contract; the three precise conditions use
   the original contract. Report all-attempt yield as well as eligible-only
   results.
3. For each eligible test, use the same legal LSI endpoints, 17 and 47 kHz,
   under unchanged firmware. Endpoints alone are an endpoint screen, not a
   100-seed robustness verdict. Freeze clock-only predicted 100-seed vectors
   when a source permits a defensible scalar threshold. Run at most one
   eligible suite per model × condition among predictable suites over all
   100 existing seed frequencies (at most 12 validation suites), balanced
   across tasks by a presaved rotation and random seed. Any mismatch stops
   the clock extension for review. Unsampled predictable suites remain
   labeled predictions; nonpredictable suites without a 100-seed run remain
   unknown, not clock-robust. A full nonpredictable schedule would require a
   separate runtime decision.
4. At nominal clock, challenge every eligible suite with the already
   validated fast (64-kHz), slow (10-kHz), and driver-path nonarrival
   operators. Callback and pending suites also receive the signed one
   RTC-second firmware alarm offsets. Counting suites are offset
   non-activation controls. A **kill** requires a logged active operator and
   an explicit failing selected ztest assertion. Pass is survival;
   simulator/startup error is missing; nonactivation is unscored. Keep
   reference activation, original records, and diagnostic replays separate.
5. Primary descriptive contrasts are task-matched: loose versus fresh
   absent for exact-calendar and readback checks/offset kills; reminder
   versus fresh absent; numeric range versus reminder for clock flips,
   forecast adequacy, slow-fault kills, and all-attempt yield. Model
   interactions are exploratory with two suites per task cell. Report
   negative results and missing outcomes; cluster by task.

### Runtime and cost estimate

Historical RTC generation metadata give per-call median input/output token
counts of about 13,958/1,134 for Luna, 14,137/2,903 for Sol, and
14,586/2,237 for Astra. Twenty-four calls per model at those medians
project **1.02 million input and 0.151 million output tokens** for the
72-call pilot, before retries. On the official Standard API schedule for
these exact model IDs, assuming no cache benefit, the **API-equivalent**
estimate is about **$7.60**, or about **$9--12** with token variation and
retries. Sources: [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Sol](https://developers.openai.com/api/docs/models/gpt-6-sol),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).
The historical authenticated Codex CLI did not expose billed dollars, so
this is **not** a statement of what this account would be charged or how
its credits would be debited. Check the account's actual billing/limit route
before approval if a dollar cap matters.

The 72 calls are roughly 1.5--3 hours of sequential generation at prior
throughput. Allow about 1--3 summed machine-hours for builds and five-run
nominal gates, 1--2 for endpoints, 3--5 for nominal fault probes and mutant
builds, and up to 17 for 12 sampled 100-seed validations at historical
40--50 second simulator records. With three separate Renode workers,
this is approximately **8--15 wall hours including generation and
auditing**, plus **3--6 hours of one-time adapter/prompt-lock engineering**.
If fewer eligible predictable suites exist, the schedule shrinks. Running
all eligible new suites over 100 seeds would add tens of serial
machine-hours and is not in this modest proposal.

## B4: same-spec human packet

The [prepared packet](../materials/same_spec_human/README.md) contains all
six byte-identical frozen RTC prompts, SHA-256 manifest, author instructions,
submission metadata template, and evaluation steps for an isolated human
cohort. It specifies a one-shot source-only submission and identical build,
functional, nominal, legal-clock, and fault gates. It has **not** recruited,
assigned, or evaluated anyone. A small reviewed adapter is still needed to
place human submissions in a new manifest and result namespace without
changing the factorial runner or frozen records.

## B3, B5, and B6: feasibility notes only

- **B3 random upstream expansion.** The 33-file source scan is not a list
  of 33 independently runnable selected cases. Three selected RTC cases
  already run on this board; the other 30 include counter/timer tests with
  different drivers, configurations, and potentially incompatible board
  requirements. Feasibility qualification and a fixed-seed random draw
  among a clearly defined runnable frame are possible but likely require
  1--3 engineering days before any same-schedule runs. The qualifying count
  is unknown; no random sample was drawn here.
- **B5 portability.** Zephyr's local tree contains non-STM32 RTC drivers,
  but the checked STM32L and STM32F board definitions still use the STM32
  RTC driver. A second board meeting all three requirements, Renode RTC
  support, a different Zephyr RTC driver, and a documented wide-tolerance
  oscillator, has not been verified. Treat portability execution as
  infeasible until board, peripheral model, and datasheet range are
  established together; initial qualification is roughly 1--2 days.
- **B6 fidelity.** A minimal physical STM32F4 cross-check is more direct
  than assuming QEMU models the relevant RTC path: on a board with a
  traceable independent timebase, timestamp RTC alarm callback GPIO edges
  while measuring or bounding LSI frequency, then compare observed
  calendar arrival and software delivery separately with $320000/f$.
  It needs a board, programmer, logic analyzer or oscilloscope, and clock
  measurement access. With equipment available, a first nominal and
  endpoint-like measurement protocol is roughly half to one engineering
  day; it cannot force a physical LSI to both datasheet endpoints. No
  physical or QEMU measurement is claimed.

**Decision gate:** approve, revise, or reject the combined generation
pilot and any later human or cross-platform work separately. Nothing in
this document authorizes execution.
