# Fresh three-model, two-context factorial: generation and gates

**Status:** 2026-10-04 UTC. This report stops after generation, source review, build, and nominal gates. No new factorial Phase 3 varied-timing run has started.

## Frozen design and audit

The approved design used 13 fixed Zephyr tasks, three separately registered model cohorts (Luna, Sol, Astra), two prompt conditions (documented clock range absent/present), and five fresh generations in every task/model/condition cell: **390 outputs**. The historical 65 Luna suites, the RTC bound-context supplement, and the earlier Sol pilot are excluded. All 390 new prompt deliveries used direct-argument `codex-cli 0.158.0-alpha.2.1`; model calls ran from 2026-10-03 19:02 to 2026-10-04 02:03 UTC. The CLI did not expose an exact server snapshot or sampling seed. Every completed output has frozen prompt and source hashes, response/events, date, and token usage; none used tools.

`python3 analysis/factorial_generation_audit.py`, `python3 analysis/factorial_source_review.py`, and `python3 analysis/factorial_gate_summary.py --require-complete` pass. The last audit checks that each build and nominal run uses the frozen source and ELF hashes. The saved call order, inputs, metadata, build logs, UART, monitor transcripts, and nominal traces are under `generated/spec_context_factorial_v1/` and `results/spec_context_factorial_v1/`. Raw records were never hand-edited or overwritten.

## Gate attrition

All cells planned 65 outputs. “First nominal” is pass on the first fresh run among built suites; “5/5” requires all five original nominal outcomes to be pass. By protocol, only the 330 built suites labeled functionally adequate received five repeats; 30 built but source-inadequate suites had one nominal run, and 30 did not build. Thus an unscreened suite's 5/5 status is **unmeasured**, not a five-run failure. The original strict gate additionally requires no source timing issue found. The amended primary gate requires functional adequacy but **does not filter on timing-bound adequacy**. See the [prestart reconciliation](PHASE3_PRESTART_GATE_RECONCILIATION.md) for every source-inadequate suite and the exact Boolean gate audit.

| Model | Range in prompt | Built | First nominal pass | 5/5 nominal pass | Original strict eligible | Amended functional eligible |
|---|---|---:|---:|---:|---:|---:|
| Luna | Absent | 52 | 41 | 38 | 25 | 38 |
| Luna | Present | 50 | 41 | 37 | 27 | 37 |
| Sol | Absent | 65 | 64 | 59 | 28 | 59 |
| Sol | Present | 65 | 63 | 62 | 31 | 62 |
| Astra | Absent | 65 | 65 | 63 | 30 | 63 |
| Astra | Present | 63 | 62 | 62 | 34 | 62 |
| **Total** | | **360/390** | **336/390** | **321/330 screened** | **175/390** | **321/390** |

Source review labels across all 390 outputs are **330 functionally adequate and 60 inadequate**. Independently, timing-bound review found **154 inadequate, 177 with no issue found, and 59 unknown**. Within the 321 amended-eligible suites, those timing labels are **105 inadequate, 175 no issue found, and 41 unknown**. This is why the strict gate loses 146 nominally runnable, functionally adequate suites, including many with the timing assumptions RQ2 is meant to challenge. A source-only timing label is a candidate mechanism, not an observed pass-to-fail flip.

The ten HSI tasks and three correlated RTC cases remain separate strata. The amended eligible counts for HSI are Luna 68/100, Sol 91/100, Astra 96/100; for the RTC stratum they are Luna 7/30, Sol 30/30, Astra 29/30. These are output yields for one Zephyr repository and board, not independent-project success rates. The `range_present` prompt has fewer `inadequate` source tags in every model's 65 outputs (Luna 26 versus 34, Sol 21 versus 30, Astra 18 versus 25), but unknown counts differ and the reviewer could see model/condition labels. This descriptive pattern is **not** an RQ2 robustness result or a model ranking.

## Failures, missingness, and review corrections

Thirty frozen sources failed compilation. Among the 360 builds, the first nominal outcomes were 336 pass, 23 assertion fail, and one timeout. The 30 source-inadequate builds account for 12 first-run passes, 17 assertion failures, and the timeout; none received repeats. The five-repeat records for source-adequate builds contain six virtual-zero harness errors: four at call 67 from a Renode history-file permission mistake during late repeat completion, and one each at calls 153 and 155 from monitor startup timeouts. Original outcomes remain non-passes for the 5/5 gate. Separate exact-ELF diagnostics passed **5/5** for call 67 and **1/1** each for calls 153 and 155; they do not replace the six registered errors. The diagnostic summaries and raw traces are under `results/spec_context_factorial_v1/diagnostic_call67/`, `diagnostic_call153_repeat003/`, and `diagnostic_call155_repeat002/`. The sole saved nominal timeout, call 69, remains a timeout; no diagnostic pass has been substituted.

After inspecting complete build logs and **before any factorial varied run**, the first reviewer corrected seven executable-assertion labels: six `met` → `not_met` and one `not_evaluable` → `not_met`, all due to frozen compile errors. Old/new labels, dates, and compiler reasons are retained in `analysis/factorial_source_decisions.json` under `adjudication_history`. Timing labels were unchanged. This was an unblinded build cross-check, not a source repair or outcome-driven Phase 3 selection. The frozen sources, builds, and nominal records are unchanged.

The user's 30-item independent RQ1 form at `analysis/blind_rq1/labels.csv` is still the blank 280-byte template in this workspace. The first reviewer's withheld key has not been opened for agreement analysis or disclosed. Cohen's kappa and item disagreements remain pending the completed independent labels.

## Generation usage and limits

| Model | Completed calls | Input tokens | Cached input tokens | Output tokens |
|---|---:|---:|---:|---:|
| Luna | 130 | 1,807,409 | 1,462,272 | 91,003 |
| Sol | 130 | 1,831,733 | 1,393,920 | 226,680 |
| Astra | 130 | 1,889,111 | 874,496 | 173,424 |
| **Total** | **390** | **5,528,253** | **3,730,688** | **491,107** |

Two interrupted Sol attempts at call 253 emitted no completion or usage; their possible account consumption is unknown. A separate initial sandboxed CLI attempt failed before a model event. `notes/API_COSTS.csv` logs the completed calls. The authenticated ChatGPT CLI did not return billed dollars or a credit debit, so a dollar total cannot be inferred from these token counts.

## Review boundary

The next registered step is to run only amended-eligible frozen suites on their locked 100-seed task schedules, with exact endpoints outside rate denominators, replay every failure, preserve harness errors as unknown/non-evaluable, and report upstream paired comparisons and both gate views. **Wait for user review before starting those Phase 3 runs.**
