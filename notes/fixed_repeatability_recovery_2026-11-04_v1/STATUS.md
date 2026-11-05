# Repeatability verified; separate counter repair blocked

Both repeatability recovery archives and all 180 primary records are now
independently verified. `combined_report_v1/REPORT.md` and `TIMELINES.md` retain
the six-cell results and source-linked measurement/inference timelines.
Selected outcomes: 120 pass, 60 fail, zero skip, zero missing. Every cell has
30 matching explicit verdicts: **no observed same-setting flakiness** in these
cells; rare flakiness remains possible. Both independent audit paths agree on
180/180 outcomes, and all 180 full-application vectors match an archived vector
at the same frequency. All other case verdicts and capability skips are saved.

The fresh archived-input audit rechecked 14 original records, 32 input hashes,
and both unchanged ELFs. Both recovery archives have 838 verified entries and
unchanged before/after checks over 30,067 protected files. Old preflight attempts
remain separate and launched no scientific processes. No original outcome was
replaced, and no new simulation or job was launched during verification.

Counter archive 3552870 SHA256:
`7a1a0e63c2a1152f50874a930f0c7433249f4cef4f50e6b8cfad9eaec6bf16ac`.
RTC archive 3552869 SHA256:
`91fa98c49ecd7f41d6edf054670fcc7a6c4f4034980b619f572504f1f861b308`.

Separate counter-repair status: build 3552460 COMPLETED 0:0; nominal gate
3552461 FAILED 127:0; legal 3552462 and fault 3552463 still PENDING.
The exact stderr is in `combined_report_v1/gate-3552461.err`: unavailable Lmod
files followed by `apptainer: command not found`. This is an environment
blocker, not a repair verdict. No counter job/input was changed or resubmitted.
The counter follow-up has NOT been delivered because all four are not terminal.
The watcher remains PAUSED for this blocker; no automatic recovery or polling.
See `combined_report_v1/COUNTER_BLOCKER.md`. Paper TeX and PDF are unchanged.

---

# Resume check rejected, 2026-11-04 21:13 Central

After the human confirmed MFA reconnection, one bounded BatchMode sacct check
again returned `Permission denied (publickey,keyboard-interactive)` before any
job status. Remote access stopped immediately; the watcher is still confirmed
PAUSED. No automatic retries, jobs, records or manuscript changes. Existing RTC
verification remains valid; current counter job states are unknown.

---

# Access paused, 2026-11-04 18:27 Central

The new bounded BatchMode status check failed authentication before returning
any job states: `Permission denied (publickey,keyboard-interactive)` with TACC
password/token instructions. Remote access stopped immediately. The automation
update confirmed PAUSED. No retry, job mutation, transfer, code pull or new
experiment occurred. The human must reconnect and explicitly confirm resume.

RTC verification below remains complete. Counter repeat job 3552870 was last
verified RUNNING; counter build 3552460 last COMPLETED 0:0 and 3552461–3552463
last PENDING. These are historical states, not current verification. The counter
follow-up has not been delivered because all four terminal states are not yet
verified. No manuscript change. Local RTC report is committed as `6559977f`.

---

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
