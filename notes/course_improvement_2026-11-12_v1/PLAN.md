# Six-page class-paper improvement plan (2026-11-12)

## Objective and claim boundary

Improve the current five-page class report without changing frozen primary outcomes or treating simulated board configurations as independent hardware. Keep one STM32 RTC driver, the shared Renode model, and six total PDF pages including references. The fourth upstream counter case remains a separate extension. The earlier 10-kHz progress control missed its preregistered bound by 18 ms and remains a failed control in the record.

## Ordered work and stopping rules

1. Register a focused, independent, bracketed counter-rate control before writing its source or running it. Run exactly five fresh 32-kHz nominal processes, three 10-kHz slow processes and three 64-kHz fast processes. Use the original Zephyr revision, RTC-only configuration, platform/model, Renode image, CPU/SysTick and counter driver. Preserve all eleven outcomes, including failures and missing records. No adaptive repeats and no rerun of the 102-setting repair schedule. Pass/fail rules and cost ceiling live in `PROTOCOL.md`.
2. Audit the returned archive and the old 18-ms violation side by side. A qualified new measurement can support a **new bracketed activation-control result**; it does not retroactively pass the old control or prove callback delivery, fault realism, or hardware behavior. If the new control fails, keep the counter slow-fault claim unresolved.
3. Explain why each seeded operator probes a property and why none estimates natural defect prevalence. Show the upstream callback's actual assertion and a source-derived timing example; label ideal times as illustrative. State that the two-second delivery allowance is unvalidated. State the genuine TACC account/provenance.
4. Update the abstract, counter results, limitations, conclusion and claim audit only after the control audit. Keep LLM comparison secondary. Rebuild eight tables and paired counts, compile the PDF, inspect every page, and enforce <=6 pages. Publish a new versioned manuscript; leave v3 immutable.

## Page budget

The current PDF has five pages. Target at most roughly 250 net new words, using the existing timeline and counter paragraphs rather than adding a new figure or table. Reserve around 80 words for the focused control result, 75 for fault purpose/relevance, 40 for concrete trace/threshold clarification, and one provenance sentence. Trim repeated context if the compiled manuscript reaches seven pages. References count toward the six-page limit.

## Decision table

| Evidence | Paper claim |
|---|---|
| Every new control process is complete and its predeclared frequency band passes; hashes match | New bracketed counter-rate control supports activation at 10/32/64 kHz under this model. Interpret the archived selected slow-fault verdicts conditionally, while retaining the old failed control. |
| Any new control fails, lacks a verdict, or has mismatched provenance | Counter slow-fault activation/preservation remains unresolved. Report the new anomaly and keep only the fourth case's legal-clock repair claim. |

The study still cannot claim same-setting flakiness, real-hardware generality, a natural fault distribution, or a complete oracle.
