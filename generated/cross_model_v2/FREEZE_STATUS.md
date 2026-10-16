# Complete-task input freeze — 2026-09-29/30

The pending condition in the earlier [v2 protocol](PROTOCOL.md) is now satisfied. The [versioned 13-task manifest](../../subjects/phase2_tasks_v2.json) and [input hash lock](lock.json) were created only after all ten new Luna sources, ten builds, five available nominal runs, original source-oracle decisions, amended functional decisions, and source timing judgments were audited. The lock SHA-256 is `1e0f4110995f92480a4889e6471d9bf5dd5740d2c4e07251ee249de60ccfc456`. The original 11 task definitions and all 65 Luna rendered prompt hashes agree with the saved sources.

The final task set contains ten HSI tasks, the existing RTC alarm-callback task, and two correlated RTC calendar/pending-state tasks. IWDG failed its separate fidelity gate and is excluded. The initial Sol feasibility pilot and the RTC bound-context supplement remain outside the three-model cohorts. **No new Sol or Astra generation has started; user review is required by the study phase boundary before Step 4.**

Audit the frozen inputs without running a model or simulator:

```sh
python3 analysis/freeze_cross_model_v2.py
```
