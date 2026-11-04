# Shared-client final record binding contract

Status: PROPOSED; documentation only. Owner: connect-runtime. This proposal
specifies the next pure validation boundary, not an implementation authorization.
Independent review and exact-revision operator acceptance precede any later code
work. Runtime-specific source-validity mappings, runtime selection,
[issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88) and live
budgets remain OPEN. Host changes and model calls remain on hold.

## Root cause and verified inventory

CONFIRMED: the merged client checks bundle consistency, but it does not export
`validate_record_binding`. Calling a checked bundle a qualified final record
would skip the independent request/workload binding and observation-scope rules.
This is an intentionally deferred boundary, not a reported production defect or
an inference-arithmetic fix.

Inspected bases: contracts `955493fe6605176872657d99c10506f955e2fb9b` (merged
PR99 corrected oracle), client `fe1a15742f7b676251b35fdca9e13fd817aa4415`
(merged PR1; tree equals reviewed `7c58663677c256071a41737670b88f35cf716fd3`).
Historical Proposed headings in earlier plans do not supersede those merge facts.

| Existing owner | Proven behavior / required reuse |
| --- | --- |
| Client `crates/model-client/src/evidence.rs::{validate_bundle,CheckedBundle,ExpectedBinding,EvidenceError}` | Pure bounded bundle inspection; private checked fields, original-byte accessors, independent equality expectations. No final-record validator or `ObservationScope` variant yet. |
| [Oracle](../tests/runtime_qualification.py), `_parse`, `inspect_record`, `_observations` | Canonical integer ingestion; profile digest/platform/tier/backend/archive/model matching; expected instance and every observed source instance; slot equality; unavailable paths; opaque task receipts. No complete bundle/request/workload or interval proof. |
| [Qualification schema](../schemas/runtime/v1/qualification.schema.json), `intended`, `application_route`, `$defs/source`, `$defs/artifact` | Final record shape. Intended artifacts carry aliases and hashes; sources carry kind, binding digest, artifact digest, alias and instance. These fields alone do not authenticate their provenance. |
| [Host snapshot](../schemas/runtime/v1/host-snapshot.schema.json) | Collection window plus device/server observations. `effective_settings.prompt_cache_reuse` and `concurrency.requests_overlap` are unavailable `not_collected` placeholders. |
| [Companion interface](PR-Shared-Runtime-Companion-Interface.md#bounded-interfaces-and-error-contract) | Existing record-binding obligations, error meanings, authority separation and inclusive byte/depth caps. This contract refines that boundary without selecting engine validity mappings. |
| [Bundle contract](PR-Shared-Client-Offline-Evidence-Validator.md), PR97/98 | Single parser/schema owners, exact numeric domain, fixed local schema registry, evaluator configuration and no-partial-record-validator rule. |
| [Qualification fixtures](../fixtures/runtime/v1/qualification/README.md), [oracle tests](../tests/test_runtime_qualification.py), [companion fixtures](../fixtures/runtime/v1/companion/README.md) | Frozen complete/incomplete CUDA/Vulkan cases and failures; reuse before adding minimal synthetic cross-artifact cases. |

Reuse the [host capture inventory](PR-Shared-Runtime-Host-Capture.md#root-cause-and-current-source-inventory)
and [U1b validated-work inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port)
for model/runtime/template pins, prompts, framing, sampling, budgets, native-wire
replay, the 301-file receipt, issue-73 and pre-production corpus references.
Do not rebuild inventories, import private documents or claim fresh task results.
The corrected-oracle replay and client tests establish offline evidence semantics,
not live source validity, native Windows delivery or production qualification.

INFERRED: one shared record-binding owner prevents apps from independently
reconstructing these cross-artifact checks. UNKNOWN: the selected runtime's
per-field evidence sources and validity rules, and any live performance result.

## Required change surface

This PR changes only this plan and a forward pointer in the bundle contract.
No executable file, fixture, schema, lockfile, distribution manifest or host copy
changes. A later separately authorized implementation would be confined to:

- Client `crates/model-client/src/evidence.rs`: complete pure record binding,
  opaque validated result and the parent-defined `ObservationScope` error;
  reuse existing parsing, schema registry and bundle accessors.
- Client `crates/model-client/src/evidence_tests.rs` and existing evidence fixture
  tree: frozen-oracle parity plus independently bound synthetic negative controls.
- Client `SOURCE-MANIFEST.json` and `PROVENANCE.json`: existing distribution
  inventory for those exact changes. No parallel inventory or host re-vendoring.

New serialized binding/policy shapes belong to canonical contracts schemas,
not private Rust-only validators. Their representation is a prerequisite below;
this proposal does not silently add a fifth registry resource or authorize schema
changes. No new dependency is proposed. Preserve the accepted plain evaluator
configuration and PR98 numeric ingestion; any necessity to change them requires
its own evidence and separately reviewed scope.

## Pure API and independent inputs

Conceptual signature (not a compilable API commitment):

`validate_record_binding(raw_record, &CheckedBundle, admitted_profile_bytes,
independent_app_bindings, required_observation_scope) -> ValidatedRecord | EvidenceError`.

The final API must accept original borrowed bytes, immutable checked bundle data,
and bounded independent comparison metadata. It performs no filesystem, network,
process, environment, tokenizer, model, capture or callback-driven acquisition.
Aliases and digests never become file paths or URLs. It does not construct its
expectations from the candidate record and then claim independent agreement.

Input ownership:

| Input | Independent owner and comparison duty |
| --- | --- |
| CheckedBundle | Existing bundle validator; preserves original retained bytes and its checked identity, source bindings, sequence and window. It is not authenticated attachment authority. |
| Admitted profile bytes | Existing profile-admission caller; must be byte-identical to the bundle profile and satisfy the full oracle comparisons for the record. Pure validation does not admit a profile. |
| App binding metadata | Request/workload harness owner supplies the route, ordered intended request artifact references, request/workload source bindings and retained-artifact digests independently of the submitted record. Hashes represent original bytes, never parsed/reformatted request objects. |
| Required scope | Independent qualification/harness owner specifies which interval each asserted value must cover, with clock/instance association; reviewed per-field source rules and supporting evidence establish coverage or lifetime invariance. The candidate cannot choose a shorter interval. |

The app metadata cap is not a model-request cap: metadata contains independently
checked aliases/hashes/intervals, never request bodies or document text. Hashing
and retaining those original artifacts belongs to the existing harness owner.
Pure comparison cannot authenticate that owner or prove it hashed real traffic.
No function pointer, arbitrary predicate or caller-provided `approved: true` can
substitute for a closed, reviewed source-rule representation.

ValidatedRecord has private fields and no unchecked constructor/deserialization
bypass. It exposes the checked original record bytes and deterministic missing
observation paths, retaining task receipts and their order unchanged. It cannot
convert to AttachedEvidence, ReadyClient, VerifiedSession, a permit, enrollment,
task PASS or qualification approval. Complete evidence is not a successful task.

## Complete binding algorithm obligations

1. Enforce the parent's inclusive limits before parsing/copying: record, admitted
   profile and app-binding metadata each at most 256 KiB; JSON depth at most 32
   containers. Retain existing bundle/source/aggregate caps. Required-scope and
   rule-reference metadata must fit within the app-binding metadata budget, not
   introduce a second unbounded collection. Canonical schema owns expressible
   structure/types/ranges; shared parser owns duplicate, nonfinite and integer
   notation checks. No recursive external reference retrieval.
2. Port **all** `inspect_record` checks, including unique profile tier IDs, selected
   tier resolution, both observed slot values and each observed source instance.
   Preserve original profile digest semantics. Reuse the corrected `_parse`
   oracle and current client parser; do not weaken the numeric domain or rewrite
   the Python oracle to fit Rust outcomes.
3. Match final profile/platform/tier/backend/runtime archive/model/instance to the
   bundle's checked instance and admitted profile. Match each host-owned device,
   settings and concurrency observation to the snapshot, including state, value,
   reason and complete source reference. Equality is structural after canonical
   ingestion; preserve original bytes for hashing and returned views.
4. Exempt only the two named host placeholders from snapshot equality. Their
   final observed forms require independent request/workload provenance; unavailable
   forms remain valid incomplete values with canonical reasons. Never infer
   prompt-cache reuse from server capability or overlap from slot count/offered
   concurrency. An app cannot substitute request sources for server/device fields.
5. Bind `application_route`, `intended.profile` and the complete ordered
   `intended.requests` list to the independent owner's metadata. Reject changed,
   missing or extra entries, including alias/digest disagreement. The profile
   artifact digest must still equal the original admitted profile digest.
   Every asserted request/workload source must match the independent binding
   table and its retained artifact reference, including kind, alias, artifact
   digest, binding digest and instance. Host sources remain bound to the checked
   bundle's retained source objects. No dangling or ambiguous alias resolution.
6. For every asserted observed value, enforce the reviewed source rule for the
   independently required interval or instance-lifetime invariance. Matching the
   snapshot window or a live PID is insufficient. Missing rule/evidence or
   insufficient scope fails `ObservationScope`; never widen a window, invent a
   TTL/grace period, extrapolate a report or relabel a mismatch as unavailable.
7. Return canonical unavailable paths for genuinely unavailable observations.
   Do not turn these into scope errors, fill values from defaults, coerce false
   to missing or treat zero as failure where its schema permits it. Preserve
   opaque `task_evidence` references without reading/scoring them, changing task
   outcomes or resolving pending human review.

The oracle-only acceptance surface and full binding acceptance are different.
Frozen oracle cases must retain their oracle outcomes; a complete binding test
must additionally supply independent bundle/app/scope evidence. A historical
record alone is not a successful binding test. Report stricter binding refusals
separately, never as an unexplained oracle regression.

## Errors and diagnostic boundaries

Reuse existing `Limit`, `Malformed`, `DuplicateMember`, `NonFiniteNumber`,
`NonCanonicalInstance`, `Integrity`, `InstanceChanged`, `BindingMismatch` meanings.
Add only the already contracted `ObservationScope` for an asserted observation
whose reviewed validity support is absent or insufficient. Identity disagreement
is `InstanceChanged`; digest/size failure is `Integrity`; cross-artifact or
independent-expectation disagreement is `BindingMismatch`. Schema/unknown version
and noncanonical numeric notation remain `Malformed` under the existing parser.
Tests isolate one fault per category; this proposal does not redefine existing
multi-fault error precedence. Do not emit reader-only I/O, cancellation,
publication-race or absence errors from this pure API.

Diagnostics contain static categories/field paths, never submitted values,
private document text, credentials or arbitrary artifact paths. Failed binding
must not mutate the bundle/record, consume a task receipt or suppress the caller's
retained failed attempt. No automatic retry or fallback approval.

## Assumptions and explicit blockers

The generic obligations can be reviewed now. Full executable sign-off remains
blocked until a separately reviewed prerequisite closes:

- The canonical app-binding and required-scope representation, alias uniqueness,
  request/workload attribution, exact closed source-rule references and their
  schema/type ownership. Existing qualification artifacts have only alias/hash;
  the snapshot has a collection clock/window. Neither currently expresses a
  complete independently required interval/source-validity proof.
- Runtime-specific per-field mapping, temporal validity versus lifetime invariance,
  retained evidence requirements and cross-clock/boot association. Runtime choice
  remains open; no selected-engine rule, timestamp conversion or trust adapter is
  guessed here. A same-named clock is not proof of a common time origin.
- Separate implementation authorization after accepted contract/prerequisites,
  with source pins reconciled and a concrete API/fixture inventory reviewed.

There is no partial public validator that skips intervals, no all-rejecting stub
presented as completion and no app-local bypass while those prerequisites remain
open. Synthetic rules can exercise mechanics later but cannot qualify a runtime.
This document does not block independent pure bundle inspection already merged.

## Verification plan

For this documentation PR: verify cited paths/symbols against the pinned source,
read the complete diff, check local links and whitespace, and confirm only the
two declared Markdown files changed. No code tests or builds are applicable.

For a later authorized implementation:

- Reuse frozen qualification/companion/numeric fixtures and the corrected-oracle
  differential harness, preserving raw inputs and expected outcomes. Inventory
  every difference; add minimal synthetic cases only for new binding obligations.
- Probe both valid complete and valid incomplete CUDA/Vulkan branches, false/zero,
  unchanged task receipts, reordered request lists, missing/extra/mixed source
  entries, duplicate aliases, wrong instance/profile/tier/backend/model/archive,
  forged app sources, altered retained bytes and inconsistent observed slots.
- Probe independently specified intervals at coverage boundaries, empty/reversed
  intervals according to the accepted future shape, wrong clock/boot/instance,
  absent policy, out-of-scope evidence and lifetime claims without proof.
  Unavailable observations must remain incomplete success, not scope failure.
- Probe exact byte/depth limits and one over, empty/malformed/duplicate/nonfinite/
  rounded numeric inputs, bounded mixed arrays, no network schema resolution,
  private diagnostics and no public unchecked constructors/capability conversions.
- Verify original request hashes and response-schema property order without
  reserialization or insertion into the native generation path. Reuse existing
  transport byte-preservation tests; evidence validation cannot reorder app schemas.
- Remove each binding/scope guard in an isolated mutation control and require the
  corresponding negative test to fail. Reuse immutable evidence outside worktrees;
  distinguish oracle parity from full binding and from live qualification.

## Explicit non-scope

No implementation, builds, fixture replay, schema changes, dependency changes,
host changes/re-vendoring, capture/publication/reader implementation, qualification
permit, app adoption, tokenizer/model calls, engine changes, arithmetic sandbox,
runtime choice, issue88 closure, hardware/admission changes, live budgets,
Ollama/production changes, remote creation or publication/license decision.
Windows remains first-release scope with later proof on Juan's native Windows
box; offline Windows JSON validation does not satisfy that proof.

## Implementation summary and cold diff audit

Documentation only: this file records the verified inventory, full binding
obligations, independent inputs, error/authority limits, future tests and open
prerequisites. The bundle contract gains only a forward pointer; its historical
inventory and implemented increment are not rewritten. Verification is source and
diff inspection, not evidence of working record-binding code.

## Gap audit

NOT DONE — implementation and runtime qualification are not delivered by this
proposal. Documentation preparation is complete for independent review; acceptance,
closed schema/type and runtime-validity prerequisites, implementation authorization,
implementation proof, host integration and live qualification remain separate gates.
