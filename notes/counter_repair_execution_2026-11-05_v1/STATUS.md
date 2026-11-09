# Conditional recovery approved, 2026-11-09T12:05:16.310349-06:00

The human replied “yeah repair” to the concrete conditional proposal. Approval
is recorded in approval.json for exact plan SHA
037f96a96a1596ced1e82e6a379641ca959a31d36aa3c24fb67b6649835fc1fc:
normal/TRA25006, four one-node jobs,32Launcher workers;20nominal gates1h,
153legal3h,153legal3h,8fault1h; estimate5.984790SU, ceiling8SU. The earlier
diagnostic ceiling0.25SU is separate. No additional normal approval is needed
for these groups within this scope, but every downstream submission remains
blocked until all20nominal gates pass independent verification.

Original scientific plan, four ELFs, settings, workers and original jobs remain
unchanged. Publish/pull this approval, verify the original code/plan before and
after pull, then submit gate ONCE and retain its exclusive intent and receipt.
Do not invoke a helper again if acceptance is uncertain. Do not change sealed
execution code or pull LS6 while a recovery job is pending/running. Existing
watcher may monitor/verify only; it cannot submit or cancel normal jobs.
