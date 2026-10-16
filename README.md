# Clock Robustness and Alarm Precision in Zephyr RTC Tests

This repository accompanies the paper [Clock Robustness and Alarm Precision in LLM-Generated and Upstream Zephyr RTC Tests](paper/draft/main.pdf). It contains the manuscript source, frozen protocols and prompts, all saved generated C test sources, experiment and analysis scripts, and non-binary run records.

## Contents

- [Paper source](paper/draft/main.tex) and [PDF](paper/draft/main.pdf).
- [Dated protocol amendments](paper/DESIGN.md).
- [Generated tests](generated/): the frozen factorial and earlier test cohorts, including prompts and saved C sources. Build outputs and per-call temporary logs are omitted.
- [Harness](harness/) and [analysis](analysis/): simulator runners, replay and fault tools, and analysis code and ledgers.
- [Subjects](subjects/): task definitions, wrappers, reference tests, and a [snapshot of the selected upstream RTC test application](subjects/upstream_rtc_snapshot/). The full upstream Zephyr checkout and compiled binaries are omitted.
- [Results](results/): saved machine-readable verdicts, traces, manifests, and audits from the study's experiment runs.
- [Notes](notes/): dated reports and audit notes.

Compiled simulator and firmware build directories, ELF files, and temporary logs are excluded. The run records and traces used for analysis are in [results](results/); generated source is in [generated](generated/).

## Reproduction entry points

Start with the [locked generation protocol](generated/spec_context_factorial_v1/PROTOCOL.md), the [RTC schedule](subjects/phase3_rtc/PROTOCOL.md), and the paper's artifact description. The study used a pinned Zephyr revision and Renode v1.17.0. Do not overwrite the frozen generated sources or raw records when reproducing the analyses.
