# Same-spec human author packet (prepared 2026-10-08; no recruitment)

This packet is a proposed baseline, not a completed study. The six files in
[`specs/`](specs/) are byte-for-byte copies of the frozen RTC prompts given to
the model IDs, with hashes in [`spec_manifest.json`](spec_manifest.json).
Each task has a range-absent and range-present version. The range-present
version includes the numerical LSI context. Assign exactly one file to an
author for each independent submission; keep task and condition labels hidden
until submission if possible. Do not show authors generated source, upstream
source, scores, reference tests, or earlier submissions.

## Author instructions to accompany the assigned prompt

1. Read only your assigned prompt. Return exactly the JSON object it requests,
   with a single `test_c` field holding one complete C ztest source. Do not
   change the task's required behavior, board, or build configuration.
2. Write independently. Do not compile, run, use an LLM, inspect local Zephyr
   source, or consult other participants during authorship. The original model
   calls had no tools or local-file access. Record whether this restriction was
   followed rather than silently excluding a submission.
3. Submit one final source per assigned attempt, with no post-feedback edits.
   A malformed JSON or noncompiling source remains an attempt. Record author
   pseudonym, assigned task/condition, prompt SHA-256, start/end times,
   assistance/disclosure, and final response SHA-256 in the submission
   manifest. Do not collect a real name in the analysis ledger.
4. No participant has been recruited or assigned. The authors must approve
   recruitment, assignment, consent/privacy handling, and compensation
   separately.

## Evaluation steps after a submission is frozen

1. Save the raw response and extracted `test_c` without repair. Hash both.
   Validate the one-field schema and preserve invalid responses as failed
   attempts. Store each submission in a new namespace; never overwrite
   `generated/spec_context_factorial_v1` or existing result files.
2. Apply the same pinned Zephyr v4.3.0 task build configuration, RTC alias
   overlay, board `stm32f4_disco/stm32f407xx`, and source-only build gate
   used by `harness/phase2/build_factorial.py`. Save build logs and ELF hash.
   A small adapter and new manifest are needed because the frozen factorial
   runner addresses its existing suite paths; do not point it at a human
   submission by modifying its lock.
3. Judge functional adequacy against the *assigned frozen specification*
   before varying the clock, with timing-bound adequacy recorded separately.
   Preserve `met`, `not met`, and `unknown`. For built, functionally
   adequate submissions, run five fresh nominal launches at the same 16-MIPS
   RTC configuration, recording every original verdict. Only five passes
   enter the legal-clock arm.
4. For eligible submissions, use the frozen 100-seed LSI map and both 17-kHz
   and 47-kHz endpoints in fresh Renode processes, with the same CPU, SysTick,
   quantum, platform variant, observation horizon, and selected-case parser
   as `harness/rtc_factorial_v2.py`. If a forecast/sample design is chosen
   instead, register it before any varied run and label unrun suites as
   predictions or unknowns. Do not replace missing verdicts with diagnostics.
5. At nominal clock, challenge each eligible source with the same fast and
   slow oscillator probes and validated nonarrival operator. Callback and
   pending sources also receive the signed alarm-offset probes; counting
   sources are non-activation controls. A kill requires an active operator
   and an explicit selected-case assertion failure. Store fault ELFs, hashes,
   raw records, and replay traces separately from existing cohorts.
6. Report all submitted attempts in the denominator, with build, functional,
   nominal, measured clock, forecast-only, missing, and fault outcomes
   separated. Compare by task and prompt condition before pooling; authors
   and suites within a task are clustered.

The existing harness modules define the experimental settings, but this
packet does not claim a ready-to-run human adapter. Preparing or executing
that adapter requires a new, reviewed protocol and new result directories.
