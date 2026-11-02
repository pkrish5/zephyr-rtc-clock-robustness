# E infrastructure-interruption recovery, 2026-11-02

## Authoritative audit and selection

Development job 3547562 completed 0:0 in 27:08. Independent Mac verification
checked archive f359400fd714d4b717ea9753dafddb0c6085d487580de598b2c7d7590b04e3d2,
its exact 16 entries, manifest, extracted bytes, internal audit file hashes,
and both complete 30,067-file protected checks. No integrity anomaly or
unfinished derived follow-up was found.

Of 17,375 frozen evaluations, 7,824 are complete and valid: 7,549 pass,
246 fail and 29 finalized harness errors. They remain unchanged. Index 7979
has a worker claim and partial monitor log but no verdict; 9,550 indices were
not started. Retry exactly the 9,551 indices in packet/retry_indices.json,
SHA-256 3b2c67281af37b8092e9c6a4c896f2bac8beccacd8c3850579707cef4fdd7830.
The complete original index-to-record hash map, interrupted bytes and full
not-started list are in packet/selection.json, SHA-256
3e4d45cb27a21bd49d673d310607ca031c65edff0655820e7d89ad05e1ebff2d.
No newly finalized record may be rerun, including a missing/error outcome.

## Infrastructure qualification (before resumption)

No firmware or E evaluator runs in this qualification. A development job,
TRA25006, one node, two-hour ceiling (at most 2 SUs), rechecks sealed inputs,
retained ELFs, original completed evidence and interrupted-file hashes, then
runs 32 container mount inspections. It collects the original full-worker
resource measurements for completed indices; missing resource files stay
missing. Timing measurements include automatic replay/reference work when
present. No scientific outcome is recalculated by this profiling.

The calibrated SIF and the original E Python evaluators are unchanged. Original
bundle, code, sources, all ELFs, execution metadata, and old STOP are mounted
read only. The writable output overlay is a new per-job SCRATCH namespace at
the historical logical path. Original builds and execution/task files are
rebound read only within that overlay. The old STOP is preserved at /original;
the new namespace starts without a STOP or completed-record copies. The fixture
never invokes worker_e.py, Renode or a compiler; it checks mount flags rather
than attempting writes to protected paths.

Private home/cache/tmp are node-local. Existing packed-storage coordination
checks WORK headroom below 700,000, hashes protected files before/after, stops
writers before packing, and verifies an archive before WORK publication. No
loose final records are published to WORK. Qualification failure blocks normal
submission. An infrastructure-only correction must retain all scientific
hashes, use new output, be logged, and stop after three consecutive failures.

## Production gate and interpretation

After verifying the fixture and timing profile, freeze separate normal chunks
of at most three hours with exact disjoint retry lists and reported SU ceilings.
The existing E worker runs unchanged, once per selected index, on unchanged
ELFs and stimuli. Existing controls/gates are reused, not rebuilt or rerun.
Every new record stores actual job/node/module/image provenance. New archives
are later unioned with original complete records by evaluation index, rejecting
duplicates. No original namespace is overwritten. Complete old harness errors
remain missing, and new harness errors also remain missing. Infrastructure
interruptions without a final record need an audited explicit recovery list.
No automatic rerun, requeue, new E2 experiment, or manuscript change is allowed.
Stop at Phase 3 with the before/after number table before paper editing.
