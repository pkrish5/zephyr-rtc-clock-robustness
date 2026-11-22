# Quality-metric study: status (2026-11-21)

Phase 1 only: registered in `paper/DESIGN.md` (2026-11-21 entry) for approval.
No firmware built or run; no TACC job submitted.

Dry run (`dryrun_v1/`, deterministic; rerun gives identical bytes):

| File | Active lines (union) | Mutants | ORRN | OAAN | OBBN | OLLN | OAAA | OBBA | OLNG | OCNG | SSDL | clang proxy pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rtc_ll_stm32.c | 873 of 1159 | 909 | 350 | 40 | 20 | 7 | 0 | 18 | 18 | 76 | 380 | 909 |
| counter_ll_stm32_rtc.c | 522 of 921 | 346 | 90 | 28 | 10 | 1 | 8 | 0 | 3 | 19 | 187 | 346 |

236 of the 909 RTC mutants lie on lines active in the counting (no-alarm)
configuration; the rest are alarm-only. OSSN/OSSA matched no active site.

Limitations of the dry run: the Zephyr SDK GCC is not installed locally, so the
compile screen is `clang -fsyntax-only` with Zephyr minimal-libc headers and an
`errno` shim (`compile_proxy_check.py`). Active-line analysis replaces missing
libc headers with empty stubs (listed in `generation_summary.json`). Production
GCC compile and TCE are Job A's first step.

Protected-file audit after these changes: `protected_after_registration_v1.json (30,067 files, 0 changed)`.
