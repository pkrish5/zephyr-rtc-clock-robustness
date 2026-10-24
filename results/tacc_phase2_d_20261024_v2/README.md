# Phase 2 D: disabled-fault controls

Job 3532515 (development, TRA25006) completed on 2026-10-24: all 216 builds and 216 nominal controls passed. The cohort contains 66 generated suites, three upstream cases, and three references for each of three disabled implementations. Original failed cache-path attempt records remain separate and were not replaced.

`evidence.tar.gz` contains 2,596 raw-output, record, build-log and app-input files. Its SHA-256 is in `evidence.sha256`. `report.json` and `breakdown.json` were independently reproduced from the returned raw files on the local machine; `local-verification.json` records agreement. `plan.json` and `plan.sha256` preserve the sealed D v2 task/input manifest.

The compute packing job 3532546 verified all 216 build ELF and log hashes. Compiler intermediates and ELFs are excluded from this transfer and remain immutable on LS6 under the original WORK result prefix. This archive does not claim to include those binaries. No firmware executions occurred during packaging or local verification.

To audit the scientific records without building firmware, extract the archive into a new temporary bundle's `study/results/` directory, copy `plan.json` and `plan.sha256` to that bundle's root, then run:

```sh
python3 harness/tacc_phase2/report.py --bundle /path/to/temporary-bundle
python3 harness/tacc_phase2/summarize_d.py --bundle /path/to/temporary-bundle
```

The archive retains its `tacc_phase2_d_20261024_v2/` top-level directory. Both commands read existing records and verify trace/UART/monitor hashes; neither runs Renode. Checking the generated ELF hashes additionally requires the excluded remote binaries.
