# Proposed counter-repair execution recovery, 2026-11-05

Approval is pending. No normal submission is authorized by this file.

Read-only diagnostic 3558303 completed 0:0. Its independently verified archive
has 902 entries, SHA256
`02f6edcd2a6a42b29aa50bf7c8042f21d7b384293aacd1eb2c4b35c111b9f8aa`.
Four saved build records, ELFs, logs and config products passed verification;
all 764 active seals and 30,067 protected originals were unchanged. It found
zero existing primary records. Module/container startup worked on c302-006.
The earlier c314-191 module-path failure is retained; its precise system cause
has not been established. No specific node is requested or excluded.

Reuse the four original built ELFs and byte-identical build records; no rebuild.
Preserve the original scientific plan, sources, Renode model/image/run function,
CPU/SysTick/quantum, timeouts, full-application order, deadlines and fault inputs.
Run only the originally unstarted indices, never the archived V0 legal schedule.
The four original jobs remain untouched, including failed/pending states.

|New group|Original task indices|Launches|Nodes|Wall limit|Estimated SU|Ceiling SU|
|---|---|---:|---:|---|---:|---:|
|gate|0–19|20|1|01:00:00|0.665400|1|
|legal-a|20–172|153|1|03:00:00|2.326996|3|
|legal-b|173–325|153|1|03:00:00|2.326996|3|
|fault|326–333|8|1|01:00:00|0.665400|1|

All jobs use normal, -A TRA25006, 32 Launcher workers per whole node. Estimated
total is 5.984790 SU (about 6); maximum requested node-hours are 8 SU. The prior
0.25-SU diagnostic ceiling is separate. These are planning estimates, not
observed repair runtimes. Formula: ceil(launches/32) times the largest measured
original counter-repeat process (1300.38 host s), times 1.15, plus 900 host s
per job for hashes/setup/packing, divided by 3600. Each process retains its
original 1800-host-second limit. Memory/concurrency stays at the calibrated 32.
TACC normal rate: 1 SU/node-hour, minimum 0.25 h/job, verified in its official
Lonestar6 guide and job-accounting page on 2026-11-05.

First run the 20 nominal gates. Every expected case must appear once, with no
harness error, missing/duplicate case or assertion failure; selected all-channels
must pass in all five launches per variant. Downstream groups are permitted only
after this packed gate archive is independently verified and the gate job
finished successfully. Each downstream compute coordinator also verifies that
archive and its full case vectors before launching. A failed gate stops the
chain; no source tuning or automatic retry.

The infrastructure fix uses the existing pinned storage runtime to initialize
tacc-apptainer/1.4.1 and launcher/3.10 and verifies Lmod path readability before
simulation. It does not source legacy common.sh or rerun login initialization
inside every Launcher task. Each unchanged sealed worker runs in the same SIF
with original logical read-only bundle/model/source paths. A new SCRATCH output
overlay contains hash-checked copies of kept original ELFs/build records. Private
container homes/tmp/caches are node-local. No loose outputs are written to WORK.
Every job publishes a verified packed archive with protected before/after
checks and fresh headroom checks. No prune, old output deletion or in-place fix.

Record each planned outcome including missing, outer process exit, full case
vector, exact task/ELF/source/image/module/job/node provenance and all trace/log
hashes. Existing records stay unchanged. New missing outcomes are never rerun
or replaced. Legal failure replays, fault activation/reference checks and final
paper edits are later verification steps under the original scientific protocol;
the primary jobs alone do not establish repair success. No E2, new driver,
generation, additional fault operator or new repeatability experiment.

Stop on any input/hash mismatch, unexpected original primary record, failed gate,
or three consecutive infrastructure failures. Submission intents/receipts are
exclusive and never removed; uncertain acceptance is inspected, never blindly
retried. No submission helper runs unless an explicit human approval record
matches this plan and the 8-SU ceiling. Bounded BatchMode only; stop on access
problems. The existing watcher cannot submit jobs or execute this recovery.
