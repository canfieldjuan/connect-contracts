# Retained observation evidence and association contract

Status: PROPOSED, documentation only. Owner: connect-runtime. This addresses the
format/association and membership gates in [PR103](PR-Shared-Runtime-Observation-Evidence.md),
using [PR104's comparison annex](PR-Llama-C1d0e7a-Observation-Annex.md).
It also explicitly amends the PR101/102 duplicate-field error boundary below.
Exact-revision acceptance is required; acceptance would cover this contract only.
Runtime selection, issue88, hardware policy and live budgets remain OPEN.
No trusted runtime rule is registered and no executable behavior changes here.

## Root cause and verified inventory

CONFIRMED at contracts `8c6eb37b874b3234de1ae37c4e5d73fc96980cbe`:

| Existing owner | Evidence and limit |
| --- | --- |
| [PR104 lifecycle and field map](PR-Llama-C1d0e7a-Observation-Annex.md#complete-field-map) | Pinned source distinguishes load lifetime from PID lifetime, configured caps from realized work, and device enumeration from selection. Some values have no safe existing reporting surface. These are comparison findings, not installed-runtime observations. |
| [Companion interface](PR-Shared-Runtime-Companion-Interface.md#file-parser-and-storage-limits) and [host capture](PR-Shared-Runtime-Host-Capture.md#source-binding-obligations-no-engine-selected) | Existing source-object, bundle and storage caps; independent expected binding digest; private adapters and real binding tables. No safe engine-specific retained format is implemented. |
| [App-binding schema](../schemas/runtime/v1/app-bindings.schema.json), `properties.sources`, and [scope schema](../schemas/runtime/v1/observation-scope.schema.json), `properties.requirements` | Closed field alternatives and array maxima, but no per-field cardinality guard. `uniqueItems` on request indices is a different invariant. |
| [Fixture index](../fixtures/runtime/v1/record-binding/index.json) and [focused shape test](../tests/test_runtime_record_binding.py), `test_fixture_inventory_hashes_and_exact_shape_outcomes` | `app-semantic-source-field.json` and `scope-semantic-field.json` deliberately pass shape checks today. No full record-binding implementation is claimed. |
| [Record-binding API contract](PR-Shared-Client-Record-Binding.md#pure-api-and-independent-inputs) | Pure validation, independent expectations, original-byte hashing, no partial public validator or source-authentication authority. |

The gap originates at the evidence contract: a digest of arbitrary bytes and a
plausible timestamp cannot establish what was measured, which load/device it
belongs to, or who owns permission to interpret it. The uniqueness gap originates
in PR101's allocation of a schema-expressible constraint to semantic validation;
PR102 implemented that accepted allocation. This is an explicit contract amendment,
not an unreported implementation regression or a downstream compensating guard.

Reuse PR103's historical inventory, PR104's pinned source blobs, and the existing
U1b/corpus receipts. Do not rebuild corpus inventories or rescore prior tasks.
INFERRED: a closed passive format can support a later producer and validator.
UNKNOWN: native acquisition, source authenticity, complete per-build rules and
any future run's effective settings. Documentation does not close those unknowns.

## Required change surface and non-scope

This slice changes this plan and reconciles the two parent observation/format
plans. No schema, fixture, code, lockfile, dependency or distribution asset changes.
The later executable schema increment, rule admission, client integration, private
host collection and native qualification each require separate authorization.
No engine is selected by specifying common evidence types. No builds, replay,
model/tokenizer calls, GPU probing, live tests, arithmetic-sandbox writes, service,
production or Ollama changes. Windows remains first-release scope; native proof
runs later on Juan's own Windows box, not a VM.

## Bounded retained formats

These are proposed wire descriptions, not new files or accepted runtime mappings.
Canonical schemas will live in connect-contracts; exact asset closure and fixture
inventory must be reviewed before a later schema increment. Reuse the existing
Digest, Alias, Artifact, Count, Label, U64Text and platform/backend definitions.
All listed object members are required, all objects closed, versions integer 1;
nullable alternatives are explicit. Reuse the corrected integer-only parser,
checked U64Text conversion, duplicate-member refusal and depth limit 32. Do not
introduce a general key/value telemetry bag, parser expression or policy DSL.

### Limits and retention

An individual retained report is at most 256 KiB of original UTF-8 JSON bytes.
Reports and their association records consume the existing maximum 32 host-source
entries and 9 MiB bundle budget; there is no auxiliary unbounded association store.
The binding table stays within 256 KiB. The app-bindings plus scope documents
still share 256 KiB, and carry references, not embedded reports. Existing 64 MiB /
1024-entry publication storage limits remain unchanged. These are evidence-format
limits, not inference budgets. Checked sums count every reference before allocation.

Report-local collections also have finite bounds: 20 fact entries; 256 lifecycle events;
32 selected-device associations; 64 loaded-component digests; 256 clock brackets.
All evidence-format string/component bounds are representation limits, not execution
budgets. Each inline association is charged to its containing source object's bytes.
Exceeding any bound refuses/truncation-invalidates the attempted capture; it never silently
omits an event or changes an assertion to successful coverage. Original failed
attempt/task receipts remain with their existing owner. Splitting a workload for
later evidence needs a new independently declared scope, not post-hoc shrinking.

Only a reviewed producer may construct the allowlisted fact/association fields
from admitted reporting sources. Never retain full `/props`, `/slots`, environment,
argv, logs, headers, socket paths, model paths, templates, prompts or responses.
No generic `text`, exception-message or debug attachment. Hashing a credential is
not permission to retain it. Labels come only from the reviewed hardware/version/
cache-type source, bounded by canonical Label and this report's byte cap; labels
may not be populated from operator free text, request metadata or filenames.
If a surface cannot be safely acquired without retaining disallowed data, it is
not an admitted source. Privacy is enforced at acquisition, not by later redaction.

Raw means the exact bytes emitted by that reviewed evidence producer. An allowlisted
projection is a new derived artifact whose producer mapping and input provenance
must be reviewed; it is not mislabelled as an untouched HTTP reply or edited log.
Hash the original emitted bytes. Never hash normalized JSON as a substitute. Evidence
is private, mode 700 directories / 600 files outside worktrees for review; public
conformance artifacts are synthetic. Pure validation authenticates no producer.

### Report envelope

Each report has exactly these members:

| Member | Closed shape and role |
| --- | --- |
| `evidence_version` | 1. |
| `kind` | `server` or `device`, matching companion source kind. |
| `instance_id` | Digest equal to the independently expected canonical instance. |
| `binding_sha256` | Exact host binding-table digest, not the ruleset digest. |
| `producer_id` | Alias in the independently admitted binding table; not a command or executable selector supplied by the record. |
| `producer_artifact_sha256` | Digest of the actual admitted producer artifact. |
| `epoch` | Load-association object below, or null when no epoch was established. |
| `devices` | Object keyed by Alias, at most 32 properties, values the closed device-association objects below; empty is not proof of CPU execution. |
| `clock` | Clock-association object below, or null when unavailable. |
| `facts` | Array of `{field, sample, payload}`; one entry per field, `sample` U64Text in `clock`'s source domain or null. `field`/`kind`/payload pairing is closed by schema. |

A null association preserves incomplete evidence, never satisfies a rule requiring
that association. Fact absence stays absent; no default-valued fact is fabricated.
This envelope is stored as an existing manifest `sources` object, addressed by
alias/digest, not a new registration field. Scope `clock_binding`, when needed,
references one such report containing the association; the host manifest already
retains it. References resolve only against the supplied bounded artifact set,
never paths, URLs or recursive acquisition. If multiple reports repeat an epoch,
device or clock identity, their shared facts must agree; conflicting copies fail
binding. None may use a report's self-declared identity as independent authority.

### Fact payloads and units

The table defines a closed representation family, not approved extraction rules.
Every fact value must come from a reviewed source; omission is preferable to
an invented value. Each payload's listed members are required. Fact-field uniqueness uses the same
per-field schema cardinality mechanism as the amendment below. `count` is canonical
Count, booleans are JSON booleans, `label` is canonical Label. Payload members are
non-null; only envelope association/sample alternatives explicitly allow null.
Other records cannot
insert canonical field names or extra payload keys. Applicability is backend-paired.

| Canonical field | Kind / exact payload members | Units and remaining admission constraint |
| --- | --- | --- |
| `effective_settings.context_per_slot` | server / `{count}` | Tokens per slot; rule must prove all relevant slots agree. |
| `effective_settings.slots` | server / `{count}` | Effective capacity in slots. |
| `concurrency.slots` | server / `{count}` | Same source capacity and value as settings slots; not a second measurement. |
| `effective_settings.logical_batch` | server / `{count}` | Effective logical token cap, not a realized batch width. |
| `effective_settings.physical_micro_batch` | server / `{count}` | Effective physical token cap, not a partition trace. |
| `effective_settings.context_checkpoints` | server / `{count}` | Effective per-slot checkpoint cap; disabled-text-only evidence cannot invent a count. |
| `effective_settings.flash_attention` | server / `{enabled}` | Resolved boolean, after initialization/fallback; requested AUTO is insufficient. |
| `effective_settings.kv_cache_type_k` | server / `{label}` | Actual attention K element type; not recurrent-state precision. |
| `effective_settings.kv_cache_type_v` | server / `{label}` | Actual attention V element type, independently evidenced. |
| `effective_settings.offloaded_layers` | server / `{count, placement_evidence}` | Actual layer count under a reviewed convention; `placement_evidence` Artifact must resolve within retained host sources. Intent/log numerator alone is insufficient; placement format/conversion remains source-specific and unregistered. |
| `device.name` | device / `{device_id, label}` | Device-association Alias and hardware name, not backend ordinal. |
| `device.compute_capability` | device / `{device_id, major, minor}` | CUDA nonnegative integer components, no floating version. |
| `device.nvidia_driver_version` | device / `{device_id, label, component_sha256}` | NVIDIA release label and associated driver component digest; requires a real source, not supported CUDA level. |
| `device.cuda_runtime_version` | device / `{device_id, label, component_sha256}` | Loaded CUDA runtime label and component digest, never compiler/toolkit substitution. |
| `device.physical_device_identity` | device / `{device_id}` | Vulkan association's exact tagged physical identifier; conversion to canonical label requires a reviewed mapping. |
| `device.api_version` | device / `{device_id, raw, variant, major, minor, patch}` | Vulkan raw U64Text and Count components; reviewed lossless decoding, not requested instance version. |
| `device.driver_implementation` | device / `{device_id, raw_id, label, component_sha256}` | Vulkan implementation U64Text ID/name and loaded ICD digest. |
| `device.driver_version` | device / `{device_id, raw, label, component_sha256}` | Vulkan U64Text raw value plus reviewed vendor-specific label, tied to ICD; no universal API-version conversion. |
| `effective_settings.prompt_cache_reuse` | request / outside host report | Existing original request artifacts and app source attribution; endpoint/default and mixed-policy aggregation rules remain separately required. |
| `concurrency.requests_overlap` | workload / outside host report | Existing offered-occurrence bindings plus future attributed execution events; no occupancy/HTTP-interval shortcut. Event format and stage-specific rule remain OPEN. |

The last two rows are coverage accounting, not allowed host `facts` alternatives.
Host snapshot placeholders remain `not_collected`. This format neither copies
request/document bytes nor replaces the harness's original request retention.
Unsupported driver encodings, unresolved offload placement or missing producers
remain unavailable; writing a label into this format does not close those gaps.

## Load-epoch association

`epoch` has exactly `{id, model_sha256, runtime_archive_sha256,
chat_template_sha256, loaded_components, events}`. `id` is an Alias allocated anew
at successful model/context initialization and never reused within the instance.
`loaded_components` contains unique closed `{role, sha256}` entries; role is one
of `server`, `backend`, `driver`, `runtime`, `icd`. Multiple same-role components
are allowed only with distinct digests; the admitted build mapping names the
required exact set. No local filesystem paths. Model/archive/template must match
the independently admitted instance/profile, not values learned from this report.

Each event is exactly `{sequence, tick, transition, epoch_id}`: checked U64Text
sequence/tick, Alias epoch_id, and transition enum `loaded`, `unloading`, `reset`,
`coverage_end`. Event ticks use the report's source clock. The reviewed producer
must observe every invalidating path at its owner, including same-process sleep/
wake, model/context replacement, backend/device remapping and relevant reset.
`loaded` means completed initialization/resolution, not load requested. A new
load allocates a new id even if hashes and all settings equal their previous values.

Sequences are strictly increasing without gaps within the retained coverage; the
opening loaded event and independently corroborated capture boundaries must bind
the particular event stream to this instance. `coverage_end` closes observation
coverage, not the epoch itself. A declared complete flag or fabricated gap-free
sequence is not proof: source review must establish the event producer's loss and
reset behavior, and native qualification must test it. A discontinuity, unobserved
start, missing close or overflowing buffer supplies no continuous validity proof.

For an invariant rule the required closed interval must be wholly covered after
successful loaded and before the earliest possible invalidation, accounting for
clock uncertainty. It cannot span two epochs; split records need independent scope
and preserve all offers. Equality of pre/post samples, PID liveness and cached
sleeping properties do not establish this. Mutating fields need their own complete
change history or interval sampling semantics; epoch identity is not a universal
immutability claim. Source-specific event acquisition remains unimplemented.

## Device association

Each device object has exactly `{backend, physical_identity, selection,
component_sha256}`. Its map key is its Alias within the epoch (duplicate keys are
parser errors, schema propertyNames owns key syntax). `backend` equals the
instance, `component_sha256` identifies the selected backend/ICD in loaded_components.
`selection` is the closed enum `model_selected` or `enumerated_only`; the latter
cannot support an asserted selected-device observation. This label needs native
selection proof from the reviewed producer, not a candidate boolean of approval.

`physical_identity` is a closed tagged union: `{kind: pci, domain, bus, device,
function}` with canonical integers bounded respectively by 65535, 255, 31, 7;
`{kind: uuid, value}` with canonical UUID; or null when no supported identity exists.
These are representation choices, not a declaration that either native backend
supplies them. Identity is scoped to the associated boot/epoch. No automatic
PCI/UUID equivalence, ordinal/name fallback or platform-derived guess. Virtual
subdevices, partitions and multi-device aggregation are unsupported until an
explicit mapping distinguishes them; a parent PCI identity alone cannot collapse
distinct logical devices. Canonical single-device facts require one unambiguous
selected device relevant to the observation. A new selection/remapping invalidates
the association even if the human-readable name is unchanged.

Driver/runtime/ICD fact component digests must resolve to the loaded component set
and to reviewed acquisition evidence for that same selected device. Prelaunch
host probes and arbitrary installed libraries do not satisfy this. Digests do not
prove a library is loaded; the private producer must establish loaded identity.

## Clock and interval association

`clock` has exactly `{source_domain, source_origin, target_domain, target_origin,
source_resolution, target_resolution, brackets}`. Domains are closed source enums
`linux-boottime-ns`, `linux-monotonic-us`, `windows-uptime-ms`, `windows-qpc-us`;
target is the existing platform-paired scope clock. Resolutions are positive
U64Text ticks in each named domain. Each origin is a closed platform-paired object
with exactly `{platform, boot_id, process, counter_origin, counter_frequency}`. Platform is the canonical enum;
boot_id is UUID; process reuses the corresponding canonical server-process shape.
Linux boot_id must equal that process's boot_id and the independently admitted
instance. Windows boot_id denotes a native boot-session UUID, not process creation
FILETIME or a freshly invented nonce; a native source for it must be reviewed before
that format can establish Windows association. This contract claims none exists in
the current collector. Process must match the actual source producer; if distinct
from the server, independently verified producer/server association is mandatory.
Counter origin and frequency are null except for QPC-relative sources, which require
U64Text origin and positive U64Text frequency in counter ticks/second. Native origin
acquisition/association remains a platform-rule gate, not an invitation to fill a
plausible UUID. Source and target origin objects are retained inline, charged to the
report cap. Equal labels or hashes of labels cannot replace these objects.

Each bracket is exactly `{source_tick, target_before, target_after}`, U64Text,
with before <= after. The reviewed producer establishes read order, monotonicity,
resolution, suspension behavior and the interval over which any conversion bound
is valid. Brackets are original observations, not fitted timestamps. Fixed units
alone do not prove common origin. Monotonic-to-boottime mapping must account for
suspend; QPC-relative time cannot simply be relabelled uptime. No global affine
fit, interpolation, extrapolation, TTL or default tolerance is accepted here.

A later closed rule may use identical independently proved domains/origins directly,
or prove a conservative target interval for each source event within its reviewed
coverage. All arithmetic is checked integer/rational arithmetic with outward
rounding; overflow refuses. This contract deliberately registers no cross-clock
conversion rule. Endpoint brackets alone cannot exclude an intervening discontinuity.
Native proof must falsify suspend/reset/restart cases before a rule is trusted.

For coverage, use latest-possible valid start and earliest-possible invalidation/end:
uncertainty must not enlarge the proven coverage. For positive overlap, the minimum
possible intersection must be strictly positive. Equal ticks are insufficient.
False overlap requires complete attributed execution evidence, not absence of a
positive sample. Scope intervals remain inclusive; an uncertain invalidation at a
required endpoint cannot satisfy coverage. Unknown association for an asserted
value is `ObservationScope`; no internal token times are inferred from nonstreaming
responses. Null clock_binding remains possible only under the parent's reviewed
invariance exception, never because epochs or timestamps merely look consistent.

## Canonical membership and distribution ownership

One private canonical **real rule catalog** belongs to local-connect-model-host,
next to its reviewed real source-binding tables. This preserves the accepted
private remainder; it does not move real mappings into the distributable client.
connect-contracts owns the catalog/report schemas and synthetic conformance data;
the shared client owns the single pure parser/evaluator implementation. The host
and offline qualification harness consume the same pinned catalog bytes and the
same client release, never independently maintained rule lists or evaluator copies.
No host or client file/path is created or edited by this proposal.

A catalog is a closed `{catalog_version, rules}` object, version 1, at most 256 KiB
and 32 levels. `rules` is an object keyed by Alias rule_id, maxProperties 256;
schema propertyNames owns key syntax and duplicate members fail in the shared
parser. Each entry has exactly `{field, source_kind,
platform, backend, tier, profile_sha256, model_sha256, chat_template_sha256,
runtime_archive_sha256, build_commit, patchset_sha256, producer_artifact_sha256,
evidence_format, semantics_id}`. Existing lexical types
apply; field and source kind are paired; platform/backend/tier are canonical enums;
profile_sha256 binds the original independently admitted profile bytes. Model and
template applicability are explicit, not inherited from a matching runtime name;
evidence_format and semantics_id are closed enums introduced only with reviewed
source-specific implementation. There are **no admitted enum members or real rule
entries in this proposal**. Rule-ID uniqueness is structural, not a second
semantic scanner or a permissive duplicate-last-wins map. An entry cannot carry
scripts, expressions, function pointers or caller predicates.

`ruleset_sha256` is the hash of the original canonical catalog artifact bytes.
Membership means that exact admitted digest plus an entry's exact rule_id and
matching full applicability tuple, not a prefix, unknown-rule fallback or a record's
claim that it is approved. The capture plan and independent qualification policy
pin this digest before seeing a candidate. A candidate may reference it, never
supply a replacement trust root. The future pure API receives independently admitted
catalog bytes/digest through a bounded immutable policy input; it does no acquisition.
This is a documented refinement to PR100's independent rule input, not a new
public constructor or a caller-supplied validity callback. Policy admission is a
private owner responsibility; offline consistency never authenticates its caller.

Catalog distribution is part of the pinned private host release, with exact bytes,
source revision and hashes in its distribution manifest. The offline harness uses
that same release artifact without fetching inside validation. Shared evaluator
code/schema assets retain canonical provenance and complete vendored equality;
no patch only to a host copy. Every semantic enum addition needs source review,
offline positive/negative parity and separate authorization. Native collection
proof is an additional qualification gate, not silently provided by an entry.
Synthetic test membership must be segregated and unreachable from real admission.

Host `binding_sha256` still hashes the exact reviewed host mapping table. Its
proposed closed shape is `{binding_version, ruleset_sha256, producers, fields}`,
version 1. `producers` is an Alias-keyed object (maximum 32) of closed
`{artifact_sha256}` entries; `fields` is keyed by the 18 host-owned canonical paths
(maximum 18), each value exactly `{producer_id, rule_id, evidence_format}`. Closed
schema propertyNames and duplicate-member parsing own key syntax/uniqueness.
Partial maps express missing sources, never waive observed-field requirements.
Semantic membership joins every field to the single catalog and referenced producer,
checks matching field/kind/format/artifact/applicability and rejects dangling entries.
The two slot fields must share the same producer/report capacity source. Catalog
and table can contain no caller selectors or code; their hashes stay independent.
App `binding_sha256` still hashes original app-bindings bytes; no change to that schema is needed for rule references
already in scope. There is no hash cycle: catalog does not contain binding-table,
app-bindings, manifest or report digests. Instance/build identity is checked against
independent inputs. Catalog bytes consume the existing binding-table allocation:
table plus catalog total at most 256 KiB for validation, not a second allowance.
Actual transport/API representation of that paired input must be reviewed in the
later schema/interface increment; existing CheckedBundle remains unchanged here.

## Explicit PR102 uniqueness and error-boundary amendment

Upon acceptance and later separately authorized executable work, canonical schemas
own uniqueness by `field` in app `sources` and scope `requirements`. For each of
the two app fields and each of the 20 canonical scope fields, add an `allOf` item
on the array with `contains` matching an object with required `field` and `const`
for that path, `minContains: 0`, `maxContains: 1`. Keep existing item schemas and
array maxima. Omitting minContains would wrongly require every field. Whole-object
`uniqueItems` alone is insufficient because same-field entries can differ elsewhere.
Do not add a parallel semantic duplicate-field validator.

This explicitly supersedes PR101's semantic-uniqueness allocation and PR103's
pending-amendment note **for these two finite-field arrays only**. Duplicate-field
shape failure becomes `Malformed`, before binding evaluation, including identical
duplicates and duplicates on unavailable observations. Duplicate JSON member keys
remain `DuplicateMember`; repeated request-index values remain schema `Malformed`.
Alias/occurrence identity, sorted/in-range indices, interval ordering, backend
correspondence and cross-document equality remain semantic `BindingMismatch`.
Wrong instance is `InstanceChanged`; raw byte/digest mismatch is `Integrity`;
absent/inadequate validity for an asserted observation is `ObservationScope`.
Invalid supplied metadata never becomes harmless unavailability. Multi-fault
precedence is not redefined; one-fault vectors must prove the named boundaries.

The later increment preserves the exact raw bytes and hashes of
`app-semantic-source-field.json` and `scope-semantic-field.json`, changing their
index expectations from shape-valid to shape-invalid (`maxContains`) and updating
the fixture README/test assertions. Preserve names as historical receipt identities;
record the error-boundary change explicitly. Other semantic fixtures stay valid
shapes. No migration of old sealed packets or retroactive result rewrite. The
schemas retain their current version/IDs as a pre-adoption correction; a manifest
pins the changed asset bytes so old and new evaluator results remain distinguishable.
No claim that already merged client assets silently adopt this increment.

Future proof: empty/one/all-distinct fields pass; identical and nonidentical same-
field duplicates fail; mixed good/duplicate fields fail; zero/false payloads remain
valid where allowed. Remove each maxContains guard and require the matching
negative case to become wrongly accepted; remove minContains:0 and require empty/
partial controls to fail. Cover every enumerated field, not two representative
ones. Exercise the actual frozen schema evaluator configuration from PR98/client
PR1 before adoption; unsupported keywords cannot be patched around downstream.

## Verification, differences and cold diff audit

For this Markdown-only slice: compare caps/owners/errors to parents; check the
20-row inventory against the scope enum; trace PR104's load/device/clock findings;
inspect the two fixture bytes and current schema/test owners; verify links, diff
and whitespace. No code tests, fixture replay or builds run. Static document checks
are not schema or runtime qualification. Durable readthrough and hashes remain
outside worktrees; no private documents or credentials enter the review packet.

Differences from prior validated work: new proposed producer report/association
formats and private catalog ownership; proposed schema-first duplicate-field error
amendment and later fixture expectation change. No request reserialization/schema
property reordering, model/template/framing, sampling, scoring, task receipts,
concurrency/admission policy, effective settings or historical results change.

Before later implementation: review exact schema/asset/input closure, then test
valid incomplete and complete evidence, every size/depth/count boundary and one over,
false/zero/null, unsafe source fields, changed raw bytes, unknown format/rule/build,
self-selected catalog, wrong producer/device, same-name devices, PID reuse and
same-PID reload, equal snapshots across reset, loss/truncation, clock-origin/suspend/
uncertainty/overflow, missing events and all rejected/cancelled/retried offers.
Guard removal must break the corresponding negative control. Human task quality,
serial/concurrent output parity and throughput remain independent pending proofs.

Cold diff surface: this new contract owns proposed formats, associations, canonical
membership and the amendment; the format parent reconciles schema-vs-semantic
ownership/errors, and the observation parent points to this gate without choosing
an engine. Executable or fixture changes would violate this slice's scope.

## Gap audit and next gates

DONE for documentation preparation only; NOT DONE for accepted formats, executable
schemas, registered rules, authenticated capture, full record binding or qualification.
Review and exact-revision acceptance remain pending. Next work requires separate
scope: schema/interface inventory and implementation authorization; source/build-
specific safe producers, placement/default/overlap meanings and semantic rules;
then offline proof and separately authorized native capture. Runtime selection,
issue88 and live budgets remain OPEN. No approval, task PASS, speedup, G0 delivery
or production cutover follows from this document.
