# Storage contract for new TACC jobs, 2026-10-31

New replay, reference and resume wrappers must source `runtime.sh` on the
compute node. Do not invoke the historical WORK-writing sbatch/task wrappers
or source their frozen `common.sh`. Those files remain unchanged as evidence.

- Build trees and loose run output: `SCRATCH/zephyr-rtc-clock-robustness/jobs/JOBID`.
- Per-task container home, temporary files, compiler/Apptainer caches:
  private directories below node-local `/tmp/rtc-USER-JOBID`.
- Final results: verified archives plus hashes/manifests under
  `WORK/zephyr-rtc-clock-robustness/tacc_work/packed-results`.
- Bind the SCRATCH output to the existing worker's locked logical output
  path. Keep original sources, plans, ELFs and existing records read only.
  Record the physical storage mapping in the job manifest.
- Record actual node, job ID, container SHA-256, Apptainer version and pinned
  modules. Never spoof a partition or reuse original execution provenance.
- A job cannot declare success until it has published and verified its WORK
  archive. Its signal handling must stop writers before packing partial
  evidence. Keep SCRATCH copies until transfer verification; final records
  must never remain only on SCRATCH.

S2 and E scientific follow-ups must additionally check the current WORK
file-count quota is below 700,000 before starting. Infrastructure cleanup
and archive jobs are allowed above that threshold because they restore
headroom. Slurm submission limits still apply. Every submission uses
`-A TRA25006`; normal-queue job details and SUs follow the user's standing
approval rules.

S2 primary collection uses the unchanged collector/selection code with its
working destination bound to SCRATCH and its original registered DESIGN
snapshot read only. Only the verified final archive is copied to WORK.
New scientific wrappers are not approved merely by existing in this folder:
their frozen task lists, protocol amendments and submission gates still apply.
