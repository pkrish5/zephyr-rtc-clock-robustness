# S2 development qualification only

This adapter does not submit jobs and refuses to execute outside the development
partition. The registered protocol is the 2026-10-25 S2 amendment in
`paper/DESIGN.md`. No existing source, ELF, forecast or result file is written.
E 3532543 and E2 are not inspected or operated on by these scripts.

## Prepared cohort and gates

- Four approved boards plus conditional F072, three complete applications each:
  RTC API, RTC-only counter basic, and counter seconds.
- Two separate watchdog builds/probes: F4 and H753 only.
- Upper bound: 17 builds and 182 firmware launches, including the single resource
  probe, five nominal launches and seven calibration settings per RTC/counter
  configuration. Failed builds do not launch firmware. Calibration is omitted
  if the five nominal applications did not complete with explicit case verdicts.
- All enabled RTC test source paths are compiled. Mask 7 matches the existing
  selected upstream alarm configuration; update/calibration paths are added.
  Explicit DTC_OVERLAY_FILE suppresses stock test board overlays. Counter builds
  use only the RTC counter and no subsecond or general-purpose timer counter.
- The generic adapter reuses the original command/RunFor monitor methods and
  removes the F4-specific GPIO startup check. The old harness is unchanged.
- Case qualification requires five explicit nominal passes. Capability skips,
  assertion failures, missing/duplicate verdicts and infrastructure failures
  remain distinct. Legal-clock calibration failures may be real test failures;
  they are not automatically infrastructure failures.
- Watchdog qualification requires reboot progression and explicit completion,
  not merely a printed reset request or a standalone pass. One bounded attempt
  per board, with at most three attempts only for documented infrastructure fixes.

## Preparation on the local computer

Run the synthetic accounting checks and syntax checks first. They do not invoke
Renode or build firmware. Prepare into a new, nonexistent bundle directory:

```sh
python3 harness/tacc_s2/test_accounting.py
python3 harness/tacc_s2/prepare.py \
  --out artifacts/s2_qualification_20261025_v1/NEW_BUNDLE \
  --renode-root /path/to/calibrated/Renode/platform-root \
  --cache artifacts/tacc_phase1_20261023_v10/renode-cache \
  --runtime-inventory artifacts/tacc_phase1_20261023_v10/returned-images/software-inventory.json
```

The output seals all code, app/driver inputs, configurations, platform closure,
100-setting schedules, seven-setting calibration subsets and the design hash.
Do not change a sealed input. Any infrastructure correction uses a new bundle,
new output paths, new audit and a status-log entry. Do not retry test assertions.

## Remote operation after the user restores the authenticated session

Commit/push reviewed new code locally, then use **git pull only** on LS6. Transfer
the input bundle to a new directory under
`$WORK/zephyr-rtc-clock-robustness/tacc_work/20261025-s2`. Do not transfer a code
checkout over the remote repository. All heavy checks, image hashing, builds,
Renode runs and reporting happen inside the following compute jobs.

Set these variables in the already authenticated LS6 shell:

```sh
export RTC_REPO="$WORK/zephyr-rtc-clock-robustness"
cd "$RTC_REPO"
git pull --ff-only
export RTC_BASE="$RTC_REPO/tacc_work/20261025-s2"
export RTC_BUNDLE="$RTC_BASE/NEW_BUNDLE"
export RTC_IMAGE="$RTC_REPO/tacc_work/20261023-v10/images/rtc-ls6-v1.sif"
mkdir -p "$RTC_BASE/slurm"
export RTC_S2_STAGE=build_probe
sbatch --parsable -A TRA25006 \
  --output="$RTC_BASE/slurm/build-probe-%j.out" \
  --error="$RTC_BASE/slurm/build-probe-%j.err" \
  harness/tacc_s2/development.sbatch
```

Record the definite job ID. The first job builds with at most four compiler
containers, runs one F4 RTC nominal launch, then calculates packing capacity
from its peak RSS and node memory with the 80%/1.5 safety rule. It stops if the
resource probe lacks complete case verdicts. The maximum request is one
development node for 90 minutes, approximately 1.5 SUs at one SU/node-hour;
actual elapsed cost is measured, not claimed here.

After verifying build/probe evidence, submit the second development stage:

```sh
export RTC_S2_STAGE=qualification
sbatch --parsable -A TRA25006 \
  --output="$RTC_BASE/slurm/qualification-%j.out" \
  --error="$RTC_BASE/slurm/qualification-%j.err" \
  harness/tacc_s2/development.sbatch
```

This is a further one-node/90-minute request, with an upper time reservation of
1.5 SUs. Nominal and calibration Launcher stages are sequential. Every run has
one jobfile line invoking one Apptainer exec, private WORK cache/home/tmp, and
node/job/image/Apptainer provenance. Missing results stay missing. The report
keeps per-case/per-board qualification and measured costs separate. A possible
production count is not authorization and still requires human review of
generated devicetrees, model clock behavior and F072 divider evidence.

Return results with rsync, verify hashes, report qualification, final workload
and SU estimates, then **STOP before production**. Never auto-submit normal.
If SSH asks for authentication or fails, stop remote operations and ask the user
to restore the session; do not retry authentication or change account settings.

## Registered build-string metadata recovery

First job 3533587 built 17 configurations but stopped before firmware because
its new plan incorrectly expected the macOS build date. The approved Linux
version is 20260907/f1dd1b4af/.NET8.0.21. `--runtime-inventory` pins that exact
existing calibrated string and seals its source hash. `resume_probe.sbatch`
uses a new bundle/output namespace, copies and verifies the unchanged first
attempt build evidence/ELFs on a development compute node, then invokes the
unchanged worker for its first firmware/resource launch. Set RTC_S2_PREVIOUS
to the old bundle. No rebuild, test/driver/worker change or weakened gate.
The recovery job requests one development node for 30 minutes (0.5 SU ceiling).
