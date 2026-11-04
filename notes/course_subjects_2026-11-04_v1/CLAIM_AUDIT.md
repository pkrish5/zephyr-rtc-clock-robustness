# Course manuscript v2: claim and concern audit

Date: 2026-11-04. Existing-data revision only. No Renode execution, new
experiment, generation, or replacement verdict. The manuscript is
`paper/draft/main.tex`; its PDF is at the same path stem. The old evidence
release and its original PDF remain unchanged. Current manuscript release:
https://github.com/pkrish5/zephyr-rtc-clock-robustness/releases/tag/course-paper-2026-11-04-v2

## Primary subject-level evidence

One row is one subject, not a sampled frequency. The same 100 frozen settings
plus two endpoints are paired across V0/V1/V1b/V2/V3.

| Subject | V0 legal failures / 102 | Each repair's legal passes / 102 | Slow fault: V0 to every repair |
|---|---:|---:|---|
| Upstream alarm callback | 27 | 102 | detect to detect |
| Upstream alarm pending | 27 | 102 | detect to detect |
| Upstream calendar counting | 18 | 102 | detect to detect |
| Sol base pending r01 | 12 | 102 | detect to detect |
| Sol base pending r03 | 14 | 102 | detect to detect |
| Astra base pending r05 | 14 | 102 | detect to detect |

There are zero missing legal or slow-fault outcomes in these six subjects.
Their 612 subject-setting pairs are repeated measurements on six subjects;
500/112 original pass/fail outcomes become 612 passes in each repaired variant.
No independence claim or six-subject population success rate is made.

The separate 11 slow-fault gains are generated counting subjects with 102/102
original legal passes and no missing legal verdicts. V1 preserves their original
40-60 second ceilings and their original sources; V1b uses 20.824 seconds and
adds no assertions. On 32 common V1/V1b slow-fault pairs: 21 retained, 11 gained,
zero lost. The 32 common V1b/V2 pairs already detect the slow fault before
polling changes. A missing V1b outcome explains V2's denominator increase to33.
This is deadline sizing evidence, not a polling detection gain. It does not
imply naive extension harmed the six repaired subjects.

V3 adds both signed offset detections in the upstream callback (each sign4/5
to5/5). Readback and calendar checks were bundled; their individual causal
contributions are unresolved. Every evaluable fast fault is accepted. No
adjacent common-evaluable tested fault loses detection, which is not proof
against all possible defects.

Sources: final reconciled `repair_primary_index.csv`, per-subject/per-variant
CSVs, mechanical `notes/repair_execution_20261024_v2/variants.json`, replay and
reference ledgers. `claim_to_evidence.csv` maps quantified claims to exact
input hashes; `manuscript_numbers_v2.json` contains executable audit results.

## Concrete upstream wait

The frozen source is
`subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c`.
Its exact definitions are:

```c
#define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
#define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)
```

Line120 sleeps for the first constant, lines126-129 check no early callback,
line132 sleeps for the second, and lines140-141 require callback arrival.
One iteration therefore checks arrival after3+10 virtual seconds. With the
32,000 prescaler, a ten-calendar-second target ideally takes320,000/f virtual
seconds:18.823529... at legal17kHz, or32 at injected10kHz. The figure illustrates
zero subsecond phase and excludes delivery latency; it is not an arrival-time
measurement. The repair retains the early check and replaces the final wait
with the remaining deadline budget. V2 can finish on the completion predicate.
The20.824-second deadline is18.824 rounded up to milliseconds plus two seconds
of **unvalidated experimental allowance**, not a guaranteed delivery bound.

## Response to Professor Shi's concerns

| Concern | Response and evidence limit |
|---|---|
| Three developer subjects are too few | State selection explicitly. Expansion has19 declared names and10 distinct ever-runnable names, with4 distinct waiting-sensitive names. Only the original3 upstream cases are repaired. No prevalence estimate or random-sample claim. |
| Count failures correctly | Report capability skips separately. Waiting reference links277pass; clean-state cascade links88pass; rate links105fail. Cascades are not additional independent waiting defects; counter-seconds remains firmware/simulator/accuracy-contract investigation. F767 is an F4 configuration replica. Full/isolated original F4 failure counts appear side by side; phase is source-supported, not measured. |
| Uniform LSI may be unrealistic | Lead with boundaries/bands. No device population distribution was measured. Uniform and legal-conditioned normal calculations remain illustrative artifact analyses. ST datasheets supply envelopes, not a measured density. |
| Generated tests may not be comparable | Restrict their context to one paragraph. They were generated from purpose-derived specifications without upstream source, with stronger requested observables and no same-spec human baseline. Do not infer model superiority or a numeric-range-only prompt effect. |
| Why LSI rather than HSI? | Pinned HSI context uses +/-1% at25C and integer99-101MIPS over different tasks, versus17-47kHz RTC input variation with fixed CPU/SysTick. HSI shows0/943 upstream and0/3270 generated evaluable seeded assertion failures, with87 non-evaluable seeded outcomes retained. It does not rule out HSI sensitivity or isolate oscillator choice causally. |
| What generalizes beyond this model? | None of the board configurations supplies independent silicon validation: all use the same existing STM32F4 RTC model. Counters are non-stock RTC-only configurations. Repair evidence concerns the one RTC API driver and original isolated contexts. |
| Is this actual flakiness? | No within-setting nondeterminism was measured. Deterministic cross-frequency verdict changes are timing sensitivity that could cause unreliable outcomes across operating conditions. |

## Reproduction and integrity

- `make tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz`
  verifies113,433 archived inputs and all8 original table hashes, without Renode.
- `make course-tables EVIDENCE_ARCHIVE=...` additionally rebuilds3 readable views,
  audits17,375 paired primary record hashes and checks manuscript quantities.
- `audit_hsi_context.py` invokes the historical verifier read-only, redirecting
  derived outputs here. All4,606 HSI record inputs/traces are audited; the100
  unstarted seed slots of a nominal-ineligible candidate are not included in
  the87 non-evaluable qualified seeded outcomes.
- All458 repair failures replay identically; all112 legal-failure reference
  links pass. The29 finalized repair harness errors remain missing.
- The original30,067-file protection ledger passes before and after revision.
- Citation metadata: retained DOI registrations checked against Crossref for
  title/authors/venue/year/pages. Publisher landing pages return403 to automated
  requests; this is recorded rather than presented as an unconfirmed DOI.
  Official ST PDFs/index confirm document titles and consulted revisions;
  corrected canonical URLs replace misleading old slugs. RM0090 is explicitly
  the consulted Rev21, not asserted latest. All citation keys resolve.

The evidence archive SHA256 remains
`805b776337f049164014fea9e2d29ca34ba750beb504e3477064015c46bdc921`.
See `final_validation.json`, `make_course_tables.txt`, `citation_url_audit.json`
and the new release checksums for the exact final source/PDF bytes.

## Remaining limits and exact small experiment for a stronger claim

The subject selection is purposive; scalar budgets favor mechanical repair.
No same-spec human cohort, hardware validation, population frequency sample,
measured delivery bound, phase trace or comprehensive fault oracle exists.
Shared frequencies/models and related generated tests are not independent
replication. The two-second allowance is not validated outside tested settings.

To test **within-setting** nondeterminism, preregister the following small
experiment before any execution (proposal only; not run or registered here):

| Frozen V0 subject | Four preselected frequencies, Hz |
|---|---|
| Upstream callback |17000,32000,24428(last fail),24734(first pass)|
| Upstream counting |17000,32000,21782(last fail),22405(first pass)|
| Sol base pending r03 |17000,32000,20701(last fail),21402(first pass)|

Run20 fresh Renode processes per subject-frequency cell:240 launches, unchanged
ELFs, harness, CPU/SysTick and quantum. Freeze run order/seed, retain every
outcome, all hashes and errors, and compare pass/fail outcomes within each
identical cell. A mixed pass/fail cell would support nondeterminism for that
cell;20 identical outcomes would not prove its absence. Estimate node time and
SUs from the existing resource probe and the selected subjects' saved wall
times, register the dated protocol and obtain required queue approval before
submitting. The completed100-frequency and repair studies need no rerun.
A same-spec human baseline or measured device-frequency distribution would
require separate new evidence; neither is claimed by this paper.
