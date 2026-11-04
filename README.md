# Clock Robustness and Alarm Precision in Zephyr RTC Tests

> Current focused course paper: [manuscript v2 (2026-11-04)](https://github.com/pkrish5/zephyr-rtc-clock-robustness/releases/tag/course-paper-2026-11-04-v2). The original evidence release is unchanged and contains an older PDF. See [claim audit](notes/course_subjects_2026-11-04_v1/CLAIM_AUDIT.md) and `make course-tables` for the subject-level revision.


This repository accompanies the paper [Clock Robustness and Alarm Precision in LLM-Generated and Upstream Zephyr RTC Tests](paper/draft/main.pdf). It contains the manuscript source, frozen protocols and prompts, all saved generated C test sources, experiment and analysis scripts, and non-binary run records.

## Contents

- [Paper source](paper/draft/main.tex) and [PDF](paper/draft/main.pdf).
- [Dated protocol amendments](paper/DESIGN.md).
- [Generated tests](generated/): the frozen factorial and earlier test cohorts, including prompts and saved C sources. Build outputs and per-call temporary logs are omitted.
- [Harness](harness/) and [analysis](analysis/): simulator runners, replay and fault tools, and analysis code and ledgers.
- [Subjects](subjects/): task definitions, wrappers, reference tests, and a [snapshot of the selected upstream RTC test application](subjects/upstream_rtc_snapshot/). The full upstream Zephyr checkout and compiled binaries are omitted.
- [Results](results/): saved machine-readable verdicts, traces, manifests, and audits from the study's experiment runs.
- [Notes](notes/): dated reports and audit notes.

Compiled build trees and temporary logs are excluded from Git. The separate
verified evidence release archive includes the saved ELFs and logs required for
the final integrity checks. The original run records and traces are in
[results](results/); generated source is in [generated](generated/).

## Reproduction entry points

The final submission's [data dictionary, file/field catalogue and commands](DATA.md)
describe every retained results/analysis artifact and the evidence archive.
**`make tables` rebuilds all eight manuscript tables from archived records without
Renode.** Python 3.11+ and make are sufficient; a cached archive can be supplied
with `make tables EVIDENCE_ARCHIVE=/absolute/path/rtc-submission-evidence-v1.tar.gz`.
Final reconciliation outputs are in
[`phase3_package_v2`](notes/final_submission_2026-11-02_v1/phase3_package_v2/).

Start with the [locked generation protocol](generated/spec_context_factorial_v1/PROTOCOL.md), the [RTC schedule](subjects/phase3_rtc/PROTOCOL.md), and the paper's artifact description. The study used a pinned Zephyr revision and Renode v1.17.0. Do not overwrite the frozen generated sources or raw records when reproducing the analyses.
