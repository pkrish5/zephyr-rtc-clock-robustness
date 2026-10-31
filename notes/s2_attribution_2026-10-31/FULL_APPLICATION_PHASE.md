# Full-application phase and boundary guard, 2026-10-31

Read-only source review. No experiment, replay, reference build or change to
the earlier frozen forecasts. Full S2 primary archive verification remains
pending at this checkpoint.

## Exact release source

The saved Phase 1 provenance identifies the source embedded in both official
Renode release packages as `f1dd1b4af7838b45a925c17603cdfed0a583844a`.
GitHub's Git tree API for that exact commit identifies its `src/Infrastructure`
submodule as `cd4b002aac2398994c4a61a34a8b31b5700facf2`. This is distinct
from today's movable release tag. Source URLs, bytes and SHA-256 checksums
are in `model_source/provenance.json`; the copied files are for source review.

- `STM32F4_RTC.cs:30-38` constructs the calendar ticker from the prescalers.
- `STM32F4_RTC.cs:242-250` handles INIT by changing the ticker's Enabled
  property; it does not reset its current count there.
- `STM32F4_RTC.cs:641-695` changes calendar fields when time/date registers
  are written, without resetting the ticker.
- `LimitTimer.cs:272-285` changes Enabled through the existing clock entry,
  retaining its other fields, including its current count.
- `subjects/upstream/zephyr/drivers/rtc/rtc_ll_stm32.c:536-623` implements
  `rtc_set_time` through INIT and calendar-register writes.

These source paths establish a mechanism for preserving the subsecond
count across calendar writes in this simulator model. They do not establish
silicon behavior or the actual phase of a particular S2 failure. Confirm
the peripheral class in each sealed board platform before applying the
mechanism to that board.

## Consequence for the explanation table

Keep the original zero-phase thresholds and validation as their original
isolated-test analysis. Do not copy their sampled failure counts or an exact
boundary into the expanded full-application cohort. Preceding tests and
clock-dependent assertion aborts can change the phase at the next time write.

Ignoring software delivery for this ideal illustration, if the preserved
phase is phi RTC seconds into a tick, a ten-calendar-second transition needs
`(10 - phi) * 32000/f` host seconds, with `0 <= phi < 1`. For a thirteen-second
window this gives a phase-dependent boundary between about 22.154 and
24.615 kHz; the thirty-poll last-observation approximation of 14.5 seconds
gives about 19.862 to 22.069 kHz. Phase itself can depend on frequency, so
this does not imply a single monotone threshold in the full application.
Alarm pending also repeats its timing check twice. Actual observations must
be matched to the first failing iteration/assertion and any service delay.

The counter source already motivates phase-dependent bounds and the possible
post-failure -EBUSY cascade; see `REFERENCE_DESIGN_DRAFT.md` and the earlier
`INTERPRETATION_GUARDS.md`. A later case's primary failure is still counted
as observed, but is not an independently demonstrated waiting defect.

Final per-case tables must lead with supported source-derived bounds or
explicitly label the absence of a single scalar boundary, then show measured
pass/fail transitions and reference/replay status. Do not promote a passing
relaxed reference to proof that an original rate-contract check was brittle.
