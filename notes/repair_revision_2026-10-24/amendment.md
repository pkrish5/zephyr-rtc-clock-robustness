

## 2026-10-24 E revision approved before any repair builds or runs: split V1

The user approves the 33-subject repair study and execution without another
approval stop, with this revision made before any repair compilation or run.
The original review-only previews remain preserved; they are not outcomes.
The 2026-10-24 E subject roster, V0 bytes, V2/V3 semantics, gates, fault
criteria, missingness policy and Phase 3 paper-approval checkpoint stay fixed.
E2 remains on hold until the user approves the E results.

- **V1 (naive extension):** new scalar wait is
  max(original scalar wait, 20,824 ms). Never shorten an existing wait.
  If the original wait is already at least 20,824 ms, retain its original
  source/deadline semantics exactly; report V1 as a no-op for that subject.
  Otherwise apply the prior deadline-normalization transformation at 20,824 ms.
- **V1b (right-sized fixed wait):** new scalar wait is exactly 20,824 ms;
  this is the previously previewed V1 behavior. Retain original wait style
  and polling cadence with the shared ceiling and original early checks.
- **V2:** unchanged from the prior amendment; derives from V1b, not the new
  extension-only V1. Use event/state waiting and 20-ms polling with the same
  20,824-ms ceiling, retaining original assertions.
- **V3:** unchanged from the prior amendment; V2 plus only the frozen task's
  missing configuration/calendar/identity checks. No invented exact upper
  calendar bound for pending. When the source already implements all required
  task checks, record V3 as unchanged from V2 rather than duplicate assertions.

Before any build, show V1/V1b versus frozen V0 for the same upstream callback
and Sol base pending r03 examples, plus Sol base counting r01 (original scalar
budget 60 seconds). The latter V1 is deliberately unchanged; V1b reduces its
budget to 20,824 ms. Source-site and assertion-retention checks are frozen
before generating the full cohort. Original non-time assertions and all
frozen source/ELF/forecast/results remain unchanged on disk.

Evaluate V0, V1, V1b, V2 and V3 for all 33 subjects, with losses retained.
The revised pre-attrition denominators are 33 x 5 x 102 = **16,830** legal-clock
slots, **825** five-launch nominal-gate slots, **495** fast/slow/nonarrival
slots and **50** activated signed-alarm-offset slots. Counting offset controls
are non-activation checks, outside the alarm denominator, and may be omitted
as the prior amendment made them optional. Explicit assertion failures need
fresh-process replay and task-reference checks at distinct failing settings.
Do not rerun the 12 historical missing cases. Use new output directories only.

A–B then D execution order remains in force. Disclose D failures/missingness
before E fault evaluation; an unexpected control failure must be investigated
without modifying frozen harness logic or inputs. Report E job/node/wall-time
and SU estimates at submission under this explicit execution approval. New
variant generation/build orchestration may be added separately; do not edit
the calibrated simulation implementation. Before paper edits, stop with the
Phase 3 old/new number table and source records.


### 2026-10-24 E V1 service-stage clarification, before builds/runs

For the naive-extension V1, retain each existing post-calendar service
allowance unchanged. In particular Sol base pending r03 retains its separate
3-second pending-service wait after extending the first scalar calendar
budget to max(15, 20.824) seconds. Its total possible duration can therefore
reach 23.824 seconds; report that stage allowance separately. Capping this
existing service wait would contradict the user's instruction never to
shorten an existing wait. V1b, V2 and V3 retain the previously registered
single 20.824-second overall ceiling and clamp that service stage to remaining
time. Other already-long V1 sources remain byte-identical to V0. This is a
pre-run operational clarification of the approved split, not an outcome-based
repair. The six updated V1/V1b diffs will expose it before compilation.
