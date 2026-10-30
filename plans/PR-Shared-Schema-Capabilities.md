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

## First capability increment

The first increment is deliberately bounded: existing admitted app schemas,
plus **candidate** support for `format: date` and bounded fixed-token patterns.
Neither extension is enabled by this proposal; each must pass the gates below.

- Date means an ISO full-date string, asserted with the schema validator's real
  calendar checker. The backend can constrain lexical structure while the same
  authoritative schema validates calendar semantics before an answer is accepted.
  The coverage receipt must name this split; it must never claim that impossible
  calendar dates cannot be generated. No parallel date regex is added.
- Other formats, including `date-time`, are unsupported in this increment.
  Adding one requires a checker availability/semantics proof and backend coverage
  qualification, not just another allowlist entry or an optional package assumed
  to exist. This restriction concerns the new profile, not removal of behavior
  from an existing app route.
- Patterns remain JSON Schema `pattern` constraints. Candidate syntax is bounded
  ASCII fixed-token language: anchored concatenations of literal letters/digits,
  hyphen/underscore and finite ASCII character classes with finite repetition.
  No backreferences, lookarounds, nested repetition, unbounded quantifiers or
  external regex check duplicating the schema. The implementation contract must
  fix exact grammar and limits from the reused app inventory before enabling it;
  this proposal does not claim arbitrary ECMAScript/Python/GBNF equivalence.
- Pattern/format combined with length or other assertions must satisfy **all**
  assertions. For this runtime, such combinations remain unsupported unless a
  conversion proof establishes their conjunction; warning-only fallback is a
  refusal. Full post-generation validation alone does not justify knowingly
  dropping a constraint the decoder could enforce through a proven lowering.
- Exact JSON parsing, duplicate-key refusal, finite/exact numeric handling,
  nesting/size caps and existing failure classifications must survive unchanged.
  Do not route Decimal values through binary floating point to add validation.

A real validator/compiler is preferred over ad hoc schema or regex inspection.
The current Rust candidate has no validator. Selecting a new dependency or
adding a parser is a separately justified implementation-contract decision;
there is no permission here to install one or hand-roll a partial validator.

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

Planned differences are explicit: a new capability identity; format assertion
only for schemas that actually declare supported formats; fail-closed conversion
coverage; and successful-result provenance binding. No existing app schema is
changed in this slice. Before adoption, inventory every additional serializer,
request, validation, error or cache difference and obtain acceptance where behavior
changes. The existing pre-production/corpus manifests and validators remain the
parity specification; do not replace them with these synthetic boundary probes.

## Verification and bounded delivery

**SC-A — contract and offline qualification:** freeze capability data and vectors,
exact app schema/request inventory, limits, converter/validator receipts and error
mapping. Reuse current fixtures and the existing source-binding/corpus manifests.
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

Remaining gates: independent contract review; exact operator acceptance; actual
app schema inventory for SC-A (reuse existing receipts); explicit pattern grammar
and budgets; selected Rust validation mechanism; converter execution proof;
then separately authorized implementation and app parity. No production service,
profile, dependency, runtime or model changed during this contract investigation.
