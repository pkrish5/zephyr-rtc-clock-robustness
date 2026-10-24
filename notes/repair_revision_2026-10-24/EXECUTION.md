# Approved E execution packet

The 2026-10-24 split was registered before any repair compilation or run.
`amendment.md` and its SHA-256 seal reproduce the DESIGN revision.
`example_diffs.md` shows V1 and V1b for the upstream callback, Sol base
pending r03, and Sol base counting r01, including the shared counting adapter.
The original V2/V3 example files remain byte-identical.

## Frozen source cohort

`../repair_execution_20261024_v2/patch_sites.json` records original hashes,
budget expressions and exact source substitutions, saved before generation.
`variants.json` records all 165 versions, source/support hashes, original
and new scalar budgets, unchanged variants and separately retained service
allowances. All original non-time assertions are retained. Two source-specific
timeout assertions are explicitly redirected to the new deadline and listed.
The earlier incomplete generator attempt is preserved as v1, excluded from
execution. Its assertion checker initially rejected a registered timeout-only
change; no build/run outcome was used to revise a source.

There are 22 V1 no-op subjects. Their original source and frozen nominal ELF
are reused, and their original deadlines remain intact. V0 always reuses the
original nominal ELF. Mutant builds use unchanged fault-driver source in new
build trees. V3 retains V2 where all required checks already exist; this is
reported as equivalence, not an independently invented oracle improvement.

## Jobs and cost estimate

Two sequential one-node normal jobs, allocation TRA25006:

1. **Gates/builds:** cap 16, two compiler workers per build, four-hour limit.
   Up to 335 fresh builds, 825 primary and 15 reference nominal launches.
   Provisional estimate **2 SUs**, reservation ceiling **4 SUs**.
2. **Controls/evaluation:** cap 32, 18-hour limit. First validate 19 reference
   fault/endpoint controls, then up to 16,830 primary legal-clock cases and
   545 primary fault cases, plus assertion replays and distinct-frequency
   legal references. Estimate **8 SUs**, reservation ceiling **18 SUs**.

Total planning estimate **10 SUs**, reservation ceiling **22 SUs**. The new
A–B job measured 1,632 cases in 1,955 seconds with 32 workers (0.543 SUs).
Scaling that observed throughput to 17,375 primary evaluations gives 5.78
node-hours before allowances for longer repaired windows, fault cases,
replays, references, builds and nominal gates. Build time is an allowance,
not a measured rate. The generous wall limits cover uncertainty; billing is
for elapsed node time with TACC's minimum charge, not the full reservation.
No optional counting offset controls are scheduled, as permitted by the
registered protocol; counting is outside the alarm-offset denominator.

E gates depend on D job 3532338. Compute-node preflight additionally verifies
all 216 D controls and builds passed and their raw hashes are intact. E
evaluation depends on successful gate-job completion and its sealed generated
ELF manifest. No source is repaired again after a gate/fault outcome is seen.
Build failures, nominal failures, harness errors and absent evaluations remain
separate; no retry-until-pass. E2 stays on hold. Stop at Phase 3 before editing
the manuscript.

## Exact submission pattern after connection recovery

Run from the existing LS6 checkout after `git pull --ff-only`; transfer the
sealed local `e-bundle` with rsync. All paths below remain under WORK.

```bash
cd "$WORK/zephyr-rtc-clock-robustness"
export RTC_REPO="$PWD"
export RTC_BASE="$PWD/tacc_work/20261024-repair-v1"
export RTC_BUNDLE="$RTC_BASE/e-bundle"
export RTC_D_BUNDLE="$PWD/tacc_work/20261024-phase2/d-bundle"
export RTC_IMAGE="$PWD/tacc_work/20261023-v10/images/rtc-ls6-v1.sif"
mkdir -p "$RTC_BASE/logs"
export RTC_E_STAGE=gates
repair_gate_id=$(sbatch --parsable -A TRA25006 -p normal -N 1 -n 128 \
  -t 04:00:00 -J rtc-repair-gates --dependency=afterok:3532338 \
  --output="$RTC_BASE/logs/gates-%j.out" --error="$RTC_BASE/logs/gates-%j.err" \
  harness/tacc_phase2/packed_e.sbatch)
export RTC_E_STAGE=evaluate
sbatch --parsable -A TRA25006 -p normal -N 1 -n 128 \
  -t 18:00:00 -J rtc-repair-eval --dependency="afterok:$repair_gate_id" \
  --output="$RTC_BASE/logs/evaluate-%j.out" --error="$RTC_BASE/logs/evaluate-%j.err" \
  harness/tacc_phase2/packed_e.sbatch
```

If a submission connection times out, inspect whether a job was accepted
before resubmitting. If authentication is requested or the connection drops,
stop and ask the user to restore the session; never attempt authentication.
