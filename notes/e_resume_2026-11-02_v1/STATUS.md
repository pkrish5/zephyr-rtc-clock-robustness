# E quota-interruption recovery, 2026-11-02

## Latest checkpoint — read-only audit submitted, 2026-11-02

User reconnected and authorized continuation. BatchMode access succeeded;
queue was empty. LS6 git pull reached Mac/origin commit
78137bf4aac0e63556dde2bed423cceaddc9cd6c with clean status.
Development job **3547562** was accepted: TRA25006, one node, 02:00:00,
reservation ceiling 2 SUs, no requeue and ten-minute packing signal.
Receipt: `audit_submission_v1.json`. One subsequent read-only sacct check
reported PENDING, start/end Unknown. No simulations or resume job submitted.

Next: when this job finishes, inspect its logs and packed-state receipt,
transfer its new archive, independently verify the exact inventory, hashes,
protected checks and classifications. Any integrity anomaly stops resumption.
Only then freeze retry indices and the dated DESIGN amendment. E2 and paper
edits remain held. Do not pull while this job runs; do not resubmit it blindly.
The earlier authentication-stop account below is retained as history.

## Current state

S2 reference validation is complete and independently verified; see
`notes/s2_reference_2026-11-02_v1/REFERENCE_RESULTS.md`. All 470 failing primary
slots have reference links. No E audit or E resume job has been submitted.
E2 and manuscript edits remain held.

The first E audit submission connection was rejected before the remote Python
command ran, with TACC password/MFA instructions and SSH exit 255. Remote access
stopped; no retry, authentication, checkout pull, namespace creation, or Slurm
submission occurred. Receipt: `audit_attempt_auth_rejected_v1.json`.
This is not an ambiguous sbatch acceptance. The user must reconnect and confirm.

Mac/origin code commit **71f1d04fe65c17640435896e1179467b0abddc52** contains the
read-only audit wrapper and reference results. LS6 was last verified at
3fa39cc8; do not assume the failed connection pulled 71f1d04f. Later Mac commits
may add status only. After reconnection use git pull only, then verify HEAD and
clean status before the single development submission.

## Prepared audit

`launch_audit.py` is compute-only infrastructure. It checks the SHA-256 of the
unchanged original auditor:
`43364d36d82af2725a45fc33db5db45fc47a6d164c84bf9192670400eb47e952`
for `notes/quota_recovery_2026-10-29/audit_e_partial.py`. It execs the proven
packed storage coordinator, with source output
`$SCRATCH/zephyr-rtc-clock-robustness/jobs/JOBID/output/e_audit` and label
`e-partial-audit`, before/after full protection checks and fresh WORK headroom
checks. It reads old E data without simulating, building, rerunning, deleting,
or modifying it.

Planned job: development/TRA25006, one node, two hours, reservation ceiling
2 SUs, no arrays, `--no-requeue --signal=B:USR1@600`. The batch wrap must be
`exec python3 <repo>/notes/e_resume_2026-11-02_v1/launch_audit.py`, so exec reaches
the coordinator in the batch PID and its USR1 packing trap receives the signal.
Use new SCRATCH submission directory
`$SCRATCH/zephyr-rtc-clock-robustness/e-partial-audit-20261102-v1` (it was not
created because authentication failed); write an acceptance receipt before
claiming any job ID. Never blindly retry a timeout or ambiguous submission.

Original data:
`$WORK/zephyr-rtc-clock-robustness/tacc_work/20261024-repair-v1/e-bundle`.
The original E job 3535400 failed on WORK quota; preserve its STOP marker,
partial files, completed records, build products, controls and all old hashes.
The reference image remains 94d7894e…aaa1 and the modules are
tacc-apptainer/1.4.1 and launcher/3.10. Every job uses -A TRA25006.

## Required gates before resumption

1. Transfer and independently verify the new audit archive and protected
   receipts. Inspect every integrity anomaly before proceeding. Incomplete
   entries are not the same as finalized harness-error missing verdicts.
2. Preserve complete-and-valid primary records exactly, including fail, error,
   timeout and other saved missing outcomes. Do not rerun a primary just because
   its derived score/replay/reference follow-up is missing.
3. Freeze exact incomplete and not-started evaluation indices from the audit,
   with execution/task/source/ELF seals. Add the dated DESIGN amendment:
   quota-interrupted evaluations without a final verdict may run again;
   completed records stay as is; finalized harness errors stay missing.
4. Register separate new output namespaces. Old logical paths may be preserved
   through SCRATCH overlays, but original files and sealed metadata/ELFs must
   remain read only. Never copy or ignore the old STOP marker in place.
   Use the original evaluation body and actual new provenance, no rebuilds.
5. Use the audit and saved per-index timing/resources to estimate chunks with
   packing/protection reserve. Each normal chunk is at most three hours;
   report nodes, wall time, SUs and job IDs under the user's existing scoped
   E-resume approval and standing normal-submission rules. Only incomplete or
   not-started primary indices may be selected. No duplicate submission or
   automatic requeue. Pack verified outputs to WORK; never leave final records
   only on SCRATCH. Fresh WORK count must remain below 700,000 for E.
6. STOP at Phase 3 with the before/after number table before paper edits.

Always use SSH/rsync BatchMode. Stop on credential requests, connection drops,
or stalled remote operations. Do not touch ~/.ssh or account settings. The
handoff's user-side keepalive command, if they choose to use it, is
`ssh -fNM -o ServerAliveInterval=60 -o ServerAliveCountMax=5 ls6`; the user
must authenticate themselves. Never edit/stage/commit their main.tex or main.pdf.
