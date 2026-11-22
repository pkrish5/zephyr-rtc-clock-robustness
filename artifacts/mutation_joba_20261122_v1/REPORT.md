# Job A (mutation-quality pilot), Slurm 3604920

- Account CCR26073, development, 1 node, COMPLETED 0:0, elapsed 01:01:34 (3694 s) = 1.03 SU (cap 2).
- Study usage, sacct actual: 4.12 + 1.03 = 5.15 SU. Conservative (counting the unexplained
  23-SU balance drop as spent): 28.15 SU. Ceiling 50 SU.
- Archive `3604920-mutation-joba.tar.gz` sha256 2850d2b1...1d97 matches LS6 (`returned/*.sha256`);
  the tarball itself and `builds/` are not committed; the gzipped manifest hashes every entry.
  `job_metadata/protected_{before,after}.json` (7.4 MB each) are omitted for size; they are in the
  archive and manifest.
- Protected-file audit of the main checkout after return: 30,067 files, 0 changed
  (`protected_after_joba_main_checkout.json.gz`).

## Results (`summary.json`, from `notes/mutation_quality_2026-11-21_v1/joba/analyze_joba.py`)

| Configuration | Mutants | Compile failures | TCE-equivalent | Duplicates | Runnable |
|---|---|---|---|---|---|
| rtc_alarm | 909 | 0 | 87 | 258 | 564 |
| rtc_counting | 909 | 0 | 681 | 37 | 191 |
| counter | 346 | 0 | 37 | 56 | 253 |

In rtc_counting most TCE-equivalent mutants lie in alarm code that is not compiled in.

- Builds 70/70. Untraced baselines: 69 complete, 1 wall_cap (counter).
- Driver line coverage (traced): upstream 3/3 median 0.74; base 34/34 median 0.72; clock 30/32
  median 0.71. Tracing changed no case vector on the 67 with both runs.
- Missing (stay missing): traced runs of astra-range_present-rtc_alarm_pending-r03/r04 (trace gzip
  truncated when read, `EOFError`); counter baseline (wall cap 1800 s at 306 of 600 virtual s) and
  counter traced run (3000 s process timeout).
- Timing sample, 40 runs: 20 killed (5 by virtual timeout), 19 survived, 1 harness_error (Renode
  CPU-thread exception). Not a mutation score.
- Job B recost: 17,375 covered RTC (app, mutant) pairs, mean 61.6 s run + 9.1 s build, 32 workers:
  10.65 node-h, 15.98 SU with 1.5x safety.
