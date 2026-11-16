# Counter deadline boundary study: prospective predictions

Status: prediction specification fixed before execution; execution packet NOT sealed or registered. No builds, simulations, remote access or allocation expenditure authorized by this document. This supersedes the November 15 v1 candidate design; that file is preserved. The final packet still needs source/ELF/settings identities, observer qualification implementation, measured runtime feasibility and allocation access. Keep existing paper and frozen results unchanged.

## Question and exact grid

Measure detection as a function of deadline length and phase, not a contest between labels. One full-application F4 counter all-channels subject. Fixed waits: 3, 6, 7.648, 8, 10 and 13 seconds; one additional 7.648-second arm uses existing 20-ms polling. Six deadline lengths, seven arms. The 6-second wait is about 22% shorter than 7.648 seconds; labels do not establish superiority.

Frequencies: 4 through 14 kHz in 1-kHz increments, then 16, 17 and 32 kHz. Exactly 14 frequencies. Elapsed subsecond phase targets: 0.10, 0.45, 0.90, at the driver read determining relative alarm scheduling, measured separately at each frequency. Tick duration is 32000/f simulated seconds; phase is not a fixed wall-time delay. 17 and 32 kHz are LEGAL controls. Other grid rates are out-of-envelope slow probes. No fast probe is added to this requested matrix; historical fast blindness remains separate.

294 primary processes = 7 arms × 14 rates × 3 phases. Full application order, callback predicate and all other assertions remain; only deadline and common phase apparatus vary. Retain every case vector, skip, failure, timeout and missing verdict. Do not infer whole-application success from the selected case.

## Fixed predictions

P=32000, n=2, elapsed phase phi. Ideal arrival t=(3-phi)P/f; selected latest-arrival acceptance is t<=D. This omits setup/delivery latency and is a model prediction, not a measured timestamp. PREDICTIONS.json/CSV specify every primary prediction before any execution. BOUNDARIES.csv gives f_boundary=(3-phi)P/D for every arm/phase.

At 10 kHz and D=7.648 s, acceptance requires phi>=0.61. Therefore both 7.648-second arms are predicted to FAIL at phi=0.10 (9.28 s) and 0.45 (8.16 s), and PASS at phi=0.90 (6.72 s): the slow fault is expected to be missed at the late phase. Equality is ideal acceptance; measured delivery can change equality behavior. Polling may add up to one 20-ms observation interval and is recorded separately. Do not revise these predictions after observing data.

Phase tolerance is ±0.02 tick. The prospective measured-arrival agreement tolerance is ±(0.02*P/f + 0.020 s), accounting for allowed phase uncertainty and at most one polling interval. This is a declared qualification threshold, NOT a validated latency allowance. Record error against both requested-phase and achieved-phase predictions; use the same stated tolerance and report actual errors. No primary cell lies within this tolerance of its deadline under the ideal model. No post-hoc widening is allowed.

## Hard qualification gate before production allocation

First establish that qualification itself fits the approved total budget; use a separately bounded qualification stage, never an unbounded preflight. If qualification needs TACC, its charges count within 4 SU. Thus “before spending allocation” means before production allocation: zero-cost qualification requires a local compatible Renode environment, whose availability has not been established.

All criteria must pass, with explicit records and no missing qualification verdict:

1. Every alignment target in the qualification set reaches ±0.02 tick at the actual driver scheduling read, including read-bracketing uncertainty. Observe modeled SSR and virtual timestamps without changing model code. Startup offsets alone do not qualify. Seal the hook address/symbol and target-read semantics against each ELF. Bound alignment attempts; no silent retry-until-success.
2. At nominal 32 kHz, observer OFF versus ON produces identical selected and full-application case vectors and identical normalized scientific trace hashes for each arm and each of the three phase targets. Both members have identical alignment logic and ELF; only observation is toggled. Exclude only new diagnostic telemetry under a normalization rule fixed before execution; retain raw hashes too. Comparing a deliberately shifted phase against an unaligned historical trace would conflate phase intervention with instrumentation. In addition, compare the unchanged archived ELF at its natural phase with observer OFF/ON. Every nominal selected verdict must pass; other cases must meet predeclared baseline vectors, not silently disappear.
3. Observed callback-arrival virtual time, measured from the scheduling read, agrees with the predicted arrival within the fixed tolerance above. Delivery observation must be independent of the selected test's deadline and must identify the correct callback/channel. A failed early deadline cannot be treated as a measured arrival. Qualify timing on nominal controls and slow cells that actually expose the relevant callback; inability to observe it is a gate failure, not an inferred timestamp. The exact qualification task list and observation horizon must be sealed before execution.
4. Actual runtime, packing/audit headroom and allocation availability demonstrate the entire remaining fixed task list fits the 4-SU ceiling. No failed gate may trigger automatic reruns or tolerance/source tuning.

Qualification failure stops the controlled-phase branch. Preserve all gate outputs. It does NOT authorize an automatic fallback job.

## Natural-phase fallback

Prepare a separate packet only if controlled phase fails qualification. Seven arms × the same 14 frequencies = 98 primary processes. Use the unaligned full application; preserve normal order and avoid phase-setting instrumentation. Say “natural startup/order context,” not one equal phase across frequencies or arms: different waits can change later application phase. Report phase as unknown unless its observer independently passes neutrality. Retain the same rate/deadline predictions as analytic bands, not measured phase predictions. Fresh nominal controls, costs and replay rules must be sealed before fallback execution. Do not merge gate failures or controlled-phase outcomes into this primary dataset.

Analytic result: under the ideal two-to-three-tick model, a fixed latest-arrival deadline that accepts every phase at legal f_min must satisfy D>=3P/f_min. For any f>(2/3)f_min, the earliest possible arrival 2P/f is less than 3P/f_min, so some late phases are accepted. Here (2/3)*17000=11333.333... Hz. This is an ideal-model bound with fixed prescaler, no other oracle checks and phase spanning a whole tick; it is not a hardware guarantee or a bound on arbitrary test oracles. At exact equality, acceptance depends on endpoint and equality conventions, so state the claim strictly above the threshold. The extra 2-second allowance enlarges the blind region: for D=7.648, some phases can ideally pass above 8368.201 Hz and every phase ideally passes at/above 12552.301 Hz, before delivery effects.

## Budget and seals still required

The prior 234-process cost calculation is invalid for this 294-primary matrix. Even before replays, ceil(294/32)=10 batches at the previous conservative 1200-second cap requires 12000 seconds, exceeding the former 3-hour production reservation. Observer OFF/ON qualifications add further processes. Do NOT claim feasibility under 4 SU until local qualification/runtime data and an exact task schedule support it. Keep the requested matrix unchanged; if it cannot fit, stop and report rather than silently prune or exceed the ceiling. No new job is submitted by this revision.

Seal implementation, exact qualification/replay inventories, provenance, walltime caps, predicted cells, immutable primary verdict rules and cost together before building/running production. This document fixes scientific expectations but deliberately does not misrepresent an incomplete execution plan as an executable preregistration.
