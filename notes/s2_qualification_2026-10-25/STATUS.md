# S2 qualification status, 2026-10-25

## Registered, not yet executed

The approved board/application roster and qualification rules were appended to
paper/DESIGN.md before new builds or runs. The 30,067 protected-file pre-audit
passed; audit SHA-256 1a8f334e170d05790645bf83d3469e4481b7cc5d7f8d15cc3f66879386ca4132.

Remote access check reached TACC but failed with Permission denied and
password/token instructions. BatchMode prevented authentication. No jobs were
submitted, no account settings changed and E/E2 were untouched. Remote work
is stopped pending the user's MFA reconnection; local preparation continues.

Qualification only is approved. Production requires the results report and a
new approval. No manuscript editing or production runs in this phase.

## Local preparation and restored access

Prepared 17 build configurations (15 RTC/counter, including conditional F072,
and two bounded watchdog configurations), with an upper bound of 182 launches.
Final input bundle: artifacts/s2_qualification_20261025_v1/bundle_v3.
Plan SHA-256: 3eac118d259f137cf0ad8ef0134f2e60285cf3a9702a27d692d4a09efba4f9c8.
Python/shell syntax and synthetic accounting checks pass. Those checks do not
build firmware, invoke Renode or provide any experimental outcome.

One local preparation bug duplicated a task index keyword. It was corrected
before sealing the final plan; the partial first bundle remains preserved.
The second unsubmitted seal was superseded by stricter calibration ordering
and missing-verdict gates. Neither preparatory version was transferred or run.
This does not consume a watchdog or compute qualification attempt.

All 30,067 protected files remain unchanged after preparation; post-audit SHA:
855007fdf137fce13dfd173a2e47b8a8f11582638a0e9cafd5e1da8b1a8ae90a.
The user confirmed MFA reconnection. A bounded read-only check succeeded,
returning WORK=/work/10970/pk23377/ls6 and a clean remote repository at
c9e61b588c4636df05470d4fad1a1c2326db4dd8. No E status was queried.

Planned first submission: development, TRA25006, one whole node, 90-minute
limit, four build containers/two compiler workers each, then one resource
probe. Time-limit reservation approximately 1.5 SU at one SU/node-hour.
After reviewing that evidence, a separate development qualification job packs
remaining nominal and calibration launches using the measured memory limit.
No normal queue submission is authorized at this checkpoint.

## Development build/probe submitted

Job 3533587, development / TRA25006, one whole node, 01:30:00, no array.
Estimated time-limit reservation 1.5 SUs. Local code 4f2eb8a4 was pushed locally
and pulled on LS6. The transferred plan hash matched
3eac118d259f137cf0ad8ef0134f2e60285cf3a9702a27d692d4a09efba4f9c8.
Remote bundle: tacc_work/20261025-s2/bundle_v3. Each build uses a new output
folder; no build/nominal result has been read at this submission checkpoint.
No production job or E/E2 status operation occurred.

## First infrastructure failure: platform package version metadata

3533587 exited 1:0 after 00:03:21 on c306-006. All 17 build tasks completed;
the first resource worker stopped at the version guard before firmware
execution. Cause: new preparation copied the historical local macOS build
date (20260906) rather than the already calibrated Linux string (20260907).
Both identify v1.17.0, f1dd1b4af and .NET8.0.21. The approved Linux string is
verified in the existing v10 software inventory and Phase 2 A-B plan.

Registered a packaging-only recovery before any firmware launch. The new plan
will use that exact Linux pin, retain local provenance and copy all first
attempt build evidence/ELFs with before/after hash verification on compute.
The simulation/build worker is unchanged. No test, assertion, driver, source,
ELF, forecast or existing result is edited. Preserve bundle_v3 and job logs.
No watchdog firmware attempt has yet occurred. First consecutive infrastructure
failure; at most three, no semantic retries. E/E2 remain untouched.

## Metadata recovery submitted

Returned all 17 first-attempt build records and logs. All 17 status=built;
every returned build-log hash matches its record. No firmware verdict exists.
The fix is committed/pushed locally as 6629ce1e and pulled on LS6. New bundle
v4 seal: cbde1752ce2435a980cbce88a94829ae1bfc322368b1ef15c9bc54803753efbb.
The 30,067 protected-file pre-fix audit remains clean (audit SHA
229e4cfa78190e2f34a7f795fbf3fb7ba1a0349f79061314cdd7fe7ee4e79ad8).

Job 3533590: development / TRA25006, one node, 00:30:00, 0.5-SU time-limit
ceiling. Its copy audit must verify all original build/ELF/product hashes,
identical scientific configuration and identical simulation worker before
launching the resource probe. First attempt records remain intact in v3.
The v4 namespace is separate. No normal job; E/E2 remain untouched.

## Resource probe passed; qualification submitted

3533590 COMPLETED 0:0, 00:05:15, c306-005. Returned raw probe trace/UART/
monitor hashes independently match its record. The full RTC application
reported five passes and two explicit skips (update callback and Y2K), zero
missing or duplicate verdicts. Wall 300.625 s; peak RSS 342970368 bytes
(327.082 MiB). Programmed RTC divider 32000, twice observed. MemAvailable
256462872576 bytes and the 80%/1.5 safety rule permit the cap of 32 workers.
A nonessential NVIC property query is unsupported and retained as a diagnostic
field; the test outcomes are complete. Do not claim a measured property value.

The copy audit verifies 17/17 original build/ELF/product sets byte-identical,
with the same simulation worker and scientific inputs. Generated DTS/config
hashes returned locally also match records. F072's actual generated clock is
40000 Hz with no prescaler override in all three builds: source predicts RTC
API divider32000 vs counter39936. Runtime F072 confirmation remains pending.

Job 3533596: development / TRA25006, one node / 01:30:00, no array, cap32.
Provisional cost0.8SU, time-limit ceiling1.5SU, using measured RTC wall plus
unmeasured counter/seconds planning allowances. Five nominal launches complete
before calibration is considered per application. Calibration is omitted with
explicit reasons where complete nominal application verdicts are unavailable.
Each counted capability skip remains a skip. Watchdog has one bounded probe
per approved board in this job. No production job or E/E2 action occurred.

## 2026-10-26: stopped qualification and evidence collection

The first status attempt failed SSH authentication; no further remote action
occurred until the user restored the MFA session. The subsequent sacct read
shows 3533596 TIMEOUT after 01:30:04 on c306-005. Its batch step was cancelled
0:15 at the job limit. No production submission or E/E2 operation occurred.
The nominal stage reached calibration, but the final reporter was not reached.
Completed verdicts, skipped launches, unfinished launches, and timeout evidence
will be retained separately. No test retries are authorized by this collection.

An audit-only development job will verify existing plan, code, DESIGN, build,
ELF, trace, UART and monitor hashes, preserve runtime-cache provenance and
archive a new snapshot. It runs the original sealed reporter on the new copy
only; no new build or firmware run and no original output modification. A
15-minute, one-node development/TRA25006 reservation has a 0.25-SU ceiling.
The collector is separate from the sealed S2 harness; original S2 code remains
unchanged. Qualification conclusions and any proposed next steps await the
returned evidence. Production remains blocked pending the user's review.

## 2026-10-26: evidence verified; qualification checkpoint

Audit-only development job 3535059 COMPLETED 0:0 in 54 seconds on c306-006.
Returned via rsync, archive SHA-256:
be4c26e901f65bddfb0319bca2d0f94c380d76c9b74f84bf81749ce5feaa85f2.
All 1,583 archive file hashes independently match. The copied original reporter
completed successfully without changing original outputs. Verified evidence is
published under results/s2_qualification_20261025_v1; derived checkpoint under
analysis/s2_qualification_20261026_v2. First local summary preparation had an
optional-CSV-column error; the incomplete local v1 is retained, not published
as a result. No experiment or input changed in that reporting correction.

Final records: 139/182; 117 complete, 15 harness wall ceilings, seven incomplete.
Twenty-eight calibration launches were omitted for incomplete nominal apps;
six other calibrations started but were interrupted, nine never started.
Four configurations meet all existing gates; seven more need fifteen remaining
calibration records. F746 counter has an MPU fault after partial UART outcomes;
its five applications are incomplete. Conditional F072 has no UART outcomes or
confirmed programmed divider. Both bounded watchdog probes lack reboot/case
completion and are excluded without retry. No new firmware attempt was made.

A potential counter failure cascade is explicitly retained: an all-channels
callback-count assertion precedes missed cancellation, then single-shot setup
fails -EBUSY. It is not classified as a second independent brittle wait.
Source-backed preliminary explanations and excerpts are in the analysis folder;
reference/replay classification remains pending. The non-stock RTC-only counter
configuration and all explicit capability skips remain documented.

Only conditional primary production costs can be given: four currently ready
configurations imply 408 app launches, about 0.66 SU; completing seven more
calibrations could yield 1,122 app launches, about 4.48 SU. These exclude
replays/references/builds and allocation rounding. No scope was silently dropped
and no normal job was submitted. STOP for qualification review and direction
on remaining calibration and failed configurations. E/E2 and paper untouched.

## 2026-10-26: reviewed exclusions and approved continuation

The user approved exclusion of F746 counter (MPU fault, no configuration fix),
all F072 (no test output, no confirmed runtime-divider finding), and watchdog
(no reboot), with source evidence entered in DESIGN.md before more runs.
F746 RTC and counter seconds remain candidates subject to all gates.

Read-only E status: 3532543 PENDING, reason Priority, not started, normal,
18-hour requested limit. No E mutation or E2 action. Development qdevelopment
MaxWall queried as 02:00:00 (partition itself shows unlimited). Resume exactly
indices 18,19,21,55,56,58,71,72,79,119,120,127,140,141,143 on one development
node with fifteen Launcher workers, one line per worker, two-hour maximum.
Expected about 0.5 SU; reservation ceiling 2 SU. No sequential stages or rebuild.

New bundle plan 2df1e0d4e31dd02b91d79978e16ed5fe18fe86186662b9e1e68507e989a2c03d
retains the original source, ELF reuse rule, config, frequencies, platform,
simulation-worker and per-run limits. Metadata includes the new design hash,
exact acceptance vectors and missing-original linkage. Two F767 seconds
lower-bound assertion failures at 24797/24734 Hz are expected from matching
F4/F746 evidence; all other runnable cases must pass and capability vectors
must match the frozen nominal templates. Any error, missing verdict or changed
vector blocks conditional production. Original missing slots remain unchanged.
Conditional production is eleven configurations /1122 application launches,
with an initial primary estimate4.48SU, one node/six-hour reservation ceiling6SU.
No normal submission until acceptance is audited. Paper/E2 remain held.
