# Retained scorer comparison: application-clock metadata amendment

## Authority, root cause and required surface

Status: PROPOSED, documentation only; owner: connect-runtime. This amends only
[migration plan section B](PR-V1-Profile-Migration-Replay.md#b-scorer-environment-and-retained-answer-parity).
Juan must accept the exact reviewed revision before this comparison rule can
replace section B's strict gate. Acceptance and merge approve the contract only;
comparator implementation, its offline application and any replay remain separately
authorized. No gate is declared complete by this document.

The unchanged Invoice and COI pipelines write `extracted_at` from the app clock.
Replaying saved answers therefore changes that field even when every extracted
value, task score and error outcome is identical. The existing requirement for
full per-case equality has no exception for this metadata. The fix belongs at the
offline comparison owner, not in an oracle, an application or model generation.

Required surface now: this annex and a pointer at the parent requirement. The
later bounded implementation extends the retained replay's comparison/reporting
owner and its focused tests; it does not introduce another task scorer. Preserve
the original strict verdict and every original byte. No clock injection, `now`
override, `score.py` edit, timestamp removal from saved results, broad ignored-key
list, global leaf-name filter or reserialization of model requests is permitted.

## Validated inventory and source evidence

Reuse the parent's pre-production evaluation, issue-73 corpus and 301-file receipt.
The retained receipt below additionally binds the existing issue-73 snapshot and
frozen helpers. Do not rebuild inventories or publish private document contents.
Artifact aliases are local evidence references, not public uploads or new runs.

Packet alias: `invoice-scorer-parity-20261107T040809Z`.

| Artifact within that packet | SHA-256 / measured fact |
| --- | --- |
| `EXECUTION-ADDENDUM.md` | `0ecd9369020b2608a4ae4a3e65fdc8a2e7de7efd1e1a69eff4f8991e0e32ab9b` |
| `EXECUTION-RESULTS.json` | `649294e3a48692b08c74378b03b55c7bd5456026a44e40bd7f665ba7d305b6f1` |
| `EXECUTION-SHA256SUMS` | `85e035d8cdc9317b6cc68314c0def4091c935cfbd3eccd8f69d0b491800c5bc4` |
| `execution-20261107T043051Z/source-binding.json` | `85eb5ce4a8debee56c3688cefec860e5a110bd0b8312da6557be85b32db10dfb`; 301 pre-production files, 153 issue-73 files, 2 frozen helpers |
| `execution-20261107T043051Z/environment-binding.json` | `ae3855994e01f7dedad59e9e937bb0615f276e24579d04b1af4f22794d4cf758`; Python 3.13.11, 37 platform-applicable locked packages |

The binding receipt identifies these unchanged clock writers by source path/hash:
pre-production `invoice-source/src/invoice_processor/pipeline.py:1030/:1073`
(`process_invoice`), `invoice-source/src/invoice_processor/certificate/pipeline.py:1127/:1138`
(`process_certificate`), and issue-73
`identity-hold/src/invoice_processor/pipeline.py:1030/:1073` (`process_invoice`).
They derive `timestamp` from `now or datetime.now(UTC)`, remove microseconds and
emit `extracted_at`. The retained `score.py` and `harness-source/eval_tasks.py`
invoke the pipelines without an injected `now`.

This receipt contains 39 unique cases: 3 Invoice, 1 COI, 2 QA and 33 corpus.
Task-score objects and error outcomes match in all 39. Strict full objects match
in 2; the other 37 differ only at the task-specific paths below. The first wrapper
attempt stopped on a QA import-owner assertion after writing that case's score;
the repaired receipt reran that QA case only and retained its identical score.
There are 40 scorer executions, not 40 unique cases or model calls. Historical
corpus results still contain two missing rows; human quality review is pending.

Oversight accepted the evidence, then corrected its review in mail `331dc801`:
the corpus path is `record.extracted_at`, and only enclosing-attempt time bounds
were recorded. Corrected review alias `invoice-scorer-parity-review.md` has SHA-256
`d5647f797e9b4141fb8e642163b11b24e2c60fc61be31101c76ec24e4ad59e57`.
This inventory supports a proposal; it does not record operator acceptance.

## Closed comparison rule

Bind each pair by the existing case alias, task and retained/replayed file hashes;
never pair by completion position. Refuse duplicate or missing case associations,
unknown tasks, invalid JSON, duplicate object members and non-finite numbers.
Use a real JSON parser with those refusal hooks and precision-preserving numeric
ingestion (integer and standard-library Decimal hooks, not binary-float rounding).
Do not import runtime-record integer-only restrictions into task-score numbers.
Compare complete parsed JSON trees: identical object member sets, positional arrays, and scalar types/values,
with no coercion or string/number/boolean equivalence. Retain raw-file hashes and
the strict whole-object result separately; object serialization order/whitespace
must not be confused with parsed-value equality.

The only differing values that may qualify for the amended comparison are:

| Task | Exact path, from the score-object root | Required owner |
| --- | --- | --- |
| `invoice` | `/delivered/extracted_at` | Invoice pipeline app clock |
| `coitext` | `/delivered/extracted_at` | Certificate pipeline app clock |
| `corpus` | `/record/extracted_at` | Issue-73 Invoice pipeline app clock |
| `qa` | None | No clock exception |

These are exact paths, not suffixes or wildcards. The named member and its parent
objects must exist in both values for each clock-bearing task, even if both
timestamps happen to equal. Missing/null allowlisted members, added/removed
members, a difference at another occurrence of the same leaf name, or any other
non-allowlisted difference fail. QA requires strict equality.
Every score, error, status and extracted document field stays within equality.

Both retained and replayed allowlisted values must be strings representing a valid
calendar instant in canonical RFC 3339 UTC `Z` form at second precision:
`YYYY-MM-DDTHH:MM:SSZ`. Use the existing datetime parser and exact UTC second-format
round trip; reject offsets including `+00:00`, fractions, missing timezone, invalid
dates, trailing content and leap seconds, which this app clock does not emit.
Do not use substring/leaf-name matching or a parallel regex as a date parser.
Validation must run for equal timestamps as well as different ones.

Only the replayed value must lie inside its bound replay interval; the retained
value belongs to an earlier run and is not required to lie in that interval.
Interval endpoints must be valid timezone-aware UTC instants, finite and ordered
before precision conversion. Compare the app timestamp inclusively against each
endpoint floored to UTC seconds, matching the writer's truncation. Never round
to nearest, extend a window, use file modification times, or infer a window from
the timestamp being checked. Absent, mismatched or inverted bounds fail.

## One retained-packet exception; future per-case bounds

The original receipt has no per-case start/end. For this packet **only**, permit
its explicitly recorded enclosing-attempt interval. The exception requires the
packet/result/seal identities above and the following exact case-to-command-file
associations. A packet name or equivalent-looking timestamp alone is insufficient.

| Attempt / selected cases | Command receipt SHA-256 | Original UTC endpoints |
| --- | --- | --- |
| `execution-20261107T043051Z`; `pre-00`, `pre-01`, `pre-02`, `pre-21` | `ecbf96bdf9566e29888dd5c24b6e8da7bb13dc0bc99be81f6c2a1ffe07e57914` | `2026-11-07T04:35:19.199796+00:00` to `2026-11-07T04:35:22.268880+00:00` |
| `execution-20261107T043051Z-resume-1`; `pre-22`, `pre-23`, `corpus-00` through `corpus-32` inclusive | `bcc92d2011d8dae1c99394c91c41fd47e298ba698f0bc3f718f319d78a04d3d9` | `2026-11-07T04:37:35.127931+00:00` to `2026-11-07T04:37:56.085165+00:00` |

Each command receipt is `replay-command.json` inside the named attempt. Verify its
exact bytes and use its endpoints, not copied constants as substitute evidence.
The results manifest binds the selected score-file hashes and aliases; the
unsuccessful first `pre-22` receipt is preserved but is not substituted for the
resumed case. Record `window_scope = enclosing_attempt` in the later comparison
report. These bounds must never be labelled measured per-case timing.

For **every future replay**, record UTC start immediately before launching each
case and UTC end after that case finishes, in the controller, bound to the same
case/attempt identifier and input/result digests. Use that case's endpoints and
record `window_scope = case`; also retain monotonic elapsed time for duration and
clock-discontinuity diagnosis. Missing or unusable case bounds fail qualification;
do not fall back to an attempt window or reuse this packet's exception.

The retained exception is justified only by the unscored app-clock origin,
identical task scores and narrowly enclosing recorded windows. It admits no
model-output, scoring, error or document-value variation. Extending this retained
exception to another packet, or adding a task, timestamp path or window scope,
requires a separately reviewed amendment. No
rerun is necessary for the existing packet only if this rule is accepted and its
separate offline comparator check succeeds; neither has occurred in this PR.

## Required verification for the later implementation

One named comparison validator owns the closed task/path/window rule; use explicit
exceptions/results, not `assert`, so optimization cannot disable qualification.
Reuse the bound scorer outputs, existing source/response receipts and raw verdicts.
No new dependency, generic framework, schema change or app validator is required.

Focused tests must prove valid equal and timestamp-different cases for every task;
both interval endpoints at second precision; and these independent refusals:

- A scored/document/error/status value changed, or a member added/removed.
- Adjacent distinct numeric values that a binary-float parser would collapse,
  and boolean/number or string/number substitutions.
- The same `extracted_at` leaf at another path, cross-task path substitution,
  unknown task, mixed valid/invalid case set, and duplicate/missing case association.
- Either allowlisted timestamp absent, null, non-string, malformed or invalid;
  non-UTC and `+00:00` offsets, fractions and trailing content, including when both
  sides contain the same invalid value. Include `0`, `false` and empty-string values.
- Replay timestamp one second before/after its interval; inverted/missing bounds;
  an earlier retained timestamp remains valid when the replay timestamp is in bounds.
- Wrong packet/result/seal/command digest, wrong attempt association, and any
  future packet trying to use enclosing-attempt timing or this retained exception.

Remove each guard in focused mutations and show its corresponding negative fails.
Check optimized Python cannot bypass the named validator. Then compare the sealed
outputs offline, without rescoring them or calling any model. Preserve a per-case
strict verdict, amended verdict, every difference and its classification, exact
task/path, window scope/endpoints and all input/output evidence hashes. A mixed set
does not become a pass because only passing cases were counted.

Keep strict `2/39` and all 37 differences visible. The evidence suggests the proposed
rule could yield amended `39/39`, but that is not an accepted or executed result
of this contract. Report both denominators and any score impact; do not overwrite
the original seal, rewrite old PASS/FAIL labels or claim perfect task accuracy.

## Non-scope, acceptance and gap audit

This PR changes documentation only. Verification now is link/hash/source and
documentation-diff checking; the comparator, its tests and offline re-evaluation
are **NOT IMPLEMENTED / NOT RUN**. Summary binding is independent work, not part
of this amendment. The parent's identity, environment, human-review, capture,
delivery and live gates remain. The selected V1 runtime and profile are unchanged;
issue 88 and live budgets remain open.

No dependency installation, rerun, engine/native build, client/host/app change,
model/tokenizer/device call, production/Ollama change or performance claim is
authorized here. Acceptance requires Juan's exact-revision approval of this rule,
oversight and connector review, followed by the normal merge gates. Implementation
and comparator execution need separate authorization. Only after that proof and
review may the Invoice/COI portion of section B be marked satisfied under the
amended rule; Summary and other independent requirements are not closed by it.

Documentation surface DONE when this annex and its parent pointer are verified.
Overall retained-score gate NOT DONE: exact-revision acceptance, independent review,
later authorized implementation/regression and comparator evidence remain pending.
