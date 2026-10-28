# Record transfer and partial verification, 2026-10-27

After the user confirmed WORK/session responsiveness, read-only SSH worked.
S2 3535524 remained COMPLETED 0:0, elapsed 03:12:41 on c309-016. E 3535400
remained PENDING, unstarted. The narrow rsync of S2 `records/` completed:
1,122 files, 3,577,648 bytes. No new job was submitted.

The subsequent recursive bundle rsync returned a poll timeout before
copying any additional files. Only the local rsync client was stopped,
exit 20, and remote access paused under the user's connection rule. No
remote results, jobs or account settings were changed.

Local record-only accounting is saved under
`analysis/s2_primary_20261027_provisional_v1/`. Every expected index and
case slot is represented; the records report 3,022 passes, 470 failures,
3,138 skips, and no errors or missing summaries. These are provisional
metadata counts, not verified UART/trace or replay/reference evidence.
H753's short-relative-alarm capability gate varies by setting; see the
README and per-case ledger. Counter shared-state cascades and seconds-rate
semantics still require attribution.

A read-only compute-node snapshot/audit/archive helper has been prepared
in `harness/tacc_s2_evidence/return_primary.py` and its development sbatch
wrapper. It performs no builds or simulations, preserves original records,
verifies logs/ELFs/inputs and protected files, and creates one archive plus
a file-hash manifest. This avoids recursive rsync listing of thousands of
WORK files. It has not been submitted. It needs a responsive session and
the normal authorized Git pull workflow before submission.

E2 and paper edits remain on hold. Existing manuscript changes were left
untouched. No frozen execution code or scientific input was modified.
The post-accounting audit again matched all 30,067 protected files:
`artifacts/s2_production_20261026_v1/returned_20261027_v1/protected_after_record_audit.json`,
SHA-256 4798cbd96dd8754853231c9cfdf952387c305155a3025938c15d730425b4d0c6.

On the next user-authorized archive continuation, the initial read-only SSH
check failed authentication with `Permission denied (publickey,keyboard-interactive)`
and TACC password/token instructions. Remote access stopped immediately;
no authentication was attempted, no Git pull ran, and no archive job was
submitted. The local helper remains prepared for a later authenticated session.

On the following authorized continuation, SSH authenticated and returned
LS6 HEAD d84f7c053e2d5e5810255a2cc1c435e032eb36f6, but the full Git status
scan did not return. Only that diagnostic client was stopped. The audit
collector and provisional ledgers were committed/pushed from the Mac as
c258b108. A separate authorized `git pull --ff-only` on LS6 also returned
no output and its stalled client was stopped. The pull's remote completion
state is unconfirmed; verify HEAD and checkout state before any further
checkout operation. No archive job or simulation was submitted.

The local pre-archive protected audit again passed all 30,067 files:
`artifacts/s2_production_20261026_v1/returned_20261027_v1/protected_before_archive_submission.json`,
SHA-256 3d838226a627df9151f52f04578c81d25ea324e36207bd7f5f6b9f466fe2446f.
The archive wrapper has a 30-minute development reservation on one node
(0.5 node-hour ceiling); it remains unsubmitted. E2 and paper remain held.
