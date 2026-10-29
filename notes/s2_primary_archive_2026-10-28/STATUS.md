# Archive infrastructure repair, 2026-10-28

## Exact failure

Job 3537962: FAILED, exit 1:0, elapsed 00:00:12, node c310-005.
Its stdout was empty. The saved stderr reports:

```
FileNotFoundError: [Errno 2] No such file or directory: '/work/10970/pk23377/ls6/zephyr-rtc-clock-robustness/artifacts/tacc_phase2_20261024_v1/protected_baseline.json'
```

The original collector's call to `harness/tacc_phase2/audit.py check`
therefore raised `subprocess.CalledProcessError` with return code 1.
The job stopped before evidence copying. The original empty `evidence_v1`
directory and both scheduler logs are preserved; exact logs are in
`failed-3537962/` beside this note. This is the first failed archive attempt.

## Infrastructure-only fix

The expected baseline was local/ignored and absent on LS6. Simply copying
that JSON would still leave protected ignored build files missing: three
representative referenced paths were checked on LS6 and were absent.

An exact copy of the baseline plus the 508 original protected files absent
from the Git index is now packaged under
`harness/tacc_s2_evidence/protected_inputs_20261024_v1/`, delivered by the
required Mac push / LS6 Git pull workflow. Their hashes all match the
original baseline; no source, ELF, forecast or original result is edited.
The 25,480,881-byte cache is input-path provisioning, not new builds.

The new development wrapper checks every existing protected file and
refuses differences, provisions only missing byte-identical paths with
exclusive creation, and checks the full original 30,067-file ledger. It
then calls the original collector wrapper verbatim. The archive's source
bundle, saved logs, metadata selection, audit logic, and original three
collector/audit files are unchanged. Their before/after SHA-256 proof is
`collector_unchanged.json` beside this note. No archive-selection change.

The retry must use a fresh `tacc_work/20261028-s2-return-v2/evidence_v2`
destination, development, TRA25006, one node, 30-minute limit (at most
0.5 node-hours reserved). The original failed destination is not reused.
The remote provisioning/full protected audit is a mandatory gate before
the collector runs. No firmware runs, builds, replays, E2 or paper edits.

Local full protection before and after preparation is recorded under
`artifacts/s2_production_20261026_v1/protected_before_archive_fix_20261028.json`
and `protected_after_archive_fix_20261028.json`. Both must show all 30,067
files unchanged before submission. The retry's job ID/receipt will be
recorded separately after confirmed acceptance. No claim of remote audit
success is made merely from submission.

Confirmed local audit SHA-256 values:

- Before: `4547290d1d14096abe220f213883051243a2661ec56754395b3f59cbb46bc803`.
- After: `0858a0374db32cfe7b24eb69d4eefd81e55682835be836316c4805a889bbd6ee`.
- Both report `count: 30067` and `changed: []`.

## Delivery checkpoint

Fix committed/pushed from the Mac as
`ea7ab441fb43838f4490f9bd9c2849e14d0ea84a`.
The LS6 `git pull --ff-only` client then returned:

```
mux_client_request_session: read from master failed: Broken pipe
pk23377@ls6.tacc.utexas.edu: Permission denied (publickey,keyboard-interactive).
```

TACC also printed its password/token instructions. Remote access stopped
immediately; no authentication was attempted. The remote pull completion
state is unconfirmed and must be checked after the user reconnects.
**No retry job has been submitted, so no new job ID exists yet.** The failed
archive remains the only executed archive attempt; its evidence is retained.
The intended retry remains development / TRA25006 / one node / 30 minutes.

## Confirmed retry submission

After the user's reconnection, the read-only check independently returned
LS6 HEAD `ea7ab441fb43838f4490f9bd9c2849e14d0ea84a`, no Git index lock,
and the retry wrapper present. The fresh local full audit again verified
all 30,067 protected files with no changes; its SHA-256 is
`b50bdc2e2a1e61b6177b18949b6d76cd5645d56bc21fc8d0ebf2f1be03356042`.
The original three collector/audit files still match their c258b108 hashes.

**3539741** was accepted on development / TRA25006: one node, 30-minute
ceiling, at most 0.5 node-hours reserved. This replaces failed archive job
3537962; no firmware builds or runs are submitted. A remote exclusive
submission-attempt receipt prevents a blind duplicate submission. The
accepted receipt is saved as `submission-3539741.json` beside this note.

Remote output: `tacc_work/20261028-s2-return-v2/evidence_v2`.
Logs: `tacc_work/20261028-s2-return-v2/slurm/return-3539741.out` and `.err`.
Provisioning receipt: `tacc_work/20261028-s2-return-v2/path-provisioning.json`.
Provisioning verifies existing bytes before adding missing identical
copies, then performs the unchanged full protected-file audit as a gate
before the unchanged collector. The remote gate has not yet been observed
to complete; submission does not imply successful verification or archiving.
No ongoing polling. E2 and manuscript edits remain on hold.
