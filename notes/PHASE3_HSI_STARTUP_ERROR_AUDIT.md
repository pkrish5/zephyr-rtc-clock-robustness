# HSI startup-error distribution — 2026-10-03

The [audit script](../analysis/phase3_hsi_error_distribution.py) reads all 4,606 qualified raw records and writes its [machine-readable summary](../results/phase3_hsi_100mips/qualified/startup_error_distribution.json). It confirms 88 `harness_error` records at zero virtual time: one nominal and 87 seeded. Every one passed its separately retained exact-input diagnostic; the original 88 remain non-evaluable.

| CPU setting | Errors / seeded attempts | Rate |
| --- | ---: | ---: |
| 99 MIPS | 28 / 1,161 | 2.41% |
| 100 MIPS | 30 / 1,978 | 1.52% |
| 101 MIPS | 29 / 1,161 | 2.50% |

There is no detected monotone relation with the saved oscillator frequency (Spearman rho = -0.0065, p = 0.670) or seed index (rho = 0.0167, p = 0.273). The 99/100/101-MIPS contingency has chi-square(2) = 4.76, p = 0.092. These are post hoc diagnostics, not proof of frequency independence; repeated suites share seed values and host execution order.

By ranked oscillator-frequency quartile, the seeded errors are 27/1,075 (lowest 25 inputs), 14/1,075, 18/1,075, and 28/1,075 (highest 25 inputs). This mild edge-heavy pattern is also inconclusive (exploratory chi-square(3) = 6.60, p = 0.086) and should not be smoothed into a claim of uniform frequency missingness.

A 5,000-draw permutation that shuffles error flags **within each suite**, preserving its error count, gives two-sided p = 0.754 for association with ranked frequency quartile. This handles suite clustering in that narrow question, but does not remove host-run-order confounding or prove missingness independent of clock input.

The errors are **not uniform by suite** (chi-square(42) = 537.24, p < 1e-80; descriptive only). Seeded errors are confined to eight of 43 eligible suites: upstream `context` 4, `fifo_api` 17, `lifo_api` 19, `msgq_api` 17; Luna `lifo_api-r01` 8, `msgq_api-r04` 11, `msgq_api-r05` 10, `queue-r04` 1. A ninth affected suite, Luna `lifo_api-r02`, has the single nominal startup error and received no seeds under the 5/5 screen. At task level, seeded errors are `context` 4/100, `fifo_api` 17/600, `lifo_api` 27/500, `msgq_api` 38/600, `queue` 1/600, and zero in the other five tasks. Task association is strong (chi-square(9) = 138.61, p < 1e-24), though host partition and execution time can confound it.

Interpretation: the virtual-zero errors and passing diagnostics indicate a runner/Renode startup problem, but its **missingness is suite clustered**, so it cannot be called uniform random harness noise. The absence of seeded assertion flips is conditional on evaluable runs, with 87 missing seeded verdicts. Run `python3 analysis/phase3_hsi_error_distribution.py` to reproduce this audit.
