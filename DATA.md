# Code, data and reproduction

The submission's authoritative analysis is the **final raw-record reconciliation**
in `analysis/final_submission_v1/`. Historical reports remain available and are
not silently updated to the final denominators. The paper is
`paper/draft/main.tex`, with an inline bibliography and generated table fragments
in `paper/draft/tables/`.

## Rebuild every paper table without Renode

Requirements: Git, make, Python **3.11 or newer**, about 1 GB for unpacked
evidence and temporary analysis. Python's standard library is sufficient. No
Renode, Zephyr toolchain, SIF image, TACC account or model API is used.

```bash
git clone https://github.com/pkrish5/zephyr-rtc-clock-robustness.git
cd zephyr-rtc-clock-robustness
make tables
```

`make tables` downloads the pinned release asset named in
[`reproduction/evidence.json`](reproduction/evidence.json), verifies its archive
SHA256 and embedded inventory, verifies every existing/extracted input, checks
the original/recovery union and S2 primary/replay/reference records, then derives
the statistics and regenerates **all eight** table fragments. It refuses to
overwrite a different existing raw input. Analysis outputs use a fresh temporary
directory; only the eight reproducible table fragments and their manifest are
rewritten. Finalized harness-error verdicts are never replaced by diagnostics.

For an offline or cached-asset run:

```bash
make tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz
```

The command ends with `status: PASS`, `rebuilt_tables: 8`,
`all_table_hashes_match: true`, and `renode_runs: 0`. Expected hashes are pinned
in [`reproduction/expected_tables.json`](reproduction/expected_tables.json).
The public-download run was verified on Python 3.12.14 and the fresh-clone
cached-archive run on Python 3.14.6. All eight LaTeX fragments match exactly.
Full-precision illustrative normal-CDF values can differ in the last floating
point bits between these runtimes (observed differences around 1e-17), so the
derived `sensitivity.csv` checksum in the provenance manifest can change. This
does not change raw evidence or any displayed paper table; the generated
manifest records the actual derived bytes. Python must have a working trusted
HTTPS CA store for downloads. The public test selected the bundled trusted CA
roots through `SSL_CERT_FILE`; TLS verification was never disabled.
The archive has 113,433 files, 634,459,796 unpacked bytes. It includes the exact
records, traces, monitor/UART logs, manifests, reference/replay evidence and
source excerpts needed for the final analyses. It excludes the SIF, full Zephyr
checkout, caches and unrelated historical build trees. It is a new publication
copy: no original data were removed or modified to create it.

## Current manuscript v2 (2026-11-04)

The original evidence release `course-submission-2026-11-03-v1` is immutable and
contains an older PDF. The focused course manuscript and source are versioned
separately as `course-paper-2026-11-04-v2`. The evidence archive and its pinned
SHA256 are unchanged. The eight detailed tables remain artifact tables; the
current paper uses three readable views of the same reconciled records.

```bash
make course-tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz
```

This first runs the eight-table reproduction above, then builds the subject,
repair-summary and expanded-scope views, hashes all 17,375 paired primary repair
records, and runs the manuscript claim audit. It executes no firmware or Renode.
The versioned audit, subject identities, paired gains/losses and claim/column
provenance are in `notes/course_subjects_2026-11-04_v1/`. All times are simulated
seconds, oscillator inputs Hz (displayed kHz), and failure/detection cells counts,
not device probabilities. One subject-table row is one original test subject;
its 102 legal settings are repeated measurements, not independent tests.

The HSI contextual paragraph reuses a separate pinned historical study. To
recheck its raw files without modifying the historical summary, run
`python3 notes/course_subjects_2026-11-04_v1/audit_hsi_context.py` before the claim
audit. The committed read-only HSI audit output is included for reproducibility;
the old HSI study is not rerun by either table command.

## Complete file and field catalogue

- [`reproduction/files.csv.gz`](reproduction/files.csv.gz): one row per retained
  Git-tracked `results/` or `analysis/` file, final analysis input, or final
  package output. Columns: `path` (repository-relative), `bytes` (bytes),
  `sha256` (hex digest), `role` (final input/final derived/historical),
  `row_or_file_meaning`, `schema_id`, and `retrieval` (Git or release archive).
- [`reproduction/fields.csv.gz`](reproduction/fields.csv.gz): one row per field
  in each schema. Columns: `schema_id`, `field`, `storage_type`, `units`,
  `meaning`. Join with `files.csv.gz` on `schema_id`. Nested JSON arrays use
  `[]`; dictionaries keyed by run IDs/paths use `{key}`. Deep metadata objects
  remain objects, not invented scalar measurements. Metadata without a
  documented physical unit is explicitly marked as such. The producer and
  frozen protocol remain authoritative for historical metadata.
- [`reproduction/catalogue.json`](reproduction/catalogue.json): catalogue scope
  and size. The catalogue is generated by `catalog_data.py`; it is an inventory,
  not a claim that every historical file is used in the paper.

Read compressed CSVs with `gzip.open(path, 'rt')` and `csv.DictReader` in Python,
or `gzip -dc path`. Empty CSV cells and JSON nulls mean unavailable/not
applicable unless their producer explicitly states otherwise. They are not
zeros or passes. Booleans in CSVs are stored as text `True`/`False`.

## Dataset units, provenance and missingness

| Dataset family | What one record/row means | Important units and interpretation |
| --- | --- | --- |
| `generated/spec_context_factorial_v1/` | One saved source-only generation attempt, with frozen model/task/prompt/repeat identity | Three models, two prompts, five attempts per task; no execution feedback during generation |
| `subjects/phase3_rtc/plan.json` | One frozen shared legal-clock schedule | Integer Hz; seeds 0–99 plus separate min/max endpoints |
| `results/rtc_factorial_v2/records/` | One original suite at one legal clock setting | `lsi_frequency_hz` Hz; `virtual_ns` simulated ns; `wall_seconds` elapsed s; case verdicts retained |
| A–B returned bundle under `artifacts/tacc_phase2_20261024_v1/` | One run for the 16 formerly forecast-only suites | Same frozen inputs and schedule; completes 66 measured eligible suites, without replacing 12 old missing verdicts |
| Original fault result directories referenced by `analysis/rtc_quality_mutant_scores/rows.csv` | One suite under one oscillator/nonarrival fault | Fast 64,000 Hz, slow 10,000 Hz; nominal nonarrival is a separate operator. `early`/`late` in this historical oscillator score mean fast/slow, not calendar offsets |
| `results/rtc_alarm_offset_v1/` | One nominal-clock alarm-compare offset probe | `sign` −1 or +1 **RTC calendar second**; counting is a non-activation control |
| S2 primary bundle, `notes/s2_attribution_2026-10-31/returned-3544535/verified/` | One full application on one board configuration at one setting, with every declared case | 1,122 launches; 3,022 passing, 470 failing, 3,138 skipped case slots. No missing primary slots |
| S2 replay bundle, `returned-replays-3546149-20261102/verified/` | One exact replay of a failing application launch | 274 launches cover 470 failed case slots; original verdicts remain primary |
| S2 reference bundle, `notes/s2_reference_2026-11-02_v1/verified-3547096-v1/` | One task-specific reference application run | All 470 failed primary case slots linked; 277 waiting-reference passes, 88 clean-state cascade passes, 105 rate-reference failures |
| Original E bundle, `verified-original-e-3549010-v1/` | Retained original repair-study primary or diagnostic record | 7,824 finalized primary indices, including 29 finalized harness errors; source/gate/ELF/control evidence retained |
| Seven recovery bundles, `notes/e_resume_2026-11-02_v1/verified-3547925-v1/` through `verified-3547931-v1/` | One newly completed previously unfinished index, or its diagnostic | 9,551 resumed indices; 9,339 pass, 212 fail, zero new missing; old missing verdicts are not retried |

Run provenance records contain node name, Slurm job ID, container SHA256,
Apptainer version, Launcher/module identities, and sealed plan/source/ELF hashes.
Monitor, UART and trace paths refer to saved bytes whose hashes are verified.
Historical absolute WORK/SCRATCH paths are provenance, not required local paths.
The reconstruction uses repository-relative publication copies.

## Final derived files and column definitions

Canonical outputs are in
`notes/final_submission_2026-11-02_v1/phase3_package_v2/`. Each file's complete
column list, stored types, meanings and units is in the catalogue above.

| File | Row/object unit and principal fields |
| --- | --- |
| `per_suite.csv` | Original eligible suite or isolated upstream case: identity/model/prompt/family; `seeded_*` counts over 100; `endpoint_*` counts over two; confirmed/optimistic robustness; slow/nonarrival detection; source/forecast/record provenance |
| `yield_cells.csv` | Model × prompt cell, denominator 15 attempts: working, confirmed robust, optimistic ceiling, robust plus two detections, descriptive nonpadding quality. The ceiling is not a confidence interval |
| `statistics.json` | Final denominators, Fisher exact tables/p-values/exact fractions, paired task results and descriptive Wilson intervals. Probabilities and Wilson bounds use 0–1; counts are integers |
| `paired_per_suite.csv` | One original suite: matched seed discordances. Shared seeds are paired simulator settings, not independent task replications |
| `original_fault_cells.csv` | Cohort/model/prompt × oscillator/nonarrival operator: detected/evaluable/missing counts and descriptive Wilson bounds |
| `original_alarm_offset_cells.csv` | Callback/pending × generated/upstream × offset sign: detected/evaluable/missing counts and Wilson bounds; offsets are RTC seconds |
| `repair_primary_index.csv` | One of 17,375 registered primary evaluations: index, subject/version, operator/condition/seed, outcome, virtual duration, owning record path/hash/job. Diagnostics are not extra primary observations |
| `repair_per_subject.csv` | Subject × V0/V1/V1b/V2/V3: legal seed/endpoint pass/fail/missing counts, fault detections/evaluable denominators, median simulated duration |
| `repair_per_variant.csv` | Variant aggregate over 33 subjects: 3,300 legal seeds and 66 endpoints; faults over 33, offsets over five alarm subjects; median evaluable seeded `virtual_ns / 1e9` in simulated seconds |
| `repair_scope.json` | Frozen scope, control/source/gate/record checks and primary totals; 30 scalar-budget generated suites (27 counting, three pending) plus three isolated upstream cases, no generated callbacks |
| `repair_replays.json`, `repair_references.json` | Diagnostic linkage and agreement per failed primary slot. 458/458 E failures replay; all 112 legal-failure reference links pass |
| `s2_per_case_with_references.csv` | Board/application/case: pass/fail/skip/missing counts over 102, nominal status, failing/passing frequency extrema in Hz, source lines/effective wait, source boundary/category and reference outcomes |
| `s2_by_board.csv` | Configuration-level distinct case counts; runnable means observed runnable at least once. F767 remains an F4 configuration replica |
| `s2_raw_audit.json` | Recount and exact hash/replay/reference checks against S2 archived raw records before table generation |
| `isolated_reconciliation.csv` | One of the original three case names, isolated versus full F4 application: matched 102 settings, seeded/all failures, discordances, last-fail/first-pass Hz |
| `examples.json`, `EXAMPLES.md` | Exact noncontiguous source quotations with line numbers, source identity, observed failure/pass bands and two-sentence explanations |
| `sensitivity.csv` | One failing original/generated/expanded case: boundary/envelope Hz; uniform and illustrative normal expected shares (0–1); explicitly separate conditional-legal, untruncated and observed-interpolation fields |
| `distribution_assumptions.json` | Uniform 17–47 kHz; illustrative normals centered at 32 kHz, sigma 5 or 7.5 kHz. These are assumptions, not measured device distributions |
| `two_axis_per_subject.csv`, `two_axis_counts.csv` | Original legal-clock status × slow-fault detection, per subject and aggregation. Expanded S2 slow-fault outcomes are **not measured**, never inferred |
| `board_survey.json`, `verified_st_documents.json` | Static target counts and verified ST document metadata. Targets are not devices or independent experimental subjects |
| `before_after_numbers.csv`, `unchanged_numbers.json` | Pre-revision/new-value/source ledger and unchanged original counts; old source is saved as `main_before_phaseC.tex` |
| `input_hashes.json`, `output_hashes.json` | Repository-relative input/output SHA256 maps; input ledger is also preserved compressed. The release archive embeds its own exact inventory |
| `manuscript_untouched.json` | Draft/PDF hashes immediately before that offline derivation; the analysis itself never edits either file |

### Scientific interpretation retained in the artifact

S2 categories: **A** independent single-boundary waiting defect; **B**
phase-dependent waiting failure with source-supported envelope; **C** cleanup
cascade, not another independent defect; **D** unresolved firmware/simulator or
accuracy-contract investigation. A failing rate reference is not reclassified
as test brittleness because an eventual-progress reference passes. Phase
carryover is supported by source and reconciliation, not directly measured.

Counter configurations are **non-stock RTC-only**. H753 uses the frozen DS12117
Rev 10 revision-V temperature/voltage envelope. Board replicas are never pooled
as independent tests. Generated tests were written from scratch from frozen
specifications derived from the documented purposes of the original three
upstream tasks; this does not establish comparability across all developer tests.

## Analysis stages and commands

`make tables` runs these stages automatically, in this order:

1. `reproduce.py`: archive SHA256, safe exact restoration, per-file hashes.
2. `repair_study.py`: original/recovery ownership union; source/ELF/gate/control
   checks; 17,375 primary outcomes, replay/reference checks, durations.
3. `audit_s2_raw.py`: primary counts/frequency bands, raw log hashes, all replay
   fields/UART/trace bytes, all failed-setting reference links.
4. `base_study.py`: frozen original+completion schedule, raw record hashes,
   original fault and offset scores, yields/Fisher/Wilson/paired statistics.
5. `s2_and_sensitivity.py`, `number_changes.py`: attribution, reconciliation,
   examples, assumed distributions, two axes and before/after ledger.
6. `render_tables.py`: eight LaTeX fragments; exact expected-hash comparison.

For manual analysis-only output, invoke `build_package.py --help`. It requires
a **new** output directory, the verified original bundle and exactly seven
recovery directories. Use `--comparison-manuscript
notes/final_submission_2026-11-02_v1/main_before_phaseC.tex` for the historical
number ledger. The wrapper is the shorter, fully specified command.

To reproduce packaging/cataloguing from an existing reconciled checkout:

```bash
python3 -B analysis/final_submission_v1/catalog_data.py \
  --inputs notes/final_submission_2026-11-02_v1/phase3_package_v2/input_hashes.json \
  --package notes/final_submission_2026-11-02_v1/phase3_package_v2 \
  --out reproduction
```

## TACC execution provenance and re-execution

Rebuilding tables does **not** submit jobs. Existing experiments used Lonestar6,
allocation TRA25006, whole-node Launcher packing with 32 concurrent workers,
Renode v1.17.0, `tacc-apptainer/1.4.1` and `launcher/3.10`. The calibrated image
SHA256 is `94d7894eda71b918f3f9273f29e5c4db3e7d74597ca0b799dcb504027f30aaa1`.
Linux packaging versus local macOS packaging was disclosed and calibration
validated; package differences are not silently treated as identical binaries.

Read `paper/DESIGN.md` and the stage-specific protocols before any re-execution.
Historical scripts/receipts explain exact sealed bundles, environment variables,
module/image hashes, task selections and job IDs:

- Image/resource/calibration: `harness/tacc_phase1/README.md`, definition files,
  `build.sbatch`, `probe.sbatch`, `calibration.sbatch`.
- Original A–B/D/E: `harness/tacc_phase2/` and its saved submission receipts.
- S2 qualification/production: `harness/tacc_s2/README.md`,
  `harness/tacc_s2_production/`, and dated `notes/s2_qualification_*` notes.
- S2 archive/replays/references: `harness/tacc_s2_evidence/`,
  `harness/tacc_s2_references/`, `notes/s2_reference_2026-11-02_v1/`.
- Quota-interrupted E recovery: `harness/tacc_e_resume/`, frozen packet in
  `notes/e_resume_2026-11-02_v1/packet/`, and its STATUS/protocol amendments.
- Read-only original collector: `notes/final_submission_2026-11-02_v1/`.

In an already authenticated human-established LS6 session, the common setup is:

```bash
module load tacc-apptainer/1.4.1 launcher/3.10
export RTC_REPO="$WORK/zephyr-rtc-clock-robustness"
cd "$RTC_REPO"
```

Each specific script requires the sealed image/bundle/plan/chunk variables from
its receipt; do not reuse a completed output namespace. Submission syntax is
`sbatch -A TRA25006 --partition=development ...` for qualification, and
`sbatch -A TRA25006 --partition=normal ...` for an approved production plan.
Whole-node SUs are estimated before normal submission. Recovery chunks were at
most three hours. This documentation is not approval to rerun a completed job.

The storage wrapper `harness/tacc_storage/run_packed.sh` sends builds/caches/
temporary outputs to SCRATCH or node-local storage, verifies packed archives,
checks WORK headroom and publishes final archives on WORK. Final evidence must
never exist only on SCRATCH. Never prune without exact archive/hash verification.
Never modify frozen sources, forecasts or finalized records. Missing outcomes
stay missing. SSH commands must use BatchMode and stop on authentication failure;
the user performs MFA. No new experiment is authorized by this reproduction guide.
