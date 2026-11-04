# Fixed-setting repeatability status, 2026-11-04

## Current recovery checkpoint: accepted3552869/3552870

The human approved path-only recovery and4.0SU combined ceiling. Registered
recovery details and authoritative new receipts are in
notes/fixed_repeatability_recovery_2026-11-04_v1/STATUS.md and submission_receipt.json.
Old3552681/3552682 are verified preflight failures with zero started indices.
Do not resubmit or reinterpret them as scientific verdicts. Original packet
and frozen code stay unchanged. The new jobs use the intended v10image path.
Earlier checkpoints below are historical.


## Latest manual check: repeat jobs FAILED at preflight; counter chain PENDING

A human-requested BatchMode check succeeded. Both3552681 and3552682 are FAILED
(exit1:0). The four counter-repair jobs3552460-3552463 remain PENDING at this
check. Read logs and independently verified both failed packed archives, each
with6inventory entries and30,067 unchanged protected files. Both stopped at
coordinator.py:14, before Launcher/Renode/any primary record. All180scheduled
indices are not started, not scientific pass/fail outcomes. No flakiness
conclusion is supported. The submission helper selected the old v9SIF path
while the sealed hash requires v10. The correct image sidecar is at
tacc_work/20261023-v10/images/rtc-ls6-v1.sif.sha256. No input was changed and
no job was resubmitted. Recovery needs a new dated infrastructure amendment,
new paths/receipts and approved cost before execution; keep these failed
archives. Counter repair jobs/code/inputs and paper remain untouched.


## Latest checkpoint: watcher PAUSED, 2026-11-04 16:25 Central

The scheduled read-only BatchMode sacct check was rejected with password/MFA
instructions before returning current job states. Remote access stopped and
the watcher was confirmed PAUSED. No pull, submission, cancellation, archive
transfer or experiment action occurred. The six accepted jobs remain untouched;
their current states are unverified in this check. Human reconnection and a
working BatchMode confirmation are required before resume. Earlier submitted/
ACTIVE checkpoints below are historical.


## Current checkpoint: submitted; watcher ACTIVE

RTC repeatability job **3552681** and counter repeatability job **3552682**
were accepted on development/TRA25006. Each packs90full-application launches
on one node with32Launcher workers. Wall limits1.5h and2h; estimated costs
0.727864SU and1.714042SU, total2.441906SU; total ceiling3.5SU.
Counter repeats depend only afterany:3552681, not on3552460-3552463.

The guarded git pull matched Mac/LS6 HEADb48da832. Active counter execution-code
hashes match before/after the pull, and the repeat plan seal matches. Receipts
were returned with rsync into submission-returned-v1 and reconciled in
submission_receipt.json. Never resubmit an accepted or uncertain job.
No paper edit or fourth-case result has been made. Earlier preparation/access
notes below are historical; this submission checkpoint supersedes them.


Preregistered and sealed before execution. Six cells x30repeats=180planned
fresh full-application launches, unchanged archived F4 ELFs. Input verification
covers4boundary records and10nominal qualification records. Same ELF hashes
in nominal and boundary runs. Source-linked baseline timelines are prepared.

Plan SHA256:9c19539dcdf8df60b945debfa2fc69e721021bf80b87e157a1a80dacaa93a613
Protocol SHA256:8871169a60dbb37b3be2aa52d668b5a5ba609a35aca8c16b5ca5b7c63ccd7da2
Registration commit:03a671be (full hash available via Git).

Two development jobs are prepared but **not submitted**. Budget estimate
2.441906SU, reservation ceiling3.5SU (one1.5h RTC node and one2h counter node).
32Launcher workers, pinned tacc-apptainer/1.4.1 and launcher/3.10, TRA25006.
No normal-queue submission. All runtime/output/packing follows SCRATCH/tmp to
verified WORK archives. No builds or extra repeats are requested.

The first BatchMode status check failed authentication. After the user
reconnected, read-only checks verified all4counter-repair jobs3552460-3552463
PENDING, unchanged LS6 HEAD2e8d7c4, original production build products present,
calibrated image path and development queue limits. Before the prepared code
pull could execute, a second BatchMode connection failed authentication.
Remote access stopped; no repeatability job was submitted, no code pull ran,
no original or counter-repair input was changed. Await user reconnection.

After reconnection: perform the prepared guarded git pull (compare active
counter-repair code hashes before/after; no changes expected), verify plan
identity and matching Mac/LS6 HEAD, and submit the two independent development
jobs under a new tacc_work/20261104-fixed-repeatability-v1 namespace. Record
receipts to avoid duplicate submissions. The active counter-repair chain must
never be resubmitted, canceled, resealed or cleaned by this workflow.

The local protected audit passes all30,067 original files. main.tex and main.pdf
remain byte-identical to the published manuscriptv2. No fourth-case results
are inserted. Finalized missing repeatability verdicts remain missing.

The separate30-minute follow-up watcher was created PAUSED (id
verify-f4-repeatability-and-deliver-counter-repair-follow-up). It must not make
remote retries before the human reconnects and it is resumed. RUNBOOK.md records
the exact continuation, receipt and independent archive-verification steps.
Offline archive/report verifiers are ready; no fresh outcome exists yet.

## Reconnection check, 2026-11-04T15:46:54.118406-06:00

The human authorized pull/submission after reconnecting. The first bounded
BatchMode read-only status/receipt check was again rejected with password/MFA
instructions before any remote command executed. Remote access stopped. No
git pull or repeatability submission occurred; watcher remains PAUSED. The
human was asked to verify a BatchMode connection-ok command in their terminal.

The new watcher is now confirmed ACTIVE on its30-minute schedule, with
failed-runs-only notifications preserved. Latest sacct verifies3552681,3552682
and all four counter-repair jobs PENDING. Never pull LS6 or change sealed code
while either repeatability job is pending/running. No fresh verdict yet.

Watcher resumed only for read-only monitoring of the four pending counter-repair
jobs and eventual delivery of the saved follow-up. The failed repeatability
archives are already verified; recovery proposal awaits human cost approval.
No retry, scientific result or manuscript change is authorized from the watcher.
