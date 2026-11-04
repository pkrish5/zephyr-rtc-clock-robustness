# Resume after the user reconnects

No repeatability job has been submitted. Remote access is stopped after the
second BatchMode authentication failure. A new user reconnection confirmation
is required before any further LS6 command. Do not authenticate or retry remote
access automatically.

Read PROTOCOL.md, packet/plan.json, COST.json and STATUS.md first. All6fixed
cells and180planned launches are sealed; execution code hashes are in the plan.
Offline verifier additions do not change the sealed run code or protocol.

1. Confirm the human has reconnected. Check existing3552460-3552463 read-only
   with bounded BatchMode sacct. Do not resubmit/cancel/reseal/clean their files.
2. Record hashes of active counter code from its bundle plan before a guarded
   `git pull --ff-only`; compare after. Mac Git confirms no change from LS6's
   last HEAD2e8d7c4 to current main in harness/tacc_s2/worker.py,
   harness/tacc_storage/, harness/tacc_phase1/common.sh or the active counter
   code. The counter code is untracked and must remain untouched. Use
   `GIT_SSH_COMMAND='ssh -o BatchMode=yes -o ConnectTimeout=20'` for git pull.
   Check matching full Mac/LS6 HEAD and clean tracked status. No git clean.
3. Verify the repeat packet plan hash is
   9c19539dcdf8df60b945debfa2fc69e721021bf80b87e157a1a80dacaa93a613.
   The second failed SSH check never executed its guarded pull, so no before/
   after receipt was created by that command. Check before assuming this.
4. On the login node, invoke only the lightweight receipt-based submission
   helper, not a worker/build/analysis:

   python3 notes/fixed_repeatability_2026-11-04_v1/submit.py --unit f4-rtc
   python3 notes/fixed_repeatability_2026-11-04_v1/submit.py --unit f4-counter

   Commands must run from the WORK repository. The second helper uses only an
   afterany dependency on the accepted RTC **repeatability** job, never on
   counter-repair3552460-3552463. Every job uses development/TRA25006, one whole
   node and32Launcher workers. RTC limit1.5h/1.5SU ceiling, counter2h/2SU ceiling;
   total estimated2.441906SU, total reservation ceiling3.5SU. Report accepted IDs.
   If an intent/receipt already exists or a submission times out, inspect it
   and sacct/squeue; never blindly invoke the helper again.
5. Return the two submission JSON receipts to this new local namespace and
   create submission_receipt.json with job IDs, paths and cost. Original remote
   primary: tacc_work/20261026-s2-primary-v1/bundle. Image:
   tacc_work/20261022-v9/images/rtc-ls6-v1.sif. Neither is rebuilt or changed.
6. Resume the paused heartbeat
   verify-f4-repeatability-and-deliver-counter-repair-follow-up after successful
   submissions and human access confirmation. It checks every30minutes, verifies
   returned repeatability archives and all180outcomes, and delivers the exact
   COUNTER_FOLLOWUP.txt once all four counter-repair jobs are terminal.
   Preserve failed-runs-only notification policy. The old watchers stay paused.
7. Return only new packed WORK result files for each repeat job using rsync:
   <job>-fixed-repeat-f4-rtc.{tar.gz,tar.gz.sha256,manifest.json.gz,json}, and
   similarly fixed-repeat-f4-counter. Never copy loose outputs back onto originals.
   The new per-job archives live in tacc_work/packed-results/; runtime and Slurm
   logs live on SCRATCH or node-local/tmp.
8. Verify each in a fresh local path using verify_archive.py. Analyze both with
   analyze.py; the --rtc/--counter arguments are the verified roots containing
   output/. Preserve incomplete/failed archive states and all missing indices.
   No repeat is silently replaced, retried, dropped or relabeled.
9. TIMELINES.md currently uses archived baseline evidence and clearly labeled
   measured/inferred timing. Add repeat observations as new evidence after the
   archive audits; do not pretend sampled UART exposure is callback-entry time.

main.tex/main.pdf stay unchanged in this repeatability workflow. No fourth-case
paper result before the counter repair primary/fault/build/gate evidence and
registered replay/reference controls are verified in the requested follow-up.
The user has not authorized normal-queue repeatability submissions or a broad
rerun. Never restart E2 or new model generation.
