# IWDG reset-state fidelity probe — 2026-09-29/30

**Decision: failed; do not admit or propose IWDG as a qualified subject.** This is a separate Renode feasibility result, not a test-timing flip or a firmware defect attribution.

The registered [protocol](IWDG_FIDELITY_PROTOCOL.md) required three nominal and two 17/47 kHz probes to reboot inside one Renode process, retain Zephyr's `.noinit` state, reach the second-boot `Testcase passed` path, and finish the selected ztest. The original unchanged-upstream build produced four immediate `Watchdog install error` failures and one virtual-zero monitor harness error. Those five [raw records and audit](../results/iwdg_fidelity/summary.json) are retained. Inspection of the pinned Zephyr STM32 IWDG driver showed that this configuration starts a default watchdog at boot, which conflicts with the test's later timeout installation.

The separately [registered configuration amendment](IWDG_FIDELITY_AMENDMENT.md) enabled `CONFIG_WDT_DISABLE_AT_BOOT=y` without changing upstream C. Its new ELF built and all five probes reached `Waiting to restart MCU`, but each hit the 30-second virtual cap with exactly one boot start and no `Testcase passed` output. The selected case did not finish at nominal 32 kHz or at either LSI endpoint. The [configured audit](../results/iwdg_fidelity_configured/summary.json) verifies all five raw run/ELF/platform/UART/trace hashes and records `pass=false`. In this setup, the probe did not demonstrate watchdog reset delivery or retained-state behavior. The exact reason for the absent reboot is not established by these logs; it may be a Renode model/platform connection or another configuration interaction.

Reproduce the audits (no new simulation runs):

```sh
python3 analysis/iwdg_fidelity_summary.py
IWDG_FIDELITY_VARIANT=configured python3 analysis/iwdg_fidelity_summary.py
```

Both configurations and the post-observation amendment are disclosed. The IWDG task remains outside the corpus, generation manifest, RQ1 denominator, and model comparisons. Revisiting it would require a new model-fidelity investigation and a fresh user review.
