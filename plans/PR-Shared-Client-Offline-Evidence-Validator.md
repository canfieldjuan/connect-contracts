# Shared-client offline evidence validator contract

Status: PROPOSED; documentation only. Owner: connect-runtime.
Exact-revision acceptance and a separate implementation go precede executable
changes. Runtime choice, [issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88),
live budgets and qualification remain OPEN. No builds, model/tokenizer calls,
Ollama or production changes are authorized by this document.

## Root cause and source inventory

CONFIRMED at contracts base `6bc06970918729f6e8942d59a6adb825b56ca6af`:
the companion schemas and their offline shape tests exist, but schema success
does not establish agreement between retained bytes, hashes, instance identity
and observation references. That missing semantic owner is the next increment;
it is not a diagnosis or correction of inference arithmetic.

The inspected canonical client checkout is the clean local candidate
`f841cde2b44ec99bc860359a88d06d6ae27309da`. It has no configured `origin` remote;
it is not represented as a verified current upstream checkout. Its
`PROVENANCE.json` calls it a local candidate not cleared for publication. Resolve
the implementation base and distribution pin before a later code PR; do not
guess a remote, patch a host-vendored copy or claim publication authority.

| Source / symbol at those pins | Reuse and boundary |
| --- | --- |
| [Companion interface](PR-Shared-Runtime-Companion-Interface.md#bounded-interfaces-and-error-contract) | Sole production owner `local-connect-model-client::evidence`; pure `validate_bundle` is this increment. Attached reading, publication and `validate_record_binding` remain subsequent increments. |
| [Companion schema contract](PR-Shared-Runtime-Companion-Schemas.md), [fixture inventory](../fixtures/runtime/v1/companion/README.md) | Closed canonical shapes, schema reference closure, frozen raw fixtures and explicit schema-valid semantic counterexamples. The implementation exists; its historical Proposed heading is not current merge status. |
| [Qualification oracle](../tests/runtime_qualification.py), `inspect_record`, `_parse`, `_observations` | Original-byte profile digest, profile/tier/backend/artifact comparisons, expected instance, observed source instance, slot equality and incomplete paths. An offline oracle, not source authentication, full profile admission or task scoring. |
| [Qualification fixtures](../fixtures/runtime/v1/qualification/README.md), [tests](../tests/test_runtime_qualification.py) | Retained complete/incomplete CUDA/Vulkan inputs, negative controls and opaque task receipts. Preserve raw bytes and expected outcomes. |
| Client `crates/model-client/src/lib.rs` | No evidence module; attachment/transport/canary are Linux-gated and `ensure_supported` refuses other platforms. Pure Windows JSON inspection must not change that route. |
| Client `crates/model-client/src/attach.rs::Object<T>` and `Integer` | Existing object-form and typed-field admission. `Object<T>` delegates duplicate checks to the target visitor; it is not a general recursive duplicate-preserving JSON parser. Do not assume it solves evidence parsing. |
| Client `crates/model-primitives/src/profile.rs::CanonicalProfile`, client `canary.rs::ReadyClient` | Existing profile/admission and readiness owners remain unchanged. Pure validation accepts independently admitted profile bytes; it cannot manufacture either authority. |
| Client `Cargo.toml`, `crates/model-client/Cargo.toml`, `Cargo.lock` | Existing parser/hash dependencies are currently Linux-gated in the client manifest. No JSON Schema evaluator is declared there. A real evaluator and its exact dependency closure still need justification and pinning. |
| Client `scripts/verify_vendor.py::verify`, `SOURCE-MANIFEST.json`, `PROVENANCE.json` | Existing complete-file/hash distribution mechanism. A later source change updates its canonical manifest/provenance; this contract does not publish or re-vendor a release. |

Reuse the [host capture inventory](PR-Shared-Runtime-Host-Capture.md#root-cause-and-current-source-inventory)
and [U1b validated-work inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port):
Qwen3.5-9B-Q4_K_M model/runtime/template pins, framing, prompts, sampling,
request/output budgets, frozen native-wire replay, the 301-file receipt, issue-73
and pre-production corpus manifests. No rebuilding those inventories, copying
private documents or rescoring historical tasks. Historical pins do not select
the future runtime. Human task-quality review and historical replay caveats stay
as recorded; this slice cannot close them.

INFERRED: one pure validator will prevent host/app semantic copies from drifting.
UNKNOWN: selected-engine source mappings, validity intervals, installed identity,
native Windows behavior and any new task or performance result.

## Required change surface and increment boundary

This PR adds only this document. The later implementation is confined to:

| Canonical client path | Responsibility |
| --- | --- |
| `crates/model-client/src/evidence.rs` | Bounded raw parsing, canonical instance comparison, schema validation and cross-object rules; `validate_bundle`, opaque `CheckedBundle`, `ExpectedBinding`, closed evidence errors. |
| `crates/model-client/src/lib.rs` | Export only the pure evidence API. Do not widen `ensure_supported`, attachment, canary or generation availability. |
| `crates/model-client/src/evidence_tests.rs` and `crates/model-client/tests/fixtures/evidence/` | Offline conformance, oracle parity and synthetic complete bundles; enumerate every new fixture leaf, source digest and expected result in the implementation PR. No private data. |
| `crates/model-primitives/assets/{qualification,companion,instance,host-snapshot}.schema.json` | Byte-identical copies from this contracts base; explicit local reference registry with these four resources only. Contracts remains canonical schema owner. |
| `crates/model-client/Cargo.toml`, `Cargo.lock` | Only justified pinned evaluator dependencies and target-independent parser/hash availability needed by this pure API. Record the exact delta before implementation; no opportunistic upgrades. |
| `SOURCE-MANIFEST.json`, `PROVENANCE.json` | Extend the existing distribution inventory and origin attribution for the exact changed canonical files. No parallel manifest or relaxed verification. |

This is explicitly the **bundle-validation increment**, not the entire PR94
interface. Do not export a partial `validate_record_binding`, add an app-specific
record validator or present CheckedBundle as a final qualified record. The later
record-binding owner must still port the complete oracle, bind request/workload
artifacts and enforce independently required observation intervals. Preserve
that obligation; do not drop it because pure bundles can be inspected earlier.

The pure module must accept Linux and Windows instance variants without OS access.
Any dependency target-gating adjustment is limited to that purpose; it provides
no Windows attachment/native-delivery proof. If the inspected canonical base has
changed, reconcile source and manifest differences before implementation.

### Pure inputs, outputs and authority

`validate_bundle` consumes borrowed original manifest, instance, snapshot,
binding-table and raw-source bytes, independent expected canonical instance bytes,
`ExpectedBinding { binding_sha256 }`, and independently admitted profile bytes.
Source inputs are a bounded collection keyed by the manifest aliases; reject
duplicate keys, missing references and unreferenced supplied entries. A digest
or alias is never a path or URL. No file reads, network, process/environment
queries, callbacks into a collector, retry loop or implicit source acquisition.

CheckedBundle has private fields and no public unchecked constructor or
deserialization bypass. Read-only accessors preserve the checked raw bytes,
identity, sequence, manifest digest, observation window and missing-observation
paths. Borrowing keeps inputs immutable for its lifetime; any owned representation
must preserve that property and enforce caps before copies. Every exported view
comes from checked data. No conversion into AttachedEvidence, ReadyClient,
VerifiedSession, a permit or an approval capability.

Expected inputs are equality expectations, not authenticated capabilities.
Checking them against candidate bytes does not establish who supplied them or
prove a live process. A caller can inspect a synthetic/historical bundle without
qualifying it. No public API derives its own expected identity from the submitted
manifest and then claims an independent match.

### Raw parsing, schema ownership and bounds

Use the canonical draft-2020-12 schemas as the single owner of expressible shape,
type, enum, lexical, required-member and bound rules. Resolve their references
only through the pinned local registry. An unknown resource fails without network
retrieval; do not replace a missing evaluator with permissive parsing, parallel
regexes or a hand-maintained schema clone. The later PR must identify and pin the
real evaluator, demonstrate required keyword/reference behavior and justify any
new dependency before coding. This document selects no library or version.

Metadata parsing rejects invalid UTF-8, BOM, trailing data, duplicate members at
every depth, NaN/Infinity and excessive nesting. Detect duplicates before a map
can discard them. Use a bounded parser visitor, not a text/regex pre-scan; reject
container depth beyond 32 while descending, before allocating an unbounded tree.
Root container is level 1. Preserve exact integers and JSON Schema integer
semantics; no float round-trip may admit an out-of-range sequence or change an
identity. Declared byte counts are checked against original byte lengths.

Binding tables and raw source artifacts are opaque byte slices here, not arbitrary
JSON fed to the metadata parser. Their selected-engine format and interpretation
belong to the later source annex. No execution or dynamic loading from them.

Apply the existing inclusive caps: manifest/instance 16 KiB each; snapshot
64 KiB; binding table, each source and admitted profile 256 KiB each; source
entries 32; aggregate bundle 9 MiB. Count manifest plus each referenced object
per reference, including aliases sharing a digest, using checked arithmetic.
Apply individual caps also to independent expected instance/profile inputs;
counting the aggregate cannot replace them. Check lengths/counts before internal
allocation or hashing; this pure API cannot prevent a caller's earlier allocation.
Schema constraints additionally reject zero/negative/wrong-type declared sizes.
These are evidence bounds, not live compute, context or request budgets.

### Canonical identity and profile consistency

Reuse the exact instance serialization and process rules in the
[accepted interface](PR-Shared-Runtime-Companion-Interface.md#exact-instance-artifact-and-hash).
Schema-validate, parse U64Text with checked unsigned arithmetic, enforce platform
PID ceilings and positive Windows creation time, then compare raw canonical bytes.
Require the specified member/process order, literal version 1, ASCII without
escapes, no whitespace and exactly one final LF. Do not normalize and admit a
noncanonical candidate. Check the independently supplied expected instance by
the same rules before exact byte equality and digest comparison.

All hashes cover original complete bytes. Manifest `instance_id`, instance
ObjectRef digest and computed instance digest must agree with the independent
expectation. Validate profile comparison shape using qualification's existing
`profile_binding` definition; it does not replace independent profile admission.
Compare original profile digest, platform, unique tier ids, selected tier,
backend/device class, runtime archive and model digest against the instance, using
the oracle's rules at this single owner. Build/template/registration/process
identity must equal the independent expected instance; never fabricate these
from a profile that does not contain them.

### Bundle provenance and incomplete evidence

Match each ObjectRef to the exact retained byte length and SHA-256. Manifest and
snapshot instance and sequence must agree; snapshot binding digest must equal
the manifest bindings reference and independent ExpectedBinding. Source aliases
are unique. Distinct aliases
may share a digest only with identical retained bytes. Reject an unused listed
source, missing artifact or any mismatched reference, even in an otherwise
incomplete bundle.

Select snapshot device shape and capture clock from the independent instance's
backend/platform. Parse counters without overflow and require start <= end.
Every observed value must refer to a retained source with the correct alias,
server/device kind, artifact digest, instance and binding digest. Both observed
slot values must agree. Host cache-reuse and overlap remain exactly
unavailable/not_collected, as required by schema. Other canonical unavailable
values, and valid observed zero/false, remain valid.

Return incomplete bundles successfully with deterministic canonical field paths
for unavailable observations. Missing paths are diagnostics, never task scores
or qualification approval. Keep source_error distinct from malformed provenance;
bad identity/reference bytes cannot be downgraded to unavailable. A complete
bundle still cannot prove source truth, interval validity or task correctness.
Equal clock ticks do not prove order or overlap. Publication-history monotonicity,
replacement/restart races and live interval validity are not checkable from one
pure bundle; those remain reader/record-binding responsibilities.

Use PR94's closed EvidenceError meanings: Limit for resource caps; Malformed for
syntax/schema; DuplicateMember and NonFiniteNumber separately;
NonCanonicalInstance for canonical-byte violations; Integrity for missing,
size/digest or retained-byte failures; InstanceChanged for expected-instance
disagreement; BindingMismatch for profile/source/cross-object disagreement.
Diagnostics contain static categories and field identifiers only. No raw JSON,
document text, credentials, arbitrary paths or nested parser-error payloads.
Reader/OS/cancellation/history variants must not acquire invented pure meanings.

## Differences from validated work and explicit non-scope

The only proposed additions are bounded raw bundle admission, canonical instance
checks and cross-object consistency in the named shared owner. Existing shape
fixtures need not be internally consistent bundles: preserve their bytes and
schema outcomes. New synthetic matched bundles are separately inventoried; the
existing semantic-overflow, manifest-mismatch and reversed-window examples stay
schema-valid and must now fail at their named semantic origin.

The oracle has no companion input and no canonical instance serialization. Port
its shared comparisons without changing their meaning; do not claim direct
whole-record equivalence from a bundle-only API. Retain a test-only comparison
adapter for shared rules, not a second production record validator. Full
record-binding parity is still required in its later increment.

No capture, filesystem reader, publisher, sequence-history state, source mapping,
engine build, runtime selection, tokenizer/model call, public release, host vendor
bump, install, app adoption, enrollment, G0, canary or performance experiment.
No schema/request reordering, request reserialization, model/template/sampling/
slot/cache changes, task-score edits or production/Ollama changes. EW#317's
request/schema order protection remains the existing exact native-wire guard;
evidence parsing is not placed on that request path. Native Windows proof still
runs later on Juan's Windows box, not a VM; Windows remains first-release scope.

## Verification plan

This documentation PR: check local links and cited source owners, compare against
PR94/PR95 and merged schemas, inspect the full diff and whitespace, record the
source pins and omissions. No executable tests, builds or live calls now.

Later authorized implementation must provide:

- Frozen fixture/schema digests and exact expected outcomes; existing complete,
  incomplete, zero/false and negative cases run through the real canonical-schema
  evaluator. Keep direct schema tests separate so later semantic failures cannot
  hide a missing schema guard. Probe unknown local references with network denied.
- Shared-rule differential checks against `inspect_record`: profile bytes/hash,
  platform/tier/backend/artifact mismatches, duplicate tiers, expected/source
  instance, observed-slot disagreement and missing paths. Preserve opaque task
  receipts and pending/failing outcomes. State explicitly which record-only
  rules are deferred, rather than labeling this full record-port parity.
- Independently authored canonical vectors for both platforms, exact raw hashes,
  wrong order/spacing/escapes/LF, duplicate members at every container level,
  overflow, PID ceilings, zero ticks and positive FILETIME. A serializer's own
  output alone is not an independent expected vector.
- Every identity/provenance edge corrupted individually, with a valid opposite
  control: same-length tampering, wrong size/hash, missing/extra/duplicate source,
  shared digest with identical bytes, mixed valid/invalid references, wrong kind,
  unused listed source, incorrect clock/device, reversed window and binding.
- Cap min-1/min/max/max+1 where representable, root-depth boundaries, empty/single/
  maximum source lists, 0/empty/false/wrong-type inputs and checked arithmetic.
  Explain unreachable aggregate-overflow cases under individual caps; do not
  invent an impossible fixture or weaken a cap to manufacture a result.
- Exact error-category assertions at the origin, with no sensitive diagnostics;
  fail-first/regression proof and guard-removal mutations. Compile-time/API checks
  that CheckedBundle cannot become readiness/attachment/approval, and both
  platform variants inspect without changing native route availability.
- Existing frozen byte replay and manifest/provenance verification at the exact
  implementation pin; no fixture rewriting to obtain green. Use focused local
  tests, then required CI. No new broad harness duplicating the existing oracle.

## Assumptions, blockers, implementation summary and gap audit

DONE by this proposal: source inventory and a single pure bundle-owner contract,
with explicit parser, integrity, incomplete-evidence and authority boundaries.
The only repository change is this document. Cold-diff review must show no
implementation, fixture, schema, workflow or dependency edits.

NOT DONE: independent review/exact-revision acceptance; implementation go;
confirmed canonical implementation/distribution base and evaluator dependency pin;
implementation or parity tests; full record-binding port; authenticated reader;
selected-runtime source/interval annex; capture; G0 and consumer approval;
native-platform proof; live/task qualification and human quality review.

The evaluator choice/pin and any necessary dependency delta must be made concrete
and reviewed before code, not deferred to an unreviewed install. Scope expansion
beyond the paths/responsibilities above needs a contract amendment. Publication
and rights clearance remain separate from permission to prepare local code.

This contract proposes an explicitly independent pure-validation increment before
runtime selection; it does not dispatch PR94's dependent reader/capture sequence.
Runtime choice, issue #88 and live budgets block dependent work, not documenting
this bounded offline design. No historical PASS or schema-valid bundle closes
those gates.
