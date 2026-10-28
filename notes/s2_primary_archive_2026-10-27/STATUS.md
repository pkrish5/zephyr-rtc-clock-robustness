# S2 primary evidence archive, 2026-10-27

The user confirmed LS6 HEAD
`c258b10833db93f0c9a770d3bbd54900290dc466`. The submission guard independently
checked that hash before submitting the prepared collector. No further Git
checkout operation was needed.

## Submitted audit

- Job **3537962**, development, `-A TRA25006`, one whole node.
- Wall-time ceiling: 30 minutes, 0.5 node-hours reserved at most.
- Purpose: read-only snapshot, input/ELF/log/trace/protected-file audit,
  then tar.gz creation with per-file and archive SHA-256 manifests.
- No builds, firmware runs, replays, reference challenges or E2 generation.
- Original raw records remain in their existing directory.

Latest scheduler check: **PENDING (Priority)**, no assigned node, zero
elapsed time. No collector logs exist yet because it has not started.
The last E check returned 3535400 PENDING/unstarted. Do not infer completion
or audit success from this submission.

Remote destination:
`$WORK/zephyr-rtc-clock-robustness/tacc_work/20261027-s2-return-v1/evidence_v1`.
Expected archive and checksum:
`evidence_v1.tar.gz` and `evidence_v1.tar.gz.sha256` in that same parent.
Collector logs: `slurm/return-3537962.out` and `.err` under that parent.
Submission receipt: `submission.json` alongside this note.

## Resume after completion

1. Read the job state and log tails. If it failed, preserve the attempt and
   diagnose before any infrastructure-only retry. Do not rerun simulations.
2. Rsync only the archive, checksum and collector scheduler logs into a new
   local return directory. Do not recursively rsync the original bundle.
3. Run `harness/tacc_s2_evidence/verify_returned.py` with the archive,
   checksum, a fresh extraction destination, this repository, and a fresh
   analysis output directory. It rejects unsafe paths/links, checks the
   complete extracted file manifest, verifies before/after protection,
   independently repeats the raw-log/ELF audit, and compares audit outputs.
4. Confirm the original 1,122 downloaded JSON records match the archive's
   records byte for byte. Retain the provisional ledger as a historical
   checkpoint, rather than overwriting it.
5. Save the verified result summary and archive hashes. Replay/reference
   attribution remains a separate, unfinished step. Counter cascade and
   seconds-rate-contract cautions still apply.

E2 and manuscript edits remain on hold. Existing user manuscript changes
were not staged or modified. The local pre-submission protected audit
matched all 30,067 files (SHA-256
3d838226a627df9151f52f04578c81d25ea324e36207bd7f5f6b9f466fe2446f).
