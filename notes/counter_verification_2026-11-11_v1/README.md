# Counter verification follow-up

This namespace holds the preregistered diagnostics for the already measured
counter-repair extension. It is excluded from primary subject/yield counts.

- PROTOCOL.md specifies reference properties, exact replay rules, observer
  tolerances, stopping and missingness rules, and the account-only adaptation.
- selection.json links 17 replay tasks and all 87 residual failing case slots.
- COST.json records the one-node development/CCR26073 estimate and 2-SU cap.
- packet/ contains immutable reference/execution manifests and their hashes.
- subjects/counter_verification_20261111_v1 contains the two new reference apps.
- harness/tacc_counter_verification contains the isolated execution adapter.

Preflight (Mac, no simulation): check every packet/source/code hash, bash -n
on the new shell files, and the original 30,067-file protected audit. Source,
ELF, clock, CPU/SysTick and simulation run body remain unchanged for replays.
The runtime/run_packed copies have only the preregistered two mechanical diffs.

After commit/push, use git pull --ff-only on LS6, verify matching clean HEAD and
unchanged original counter scripts, then invoke ONCE:

    python3 harness/tacc_counter_verification/submit.py

The helper is development-only, CCR26073, 2 hours, and writes an exclusive
intent/accepted-or-uncertain receipt under
$WORK/zephyr-rtc-clock-robustness/tacc_work/20261111-counter-verification-v1/.
Never call it again for an accepted or uncertain submission. Record the actual
job ID before checking sacct. No git pull while this diagnostic is pending/running.

Every phase writes into SCRATCH/node-local storage. Final files have stem
<job-id>-counter-diagnostics under the existing WORK packed-results directory:
tar.gz, tar.gz.sha256, manifest.json.gz and json. Return only those four files
with rsync into a fresh local returned namespace. Independently check SHA,
manifest/member/extracted hashes, original protected audit and code/source/ELF
seals before reading outcomes. Keep interrupted/failed/missing/unstarted states.
The local verification/report script is separate from sealed run code.

All scientific conclusions and paper updates remain blocked until qualification,
replays, functional references and activation controls have been independently
reviewed. A reference or replay anomaly is data, never a reason to tune sources
or replace primary outcomes. Original stranded jobs remain untouched.
