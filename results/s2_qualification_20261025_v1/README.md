# S2 development qualification evidence, collected 2026-10-26

These are qualification outcomes, not the 100-setting production experiment.
No production job is authorized by these files. E and E2 were untouched.

- 3533587 built all 17 configurations, then failed the version-string guard
  before firmware. Its evidence is retained under `first-attempt/` in the archive.
- 3533590 completed the resource probe with approved Linux runtime metadata.
- 3533596 reached the 90-minute limit during calibration; incomplete and
  unstarted runs remain missing. No retries replace these originals.
- 3535059 is an audit-only development job, completed 0:0 in 54 seconds. It
  verified and copied evidence and ran the sealed reporter against the copy.
  It ran no firmware and performed no builds.

`evidence_v1.tar.gz` SHA-256:
`be4c26e901f65bddfb0319bca2d0f94c380d76c9b74f84bf81749ce5feaa85f2`.
The archive contains all 139 finalized run records and their UART, monitor,
trace, process/resource, generated configuration and build/ELF evidence,
plus partial logs for interrupted launches. `archive-files.sha256.json`
contains 1,583 verified file hashes. The sealed reporter's outputs are copied
here for convenience and retain their original bytes.

The archive's `raw/` directory is a snapshot. The derived qualification report
was created in this copy, not in the original stopped job's output directory.
Runtime cache inventories preserve publicly fetched SVD data, including F7's
STM32F7x6.svd.gz; those F7 bytes were not pre-frozen in the original F4-only
cache. All completed F7 runs used the same returned F7 SVD hash.

Reproduce the local summary without running an experiment:

```sh
sha256sum -c evidence_v1.tar.gz.sha256
tar -xzf evidence_v1.tar.gz
python3 ../../harness/tacc_s2_evidence/summarize.py \
  --evidence evidence_v1 --out /path/to/new-summary-directory
```

See `analysis/s2_qualification_20261026_v2/REPORT.md` for the checkpoint,
exclusions, missingness and conditional workload/cost estimates. All printed
case-level verdicts in incomplete UART logs remain available; they are not
promoted to five complete nominal application runs.
