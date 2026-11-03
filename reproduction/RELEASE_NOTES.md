# Course submission: clock robustness and alarm precision

Verified submission artifacts for the five-page paper (including references).

- All 66 eligible generated suites are now measured; 3/34 base versus 0/32 range-prompt suites flip (Fisher p=0.2391608392).
- The paired 33-subject repair study reconciles all 17,375 primary evaluations; 29 finalized missing outcomes remain missing.
- S2 retains per-configuration case/skips and reference attribution; failed rate references remain firmware/simulator/contract investigations.
- The PDF has 23 resolved inline references, zero unresolved citations and zero overfull boxes.

## Reproduction

Download `rtc-submission-evidence-v1.tar.gz` and run:

```bash
make tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz
```

The command verifies every archived input and rebuilds all eight paper tables without Renode. DATA.md contains the file/field catalogue, units, missingness rules and TACC provenance. Archive SHA256:

`805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921`

No E2 arm or new experiment was performed for this release. Expanded S2 slow-fault coverage is not measured. F767 is an F4 configuration replica; phase carryover is source-supported, not directly measured. No physical-board validation is claimed.
