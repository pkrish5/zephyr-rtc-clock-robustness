# Recovery ready for review; normal approval pending

Diagnostic 3558303 passed independent archive/build/input/module verification.
The proposed wrapper reuses all four saved ELFs and exact original task indices,
worker and scientific plan; it changes only startup/storage orchestration.
All four dry-run commands and their exact allocation/wall/cost fields are in
`dry_run_commands.json`. No normal job has been submitted. A real approval.json
is intentionally absent; approval.example.json is false and cannot submit.

Proposed normal/TRA25006 groups, each one node and32Launcher workers:gate20
launches/1h, legal-a153/3h, legal-b153/3h, fault8/1h. Estimated total5.984790SU,
reservation ceiling8SU. The already-completed diagnostic ceiling0.25SU is
separate. Estimates are from original counter repeats, not measured repair data.
Downstream submission requires independent verification of the completed gate
archive; the compute jobs revalidate it before simulation. No old job is canceled.

Wait for explicit approval of this work and8-SU ceiling. Then record the actual
human approval with the exact plan hash; publish/pull explicit new paths only;
submit gate once with --submit and save its intent/receipt. Do not schedule
legal/fault groups until all20nominal gates are independently verified as passing.
No gate failure, hash mismatch or new missing outcome may be hidden by a rerun.
