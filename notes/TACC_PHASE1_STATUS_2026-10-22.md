# Lonestar6 Phase 1 preparation, 2026-10-22

The implementation and prospective calibration amendment are in
`harness/tacc_phase1/` and `paper/DESIGN.md`. The manuscript and its existing
uncommitted edits were not changed during this preparation. No firmware
generation, Renode simulation, container build or Slurm submission has run.

Original binaries exist locally and were checked against the saved hashes,
including all 16 forecast-only binaries. The planned calibration selects
the three flipping pending suites and five complete-passing suites across
model/prompt/task strata, with 102 settings per suite. The resource probe
has its own namespace. Runtime and calibration records cannot be retried
or replaced in place.

The user authorized reuse of `ssh ls6`, restricted all remote work to
`$WORK/zephyr-rtc-clock-robustness`, and authorized development jobs under
`TRA25006`. Pin `tacc-apptainer/1.4.1` and `launcher/3.10`; require separate
approval before any normal-queue job.

The first noninteractive read-only SSH preflight stalled after printing:

```text
/work is mounted not "FULL" nor "IDLE"!
```

It returned neither the requested WORK path nor repository status. Only
the agent's own stalled SSH client was terminated. No SSH/account setting
was edited, no authentication was attempted, and no reconnection was
attempted after reporting the problem. Await the user's confirmation that
the existing session can execute a command normally before remote work.

Official release metadata verified during preparation: Renode Linux
portable archive SHA-256
`4ba7c68b59e2447f188ef4b4b112fcccd2802582c460beedceb63b84e5605a5f`;
SDK 0.17.4 Linux x86_64 minimal archive SHA-256
`a7258bf50c892c4669712b2aacdfcd5e303245bcf36cb458a296039a664594f5`.
The Renode Linux archive embeds .NET 8.0.12, while the original environment
reported .NET 8.0.21. The image definition therefore selects the external
8.0.21 runtime, with a strict version check before the resource probe.
This Linux image has not yet been built or validated; no image hash or
calibration agreement is claimed.

## User-authorized SSH retry, 2026-10-22

After the user requested another attempt, a noninteractive read-only check
returned `WORK=/work/10970/pk23377/ls6` and `/usr/bin/sbatch` with exit 0.
The conditional repository HEAD check printed no HEAD, so the expected
checkout has not been confirmed. A subsequent read-only directory check
timed out after 35 seconds without output; its SSH client was terminated
by the timeout. Authentication prompts were disabled. Remote work stopped
again under the user's connection-failure rule. No remote files were
modified, no bundle was transferred, and no jobs were submitted.

## Connection restored and first development build, 2026-10-22

On the next user-authorized retry, SSH succeeded. The authorized project
directory was absent; it was initialized there and populated using
`git pull` from the public repository at d4fd0a8319f714a96d9c94f2f13526e579ae05ae.
The sealed v1 input bundle transferred successfully. Development job
3529750, allocation TRA25006, stopped during pinned module loading with
`BASH_COMPLETION_DEBUG: unbound variable`; no image or Renode run occurred.

The module wrapper now suspends nounset only during module loading.
Ten infrastructure unit tests and shell syntax checks pass. A separate
v2 bundle preserves the same 816 calibration tasks and expected local
verdicts (776 pass, 40 fail), with plan SHA-256
`35f10f450591f8c3f393e813c2e6a3a77d79dde1343b98fdc48780c7fb434fb8`.
The next attempt uses `tacc_work/20261022-v2`; v1 and its job logs remain.
