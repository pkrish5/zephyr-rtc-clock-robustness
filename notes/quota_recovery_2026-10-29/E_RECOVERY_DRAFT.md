# E quota-recovery protocol draft

Prepared before inspecting E's partial per-index outcomes. This is not yet
the dated DESIGN amendment and authorizes no run. Step 4 begins only after
the approved cleanup and recurrence-prevention steps.

## Frozen scientific inputs

Keep the existing task order and indices, version sources, operator macros,
ELFs, platform/frequency mapping, reference tests, simulator/runtime, nominal
gates and exact task/execution manifest bytes. No new generation, build,
nominal rerun, test modification, or E2 call. Existing files are read only.

## Per-index accounting

Audit every index in the sealed `tasks-evaluate.json`, verifying the seal
against `execution.json` and its SHA file. First revalidate the 19 controls,
nominal-gate metadata and referenced ELF/source hashes.

1. **Complete and valid:** a complete primary JSON record with matching
   task/provenance/input fields and matching saved raw-artifact hashes.
   Retain it byte for byte. Recorded harness errors, timeouts and unknown
   outcomes remain completed records with missing test verdicts, excluded
   from retry. A pass/fail is not required for preserving a valid record.
2. **Incomplete:** attempt evidence exists, but there is no valid finalized
   primary verdict record because quota interrupted record creation. Keep
   all partial files and their hashes. Require quota evidence; unexpected
   non-quota or integrity failures stop the resume instead of being relabeled.
   Report any visible partial UART verdict separately, without treating it
   as a finalized original score or overwriting its evidence.
3. **Not started:** no primary record or simulator-attempt evidence exists.
   Launcher dispatch alone, including immediate exits after STOP, is not
   evidence that a simulator evaluation ran.

A valid primary record with unfinished derived score or replay/reference
work does not authorize a second primary simulation. List missing follow-up
evidence separately. Derived scores may be reconstructed from preserved
records into a new analysis namespace. Any remaining registered replay or
reference execution needs its own explicit follow-up task list; preserve
completed follow-ups and never silently rerun a complete primary index.

## Before resuming

Append a dated amendment to DESIGN before scheduling evaluations: quota-
interrupted evaluations lacking valid finalized records are retried in a
new namespace, while completed records and their missing outcomes stay as
is. Document that this is recovery from interrupted infrastructure rather
than retry-until-pass. Retain the original STOP marker and all original
records. Save the classified index CSV/JSON and exact retry indices/hashes.

Use jobs no longer than three hours, calibrated packed concurrency and the
same frozen simulation functions. Put build/cache/runtime/temp trees on
SCRATCH or node-local /tmp. Pack each job's outputs and audit metadata before
copying its final checksummed archive to WORK; final records must never be
retained only on SCRATCH. Report the per-job estimate and IDs. No manuscript
edits; Phase 3 still requires a before/after number table and a stop.
