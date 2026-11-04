# Fixed-setting F4 full-application repeatability protocol v1

Preregistered 2026-11-04 before any fresh repeatability process. This is a new,
independent experiment authorized by the user; it neither reruns the completed
100-frequency schedule nor changes any existing repair study. Outputs, jobs and
protocol are separate from counter-repair3552460-3552463. No paper result from
the added counter-repair subject is written until that job chain is verified.

## Question, fixed subjects and cells

Do unchanged full F4 applications produce mixed explicit selected-case pass/fail
verdicts at a fixed oscillator setting across30 fresh Renode processes?
No new source, build, driver, model, fault, or model generation is involved.

| Full application | Selected case | Fixed LSI inputs, Hz | Repeats per cell |
|---|---|---|---:|
| RTC API |rtc_api.test_alarm_callback|23673;23847;32000|30|
| RTC-only counter basic |counter_basic.test_all_channels|29143;29352;32000|30|

There are exactly6 cells and180 new launches. Each launch runs the entire
unchanged application in its original case order, in a new Renode process.
This does not isolate a case, randomize phase, or perturb scheduling. All other
case verdicts, including downstream cleanup outcomes, are retained as context.
Case-frequency selection came from the user's request and archived boundary
records, not from new outcomes. The nominal32000-Hz setting is absent from the
100 sampled production inputs; it is verified against five archived nominal
qualification runs using the same exact ELF. Do not mislabel it a seeded slot.

## Verified frozen inputs

`input_verification.json` contains exact record, trace, UART, platform, build,
resource and ELF checks performed locally before sealing this protocol.
Production plan SHA256:
`719b3bc42f2b93f44455a11eca3eacd69eacbbf4e8c714b90300d5a8343d0612`.

- RTC full-application ELF:
  `f7361cc795f36cc56a611776ee8ce7f631fcaa0b0ab616177f339eb7074796d7`.
- Counter full-application ELF:
  `ceda84d8a03383be5857e546d2ac87ecd2ed9c72c9e45bf0ca47661437c7ccb1`.
- Zephyr commit3568e1b6d5cdd51a6b964a2a1d6d29200fea2056; original tests,
  overlays, RTC-only counter configuration and callback code are unchanged.
- Calibrated SIF SHA256:
  `94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.
  Renode v1.17.0, Linux build1.17.0+20260907gitf1dd1b4af, .NET8.0.21.
- CPU16MIPS, SysTick16000000Hz, quantum1000ns, observation step500000000ns;
  base F4 platform and STM32F4 RTC model unchanged. The selected LSI frequency
  stays fixed within each cell. These are simulated clock settings, not measured
  silicon values. CPU/MIPS here is the pinned S2 setting, not the HSI context arm.
- RTC application ceiling180 virtual seconds /900 host seconds; counter600
  virtual /1800 host seconds, unchanged from S2. Task timeout and missingness
  policies are fixed before execution, not increased after a result.

The adapter calls the hashed original S2 `run()` simulation implementation.
Only condition/index/output paths identify new records, and an outer metadata
file associates each launch with its sealed cell and repeat number. There is
no source instrumentation, new random seed, phase reset, callback delay or
internal run-loop change. The same logical ELF/model paths are mounted read
only; only the output directory is overlaid with new SCRATCH storage.

## Schedule and sealed TACC cost

`plan.json` enumerates every index before execution. Within each application,
repeat number0..29 is outermost and the three frequencies are interleaved in
ascending order; no adaptive scheduling or early stop after concordant results.
32 TACC Launcher workers pack runs onto one whole node. Launches may overlap;
virtual simulation settings remain fixed. A private container home/cache/tmp
and fresh process are used for every launch. The two jobs are independent of
the counter-repair chain; counter repeats may depend only on completion of the
RTC repeat job to respect development queue limits.

AllocationTRA25006, development queue, pinned modules tacc-apptainer/1.4.1 and
launcher/3.10. No normal-queue submission is authorized by this protocol.

| Job | Launches | Nodes | Workers | Wall limit | Estimated SUs | Reservation ceiling SUs |
|---|---:|---:|---:|---|---:|---:|
| F4 RTC repeats |90|1|32|01:30:00|0.727864|1.5|
| F4 counter repeats |90|1|32|02:00:00|1.714042|2.0|
| Total |180||| |2.441906|3.5|

`COST.json` seals the arithmetic:1.5 times the sum of30 times each cell's maximum
archived host wall time, divided by32 workers, plus one original task-timeout
tail and900s setup/hash/audit/packing allowance. It is an estimate, not a runtime
guarantee; queue wait is excluded. TACC documents1SU per development node-hour,
minimum0.25h billing,128cores and256GiB per node:
https://docs.tacc.utexas.edu/hpc/6lonestar/running/
https://docs.tacc.utexas.edu/hpc/6lonestar/system/

Maximum archived peak RSS is334932KiB;32workers with1.5 memory safety use a
16076736KiB budget (about15.33GiB), below80% of256GiB. Record actual resource
usage and Slurm accounting; do not substitute estimates for observed costs.

## Outcome and missingness rules

For each planned index retain raw UART, monitor, platform, trace, record,
resource, process exit and outer provenance, including node, job ID, image hash
and Apptainer version. Report counts of pass, fail, skip and missing for each
of six cells, summing to30 per cell. Also export all application case vectors.

Primary selected-case verdict is evaluable only if the full application
completes without a harness error, expected case names appear exactly once,
and the selected case has one explicit PASS/FAIL/SKIP. Otherwise classify this
launch as missing, retain its partial vector, error and process exit, and give
the reason. A timeout, crash, absent/ambiguous verdict or infrastructure error
is not a selected-case failure. Never drop a planned launch, rerun a finalized
missing outcome, replace an archived record or select the better run.

Mixed PASS and FAIL within an otherwise identical cell is observed same-setting
flakiness in that cell under this model. Compare skips separately; varying
capability outcomes are not silently collapsed into passes. If all30 explicit
verdicts agree in every cell, report **no observed same-setting flakiness**.
Do not claim rare flakiness is ruled out or estimate a device-population rate.
If outcomes are missing, say how many are evaluable and do not assert that all
30 agreed. Between-cell pass/fail changes alone remain timing sensitivity.

Compare normalized trace observations/registers and UART bytes where useful,
excluding run IDs/provenance from semantic comparison. Raw trace hashes contain
new run IDs and need not equal archived hashes. Hash equality is an integrity
check; the pass/fail analysis uses explicit selected-case verdicts.

## Storage, integrity and stop rules

Register this study in a dated DESIGN.md amendment before execution. Seal this
protocol, COST.json, input verification, task list and all execution-code hashes.
Commit/push on the Mac and git pull only on LS6. Do not edit code on LS6.
Do not stage, clean, overwrite or resubmit any counter-repair files/jobs.
Check their active input seal and original ELFs before and after each repeat job.
All30,067 protected original files must remain unchanged. Any source/ELF/model/
clock/seal mismatch stops execution, preserving evidence rather than repairing
inputs in place. Scientific or harness logic corrections require a new dated
amendment and namespace; no automatic replacements.

Use node-local/tmp for caches/runtime and SCRATCH for loose outputs. Each job
packs and verifies its complete or interrupted output into one new WORK archive
with a full member/hash inventory and sidecars before success. Check WORK
headroom at entry and publication. No prune is requested. Never leave final
records only on SCRATCH. Keep original build records and ELFs read only.

SSH is always bounded BatchMode. Stop remote access on authentication/MFA,
dropped connection or stalled I/O; user reconnects. No credential handling.
If submission acceptance is uncertain, inspect receipt/queue before retrying.
No study worker is automatically requeued or rerun.

## Timelines and follow-up

Prepare one evidence-linked timeline per test from the retained archived and
repeat traces and exact source lines. Mark simulator observation time, UART's
kernel-reported case duration, and source-based ideal timing separately. Sampled
UART exposure is not the timestamp of callback delivery. The existing traces
have no direct subsecond-phase or callback-entry timestamp; do not infer a
measured one from a verdict boundary. Do not instrument these unchanged ELFs.

After counter-repair3552460-3552463 all finish, send the user's exact follow-up
prompt saved as `COUNTER_FOLLOWUP.txt`. Their collection, replays/references and
manuscript update belong to that follow-up, not to this repeatability execution.
