# Proposed path-only infrastructure recovery, 2026-11-04

Status: prepared for review, **not registered or authorized for execution**.
No old submission helper, protocol, task list, source, ELF or record is changed.

## Evidence

Both accepted development jobs3552681/3552682 failed the actual SIF SHA256 check
at coordinator.py:14 before Launcher or any Renode process. Their independently
verified archives each have6entries, zero primary records, and unchanged30,067
protected files before/after. All180planned indices are **not started**.
This supplies no same-setting flakiness evidence or test pass/fail verdicts.

Cause: the helper mistakenly selected tacc_work/20261022-v9/images/rtc-ls6-v1.sif.
Its existing sidecar says831dffc44d479a06ed7945a68bd746302319d2160edb19d731e3f0cd380d4239.
The intended/calibrated SIF is already present at
`tacc_work/20261023-v10/images/rtc-ls6-v1.sif`; its sidecar and image.json identify
94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1,
the exact hash sealed by the original study. Full actual-image hashing remains
a compute-node preflight gate; it is not weakened or skipped.

## Concrete proposed changes

`submit_proposed.py` is a new, uninvoked helper. It changes only:

- The selected physical image path from v9 to v10.
- New submission intent/receipt/log namespace, v2, and distinct job names.
- A lightweight pre-submit image-file/readability and existing hash-sidecar/
  image.json check. The compute-node full SHA256 guard still decides validity.

The worker, original S2 simulation, protocol, cell list, frequencies,30repeats,
source/ELFs, CPU, SysTick, model, observation step, quantum, and per-task limits
all remain byte-identical. The original sealed packet is reused read only.
The two old failed archives/intents/receipts remain untouched. No retry fills
or replaces an old verdict; no evaluation ever started in those jobs.

Before execution, append a dated infrastructure amendment to DESIGN.md, seal
this helper/change list and new output namespace, commit/push from the Mac,
pull only when no active repeatability job uses the checkout, and verify the
active counter-repair input hashes again. Never touch3552460-3552463.

## Cost requiring approval

Fresh recovery jobs retain the original one-node32-worker budgets:
RTC1.5h (estimate0.727864SU), counter2h (estimate1.714042SU).
Fresh reservation ceiling:3.5SU; fresh estimate:2.441906SU.
The two failed short development jobs imply0.5SU total under the documented
0.25node-hour minimum per job (accounting to be confirmed), so the combined
ceiling becomes4.0SU, above the original3.5SU reservation ceiling.
Request approval for this path-only recovery and increased combined ceiling
before submitting. Do not shorten timeouts or discard planned repeats merely
to conceal the infrastructure cost.
