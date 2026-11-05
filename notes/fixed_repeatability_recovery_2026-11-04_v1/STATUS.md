# Verified RTC repeatability checkpoint, 2026-11-04 17:57 Central

Job **3552869 completed 0:0**. Its four packed files were returned into
`returned-3552869-v1/` and independently verified in `verified-3552869-v1/`:
838 exact inventory entries; complete state; archive SHA256
`91fa98c49ecd7f41d6edf054670fcc7a6c4f4034980b619f572504f1f861b308`.
Both coordinator input guards passed. The archive's before/after protected-file
checks retain all 30,067 files unchanged, including the counter input seal.

The new offline `audit_unit.py` checked all 90 records and provenance,
process exits, UART case vectors, trace/platform/log hashes and fixed settings.
`rtc_report_v1/` retains one row per planned repeat plus every application case
verdict. Selected `rtc_api.test_alarm_callback` outcomes:

|Fixed clock|Pass|Fail|Skip|Missing|
|---|---:|---:|---:|---:|
|23.673 kHz|0|30|0|0|
|23.847 kHz|30|0|0|0|
|32 kHz|30|0|0|0|

No observed same-setting flakiness in these three cells; rare flakiness is not
ruled out. Cross-frequency differences remain timing sensitivity. Normalized
traces also agree within each cell; this is supporting evidence, not a new
nondeterminism claim. Kernel-reported durations and sampled UART exposure
remain distinct and do not directly measure callback arrival or subsecond phase.

Latest bounded BatchMode sacct: counter repeat job **3552870 RUNNING**;
counter-repair build **3552460 COMPLETED 0:0**, with **3552461–3552463 PENDING**.
Build termination is not build/gate/scientific verification. Do not deliver the
counter follow-up until all four counter-repair jobs are terminal. No jobs were
submitted, resubmitted, canceled or changed in this wake. No LS6 pull or source
change. Old failed preflights remain separate with zero scientific launches.
The watcher remains active for counter repeats and the eventual follow-up.

---

# Approved repeatability recovery: accepted jobs

Recovery was registered before execution and submitted under the human's
4.0-SU combined ceiling. New RTC job3552869 and counter job3552870 were accepted
on development/TRA25006, one node and32Launcher workers each. Each has90fresh
launches. Counter depends only afterany:3552869. New image path is v10, with the
original sealed94d7894e...aaa1 target; actual SIF hashing remains at compute entry.
New submission namespace is tacc_work/20261104-fixed-repeatability-v2. New Slurm
logs are SCRATCH/zephyr-rtc-clock-robustness/fixed-repeatability-20261104-v2/slurm.

Fresh estimate2.441906SU, fresh ceiling3.5SU; estimated old failed minimum0.5SU;
approved combined ceiling4.0SU. Old failed archives/receipts remain unchanged.
The original scientific packet, all6cells/30repeats, source/ELFs, settings,
simulation body and analysis rules remain unchanged. Old jobs had zero starts.

Matching clean Mac/LS6 submission HEADeb2254ad was verified before submission.
The active counter code/plan guard matched before/after pull, and all11sealed
run-code files matched the original plan. No counter-repair job/input was
changed. Never git pull LS6 or edit sealed code while3552869/3552870 are
pending/running. Never invoke either submission helper again for accepted IDs.

Return only four packed files per recovery job from tacc_work/packed-results,
with stems3552869-fixed-repeat-f4-rtc and3552870-fixed-repeat-f4-counter into
fresh returned namespaces. Reuse the original verify_archive.py with the new
IDs, retaining failed/interrupted states. Use analyze.py only on newly verified
recovery archives. Count every scheduled pass/fail/skip/missing and retain all
old unstarted evidence separately. No claim of within-setting flakiness unless
mixed explicit pass/fail is observed at identical verified settings.

The separate counter-repair jobs3552460-3552463 remain immutable. When all are
terminal, deliver the exact saved COUNTER_FOLLOWUP.txt once. No fourth-case
paper results before all registered primary/fault/gate/replay/reference
verification. Keep main.tex and main.pdf unchanged in this watcher.

Last verified sacct:3552869 RUNNING,3552870 PENDING; the four counter-repair
jobs PENDING. A further read-only RTC preflight check returned all_passed:true,
counter_inputs_unchanged:true and the exact original plan hash; command.err was
empty. Thus the actual v10SIF/image/input/ELF/code guards passed before launch.
The30-minute watcher is ACTIVE and updated to these new IDs/receipts. It must
not resubmit, pull LS6 or alter sealed inputs. Old failed attempts stay separate.
