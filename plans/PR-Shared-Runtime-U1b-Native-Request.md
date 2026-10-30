# U1b first implementation slice: native request transparency

Status: PROPOSED, contract-only; no implementation or model dispatch authorized
by this document. Owner: connect-runtime. Parent: [accepted U1](PR-Shared-Runtime-U1.md).
Exact-revision operator acceptance follows independent contract review.

## Root cause

Doc Sum's `PromptFraming`, token assembly and completion body construction live
inside the private-child runtime. The shared-host adapter needs those exact
owners; copying their output format into a new client would create independent
framing and risk changing the pre-production specification. This slice extracts
only the native request seam needed by U1b. It does not open another unrelated
U1a primitive extraction or build a generic engine abstraction.

Source inspection also finds a prerequisite: current main does not contain the
validated native-profile framing. Extracting from current main alone would omit
message-boundary metadata and thinking control required by the qualification
handoff. Do not silently call that a faithful port.

## Inventory and base binding

| Item | Exact source / evidence | What it proves |
|---|---|---|
| Current remote main | document-summarizer `7911f4375772fbc2e6c063a4e4a82aea7d638751` | `llama_cpp.rs:519` assembles token arrays; `completion` at576 builds the old body; `PromptFraming::load` at1450 lacks the closed-thinking setting and ordered message delimiter metadata. This is current main, not the qualification reference. |
| Intended native source dependency | [Doc Sum PR126](https://github.com/canfieldjuan/document-summarizer/pull/126), OPEN at `e12ac4a72330bb6eb000119e77806ecce313d591` | [llama_cpp.rs:577](https://github.com/canfieldjuan/document-summarizer/blob/e12ac4a72330bb6eb000119e77806ecce313d591/src-tauri/src/pipeline/llama_cpp.rs#L577), `completion_request`; `PromptFraming` at1464; request structs at2125 onward. Adds thinking control and ordered metadata through one owner. The open PR is a dependency, not a claim of merge or adoption. |
| Proven message-boundary source | `456fa8aa9ee5e677997a3c46132c86e583777326`; alias `native-message-boundary-repair-20261007/production/receipt.json`, SHA-256 `6848dd2dabcd5b60c78052c065227d3e7aac7d680089cf81554b9938c145c520` | Existing pre-production receipt rehashed, not replayed. Reuse its inputs, request/token records, runtime/model identity and results; do not rebuild private corpus inventories. Its full tuple must be compared with delivered U1b, not assumed equal. |
| Existing offline regression owner | [llama_cpp_framing_tests.rs](https://github.com/canfieldjuan/document-summarizer/blob/e12ac4a72330bb6eb000119e77806ecce313d591/src-tauri/src/pipeline/llama_cpp_framing_tests.rs): `native_prompt_closes_thinking_without_interpreting_content_as_control`, `native_prompt_unflagged_keeps_qualified_open_framing`, `native_requests_preserve_template_message_boundaries` | Existing synthetic transport/token fixtures exercise both thinking settings, stages, structured/text requests and adversarial control-looking content. Their mock tokens are not model-tokenization proof. |
| Qualification handoff | `U1b-qualification-handoff-20261030.md`, SHA-256 `03e18f2eafbc31a2b2c40c9567f1e229af6bd37f4a3be1b7b43210695e99c2e0` | G0 delivery tuple is pending; real canary design is not dispatch acceptance. ds-qualify-c9 owns G1/G2 and 32k task qualification. Authorized model calls remain zero here. |

Implementation is based on the reviewed native dependency, not the dirty primary
checkout. Before code, bind the exact reviewed dependency head and permitted
stacking/landing order. If PR126 changes the extraction seam, update this inventory
and obtain review of the contract delta; do not lift all unrelated changes from
that branch or merge its PR through this contract. The qualification branch and
installed apps are separate identities. No new installed binding is claimed.

## Required change surface

Only the U1b seam already listed by U1:

- `src-tauri/src/pipeline/native_request.rs`: one internal owner for native
  framing fragments and delimiter metadata, checked token composition, tokenizer
  and completion request serialization, bounded response wire types and decoding
  that the future shared transport can consume.
- `llama_cpp.rs`: delegate those operations to the owner. Retain private-child
  startup, descriptor loading, authentication transport, supervision, cache,
  lease, admission and lifecycle policy in the existing runtime.
- `pipeline/mod.rs`: register the module without a new public app API.
- `llama_cpp_framing_tests.rs` and adjacent request/response tests: reuse existing
  fixture inputs and expected bytes; add exact before/after comparison at the
  extracted seam. Do not replace tests with a second handwritten serializer.

The shared native owner produces or consumes bounded bytes/types, without owning
a server, socket, credentials or host lease. Reuse existing serde/HTTP parsing
and locked dependencies. No new framework, runtime, dependency or transport trait
hierarchy is justified by this extraction. Caller transport remains responsible
for I/O, cancellation and deadlines at the same boundaries. Do not turn the
module into an app-independent public client package: prompts and application
request policy remain Doc Sum-owned under U1.

## Preserved behavior and explicit differences

The only intended behavior difference is internal ownership. Preserve:

- Identical token-array order; model content tokenized with special parsing off;
  control fragments with it on; `add_special=false` and `with_pieces=false`.
- The existing delimiter array in its exact order, thinking-enabled/disabled
  framing, message end token, seed, temperature, cache flag and output allowance.
- Structured schema bytes/property order after the existing projection, and text
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

No `SharedHost` selector, settings write, snapshot version change, dependency or
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
   against the selected dependency before editing. No ignored live tests.
2. Extract the owner and run the same fixture matrix against old and new owners
   in isolated test processes. Assert byte equality, token-array equality and
   identical typed failures, not merely equal decoded JSON.
3. Preserve source-isolation probes: content containing ChatML/thinking markers
   never becomes control; empty or missing framing is refused; both thinking
   settings retain exact behavior; schema property order and omitted members match.
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
   field values must be caught by the existing-owner parity proof.

No failure is invented: this is a behavior-preserving extraction. A new access
seam test may fail to compile before implementation; report that separately from
a runtime behavior regression. Existing baseline regressions must run first.

## Delivery, gaps and acceptance

Deliver source pins and hashes, old/new serialized request/token receipts, exact
output/typed-error parity, test/CI results and the bounded raw-response interface
to oversight for relay to ds-qualify-c9. Do not claim a client release, installed
runtime, canary qualification, 32k correctness or speed result from those receipts.

NOT DONE: contract review/acceptance and the reviewed native dependency/landing
order remain required before extraction. G0's client/consumer artifact tuple,
loaded-runtime identity, settings/snapshot binding, real canary interface and
transport-transparency receipt remain delivery-pending. The handoff mentions an
ADR-0015 binding; no such file was found in inspected connect-contracts main
`9ef8a3760ebb1d2f216f6a704fec2343ba4ea6bc`. Obtain its exact source identity through
coordination instead of inventing a binding or treating that note as acceptance.
