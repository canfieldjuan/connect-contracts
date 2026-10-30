# Shared schema capabilities — contract proposal

Status: PROPOSED; contract-only. Owner: connect-runtime.
Parent: [shared runtime unification](PR-Shared-Runtime-Unification.md).
Related: [U1 client contract](PR-Shared-Runtime-U1.md).

This proposal needs independent contract review and Juan's exact-revision
acceptance before implementation. It does not expand U1's accepted executable
surface. Publication, app adoption, dependencies, live qualification, runtime
changes and production cutover retain their separate gates.

## Problem and origin

Schema admission, decoder coverage and output validation are different
boundaries. A keyword allowlist alone cannot establish all three. The legacy
gateway currently rejects `pattern` and `format`; simply allowing them would
expose a latent format-validation gap at `worker._validated_result`. The pinned
llama.cpp converter also has lossy branches. Moving the apps to the shared host
must not carry a gateway-specific allowlist forward as the permanent authority,
or imply that a successful grammar conversion enforces every schema constraint.

The fix belongs at the schema contract and request/output boundaries, not in a
new date regex, downstream cleanup, or a modified model prompt. Preserve one
app-owned authoritative output schema and distinguish task semantics from its
structural guarantees.

## Verified inventory and limits of evidence

Inspection date: 2026-10-30. These are source observations and offline synthetic
probes, not a fresh installed-artifact binding or inference qualification.

| Source | Revision / binding | Relevant owner |
|---|---|---|
| Gateway inspected source | `f105bfd0fba0c8f0866902751c0ec7018171ea39` (origin/main); primary checkout remains `2fee4b5a0fb6d0e76df51e06f0c4bdbefc7e0adc` | [contracts.py:37](https://github.com/canfieldjuan/local-inference-gateway/blob/f105bfd0fba0c8f0866902751c0ec7018171ea39/src/local_inference_gateway/contracts.py#L37), `Generation.validate_generation_shape`, `_validate_supported_schema`; [worker.py:377](https://github.com/canfieldjuan/local-inference-gateway/blob/f105bfd0fba0c8f0866902751c0ec7018171ea39/src/local_inference_gateway/worker.py#L377), `_validated_result` |
| Invoice inspected source | `f7281d71e050fd5e9c746bb5e45c55862af12c26`; dirty checkout untouched | [schema.py:23](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/schema.py#L23), `FieldRef`, `ExtractionResponse`, `gateway_extraction_schema`; [parse.py:424](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/parse.py#L424), `resolve_document_dates`; [pipeline.py:1086](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/pipeline.py#L1086) |
| Canonical runtime source pin | llama.cpp `c1d0e7a004015f23bc0233470b747b596f29b264`; exact converter retrieved independently of sandbox | [common/json-schema-to-grammar.cpp](https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/common/json-schema-to-grammar.cpp), `SchemaConverter::visit`, `_visit_pattern`, `STRING_FORMAT_RULES` |
| Canonical client candidate | local-only `adae73240c99f0e5329e6038f09d63309e13301d` | `Cargo.toml` lists only model-primitives; its dependencies contain no JSON Schema validator. No shared validator implementation is claimed. |
| Offline Python environment | existing gateway venv: jsonschema `4.26.0`, pydantic `2.13.5`, httpx `0.28.1` | Exact inspected gateway source exported into the evidence packet; no services started or dependencies changed. This is not a production environment attestation. |

**CONFIRMED:** gateway admission rejects unknown keywords, including `pattern`
and `format`. Its existing output validator enforces pattern and length when
isolated from admission, but constructs `Draft202012Validator` without a format
checker. The isolated probe therefore accepts invalid dates. These bypass probes
do **not** demonstrate that current admitted production requests contain formats.

**CONFIRMED:** the installed `FormatChecker` rejects invalid dates when enabled,
but accepts an unknown format name. Its available checker set lacks `date-time`.
Checker existence and a closed format-name set must both be checked at admission;
validator defaults are insufficient.

**CONFIRMED by pinned source, not executed converter qualification:**
`_visit_pattern` at385-399 falls back to the general string rule for unsupported
patterns, recording a warning. `visit` at1036-1050 returns a pattern or format
rule before the length branch. `STRING_FORMAT_RULES` at249-257 constrains a date's
month/day spelling but not leap years or month-specific day counts. These are
coverage limits, not proof that every accepted schema is faithfully decoded.

**UNKNOWN:** current installed gateway/backend versions, full converter
acceptance for each app schema, and Rust validator selection/semantic parity.
The newer sandbox source is not substituted for the canonical runtime pin.

## Ownership and versioned capability contract

1. **Apps own task schemas and interpretation.** Schema property order, request
   bytes, prompts, sampling, model identity and output budgets remain unchanged
   during parity qualification. App validators still own provenance, extraction
   accuracy, summary fidelity and deterministic document interpretation.
2. **connect-contracts owns the language-neutral capability profile and vectors.**
   A versioned, immutable profile states the dialect, admitted keywords and
   combinations, closed format names, pattern syntax, resource bounds, backend
   conversion identity and complete output-validator requirements. Change any
   of those semantics or bounds: change the profile identity. Existing Connect
   v1/v2/v3 envelopes and ADR-0011 host descriptor are not changed by this plan.
3. **Shared client request/output admission owns enforcement.** Reusable adapters
   consume the same profile and conformance vectors. A legacy gateway adapter may
   consume it while that route remains; it must not grow a competing authority.
   The host continues to own lifecycle, not application schema interpretation.
4. **Backend generation coverage is an explicit property, not inferred from
   admission.** Bind backend build/converter and configuration to a coverage
   receipt for the exact schema bytes and capability profile. Distinguish full
   generation enforcement, declared semantic validation at output admission, and
   unsupported. Unknown coverage is unsupported until qualified.

Reject malformed schemas, unknown keywords, unknown/absent format checkers,
remote references, unsupported recursive/reference forms, unsupported keyword
combinations and exceeded budgets before dispatch. Do not strip a rejected
constraint or retry the same task with weaker schema/model settings. Recognized
annotations have explicit semantics; `default` must not insert missing values.
Keep the legacy task-specific reference/choice rules and their resource bounds
as a separately identified compatibility profile until existing app vectors
prove a replacement. Do not broaden them merely because the backend accepts more.

Every admitted constraint stays in the authoritative schema. Decoder lowering
is permitted only as a named, deterministic, semantics-preserving transformation
with a schema identity and conformance proof. No alphabetical reserialization
or other request-byte change is bundled with capability adoption. An inherited
serialization difference is inventoried and qualified separately, not hidden.

## Consumer-led increment: Doc Sum with U1b

The first increment is the schema behavior needed by **U1b, Doc Sum on the
shared host**. No format or general fixed-token pattern extension is selected.
The original draft proposed candidates without a demonstrated consumer; that
scope error originated in `19530021cc6b40e6f7f83b11cf43500a79b8358b` and is removed
here rather than covered by another admission rule. Date-checker observations
above remain evidence of a latent risk, not a feature backlog or current app bug.

### SC-A initial Doc Sum inventory

Inspected remote main is `7911f4375772fbc2e6c063a4e4a82aea7d638751`, independently
confirmed against the remote. The primary dirty checkout remains `a19639a`; it
was not edited. Qualification branches are separate revisions and are not
implicitly included or declared equivalent. File references below are under
`src-tauri/src/pipeline/` at that exact remote-main revision.

| Current consumer / source | Current schema and out-of-schema check | Consequence for U1b and subsequent capability work |
|---|---|---|
| Coherent synthesis: [summary/coherent.rs:6659](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/summary/coherent.rs#L6659), `prompt_and_schema_for_version`; `parse_response_with_limits` at6782 | `units` min/max; text minLength/maxLength; source-ID enum, min/maxItems and uniqueItems. Parser checks counts, canonical bounded text, known IDs and within-unit uniqueness at6791-6853. | Existing consumer for bounded strings/arrays, enums, closed objects and uniqueness. These are not new pattern/date requirements. Capture exact schema and projected bytes separately. |
| Long source selection: [summary/coherent.rs:3506](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/summary/coherent.rs#L3506), `source_selection_prompt_and_schema`; result checks at3825-3870 | Each array has exact count, ID enum and uniqueItems; parser also rejects repeated IDs across different role arrays. | Within-array uniqueness is schema-expressible and already declared. Cross-array disjointness is a separate relational rule; do not pretend ordinary uniqueItems enforces it or replace the named semantic owner. |
| Text admission: [summary.rs:5195](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/summary.rs#L5195), `canonical_bounded_text`; exhaustive caller table below | Requires nonempty text, `trim() == value`, and a character ceiling. Schema already has nonempty/length bounds but not the leading/trailing whitespace constraint. | Concrete schema-expressible gap to investigate. Before selecting pattern support, prove identical Rust Unicode-whitespace semantics in schema validation and pinned decoding, including sibling length constraints; do not substitute an ASCII approximation or alter request bytes during the parity port. |
| Native and gateway request paths: [model.rs:1403](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/model.rs#L1403), `response_format` / `decoder_compatible_schema` at1435; gateway `request_core` also calls this owner at `gateway_client.rs:707`; [llama_cpp.rs:737](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/llama_cpp.rs#L737) | Projection removes uniqueItems and maxLength above MAX_DECODER_STRING_LENGTH (1536); current coherent text ceiling is1200, so that particular ceiling remains. | Confirmed lossy projection at one existing owner. Both transports consume this one projection owner. Native U1b parity follows the native route; gateway history is separately inventoried, not silently substituted. Record behavior and proof before a correction; do not change it implicitly while extracting native requests. Comments about unsupported decoder behavior are hypotheses until converter qualification reproduces them. |
| Analysis / verification: [summary.rs:2287](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/summary.rs#L2287), `analysis_output_schema` / `verification_output_schema` | Bounded collections, supplied-ID enums, bounded claim text, closed objects and verdict enum. | Include unchanged in the request inventory. No date format consumer is established. Historical synthesis in `summary/legacy_generation.rs` is cfg(test) at summary.rs:34-35 and must not be counted as an active production requirement. |

### Complete caller inventory for the existing text owner

This table replaces the initial single-call example introduced in `b42149c`.
It records every `canonical_bounded_text` call in tracked pipeline Rust source
at the inspected revision. A call on app-owned source or assembled text is not
by itself demand to constrain a new model output field. The predicate remains
one owner at `summary.rs:5195`; this contract introduces no second validator.
All paths below are relative to `src-tauri/src/pipeline/` at the revision above.

| Call site | Value / field | Role and schema consequence |
|---|---|---|
| `summary.rs:3402` | `candidate.exact_quote` | source/catalog admission; not generated text |
| `summary.rs:3469` | `raw_item.claim_text` | model evidence[].claim_text; schema min/maxLength, whitespace absent |
| `summary.rs:4049` | `evidence.claim_text` | persisted/versioned analysis validation; model-derived claim |
| `summary.rs:4070` | `evidence.exact_quote` | persisted source quotation; catalog/provenance validation |
| `summary.rs:4844` | `claim.text` | assembled/persisted summary claim; shared downstream validator |
| `summary.rs:5472` | `quote` | cfg(test) fixture_model_output; not production |
| `summary/coherent.rs:5373` | `claim.text` | app-added clause-reference suffix; assembly check |
| `summary/coherent.rs:6805` | `unit.text` | model units[].text; min/maxLength declared, whitespace absent |
| `summary/coherent.rs:7205` | `unit.text` | same model field during clipped-unit recovery; not a new schema |
| `summary/coherent/trim.rs:56` | `retained` | derived prefix of unit text; deterministic recovery, not independent model field |
| `summary/pages.rs:222` | `mid_word` | test completeness_and_length_boundaries_are_independent |
| `summary/legacy_generation.rs:1017` | `raw_claim.text` | cfg(test) legacy claims[].text |
| `summary/legacy_generation.rs:1123` | `candidate.text` | cfg(test) legacy candidate.text |
| `summary/legacy_generation.rs:1149` | `raw_claim.text` | cfg(test) legacy claims[].text |

Source verification corrects two classifications in the review's examples:
`summary.rs:5472` is inside `#[cfg(test)] fixture_model_output`; `pages.rs:222`
is a test assertion. They are retained in the inventory, not counted as new
production schema demand. Existing historical generation calls are likewise
test-only. Count/length/whitespace expression work must distinguish current
model fields, historical restoration and deterministic app assembly.

The projection's external callers are `model.rs:1432` (`response_format`, used
by native and direct-model paths) and `gateway_client.rs:707` (`request_core`).
Recursive calls within `decoder_compatible_schema` are its traversal, not
independent policy owners. U1b preserves both old-route behavior and native
request bytes; no gateway edit is granted by listing its reader here.

This is an initial source inventory, **not** a full app or SC-A PASS. Semantic
completion, source support, attribution, cross-array identity, relation and
provenance checks remain app-owned; JSON validity is no substitute for them.
Every later app must receive the same inventory of current out-of-schema checks
before its increment. Do not build speculative capabilities for Email or Invoice.

### Boundary and delivery rules

- Preserve the current admitted task schemas and request bytes for U1b parity.
  Document inherited conversion losses explicitly; preserving them for a port is
  not certifying complete schema enforcement or approving their permanent use.
- Add a capability only for an inventoried consumer after a separate accepted
  correction contract. `format: date`, `date-time` and the former generic
  fixed-token pattern candidate are removed from the increment. Unknown names
  still fail closed; no new format checker dependency is justified by this slice.
- Constraints stay in the authoritative schema. Any proposed whitespace pattern
  must compose with lengths and match existing Unicode semantics; otherwise its
  implementation gate stays unresolved. No parallel regex or blanket ASCII rule.
- Warning-only conversion fallback cannot qualify as enforcement. Capture the
  actual original/projected schema and per-constraint decoder coverage; do not
  label discarded constraints as semantics-preserving lowering.
- Preserve exact JSON/numeric handling, resource limits, typed failures and app
  validation during the port. The current Rust client has no schema validator;
  selecting a new dependency still requires a separately justified contract.
- Pace this work with U1b. Stop unrelated U1a extraction; remaining client attach,
  transport and canary work is included only as the real Doc Sum path needs it.
  Schema corrections are not permission to expand U1b's accepted no-behavior-
  change surface. Doc Sum's 32k qualification remains with ds-qualify-c9.

## Full output admission and failure behavior

Validate the final parsed value against the **complete authoritative schema**
with asserted supported formats before publishing, persisting as a successful
result, or returning it as accepted to an app. Validate the value actually used
by downstream code. Preserve original output bytes where the existing contract
requires them; validation must not repair or normalize a model answer.

Distinguish invalid schema, unsupported capability, invalid output and transport
failure with typed outcomes. This proposal does not change existing wire errors
or retry semantics: adapters must map these through separately reviewed contracts.
An invalid answer is not a capacity rejection and does not authorize fallback.

Bind stored success/replay provenance to schema identity, capability profile,
validator identity and backend coverage receipt. Old entries lacking the binding
are not silently upgraded to a new profile. Their existing semantics remain in
legacy mode; a new-profile route must revalidate under an explicitly accepted
migration or refuse reuse. Do not break acknowledgment/expiry/encrypted storage.

## Invoice preservation and porting differences

`FieldRef.text` is **verbatim source text**, including date strings that are not
ISO. Do not add `format: date` to it, require the model to interpret date order,
or change `gateway_extraction_schema` property order. The normalized record and
joint source-backed date interpretation remain owned by `resolve_document_dates`
and its pipeline caller. A structurally valid extraction is not proof that the
correct issue date, amount or provenance was selected.

Any later adopted capability increment must list its differences explicitly:
a capability identity, qualified conversion coverage and successful-result
provenance binding are proposed boundaries, not changes bundled into U1b. No
format assertion or pattern language is selected without inventoried demand. No existing app schema is
changed in this slice. Before adoption, inventory every additional serializer,
request, validation, error or cache difference and obtain acceptance where behavior
changes. The existing pre-production/corpus manifests and validators remain the
parity specification; do not replace them with these synthetic boundary probes.

## Verification and bounded delivery

**SC-A — consumer inventory and offline qualification:** start with Doc Sum
for U1b. Inventory each active schema and current out-of-schema check, classify
what the schema can express versus app-owned relational/semantic checks, and
select only demonstrated demand. Then freeze exact schema/request bytes, limits,
converter/validator receipts and error mapping. Reuse current fixtures and the existing source-binding/corpus manifests.
Run existing validator and converter without generation where possible. The
current packet proves only the boundary observations above; it is not SC-A PASS.

**SC-B — one shared enforcement owner:** after exact acceptance, implement the
selected reusable validator/adapter with fail-first tests. Use schema/type/parser
mechanisms already available at that owner. A new dependency requires its own
justification and acceptance. Do not add duplicate app checks.

**SC-C — app-by-app adoption:** prove unchanged baseline results with the existing
real validators and saved requests before changing constraints. Live requests,
production routing and model settings require their own authorized qualification.
A legacy gateway patch is deferred unless a current app requirement cannot wait
for migration; if needed it must consume this same authority, not define a fork.

Required probes cover good and bad values; mixed/partial objects; unknown keywords
and format names at every admitted nesting position; unavailable checkers; valid
leap dates/invalid calendar dates; pattern anchoring, escapes and Unicode; sibling
assertion composition; empty/single/limit/past-limit values; falsy caps; duplicate
keys/nonfinite/exact decimals; unknown versions; cache identity mismatch; output
truncation; and proof that the downstream consumer uses the validated value.
Backend coverage tests must demonstrate both rejected bad values and reachable
valid values, so over-restrictive grammars also fail. Preserve every refusal.

No LGTM, runtime performance claim or task-quality claim follows from this draft.
Acceptance criteria: all applicable vectors pass at exact pins; no weakened
constraints or undocumented differences; existing app correctness and byte-parity
gates pass; human summary-quality review remains explicit where required.

## Evidence and remaining gates

Durable synthetic packet alias: `schema-capability-contract-20261030`.
`source-receipts.json` binds exported gateway sources and pinned converter.
`probe_schema.py` and `probe-results.json` reproduce the observed Python behavior.
The publication-safe report records their SHA-256s; no private corpus content,
credentials or real application outputs are included.

Remaining gates: independent contract review; exact operator acceptance;
complete Doc Sum schema/request/check inventory for SC-A (reuse existing receipts);
Unicode whitespace and uniqueness coverage proof where demanded; selected Rust
validation mechanism only if needed for the bounded accepted correction; converter execution proof;
then separately authorized implementation and app parity. No production service,
profile, dependency, runtime or model changed during this contract investigation.
