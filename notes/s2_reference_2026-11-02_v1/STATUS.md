# S2 reference validation, 2026-11-02

## Latest checkpoint: complete and independently verified

3547096 COMPLETED 0:0, 39:00. Archive
`7b4ce8ae94d65ec889a5026e3846911d3fba7028329798de44247f4b67e92fb6`
passed independent Mac verification: 3,137 entries, kept build products/raw
hashes, 30,067 unchanged protected files. All 77 qualification and 274
evaluation launches completed with no missing verdict or harness error.
All 470 primary failing case slots are linked: 277 waiting-reference passes,
88 clean-state cascade-reference passes, 105 retained rate-reference failures
with progress passes. No primary record was replaced. See REFERENCE_RESULTS.md
and verified-3547096-v1/primary_failure_reference_links.csv.

This reference job is over; its checkout no longer needs to remain pinned.
The read-only watcher stays paused. Next is the authorized E partial-record
audit on development, then a separate dated exact-index retry amendment.
E2 and manuscript edits remain held. Earlier connection notes below are history.

## Submitted job and current blocker

**3547096 accepted** on development, TRA25006, one node, 02:00:00, at most
2 SUs. Submission receipt: `submission_v1.json`. This is the only reference
submission. Last verified state: PENDING, no start or end, elapsed zero.

After successful reconnection, the LS6 queue was empty and WORK read 686,917
files. A clean `git pull --ff-only` advanced LS6 from 2cf37d57 to the registered
Mac/origin commit **3fa39cc83b3eea080ef981226276ca9ace7c7501**. No source or
existing record was changed on LS6. The development job was accepted with that
exact HEAD. Do not pull LS6 again until 3547096 finishes.

A subsequent read-only status request returned:

```
mux_client_request_session: read from master failed: Broken pipe
pk23377@ls6.tacc.utexas.edu: Permission denied (publickey,keyboard-interactive).
```

The server also displayed password/MFA instructions. Remote access stopped
immediately; no authentication, retry, cancellation, or duplicate submission.
The user has been asked to reconnect personally. The job may advance while the
client is disconnected; its state after PENDING is not yet verified.

## Registered packet

- Protocol: `PROTOCOL.md`; DESIGN amendment dated 2026-11-02.
- Plan SHA-256:
  `ceb14326dea354408799e1e9a2356ee5c29dec4851998ad3fb56107798a3e7c7`.
- Execution code manifest SHA-256:
  `c649855b2146b0fa46cc9ac18695f330f875af17e1893789cde49fc2be02acbd`.
- Eleven new builds, then 77 qualification launches. Only a valid qualification
  audit allows the 274 reference evaluation launches covering all 470 primary
  failing case slots. No reference result has yet been inspected.
- References use new sources. Frozen S2 build/run bodies and all original
  sources, ELFs, forecasts and records are unchanged. F767 is labeled as an F4
  configuration replica. E, E2 and paper edits have not started.

## Resume after explicit reconnection confirmation

Use `ssh -o BatchMode=yes -o ConnectTimeout=20` for every SSH access and
`rsync -e 'ssh -o BatchMode=yes -o ConnectTimeout=20'` for transfer. Stop again
if access fails or asks for credentials. Never resubmit without reconciling
the existing job and its receipt.

1. Check `sacct -X -j 3547096 --format=JobID,State,ExitCode,Elapsed,Start,End`.
2. Logs:
   `$SCRATCH/zephyr-rtc-clock-robustness/references-20261102-v1/references-3547096.{out,err}`.
   Detail is in
   `$SCRATCH/zephyr-rtc-clock-robustness/jobs/3547096/output/`:
   `job_metadata/command.{out,err}`, `stdout/build/`, `stdout/run/`, and
   `audits/{qualification,evaluation}.json`.
3. On completion transfer the four WORK files
   `$WORK/zephyr-rtc-clock-robustness/tacc_work/packed-results/3547096-s2-reference.*`
   into a new local directory. If failed, inspect and report the exact cause
   before any repair/resubmission. Scientific input or logic changes require
   approval; do not quietly refreeze or edit the packet.
4. Local verifier/comparator (not part of the execution seal):

   ```bash
   python3 -B notes/s2_reference_2026-11-02_v1/verify_and_compare.py \
     --repo /Users/pranavkrishnan/Development/Flakey_Tests_Embeded \
     --returned <new-return-directory> --job 3547096 --out <new-analysis-directory>
   ```

   Require valid qualification/evaluation audits and complete coverage before
   claiming reference validation is done. A failed or missing reference never
   licenses a brittle-test label; missing results remain missing. The retained
   rate-contract case is separate from legal-clock progress. A clean-state
   single-shot reference cannot turn the original cascade into an independent
   waiting defect. Preserve full-application/isolated comparison and the phase
   explanation as supported but not directly measured.
5. Only after the reference step is complete, audit partial E using the existing
   read-only `notes/quota_recovery_2026-10-29/audit_e_partial.py` on a compute
   node. Use the new packed storage wrapper and a new result directory. Do not
   run the audit on a login node or resume E using the old WORK-writing wrapper.
   Retain finalized errors/missing verdicts; identify only incomplete and
   not-started indices. Register their exact retry list and quota-interruption
   policy in a dated DESIGN amendment, then submit the approved normal chunks
   of at most three hours with job IDs and SU estimates reported. E2 and paper
   edits remain held; STOP at Phase 3 before/after numbers before paper edits.

The current user changes to `paper/draft/main.tex` and `main.pdf` must never
be edited, staged or committed by the agent. Stage new evidence by explicit
path only. Mac commits after 3fa39cc8 may contain status/local analysis only;
do not pull them into a pending or running reference job's checkout.
