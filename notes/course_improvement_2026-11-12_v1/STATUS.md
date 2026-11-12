# Six-page revision status

- Focused bracketed control preregistered before source/build/run in `PROTOCOL.md` and sealed in `packet/`.
- Control code committed through `20a279a2` and pushed to `origin/main` before the new Renode processes ran.
- Original 2026-11-11 18-ms control violation remains failed and unchanged.
- The user completed TACC MFA. The clean TACC checkout matched sealed commit `20a279a2`; packet plan/execution checksums passed. One development/CCR26073 job, `3578143`, was accepted and completed `0:0` on 2026-11-12 in 3:52, within its one-hour/1-SU ceiling. Its accepted receipt and exclusive intent are in `submission-returned-v1/`. Do not submit it again.
- All four packed output files were returned to `returned-3578143-v1/`. The independent local `verify_return.py` checked the archive, source/ELF/plan hashes, 30,067 protected originals, Slurm completion, all eleven raw UART lines and assigned/excluded rate bands. `verified-3578143-v1/verification.json` reports 11/11 qualified: 3 ticks at 10 kHz (3/3), 10 at 32 kHz (5/5), and 20 at 64 kHz (3/3), each over an approximately 10-second bracket.
- The manuscript incorporates this result. The final TeX/PDF compile to five pages including references; all five pages were inspected. Eight tables, 17,375 original paired records and all 42 v4 claim checks passed from the pinned archive. No overfull box or unresolved citation/reference remains. The old 18-ms five-tick control failure remains a separate limitation.
- The v4 release package contains the manuscript, source, supplemental raw evidence, claim audit, validation record and checksums. Clean-checkout and public-release verification are the remaining publication gates.
