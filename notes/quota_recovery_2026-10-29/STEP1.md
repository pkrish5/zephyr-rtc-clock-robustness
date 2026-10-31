# Step 1: verified WORK inventory

Diagnostic job 3540537 completed 0:0 in 00:06:51 on c307-005. All eight
report files matched their SHA-256 manifest after retrieval from SCRATCH.
The scan had no read errors and followed no symlinks.

WORK quota before recovery: 1,024,001 entries against a 1,024,000-file
soft quota. Byte usage remained below quota. Quota is the accounting
authority; the scan separately counted 1,023,999 descendant path entries
(539,981 regular files, 289,282 directories, 194,655 symlinks, 81 other
entries). The scan and quota use different counting methods; the path count must not
be substituted for filesystem quota accounting.

## Top-level directories

The sole directory under WORK is `zephyr-rtc-clock-robustness`, containing
all 1,023,999 counted entries. Its direct subtrees are:

| Directory | Entries including descendants |
|---|---:|
| tacc_work | 991,838 |
| results | 27,365 |
| generated | 2,652 |
| notes | 899 |
| .git | 675 |
| analysis | 204 |
| subjects | 188 |
| harness | 152 |
| materials | 12 |
| paper | 11 |

Source: `returned/scan/work_top_level.csv` and `project_top_level.csv`.

## Largest sources

| Subtree | Entries |
|---|---:|
| E result builds | 325,180 |
| D v2 result builds | 209,431 |
| E per-run runtime directories | 113,116 |
| Old v5 Apptainer temporary tree | 75,496 |
| Earlier D bundle | 67,775 |
| Earlier Phase 2 runtimes | 22,451 |
| Earlier S2 bundle_v3 | 17,275 |
| S2 primary runtimes | 15,403 |

Across the scan's mutually exclusive descriptive categories, build trees
account for 620,375 entries, runtime homes/caches/tmp for 178,904, and
verdict/log/execution evidence for 94,939. Dependency/toolchain trees have
45,002 entries and other caches/package stores 30,727. These categories are
triage, not a deletion manifest. The largest sources match the anticipated
repeated builds, runtime caches and obsolete container-build temporary data.

Sources: `returned/scan/subtree_counts.csv`, `tacc_attempt_children.csv`,
and `categories.csv`.

## Protected exclusions and decision

The immutable baseline has 30,067 paths, of which 29,582 were present and
485 absent on LS6 during this scan. Presence is not a content-hash audit.
The incomplete previous audit-dependency provisioning explains missing
paths; they must not be silently dropped from later protection checks.

No baseline path is under `tacc_work/`. The authoritative frozen sources,
forecasts, root `results/` records, and all other listed protected paths
are excluded from cleanup. The checkout recovery backup
`tacc_work/20261026-git-checkout-recovery-v1` has 44 entries and is excluded
regardless of archival status. Every concrete deletion list must still be
checked against the baseline, frozen bundle inputs and kept ELF/log/hash
metadata immediately before deletion.

The first concrete candidate is only the completed A–B output directory:
`tacc_work/20261024-phase2/ab-bundle/study/results/tacc_phase2_ab_20261024_v1`.
Its existing WORK archive is `tacc_work/20261024-return-v1/ab-results.tar.gz`,
SHA-256 `1704dc2bc2f2b71f7d2fdb6c49319469704603a895defaaf3253f03585fd40ea`.
That archive was already extracted and independently checked on the Mac
in the original A–B return. Reusing it avoids needing a new WORK inode
before cleanup. A compute job must recheck exact file-list coverage and
all extracted content hashes against current originals before pruning.
No ELF, build log, frozen input, backup, or protected path may be removed.
The archive remains on WORK throughout, with an independent local copy.

Step 1's stop conditions are not triggered by this candidate: the largest
sources are expected and the proposed output prefix is disjoint from the
protected list. Further candidates need their own guard and verification;
no broad deletion of `tacc_work`, build trees, or caches is authorized by
the scan alone. No files have been deleted at this checkpoint.
