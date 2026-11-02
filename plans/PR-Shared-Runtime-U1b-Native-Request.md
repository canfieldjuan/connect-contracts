# Acceptance record — U1b native framing prerequisite

Juan accepted the exact reviewed revision on 2026-10-30:
> accept 85 at c0e7ef6

- Accepted revision: `c0e7ef632aae284626138c3883fbd9244bf375f0`.
- Accepted file: `plans/PR-Shared-Runtime-U1b-Native-Request.md`.
- Accepted body SHA-256: `2f2a0e46e3b3395ed49fc6fcfcfdcbd027d98f4801fb24a8a3886e0670fbb198`.
- Authority provenance: Juan's verbatim decision relayed by oversight in mailbox
  message `64f5374a` at `2026-10-30T21:53:09+00:00`.
- Independent contract review: [oversight PASS](https://github.com/canfieldjuan/connect-contracts/pull/85#issuecomment-6534048852).

This is an acceptance-only record. The accepted body below is retained
byte-for-byte, including its historical proposed status and pending gates.
Acceptance applies to the named revision, not to later revisions. This record
performs no implementation or merge; acceptance-delta review and guarded merge
remain separate steps. All qualification and live-dispatch gates in the body
remain in force.

---

# U1b first implementation slice: main-based native framing prerequisite

Status: PROPOSED, contract-only; no implementation or model dispatch authorized
by this document. Owner: connect-runtime. Parent: [accepted U1](PR-Shared-Runtime-U1.md).
Exact-revision operator acceptance follows independent contract review.

## Root cause

Doc Sum's `PromptFraming`, token assembly and completion body construction live
inside the private-child runtime. The shared-host adapter needs those exact
owners; copying their output format into a new client would create independent
framing and risk changing the pre-production specification. This slice ports
the proven framing operations into one main-based native request owner needed
by U1b. It does not open another unrelated
U1a primitive extraction or build a generic engine abstraction.

Source inspection also finds a prerequisite: current main does not contain the
validated native-profile framing. Extracting from current main alone would omit
message-boundary metadata and thinking control required by the qualification
handoff. Do not silently call that a faithful port.

## Inventory and base binding

| Item | Exact source / evidence | What it proves |
|---|---|---|
| Current remote main | document-summarizer `7911f4375772fbc2e6c063a4e4a82aea7d638751` | `llama_cpp.rs:519` assembles token arrays; `completion` at576 builds the old body; `PromptFraming::load` at1450 lacks the closed-thinking setting and ordered message delimiter metadata. This is current main, not the qualification reference. |
| Framing source reference, not Git base | [Doc Sum PR126](https://github.com/canfieldjuan/document-summarizer/pull/126), OPEN at `e12ac4a72330bb6eb000119e77806ecce313d591` | [llama_cpp.rs:578](https://github.com/canfieldjuan/document-summarizer/blob/e12ac4a72330bb6eb000119e77806ecce313d591/src-tauri/src/pipeline/llama_cpp.rs#L578), `completion_request`; `PromptFraming` at1464; request structs at2118 and2137. Adds thinking control and ordered metadata through one owner. PR126 depends on PR116; neither is the prerequisite Git base for this port. |
| Proven message-boundary source | `456fa8aa9ee5e677997a3c46132c86e583777326`; alias `native-message-boundary-repair-20261007/production/receipt.json`, SHA-256 `6848dd2dabcd5b60c78052c065227d3e7aac7d680089cf81554b9938c145c520` | Existing pre-production receipt rehashed, not replayed. Reuse its inputs, request/token records, runtime/model identity and results; do not rebuild private corpus inventories. Its full tuple must be compared with delivered U1b, not assumed equal. |
| Existing offline regression owner | [llama_cpp_framing_tests.rs](https://github.com/canfieldjuan/document-summarizer/blob/e12ac4a72330bb6eb000119e77806ecce313d591/src-tauri/src/pipeline/llama_cpp_framing_tests.rs): `native_prompt_closes_thinking_without_interpreting_content_as_control`, `native_prompt_unflagged_keeps_qualified_open_framing`, `native_requests_preserve_template_message_boundaries` | Existing synthetic transport/token fixtures exercise both thinking settings, stages, structured/text requests and adversarial control-looking content. Their mock tokens are not model-tokenization proof. |
| Qualification handoff | `U1b-qualification-handoff-20261030.md`, SHA-256 `03e18f2eafbc31a2b2c40c9567f1e229af6bd37f4a3be1b7b43210695e99c2e0` | G0 delivery tuple is pending; real canary design is not dispatch acceptance. ds-qualify-c9 owns G1/G2 and 32k task qualification. Authorized model calls remain zero here. |

### Full chain and coordinated landing order

The initial proposal (`daaeb9d`, retained at reviewed `bfeff7b`) named PR126 but
omitted its dependency on [PR116](https://github.com/canfieldjuan/document-summarizer/pull/116).
Source and PR metadata confirm PR116 is open at
`f48bb5035612c11747385ef7a553d915ec7da6a0`, based on main; PR126 is open at
`e12ac4a72330bb6eb000119e77806ecce313d591`, based on
`codex/summary-clause-verification`. The held summary stack must not become a
prerequisite for the infrastructure needed to qualify that same stack.

The source-grounded answer from ds-qualify-c9, relayed by oversight, selects:
**main-based framing prerequisite → shared-host attach → qualification → held
summary stack after its own gates**. This contract adopts that order. Branch the
implementation from inspected main `7911f4375772fbc2e6c063a4e4a82aea7d638751` in
an isolated checkout; if main moves, reconcile the relevant diff before code.
Do not inherit, merge or blanket cherry-pick PR116/126. The introducing commits
`f55dd606024a5ecf4a1fa4a6eea01a04510cae98` and
`456fa8aa9ee5e677997a3c46132c86e583777326` contain unrelated changes; use their
framing operations and proof as source references, not as wholesale patches.
This is a coordinated plan, not an implemented or accepted extraction.

### Framing, configuration and cache ownership

At the reference source, `llama_cpp.rs:521-575` owns content tokenization and
composition, `completion_request` at578-593 owns delimiter-bearing serialization,
and `PromptFraming` at1464 owns delimiter order and optional closed thinking.
`model_settings.rs:1391-1415` projects `QualifiedProfile.disable_thinking` into
`GgufRuntimeConfig`; `runtime_cache_key` includes that value at1618. Main's
factory at `model_settings.rs:1361` and cache key at `llama_cpp.rs:1535` predate
that field. A framing-only copy which ignores configuration/cache would be
incomplete; copying all reference profile rows would change accepted main behavior.

Use a closed internal framing-policy type at the native owner to distinguish
unchanged legacy framing from qualified host framing. Main's existing profile
factories explicitly select legacy behavior; no new model/profile is admitted,
no existing output or cache identity changes, and no settings file is written.
Qualified mode preserves the reference delimiter order and the thinking choice
provided by the reviewed shared-host profile owner. A caller must not choose it
from a free-form flag, environment default or model-name heuristic.

The canonical shared profile already declares `enable_thinking:false` and
`--reasoning off`. The existing canonical-profile owner verifies exact profile
bytes (`CanonicalProfile::load`, with read-only `Tier::argv` in the shared
primitives consumed by host `3a2e3a439afb56267207b30e40c8439b5784dee1`). The later
reviewed host adapter must bind the qualified framing policy to that admitted
profile and parse structured kwargs with the existing JSON parser. Missing,
conflicting or unsupported policy fails closed. This first offline prerequisite
does not add a client dependency or pretend to have delivered that adapter.

A runtime/framing cache must never reuse entries across policies or qualified
profile identities. Preserve legacy key bytes for legacy requests; qualified
entries use an explicit distinct policy/profile binding. Tests prove both
unchanged legacy identity and refusal of cross-policy reuse. Per-instance host
canary caching and leases remain the subsequent attach slice's responsibility.

### Schema-order boundary: framing parity only

Choose the bounded **framing-transparency-only** scope. The source reference's
`completion_request` takes `DecoderSchema`; its `model.rs:1440-1515` serializer
selects ordered projection through `CLAIM_COMPARISON_SCHEMA_NAME` at1450. Main's
`response_format` at1403 uses the earlier representation and has no C9 selector.
Do not import `DecoderSchema`, the C9 schema name, summary verifier, dynamic
schema budgets or other held semantics in this prerequisite.

Preserve main's structured-schema representation and property serialization.
For reference comparisons, prove framing/token/error parity with text requests
and supported non-C9 structured fixtures, with each schema representation named.
**Full e12ac4a structured C9 transport parity is PENDING.** It requires an
independently reviewed schema-order prerequisite/integration before G0/G1 can
bind C9's exact bytes. Do not label this slice full request transparency across
all reference schemas or substitute JSON object equality for wire-byte equality.

## Required change surface

Only the U1b framing seam and its necessary configuration/cache projection:

- `src-tauri/src/pipeline/native_request.rs`: one internal owner for native
  framing fragments and delimiter metadata, checked token composition, tokenizer
  and completion request serialization, bounded response wire types and decoding
  that the future shared transport can consume.
- `llama_cpp.rs`: delegate those operations to the owner. Retain private-child
  startup, descriptor loading, authentication transport, supervision, cache,
  lease, admission and lifecycle policy in the existing runtime.
- `model_settings.rs`: only explicit legacy-policy selection at the existing
  native config construction owner; no reference-stack profile/default import.
- `pipeline/mod.rs`: register the module without a new public app API.
- `llama_cpp_framing_tests.rs` and adjacent request/response tests: reuse existing
  synthetic fixture inputs and expected bytes; add exact before/after comparison
  at the ported seam. Copy only necessary offline helper/test symbols; the full
  reference file includes ignored live/C9 harnesses and must not be copied. Do
  not replace tests with a second handwritten serializer.

The shared native owner produces or consumes bounded bytes/types, without owning
a server, socket, credentials or host lease. Reuse existing serde/HTTP parsing
and locked dependencies. No new framework, runtime, dependency or transport trait
hierarchy is justified by this extraction. Caller transport remains responsible
for I/O, cancellation and deadlines at the same boundaries. Do not turn the
module into an app-independent public client package: prompts and application
request policy remain Doc Sum-owned under U1.

## Preserved behavior and explicit differences

Legacy requests remain byte-identical to main. The new qualified framing mode
adds the reference metadata and closed-thinking capability for later shared-host
use; it is not activated on old routes. Its bytes are compared against the
reference rather than described as unchanged from main. Preserve:

- Identical token-array order; model content tokenized with special parsing off;
  control fragments with it on; `add_special=false` and `with_pieces=false`.
- The existing delimiter array in its exact order, thinking-enabled/disabled
  framing, message end token, seed, temperature, cache flag and output allowance.
- Main structured schema bytes/property order after the existing projection, and text
  requests' omission of the `json_schema` wire member. A logical absent schema
  does not authorize changing omission to an explicit JSON null.
- Exact JSON serializer behavior and byte representation, not only object equality.
  Reuse source-bound fixtures and capture original wire bytes before extraction.
- Existing token budgets, context checks, response byte ceilings, stop/truncation
  handling, required token accounting, errors/retryability and cancellation points.

Expose the decoded **raw content** before the app's existing final trim. The old
app response policy retains that trim at its caller. The future exact-answer
canary must use the raw owner output and its reviewed checker; using the trimmed
ModelResponse would falsely accept leading/trailing changes. This adds an internal
access seam, not a new canary, normalization rule or generation behavior. No
answer-forcing grammar, retry, fallback or standalone canary formatter is added.

Schema constraints and `decoder_compatible_schema` are unchanged. The schema
capability draft [PR84](https://github.com/canfieldjuan/connect-contracts/pull/84)
tracks their actual consumers separately. Fixing those constraints during this
port would destroy the unchanged-baseline comparison. Any other difference in
framing, thinking, serialization, limits, grammar, cancellation or error policy
is a contract failure and must be resolved at the source owner before progression.

## Explicit non-scope

No `SharedHost` selector, persisted settings write, snapshot version change, dependency or
release publication in this first implementation PR. No `model.rs`, gateway
request/retry/replay, app schema, prompt, summary semantics, OCR, profile, model,
engine, GPU, concurrency or production change. No service startup, tokenizer HTTP
call against a real server or model inference, including a canary. Synthetic local
fixtures must be labelled and must never probe existing app endpoints.

Follow-on U1b slices deliver the necessary reviewed client attach/transport/canary
interface, Doc Sum opt-in adapter and snapshot binding, then G0 receipts. Those
are the parent U1 requirements, not completed work or independent horizontal
extraction permission. No default change or cutover is bundled with U1b.

## Verification plan

1. Freeze the original source, existing fixture inputs and exact serialized
   tokenizer/completion requests. Run the existing relevant synthetic regressions
   against the pinned main/reference owners before editing, using only the
   selected offline tests. No ignored live tests.
2. Extract the owner and run the same fixture matrix against main legacy and
   ported legacy owners, plus reference and ported qualified framing owners, in
   isolated test processes. Assert byte equality, token-array equality and
   identical typed failures, not merely equal decoded JSON.
3. Preserve source-isolation probes: content containing ChatML/thinking markers
   never becomes control; empty or missing framing is refused; both thinking
   settings retain reference behavior in qualified mode; legacy mode stays
   identical to main. Main schema order/omission matches; C9 parity is pending.
4. Probe malformed/oversized/truncated responses, stop types, missing or mismatched
   token accounting, empty raw content, whitespace-bearing raw content and the
   old app's final trim separately. Require the future canary access seam to
   preserve whitespace exactly. Test boundary values on response and token caps.
5. Preserve current cancel-before-tokenize/send behavior and existing timeout
   tests. Mocks must observe actual sent bytes and no send after cancellation.
   No leaked worker is acceptable; no new worker is introduced in this slice.
6. Run adjacent tests, fmt and applicable clippy checks. Required CI owns broader
   duplication; existing Windows routes/build gates remain required. Deliberate
   byte mutations to delimiter order, thinking prefix, schema omission, flags and
   field values and cross-policy cache reuse must be caught by the owner parity
   proof. Failures caused by absent C9 schema support are not masked or counted
   as parity successes; that work is outside this slice.

No failure is invented: legacy behavior is preserved while qualified framing
is ported from its separately identified reference. A new access
seam test may fail to compile before implementation; report that separately from
a runtime behavior regression. Existing baseline regressions must run first.

## Delivery, gaps and acceptance

Deliver source pins and hashes, old/new serialized request/token receipts, exact
output/typed-error parity, test/CI results and the bounded raw-response interface
to oversight for relay to ds-qualify-c9. Do not claim a client release, installed
runtime, canary qualification, 32k correctness or speed result from those receipts.

### Qualification identity dependency

[ADR-0015 / PR70](https://github.com/canfieldjuan/connect-contracts/pull/70)
is OPEN and Proposed at `664f3f7bed43c7a0542a248203a147f2e378868b`,
`adr/0015-runtime-accuracy-qualification-identity.md`. It is absent from main,
not missing or unwritten. The accepted parent unification work order's
"Qualification and platform dependencies" already assigns its sequencing to
connect-runtime. This corrects the incomplete source lookup in the initial draft.

Use the existing proposed ADR path, with its separate exact acceptance/review
rather than inventing another identity authority: ADR → qualification-record
schema and offline fixtures → effective host settings capture → application
bindings. Its later explicit-argv profile revision is not part of this slice.
No merged schema, host capture implementation or effective settings are inferred
from the draft. This work does not merge or implement PR70. The dependency must
be settled before qualification; offline framing preparation may proceed under
its own accepted contract. No qualification PASS can be claimed from intended
argv, documentation defaults or historical pins alone.

NOT DONE: this revised contract requires independent review and exact operator
acceptance before implementation. Main-based framing/config/cache port and its
two-baseline parity proof are not executed. Full structured C9 transport parity,
ADR-0015/schema/capture acceptance and delivery, G0's reviewed client/consumer
artifacts, loaded-runtime identity, settings/snapshot binding, raw canary interface
and transport receipts remain pending. G1 must freeze the actual combined
candidate; G2 requires Juan's acceptance before model or real tokenizer calls.
The held summary PRs keep all their existing gates.
