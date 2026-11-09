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
