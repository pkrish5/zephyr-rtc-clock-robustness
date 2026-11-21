# Independently verified qualification FAIL — 3589708

Access restored and evidence returned. All 84 planned records complete, all eight builds and integrity checks pass, all 42 nominal runs / 21 observer pairs qualify. All achieved phases qualify. Nine timing diagnostics fail arrival agreement; see REPORT_3589708.md and timing_diagnosis_3589708_v1.json. Controlled-phase primary sweep BLOCKED. No resubmission or tolerance changes. Next authorized candidate is a separately sealed natural-phase fallback. Full conservative debit remains 4/50 SU, 46 uncommitted.

# Job 3589708 user-reported FAILED 1:0

User supplied start 2026-11-17T13:10:54, elapsed 00:54:33. Duplicate pasted rows refer to the same job. Cause remains unknown; packed archive/log collection and independent verification are required. Main sweep remains blocked. Do not resubmit or tune sources/tolerances. Remote access remains paused after the last authentication failure until the user confirms manual reconnection. Conservatively retain the full 2-SU reservation debit; the 50-SU total ceiling is unchanged.

# Remote verification paused: access failure

Latest user-requested check failed before sacct returned: SSH exit 255, existing master broken pipe, then Permission denied with TACC password/token instructions. No remote retry, job change or submission was made. Current job state is UNKNOWN; last verified state of 3589708 was PENDING. User must reconnect manually before verification resumes. Check time UTC: 2026-11-17T20:44:42.310067+00:00

# Qualification job 3589708 ACCEPTED — PENDING

Latest bounded sacct: PENDING 0:0, no start. Accepted on CCR26073 development, one node, two hours / 2 SU ceiling. Exclusive intent and accepted receipt returned to submission-returned-v1. NEVER invoke submit.py again. No git pull or execution-file changes on LS6 while pending/running. Submission HEAD 6053b004f3738800272a25ac2301c5e194909391 matches Mac/LS6. Fresh allocation check: CCR26073 1494 SU available; user study ceiling 50 SU, 4 SU conservatively committed including prior attempts, 46 SU uncommitted. No phase results yet.

# Sealed controlled-phase qualification; awaiting submission

Latest user authorization raises the total study ceiling to 50 SU. This qualification remains capped at 2 SU; prior conservative reservations debit 2 SU, leaving 46 SU after acceptance. The primary sweep has not run and is not submitted here.

Execution seal: 9a96e96c93ff4bf79bcc30756cba98a66f81084fa6b81e8b9cc969519d754d95. Eight new builds; 42 nominal OFF/ON processes followed conditionally by 42 selected-case timing diagnostics. Full-app nominal equality, achieved phase and arrival agreement are hard gates. See PROTOCOL.md and COST.json.

Static syntax/matrix/source-boundary checks passed. The timestamp parser was checked against the independently verified archived observer run and rejects a deliberately wrong phase. All 30,067 protected local files remain unchanged. No new build or simulation has run locally. Remote bounded BatchMode succeeded; tracked checkout clean at 8c359a6c650b23c126c862a2c9df6578f0aad2ac; only original stranded 3552462/3552463 pending, untouched.

After acceptance, never resubmit, and do not pull LS6 execution code while active. Return four packed files to a fresh namespace and run verify_return.py with authoritative sacct state. A successful job alone is not scientific qualification. All failed/missing controls remain retained. No paper/publication change.
