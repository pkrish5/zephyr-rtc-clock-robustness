# Counter-repair diagnostic verification, 2026-11-11

Registered before generating reference sources, building, or running a new
diagnostic. This completes the representative replay/reference/control work
required by the frozen 2026-11-04 counter-repair protocol. It is not a new repair
arm or replacement for any primary outcome. Original scientific sources, plans,
ELFs, forecasts, 334 repair records and the 180-repeat pilot remain unchanged.
No E2, new driver, hardware study, generated-test arm, delay injection, new fault
operator, margin tuning, or repeat of the full clock schedule is authorized.

## Sealed selection, from already verified primary records

1. For each V1/V1b/V2, replay the unchanged full application at the 17-kHz legal
   endpoint, its sole legal frequency with a single-shot callback-count failure
   and no short-relative failure, and the passing 47-kHz endpoint. These are
   nine representative legal diagnostics. Preserve every original task field,
   including its index, same ELF, simulator setup and full-application order.
2. Replay all eight original V0/V1/V1b/V2 oscillator-probe tasks once: 10 and
   64 kHz. There are 17 replay processes in total. No diagnostic replaces a
   primary, missing outcome or original replay. A mismatch stops interpretation
   and blocks subsequent reference evaluation; preserve both observations.
3. Reference evaluation covers the union of all legal frequencies where the
   repaired full applications report any assertion failure, plus 47 kHz as a
   passing endpoint. Shared references may cover several primary case slots;
   this is coverage, not independent replication. Keep exact links to every
   residual failing case. Expected union: 16 failing frequencies plus 47 kHz.
4. An independent counter-progress control runs at the already used 10-, 32-
   and 64-kHz inputs. These diagnose activation of the existing oscillator
   probes; they do not introduce a new fault or claim a device distribution.

The exact indices, frequencies, record/ELF/build/log hashes and failure signatures
are frozen in selection.json before any new source or execution. Selection uses
source assertion classes, not individual loop-count numbers, and is not random.

## New task-specific functional reference, specified before generation

One new functional-reference application has three cases, with explicit clean
state and unconditional fixture cleanup between cases:

- All-channels: preserve the earlier verified reference's two-tick request,
  supported/unsupported channel behavior, callback ID/user-data/ISR/counter checks,
  independent-time premature check, bounded completion, and cancellation.
- Short-relative: request one tick 100 times sequentially, retaining cumulative
  counts and requiring each next alarm to be accepted after callback without an
  intervening manual cancel. Require the callback count to equal each iteration's
  target exactly; reject duplicates, identity/context errors, premature delivery,
  and callback counter progress shorter than the requested tick. This reference
  changes the waiting policy, not the operation/count property. Cleanup occurs
  after the case, including on assertion failure.
- Single-shot: preserve the existing clean-state two-tick reference and its
  additional three-second no-repeat observation. It diagnoses delivery independent
  of the original preceding case's leftover state, not phase equivalence.

Use 20-ms non-destructive polling and SysTick-derived uptime. For one requested
tick, the driver compensation gives a one-to-two physical-tick arrival interval.
Set the reference ceiling to ceil(3*32000/17000+5)=11 simulated seconds and the
earliest threshold to floor(32000/47000*1000)-2=678 ms. For two ticks, retain the
earlier ceiling13 s and earliest1360 ms. The extra uncertainty tick and five
seconds are experimental allowances, not certified ISR/service-latency bounds.
Check the deadline before accepting callback completion. Record reference
callback elapsed times separately; no primary ELF is instrumented. Reference
phase/order need not match the upstream application. A reference failure or
missing outcome blocks a reference-supported brittleness conclusion and is
retained as an unresolved firmware/model/property question, not tuned away.

## Independent oscillator-activation control

A separate new control application reads the RTC-only counter, requests no alarm,
and polls until at least five counter ticks of progress. Capture elapsed uptime
and actual tick delta; stop at20 simulated seconds. Print both values. With
unknown initial phase, delta d gives an ideal ((d-1)*32000/f, d*32000/f] interval;
allow2 ms uptime quantization below and22 ms polling/quantization above. For
d=5, expected bands at10/32/64kHz are12.8–16s,4–5s,2–2.5s respectively, before
the declared observation tolerance. These are model/source-derived intervals,
not observed outcomes. Check disjoint slow/nominal/fast bands against the raw
measurements and exact platform/model hashes. A violated band is unresolved;
do not redefine its tolerance after observing results. The control independently
checks clock progress, not callback-entry phase or arbitrary delivery delay.

## Execution and account

Use the pinned v10 SIF hash
94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1,
Renode1.17.0/.NET8.0.21, Zephyr3568e1b6d5cd, the original F4 RTC-only configuration,
CPU16MIPS, SysTick16MHz, quantum1000ns and0.5-s RunFor observation. Reuse the
original S2 build/run function bodies unchanged. New outer adapters may select
development and CCR26073 truthfully; no account or partition is spoofed. Original
counter worker's normal-only entry wrapper is not changed; the same frozen run()
body is imported directly by the new replay adapter after checking all its seals.

One development job, -A CCR26073, one whole node,32Launcher workers, two-hour
limit,2-SU reservation ceiling. This uses the standing development authorization;
no normal submission is covered. Any normal job requires a concrete cost report
and approval. The user requested use of the newly available CCR26073 allocation.

Build two diagnostic ELFs (functional reference and progress control), using two
parallel builds with two compiler workers each. Require five complete passing
nominal launches per new ELF (10 qualification processes). Then run17 replay
processes, compare full case vectors, UART and normalized traces with the saved
primaries, and only on agreement run17 functional legal references plus the two
10/64-kHz progress controls. The five nominal control launches supply the32-kHz
control condition. Total46 diagnostic processes, two builds. No adaptive repeats.
Keep every pass/fail/skip/missing and any unstarted phase separately. Nominal
qualification or replay anomaly blocks later phases. Evaluation reference/control
failures remain data, not infrastructure-retry opportunities.

Functional references:700 virtual seconds /3000 host seconds per process.
Progress controls:40 virtual /900 host seconds. Replays retain the exact original
600 virtual /1800 host ceilings. These are new diagnostic process budgets, not
edits to any primary wait. The cost estimate uses a conservative5host seconds
per expected simulated second, the longest selected primary replay with15%
overhead,600host seconds for two concurrent builds, and900s setup/packing.
Exact arithmetic and critical-path assumptions are saved in COST.json before
submission. A job timeout preserves partial evidence; it does not authorize
replacing a finalized missing result.

## Infrastructure-only account adaptation and storage

Do not edit frozen harness/tacc_storage or any existing source. New namespace
copies of runtime.sh/run_packed.sh change only the accepted account to
CCR26073/ccr26073 and the runtime source path. Verify those exact mechanical
diffs against their original hashes. Actual SLURM_JOB_ACCOUNT remains unchanged
and is recorded. Use pinned tacc-apptainer/1.4.1 and launcher/3.10. All builds,
caches, temporary directories and loose records use SCRATCH or node-local/tmp;
kept ELFs, build logs and config products are packed and verified on WORK.
Check file headroom before execution and publication. No deletion or pruning.

Check all30,067 protected originals, the764 active counter input/code seals,
four original ELF/build hashes, and new protocol/source/code seals before/after.
Source/ELF mismatch stops execution and preserves evidence. Use exclusive
submission intents/receipts; never resubmit an accepted or ambiguous job.
All new scientific changes after an observed gate require a new prior amendment
and human review. Infrastructure-only fixes may use the standing development
rules, with logged before/after hashes and at most three consecutive failures.
Stop remote access on any SSH credential/MFA/authentication failure, drop or
stalled I/O. Bounded BatchMode only; never authenticate or alter SSH settings.
No LS6 edits/push. Paper TeX/PDF remain unchanged until verification is complete.
