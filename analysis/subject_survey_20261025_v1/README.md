# S1 read-only subject survey

Final outputs:

- `REPORT.md`: findings, exclusions, proposed boards and planning costs.
- `test_cases.csv`: every case declaration, source span, build evidence, model status, timing cues, configuration and exclusion notes. There are 45 ztest declarations plus one console behavior in the requested applications; 22 adjacent declarations are explicitly excluded.
- `stm32_board_targets.csv`: one row per STM32 board DTS target, including resolved source/clock/status evidence; `stm32_board_summary.json` contains counts.
- `board_overlays.csv`: board-owned revision overlays, clock-related changes and their hashes.
- `verification.json`: protected-file audit and confirmation that S1 performed no builds or runs.
- `board_candidates.csv`: source-backed frequency ranges and qualification requirements.
- `run_estimates.csv`: firmware launches and case/configuration slots, with unmeasured wall-time/SU assumptions.
- `verified_st_documents.json`: exact verified ST titles, numbers, URLs and evidentiary limits.
- `renode_model_sources.json`, `renode_platform_inventory.csv`, `renode_platform_hashes.json`: exact-release model sources and recursively resolved platform evidence.
- `source_inputs_sha256.json`: 3,875 read-only Zephyr/module/include/test inputs.

These are static survey outputs, not new experimental verdicts. Build status is unknown unless a frozen build record is cited. Model presence does not mean the test can complete. The existing watchdog fidelity failures are retained and excluded from proposed qualified subjects. All S2 jobs and S4 model calls require approval.

Reproduction uses a new empty output directory and does not build firmware or launch Renode:

```sh
python3 analysis/subject_survey_20261025_v1/board_survey.py \
  --zephyr subjects/upstream/zephyr --cpp /path/to/clang \
  --out /path/to/new-survey/board_resolved_v3 --work /path/to/new-preprocessor-output
python3 analysis/subject_survey_20261025_v1/case_survey.py \
  /path/to/new-survey/cases_reviewed_v2
python3 analysis/subject_survey_20261025_v1/export_survey.py \
  --out /path/to/new-survey --renode-root /path/to/calibrated-renode-platform-root
```

Use the pinned upstream checkout and STM32 module DTS includes. The board script requires Zephyr's bundled dtlib and a C preprocessor only; its command is `-E`, never compilation/linking. It counts DTS targets rather than market-share-weighted boards. It applies no application overlays. `cases_reviewed_v2/` and `board_resolved_v3/` retain the source-derived intermediate tables consumed by the exporter. Earlier diagnostic passes remain local and are not authoritative.

Limitations: lexical wait cues are supporting evidence, include fixture/callback paths and do not by themselves establish an unjustified timing assumption. Test application metadata and driver capability checks are reviewed separately. The final report distinguishes expected skips, unsupported configurations and actual prior fidelity failures. ST PDFs were verified through ST-hosted indexed content; failed local download attempts are not presented as archived documents.

`REPORT.md` includes a final semantic review of driver API support, existing build symbols, model-source behavior and board revision overlays; these reviewed notes extend the mechanically exported tables.
