# Diagnostic 3558303 submitted; access paused

Accepted development/TRA25006 job **3558303**, one node, 15-minute limit,
0.25-SU reservation ceiling, no simulation or build. Receipt/intent were returned
to `submission-returned-v1/`; `submission_receipt.json` records the accepted ID.
Do not invoke submit_audit.py again or submit a duplicate.

Matching Mac/LS6 submission HEAD was
`cbf77af0e8e9f27719a48c71b2f84b06e3bfeeea`. Active counter scripts and original
plan matched before the pull; active scripts matched afterward. The diagnostic
uses plan `cf3c0991bb7a596cf3f6c1783e4358b3301df50d6c1b278d6e648e09c5dd16b2`.
The revised runtime seal is the original 764-file seal; the supplementary
20-file Mac seal stays checked locally. No original input was changed.

The first status check after receipt return failed authentication with TACC
MFA/password instructions (SSH exit255), so remote access stopped immediately.
Watcher update confirmed PAUSED. No current job execution state is known;
accepted does not mean completed or scientifically verified. Last recorded
access event: 2026-11-05T15:21:30.133788-08:00. Human reconnection/confirmation is required.

After access resumes, check existing 3558303 once, plus the original chain.
If terminal, return its four packed files with stem
`3558303-counter-infra-audit` from WORK/tacc_work/packed-results into a fresh
returned directory and run `verify_audit.py --returned ... --job 3558303 --out ...`.
Keep complete/failed/interrupted evidence. No heavy login analysis or hashing.
If no archive exists, read the existing SCRATCH Slurm logs once; no blind retry.
No normal replacement or original-job cancellation is authorized.

Original counter3552460 completed,3552461 failed127,3552462/3552463 last pending;
no new outcome has been claimed. Counter follow-up not delivered, and no paper
change. The complete separate repeatability result remains verified and delivered.
