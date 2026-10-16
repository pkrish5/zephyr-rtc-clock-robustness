# Clock Robustness and Alarm Precision in Zephyr RTC Tests

This repository accompanies the paper [Clock Robustness and Alarm Precision in LLM-Generated and Upstream Zephyr RTC Tests](paper/draft/main.pdf). It contains the manuscript source, frozen protocols and prompts, generated C test sources, experiment and analysis scripts, and compact analysis ledgers.

## Contents

- [Paper source](paper/draft/main.tex) and [PDF](paper/draft/main.pdf).
- [Dated protocol amendments](paper/DESIGN.md).
- [Frozen factorial materials](generated/spec_context_factorial_v1/): locked prompt order, prompts, metadata, and generated test sources. Build outputs and per-call temporary logs are omitted.
- [Harness](harness/) and [analysis](analysis/): simulator runners, replay and fault tools, and analysis code and ledgers.
- [Subjects](subjects/): task definitions, wrappers, and reference-test source. The full upstream Zephyr checkout and compiled binaries are omitted; the paper identifies the pinned upstream revision.
- [Notes](notes/): dated reports and audit notes.

The large raw Renode traces and build directories are excluded from this code repository. The evaluation dataset and results are intended for a separate data link in the paper. Until that link is supplied, the paper retains its [DATA_URL] placeholder.

## Reproduction entry points

Start with the [locked generation protocol](generated/spec_context_factorial_v1/PROTOCOL.md), the [RTC schedule](subjects/phase3_rtc/PROTOCOL.md), and the paper's artifact description. The study used a pinned Zephyr revision and Renode v1.17.0. Do not overwrite the frozen generated sources or raw records when reproducing the analyses.
