# All downstream primary records verified, 2026-11-10

Jobs3570473/legal-a,3570474/legal-b,3570475/fault each COMPLETED0:0.
Exactly12packed files returned to returned-downstream-20261110-v1; authoritative
Slurm snapshots are saved there. verify_execution.py independently verified
archives into verified-3570473-v1,verified-3570474-v1,verified-3570475-v1.

Selected all-channels outcomes:legal-a153pass,legal-b153pass,fault5pass3fail;
zero selected skips/missing. Each repaired variant V1/V1b/V2 passes102/102same
legal settings, including all44archived V0 failing settings. This is one upstream
subject under3interventions, not306independent tests. The full application is
not uniformly passing:per variant short-relative88pass14fail;later single-shot
87pass15fail. Compared with archived V0,29of44later failures become passes and
15remain. Short-relative was previously skipped at44baseline settings; it is
now observed passing30/failing14 there. No failure cause is finalized here.

Slow10kHz selected primary probe:V0fail,V1pass,V1bfail,V2fail;all four64kHz
fast probes pass. Preserve V1's slow-probe pass. Activation/reference/control
checks and representative failure replays remain separate follow-up work before
scientific repair/detection/cascade claims or paper edits.

Primary handoff:primary_handoff_20261110_v1/HANDOFF.md,summary.json,exact paired
outcomes and primary record/UART hashes. All3archives have unchanged30067protected
originals,valid764seal input guards,4unchangedELFs,and valid verified gate links.
No new jobs,LS6pull,prune,source/record edits or paper changes occurred. Current
job monitoring is complete; no further polling of these terminal jobs is needed.

---

# Access paused after scheduled check, 2026-11-09 23:29 Central

The first tool permission review timed out before process creation; the one
explicitly allowed review retry then launched one bounded BatchMode SSH check.
That check returned TACC password/MFA instructions and Permission denied,
exit255, before any Slurm state. Remote access stopped immediately; watcher
update confirmed PAUSED. There was no automatic retry of a remote connection.
Jobs3570473/3570474/3570475 are already accepted and remain untouched. Current
states are unknown; earlier PENDING states are historical. Human reconnection
and confirmation are required before further monitoring or transfer. No job,
sealed code, raw evidence or manuscript was changed. Never resubmit these jobs.

---

# Downstream access paused, 2026-11-09 17:04 Central

Scheduled bounded BatchMode check of3570473/3570474/3570475 returned TACC
MFA/password instructions and Permission denied, exit255, before any Slurm state.
All remote access stopped. Automation update confirmed PAUSED. No retry,
submission, cancellation, transfer, or sealed code/evidence/paper edit occurred.
The three jobs are already accepted; never resubmit. Their current states are
unknown; PENDING Priority is historical only. Human reconnection/confirmation
is required. The independently verified gate qualification hash and saved
accepted downstream receipt remain intact. Resume read-only monitoring and
verification after confirmation, preserving every missing outcome.

---

# Access paused, 2026-11-09 13:11 Central

Scheduled bounded BatchMode status check returned password/MFA instructions and
Permission denied (publickey,keyboard-interactive), exit255, before Slurm state.
Remote access stopped immediately; automation update confirmed PAUSED. No job
was submitted, resubmitted, canceled or changed. Current gate state is unknown;
PENDING is the last verified historical state only. Human reconnection and
confirmation are needed before another remote check. Never resubmit3569909.

The newer conditional watcher authorization below remains valid for exactly
legal-a/legal-b/fault within8SU after all20gate outcomes independently qualify.
It does not permit submission before qualification, and none occurred this wake.
Original records and paper remain untouched. No automatic authentication/retry.

---

# Approved nominal-gate job3569909 submitted; PENDING

Normal/TRA25006,1node,32Launcher workers,1hour,20fresh nominal launches;
estimate0.665399SU and1SU ceiling within the approved8SU chain. The accepted
receipt and exclusive intent were returned to submission-gate-returned-v1/;
summary submission_receipt.json. Never call submit.py --group gate again.
Last verified sacct:3569909 PENDING0:0. No scientific gate result is available.

Matching clean Mac/LS6 submission HEAD93ab81e7d1f5b2de933e7576de0724190f53fba5
was verified, with original active counter code unchanged before/after pull.
Keep this LS6 execution code sealed: no pull while recovery jobs pending/running.
The new verify_execution.py is a local offline verifier, outside the execution
seal; it does not change any simulation. All originalELFs/tests/plans unchanged.

After terminal status, return four packed files with stem
3569909-counter-recovery-gate into a fresh local returned directory. Save the
verified sacct state/exit in a JSON with job_id,state,exit_code, then run:
python3 notes/counter_repair_execution_2026-11-05_v1/verify_execution.py --returned <fresh-returned> --job 3569909 --group gate --sacct-json <saved-state.json> --out <fresh-verified>

Only qualification.json with passed:true after20complete passing nominal vectors
permits downstream submission. Any missing/error/assertion/hash discrepancy stops
the chain and is retained; no source tuning, outcome replacement or automatic
retry. Approved downstream groups are legal-a153runs/3h,legal-b153runs/3h,
fault8runs/1h,1node32workers each, together within8SU. No further permission is
required within this approved scope, but the read-only watcher cannot submit
normal jobs; the main workflow must do so after independent gate verification.
No downstream job, old-job cancellation, new scientific condition or paper edit.

---

# Conditional recovery approved, 2026-11-09T12:05:16.310349-06:00

The human replied “yeah repair” to the concrete conditional proposal. Approval
is recorded in approval.json for exact plan SHA
037f96a96a1596ced1e82e6a379641ca959a31d36aa3c24fb67b6649835fc1fc:
normal/TRA25006, four one-node jobs,32Launcher workers;20nominal gates1h,
153legal3h,153legal3h,8fault1h; estimate5.984790SU, ceiling8SU. The earlier
diagnostic ceiling0.25SU is separate. No additional normal approval is needed
for these groups within this scope, but every downstream submission remains
blocked until all20nominal gates pass independent verification.

Original scientific plan, four ELFs, settings, workers and original jobs remain
unchanged. Publish/pull this approval, verify the original code/plan before and
after pull, then submit gate ONCE and retain its exclusive intent and receipt.
Do not invoke a helper again if acceptance is uncertain. Do not change sealed
execution code or pull LS6 while a recovery job is pending/running. Existing
watcher may monitor/verify only; it cannot submit or cancel normal jobs.

Read-only30-minute watcher is confirmed ACTIVE for existing3569909. It stays
quiet on pending/running and verifies returned evidence after terminal state;
it cannot submit downstream normal jobs. Local offline verifier is syntax
checked and excluded from the sealed execution manifest, which remains unchanged.
All20Mac counter seals and paper source/PDF hashes checked unchanged after setup.

---

# Conditional watcher submission authorized, 2026-11-09

The user subsequently asked to make the active 30-minute watcher submit the
required follow-up jobs automatically. Its prompt is updated and ACTIVE. This
supersedes the earlier read-only-watcher restriction only for the three already
approved groups (`legal-a`, `legal-b`, `fault`), after independent verification
of all 20 nominal gate launches from job 3569909. The watcher checks existing
Slurm jobs and exclusive submission intent/receipt files before invoking the
sealed helper once per group. It stops on failed or ambiguous verification,
submission, or access; it never retries the gate or an uncertain submission.
The original scientific plan, execution code, sources, ELFs, and 8-SU ceiling
are unchanged. No follow-up job has been submitted at this checkpoint.

---

# Gate verified and follow-ups submitted, 2026-11-09

The scheduled watcher paused after an SSH authentication failure at 13:11
Central. A bounded SSH check in the active user chat subsequently succeeded.
Gate job 3569909 finished COMPLETED 0:0 at 13:23:47 Central. Its four packed
files were returned and independently verified locally: 20/20 complete nominal
passes, zero missing, 30,067 protected originals unchanged. The generated
qualification.json was SHA-checked after transfer to a new remote proof path.

The existing helper then accepted exactly one submission for each previously
approved group: legal-a 3570473, legal-b 3570474, fault 3570475. All three
were PENDING Priority at the post-submission check. Their remote exclusive
intents and receipts were returned and checked against the frozen plan in
downstream_submission_receipt.json. Total planned recovery remains below the
approved 8-SU ceiling. The automation was reactivated with a monitoring and
offline-verification prompt for these exact three jobs; it may not resubmit.
The fourth-case legal and fault results are not yet available.

Completed-job watcher is confirmed PAUSED. Automatic approval review declined
deletion because the original verbatim counter follow-up delivery condition is
still unmet; no workaround was used. Original stranded jobs remain untouched.
