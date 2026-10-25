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
