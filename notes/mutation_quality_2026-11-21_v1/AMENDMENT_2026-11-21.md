## 2026-11-21 Quality-metric study (mutation score, driver line coverage): registration for approval, before any build or run

Purpose. Add an established test-quality metric alongside the hand-picked fault
probes, per the course instructor's request. No firmware has been built or run
for this study. Frozen sources, forecasts, protected files and raw records stay
unchanged; all outputs go under `notes/mutation_quality_2026-11-21_v1/` and a new
`results/mutation_quality_2026112x_v1/`. Missing outcomes stay missing.

Operators and citation. First-order source mutants of the two pinned Zephyr
v4.3.0 drivers our tests link: `drivers/rtc/rtc_ll_stm32.c` (RTC API) and
`drivers/counter/counter_ll_stm32_rtc.c` (counter). The operators are the
type-free subset of Agrawal, DeMillo, Hathaway, Hsu, Hsu, Krauser, Martin,
Mathur and Spafford, *Design of Mutant Operators for the C Programming
Language*, Purdue SERC-TR-41-P (Rev. 1.04, 2006; first edition 1989), checked
against that report's text: Ocor binary-operator replacement (Table 4: ORRN,
OAAN, OBBN, OLLN, OSSN, OAAA, OBBA, OSSA; each operator replaced by every other
in its class), OLNG (10.2.2: `x op !y`, `!x op y`, `!(x op y)`), OCNG (10.2.3:
negated controlling condition of if, while, do-while and the for condition; the
`?:` form is not implemented) and SSDL (9.3: each statement deleted, semicolon
kept). CRCR, VTWD and the other variable/constant operators need type
information and are not used. Mull (LLVM in-process runtime) cannot execute in
bare-metal firmware under Renode, so no existing tool is used; a
source-to-source generator (`generate_mutants.py`) implements the operators.

Generation rules. Mutants are generated mechanically at every site the rules
match; none is chosen by hand. A site is eligible only on a line that the C
preprocessor keeps under a recorded configuration of an application that links
the file: the RTC counting and RTC alarm (`CONFIG_RTC_ALARM=y`) configurations
of the factorial build, and the counter_basic configuration of job 3598828.
Preprocessor directives, comments, strings and code outside function bodies are
not mutated; an SSDL site whose statement spans a preprocessor directive is not
generated (14 sites, listed). Textually identical mutants are merged.

Exclusions and equivalent mutants. (1) A mutant that the production compiler
(Zephyr SDK 0.17.4 GCC, pinned container, recorded driver flags) rejects is
excluded as a compile failure and counted. (2) Trivial Compiler Equivalence
(Papadakis, Jia, Harman, Le Traon, ICSE 2015, doi:10.1109/ICSE.2015.103): per
configuration, a mutant whose driver object code (sections other than debug)
equals the original's is equivalent and excluded; mutants whose object code
equals another mutant's are duplicates and only the first by id is run. (3) A
mutant on a line inactive in a suite's configuration is not compiled into that
suite and is reported as not applicable. (4) Coverage rule: a mutant is covered
by a suite iff its line executed when the unmutated suite ran at 32 kHz
(below); uncovered mutants are reported as uncovered, never as killed or
survived, and are not run against that suite. A line with no DWARF address
takes the status of the nearest preceding addressed line in the same function.

Test sets. (a) The three upstream developer tests (alarm callback, alarm
pending, calendar counting); (b) the 34 eligible base-prompt (`range_absent`)
generated suites and (c) the 32 eligible clock-range-prompt (`range_present`)
suites of the RTC factorial (counts from
`analysis/rtc_factorial_v2_final_summary.json`). (e) The counter driver is
linked by none of (a)–(c); it is scored only with the unchanged upstream
counter_basic application (V0) at 32 kHz. Optional (d), the V0–V3 repair
variants of the 33 repair subjects, is not requested here (cost below).

Execution and outcomes. Unchanged ELF build recipe, container, Renode 1.17.0,
board, 16-MIPS setting, quantum and step as the factorial; only the linked
driver source differs (the existing configure-time driver substitution used by
`harness/rtc_driver_variants/`). One run per (suite, covered mutant) at the
nominal 32 kHz setting. Per run: killed-fail (any case verdict differs from the
original's pass), killed-crash (fault, reset or no suite completion),
killed-timeout (virtual-time cap reached), survived (identical pass vector),
build-failure, or harness-error. Harness errors are missing, never survivors.
Each unmutated suite also runs once in the same job as an in-job baseline; a
baseline that does not pass flags that suite's results.

Metrics. Mutation score = killed / (killed + survived) over compiled,
non-equivalent, covered mutants, per suite, at 32 kHz; reported per set as
median and interquartile range, per task as the upstream suite versus the
distribution of matched generated suites, and as the set-level union (with its
size caveat). Sensitivity: score with timeouts excluded. Driver line coverage =
executed / addressed lines of each driver per suite (median, IQR, set union),
from Renode's execution tracer (`CreateExecutionTracing ... PC`, binary,
compressed) and `tools/execution_tracer` `coverage` (LCOV DA) shipped with
Renode 1.17.0 on the unmutated ELFs. Optimised (-Os) line attribution is
approximate; the ELFs are the measured ones, not rebuilt at -O0.

Kill verification. After job B returns and its records verify, a sealed random
10% of kills per set (at least 30 per set, at most 1,000 total) plus every
killed-timeout up to the same cap is replayed once; disagreements are reported
and those mutants are classed unstable, not killed.

Run plan (allocation to be confirmed by the user; TRA25006 and OTH24028 are
not used). Dry run, done locally with no firmware: 909 RTC-driver and 346
counter-driver mutants generated; all pass a clang syntax proxy; production GCC
compile and TCE pending. Job A (development, 1 node, <=2 h, <=2 SU): GCC compile
and TCE of all mutants, configure every app, one traced coverage run per suite,
40 timed mutant runs; report exact covered counts and recost, then STOP. Job B
(normal, 1 node): builds and mutant runs for (a)–(c) and (e). Upper bound before
coverage filtering 43,877 RTC runs (41 alarm suites x 909 + 28 counting suites x
236) plus 346 counter runs; at 75 s mean wall (45 s median observed plus
timeout allowance), 32 workers and 4 s per incremental build this is 30.6
node-hours, 45.9 SU with the usual 1.5 safety factor. If 40% of mutants are
covered per suite, about 18.7 SU. Job C (normal, <=2 SU): kill replays. Total
expected about 22 SU; requested ceiling 50 SU. Option (d) adds about 132 apps and
roughly 40–95 SU and is deferred.

Already-collected data (no runs): generated-test flakiness by prompt, slow-fault
detection by prompt, and over-padding counts by prompt and model will be
recomputed from archived records with scripts in the same directory.
