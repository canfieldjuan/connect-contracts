# App-binding and required observation-scope format contract

Status: PROPOSED; documentation only. Owner: connect-runtime. This refines the
representation prerequisite of [accepted record binding](PR-Shared-Client-Record-Binding.md),
merged in PR100. It proposes formats and their later verification, not executable
schemas, implementation, capture or qualification. Exact-revision acceptance and
separate implementation authorization remain required. Runtime-specific validity
rules, runtime choice, issue88 and live budgets remain OPEN. Host changes and
model calls remain on hold.

## Root cause and verified inventory

CONFIRMED at contracts `5ce38a92f5ccfcc723425a011d76009b85a47a5c`:
`qualification.schema.json` represents artifact references and observation sources;
`host-snapshot.schema.json` represents a collection window. Neither represents
the independent app bindings and required observation scope that PR100 needs.
Without a canonical representation, a later port could infer expectations from
the submitted record, hash reformatted requests, or confuse collection bounds
with evidence that a value was valid throughout a workload.

| Existing source owner | Reuse / limitation |
| --- | --- |
| [Qualification schema](../schemas/runtime/v1/qualification.schema.json), `intended`, `application_route`, `$defs/{artifact,source,alias,sha256,count,route}` | Original artifact alias/hash pairs, source kind/binding/artifact/instance references, route and lexical types. No request-occurrence linkage or required interval. |
| [Instance schema](../schemas/runtime/v1/instance.schema.json), `$defs/{u64_text,linux_process,windows_process}` | Canonical instance digest binds platform/process identity; Linux includes boot IDs. Windows process creation FILETIME is not a GetTickCount64 clock-origin proof. |
| [Host snapshot](../schemas/runtime/v1/host-snapshot.schema.json), `capture_window` | Platform-specific collection clock/start/end; host-only request/workload placeholders. Collection bounds are not validity bounds. |
| [Companion interface](PR-Shared-Runtime-Companion-Interface.md#bounded-interfaces-and-error-contract) | Independent expectations, per-value validity gate, unavailable behavior and closed errors; metadata cap in its file/parser limits. |
| [Record-binding contract](PR-Shared-Client-Record-Binding.md#complete-binding-algorithm-obligations) | Complete oracle port, byte-preserving app links, snapshot equality with only two exceptions, independent scope and no partial validator. |
| [Oracle](../tests/runtime_qualification.py), `inspect_record`, `_parse` | Preserve existing cross-artifact checks and corrected integer ingestion. Does not yet validate the proposed formats. |
| Merged client `fe1a15742f7b676251b35fdca9e13fd817aa4415`, `crates/model-client/src/evidence.rs::{validate_bundle,CheckedBundle,reference,observations}` | Existing pure consistency boundary, original-byte retention, digest/size checks and missing paths. No record-binding/scope implementation; no source authentication. |

Reuse the [PR100 inventory](PR-Shared-Client-Record-Binding.md#root-cause-and-verified-inventory)
and its existing host/U1b inventory links for frozen fixture results, model/runtime/
template pins, prompts, request bytes, corpus bindings and historical proof.
No rebuilt inventories, new model assumptions or rescoring. The only proposed
behavioral additions are the explicit formats and relationships below; existing
records, bundle assets, request bytes, task receipts and parser policy stay intact.
INFERRED: canonical formats remove a representation ambiguity before a port.
UNKNOWN: runtime source extraction, validity/invariance semantics and native
clock-association evidence. This PR does not claim to close those unknowns.

## Required change surface

This PR changes this Markdown plan and adds a forward pointer to PR100's plan.
A later authorized contracts-only schema increment would add exactly:

- `schemas/runtime/v1/app-bindings.schema.json`;
- `schemas/runtime/v1/observation-scope.schema.json`;
- `fixtures/runtime/v1/record-binding/{README.md,index.json,*.json}` with an
  explicit leaf inventory and shape expectations;
- a focused offline schema test file and the existing exhaustive runtime fixture
  inventory integration, identified at that increment's pinned base.

These are proposed paths, not files delivered here. Canonical schema IDs use the
existing `https://local-connect.invalid/schemas/runtime/v1/` namespace. Reference
existing definitions through a fixed local registry; reject unknown resources
without network access. No changes to existing canonical schema definitions,
Python oracle behavior, client registry/dependencies, source manifests or host
vendored copies in this documentation slice. Later client adoption remains separate.

## Shared shape, byte and authority rules

Both proposed documents are closed JSON objects. Every listed member is required;
no unspecified members, implicit defaults, hidden observation values, commands,
URLs to fetch, parser expressions or extension bags. Nested objects are closed
as well. `oneOf` discriminators, `const`, enums, bounds, required members and
reference types belong in schemas. Cross-document equality, indexed uniqueness
and coverage belong to the future shared record-binding owner, not app regexes.

Use the existing corrected integer-only JSON parser: no duplicate members,
nonfinite values, fraction/exponent notation, negative zero or out-of-range
integers. U64Text uses the existing decimal-string definition plus checked u64
conversion; timestamps are never floating point. Root container is depth one;
maximum depth is 32. Limits are inclusive.

The **sum of both original documents** is at most 256 KiB, checked before parsing
or copying; neither can individually exceed that cap. This allocates the existing
app-binding metadata budget, not an additional budget per document. Record and
admitted-profile caps remain independently 256 KiB each. Request bodies, document
contents and raw runtime logs are not embedded. No model-context or request-size
cap follows from these metadata limits. Arrays are bounded by the byte budget
and the field-specific limits below; no recursive acquisition.

Hash each original document's raw bytes without normalizing whitespace, key order,
escaping or line endings. Only the existing instance object has canonical byte
serialization; do not impose its encoding on these documents or on requests.
Metadata is supplied by the independent qualification/request harness, not derived
from the candidate final record. Pure consistency checks do not authenticate that
supplier, a process, retained business documents or live traffic.

## Proposed app-bindings object

| Required member | Shape / meaning |
| --- | --- |
| `app_bindings_version` | Integer constant 1. |
| `instance_id` | Canonical Digest, equal to the CheckedBundle instance. |
| `application_route` | Existing qualification `$defs/route`; exact independent route expectation. |
| `profile` | Existing Artifact `{alias, sha256}`; digest of the admitted original profile bytes. |
| `requests` | Ordered array of Artifact references for the exact offered request occurrences. Empty is representable for incomplete/offline records; it proves no workload. |
| `sources` | Array of closed app-source entries below; at most two, one for each host-placeholder field. |

Each app-source entry has exactly `field`, `kind`, `artifact`, `request_indices`.
Use a schema `oneOf` pairing `effective_settings.prompt_cache_reuse` with kind
`request`, and `concurrency.requests_overlap` with kind `workload`. `artifact` is
an existing Artifact referring to retained harness evidence. `request_indices`
is a nonempty array of canonical nonnegative Count values, schema `uniqueItems`
true; semantic validation requires strictly increasing indices within `requests`.
It records which occurrences the source describes, not output/completion order.
An identical request offered twice uses distinct occurrence aliases even if the
original byte hashes match. Retries are separate offers, never collapsed.

Aliases for profile, request occurrences and distinct source artifacts form one
unambiguous app namespace. Reusing an alias is allowed only to reference the same
artifact with the same digest under the explicit reuse cases below; profile aliases
are never reused and duplicate request occurrence aliases are always refused. A
source may reference a request artifact directly when that artifact is the one
indexed request; otherwise it uses a distinct source alias.
A shared source artifact may support both fields only with identical alias/digest
and explicit occurrence attribution in both entries. Source aliases must not
collide with host-source aliases from the bundle. No arbitrary path interpretation.
Duplicate source fields are refused even when the entries are byte-identical.

`SHA256(original app-bindings bytes)` is the expected `binding_sha256` for final
**app-owned** observed sources. The app-bindings object never contains its own
digest, avoiding circular hashes. Final source kind, alias, artifact digest and
instance must match its entry; its binding digest must match that computed hash.
Host server/device sources retain the bundle's binding digest unchanged. This
uses the independent harness mapping as the app binding table; it does not
pretend the host's opaque engine binding table describes request evidence.

Compare the final `application_route`, `intended.profile` and ordered
`intended.requests` to these independent values, without reserializing requests.
Every observed app-owned field has exactly one matching source entry; every
entry must support an observed app-owned field. Unavailable fields require no
source entry and must not carry hidden sources. Failed offers, rejections and
unusable source receipts remain retained by the harness/task evidence owner;
they are not promoted to fabricated observations merely to include them here.
All offers remain in the intended request list, regardless of success.

This format establishes attribution, not how to extract a boolean from request
bytes or aggregate mixed request policies into one final observation. Those
reviewed source rules remain open. A source referring to only part of a workload
cannot establish a whole-workload assertion without the rule proving that scope.

## Proposed observation-scope object

| Required member | Shape / meaning |
| --- | --- |
| `observation_scope_version` | Integer constant 1. |
| `instance_id` | Digest equal to app-bindings and CheckedBundle. |
| `app_bindings_sha256` | Digest of the exact app-bindings bytes; one-way link, no cycle. |
| `bundle_manifest_sha256` | CheckedBundle manifest digest; binds this scope to one publication. |
| `clock` | Platform-paired enum: `linux-boottime-ns` or `windows-uptime-ms`. |
| `clock_binding` | Null or an Artifact reference to independently retained clock/instance association evidence. A reference is not proof that this evidence is sufficient. |
| `requirements` | Array of closed per-field requirements below, unique by field. |

Each requirement has exactly `field`, `interval`, `rule`.
`interval` is closed `{start, end}` with U64Text bounds and checked `start <= end`.
Intervals are inclusive coverage requirements; zero and equal bounds are
representable. They never prove event order or overlap. No default start/end,
clock substitution, tolerance or unit conversion is allowed.

`field` is a schema enum of the actual observation paths from the qualification
schema: backend-appropriate `device.*`, every `effective_settings.*` property,
and both `concurrency.*` properties. The later schema implementation must enumerate
those exact paths from the pinned canonical schema and test set equality; never
admit arbitrary dotted paths. Reuse definitions instead of introducing observation
value types here. Wrong-backend paths, unknown paths and duplicate requirements
are refused. Entries are semantically keyed by field, not positional joins.

The exact path inventory at the inspected base is:

| Group | Allowed paths |
| --- | --- |
| cuda_device | `device.name`, `device.compute_capability`, `device.nvidia_driver_version`, `device.cuda_runtime_version` |
| vulkan_device | `device.name`, `device.physical_device_identity`, `device.api_version`, `device.driver_implementation`, `device.driver_version` |
| settings | `effective_settings.context_per_slot`, `effective_settings.slots`, `effective_settings.logical_batch`, `effective_settings.physical_micro_batch`, `effective_settings.context_checkpoints`, `effective_settings.prompt_cache_reuse`, `effective_settings.flash_attention`, `effective_settings.kv_cache_type_k`, `effective_settings.kv_cache_type_v`, `effective_settings.offloaded_layers` |
| concurrency | `concurrency.slots`, `concurrency.requests_overlap` |

The requirements array has a schema maximum equal to the union of these paths;
semantic validation rejects fields outside the actual backend. Empty is valid
when no observed value needs support; it never waives an observed-field check.

`rule` is either null or a closed `{ruleset_sha256, rule_id}` reference. Digest
uses the existing SHA-256 definition; ID uses the existing Alias definition.
This is a reference syntax, **not a policy language or an open runtime registry**.
No expression, executable code, configurable predicate, `approved` boolean,
caller-declared coverage or caller-declared lifetime invariance is permitted.
A later reviewed, pinned rule set owns the finite allowed IDs and their per-field,
source-kind, runtime/build and evidence applicability. A syntactically valid
reference has no validity authority until that membership and applicability are
verified. This document registers no production or synthetic rule as trusted.

For every asserted observed field, require exactly one requirement and a non-null
reviewed/applicable rule with sufficient retained evidence. A missing requirement,
null/unrecognized rule or insufficient validity/clock support fails
`ObservationScope`; do not infer a rule from the field name. For an unavailable
field, a requirement may be absent or carry a null rule; no temporal proof is
needed and the field remains in the missing-observation list. If a requirement
is supplied, its shape/identity and interval ordering still must be valid; absent
validity for unavailable values is not an error. Unknown but well-shaped rule
references on unavailable values are not claimed to be validated or trusted.

The independent owner sets the required interval before checking the candidate;
it must not shrink it to fit the source or snapshot window. Rule evaluation must
establish coverage of that interval or instance-lifetime invariance. Requirements
contain no assertion of achieved coverage. Binding to the manifest prevents a
scope from silently attaching to another snapshot, but even a matching manifest
and capture window do not prove a setting stayed valid.

Clock-binding aliases must not conflict with another retained artifact alias/digest.
Null clock binding is valid for unavailable observations; for asserted values it
is admissible only if the reviewed lifetime-invariance rule establishes the full
required scope without cross-clock comparisons. Interval rules requiring clock
association fail `ObservationScope` without its evidence. No placeholder artifact
is required just to represent missing proof.

Clock association is explicitly not solved by these fields. The future reviewed
rule/evidence must tie the harness timestamps and source timestamps to the same
instance and time origin. Linux boot identity must agree with the canonical
instance; Windows process creation FILETIME is not interchangeable with uptime.
A label, digest-shaped reference, PID or same clock name cannot establish this.
Native clock proof, resolution/ambiguity handling and engine-specific validity
remain open. Do not infer overlap from equal ticks, offered concurrency or slots.

## Single-owner validation and errors

The future record-binding owner consumes both raw metadata documents together
with the original record, CheckedBundle and admitted profile. Reuse the existing
parser and schema owners, then enforce the cross-document relationships above;
never expose a second app-local validator or a public partial record validator.
No original-byte request/property-order change is authorized by evidence parsing.
Task receipts and human review remain opaque and retained.

Keep PR100's error meanings: malformed shape/unknown version is `Malformed`;
duplicate members and nonfinite numbers retain their dedicated parser errors;
byte/depth limits are `Limit`; mismatched instance is `InstanceChanged`; raw
artifact/digest mismatch is `Integrity`; ordered-reference, alias, attribution or
other cross-document disagreement is `BindingMismatch`; invalid/missing validity
support for asserted observations is `ObservationScope`. Reversed requirement
intervals are `BindingMismatch` even for unavailable fields (invalid metadata,
not a demand for validity proof). Single-fault tests establish each mapping;
existing multi-fault precedence is unchanged. Diagnostics contain static field
identifiers/categories only, not payloads or private artifact names.

## Verification plan

This documentation PR: compare against pinned schemas, oracle and client source;
check links, source symbols, complete diff, two-document scope and whitespace.
No builds, executable tests or fixture replays.

Later separately authorized offline format work must cover:

- Existing raw fixtures/oracle outcomes unchanged; new shape fixtures use public
  synthetic artifacts and explicit hashes/outcomes. Schema-valid is not record-
  binding-valid, source-authenticated or task-correct; record these separately.
- Valid CUDA/Linux and Vulkan/Windows shapes; valid incomplete records with no
  sources/requirements, zero timestamps, false app observations, equal intervals,
  repeated identical offered bytes with distinct aliases and retained order.
- Unknown/missing/extra members, wrong discriminators, duplicate JSON keys,
  malformed integer/U64Text forms, byte/depth maxima and one-over controls.
- Duplicate occurrence aliases/source fields/requirement fields, contradictory
  shared aliases, host/app alias collisions, mismatched raw digests, changed route,
  reordered/dropped/extra requests, wrong instance/publication, and cross-kind sources.
- Empty, duplicate, unsorted or out-of-range request indices; source assertions
  covering only a subset of the independently required workload; retained failed
  offers must not be silently dropped to make attribution pass.
- Every canonical observation path, wrong-backend paths, absent/null/unrecognized
  rules for observed values versus valid unavailable controls; reversed intervals,
  wrong clock/instance/boot and insufficient scope. Shape-only tests must not claim
  to exercise runtime-rule semantics that do not yet exist.
- Original-byte hashing including whitespace/property-order differences; schema
  request-field order remains untouched. No callback, dynamic code, network
  resolution, file acquisition or capability conversion reachable from metadata.

Schema expression owns shape constraints; named cross-artifact semantic checks
own equality/uniqueness/coverage. Later implementation must show guard-removal
controls for actual semantic guards, not create a duplicate speculative oracle
in a schema-only slice. Reuse the frozen parity harness and durable receipts.

## Assumptions, blockers and explicit non-scope

The proposed [runtime observation evidence contract](PR-Shared-Runtime-Observation-Evidence.md)
inventories existing source owners and the remaining per-field validity evidence.
It does not register rules, select a runtime or authorize implementation.

These formats are proposed equality/requirement metadata, not authenticated
capabilities. Their acceptance would close only the documented representation
choice, not supply executable schemas or validity proof. Runtime rules must still
specify finite IDs, per-field extraction/aggregation, source artifact formats,
validity/invariance, clock-association evidence and resolution behavior. No dummy
rule, all-rejecting implementation or relaxed bypass may count as completion.

No implementation, schema files, builds, fixture replays, client/host changes,
model/tokenizer calls, dependency changes, reader/capture/publication, app adoption,
profile admission, arithmetic work, runtime selection, issue88 closure, live
budgets, production/Ollama changes or additional remote creation. Native Windows
proof remains later on Juan's Windows machine; offline formats do not replace it.

## Implementation summary and cold diff audit

This plan specifies two bounded original-byte formats, their relationship to
existing records and bundles, unique occurrence/source attribution, independent
per-field interval requirements and explicit untrusted rule references. The
parent gains only a forward pointer, preserving its accepted obligations. Current
verification is documentation/source inspection; no executable result is claimed.

## Gap audit

NOT DONE — format acceptance, executable schemas, runtime-specific rule/evidence
closure, later client implementation and qualification remain separate gates.
Documentation is prepared for independent review; host changes and model calls
remain on hold.
