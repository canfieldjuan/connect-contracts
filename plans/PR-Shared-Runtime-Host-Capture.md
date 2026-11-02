# Shared host qualification-evidence capture contract

Status: PROPOSED; documentation only. Owner: connect-runtime.
Juan authorized preparation of this contract, not capture implementation or
execution. Runtime choice, [issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88)
and live budgets remain OPEN. Ollama and production remain unchanged.

This prepares the host-capture item in [ADR-0015's landing order](../adr/0015-runtime-accuracy-qualification-identity.md#landing-order)
and step 3 of the [accepted U1b sequence](PR-Shared-Runtime-U1b-Consumer-Approval.md#required-change-surface-and-sequence).
It does not reorder the separate trust/permit design, select an engine, deliver
G0, authorize a canary, or implement unqualified-hardware policy.

## Root cause and current source inventory

The missing capability is evidence delivery, not an identified runtime defect.
[PR92](https://github.com/canfieldjuan/connect-contracts/pull/92) supplies a
canonical record and offline conformance reader. It does not collect observations,
authenticate their source artifacts, or publish a snapshot from a running host.
Treating profile intent or a valid record as measured state would lose that
distinction at the capture boundary.

CONFIRMED from source: contracts main is
`70afb74cdacc68f9050d4bd2d3011765d2e87713`; inspected host main is
`bc8f46168cde990a9601fd6f0df61e0509c7d6ec`. These are source revisions, not
installed-product identities or the chosen future engine. The host's local
checkout is an older branch; the inventory below uses main's Git objects.

| Existing owner | What is established; what it does not establish |
| --- | --- |
| [Qualification schema](../schemas/runtime/v1/qualification.schema.json), [fixtures](../fixtures/runtime/v1/qualification/README.md), [reader](../tests/runtime_qualification.py) at the contracts revision above | Closed CUDA/Vulkan records; typed observed/unavailable values; `inspect_record` compares original profile bytes, instance and slot bindings. Its independently supplied expected-instance digest is not authenticated by this offline helper. |
| [Host `Records::write` and `run_host`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L79) | Descriptor-relative temporary write and rename of registration; starting/ready/stopping lifecycle. No qualification snapshot is published by these paths. |
| [Client `Server`, `BoundInstance`, `Attached`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/attach.rs#L368) | Registration rejects unknown fields; retained attachment owns admitted directory/lease and process binding. Adding a field to existing `server.json` would break this reader. |
| [Client `Props`, `Settings`, `verify_identity`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/transport.rs#L305) | Model/build/template/context checks; `Settings` models only `n_ctx`. This is not a full settings collector and does not prove the engine lacks other reporting fields. |
| [Client `Definition::admit`, `Binding`, `ReadyClient`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/canary.rs) | Separate approval and current-instance readiness authority. Evidence capture must not mint these capabilities or expose their private constructors. |
| [Transport `Attached::exchange`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/transport.rs#L112), [native-wire test](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/transport_tests.rs#L93) | Caller bytes enter `Full::new(body)` without JSON reserialization; `real_unix_stream_replays_all_frozen_requests_without_reserialization` is the retained regression owner. This is not full app output parity. |

Reuse the complete [U1b validated-work inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port),
including its original/qualified framing, prompts, request settings and budgets,
wire receipt, source bindings and historical results. In particular:

- Current profile byte SHA-256 is
  `58bf361ec2d2a082931ffe19fb70dc9a22ffd8d7c10bc7837df137f843cd60d1`.
  It names Qwen3.5-9B-Q4_K_M, context 32768 and engine commit
  `c1d0e7a004015f23bc0233470b747b596f29b264`. These are intent inventory,
  not selection of the future engine or observation of a loaded model.
- The U1b framing receipt records 18 wire cases / 108 payloads and retains
  full structured C9 parity as pending. Its canonical client pin is
  `f841cde2b44ec99bc860359a88d06d6ae27309da`. No receipt is rerun here.
- Reuse the parent work order's 301-file binding receipt, issue-73 and the
  pre-production evaluation/corpus manifests. Do not rebuild inventories,
  copy private inputs, rescore tasks, or substitute synthetic quality fixtures.
- PR92 synthetic profiles are comparison surfaces, not bootable profiles.
  The coordinated [platform/profile migration](../adr/0012-shared-local-model-runtime-windows.md#profile)
  still precedes affected G0 bindings. PR92's pinned-dependency replay caveat
  remains outstanding; this documentation does not close it.

UNKNOWN: selected runtime reporting surfaces/encodings, observed device/settings,
current installed bindings and any task result on a future candidate. Nothing
in this inventory freezes them or implies a speed or concurrency improvement.

## Required change surface and ownership

This PR adds only this document. The proposed design separates three owners:

| Owner | Inputs and responsibility | Must not claim |
| --- | --- | --- |
| Private host capture owner | Already admitted profile/artifact identity, verified host/server instance, selected-device evidence and reviewed server reporting bindings; collect a host snapshot and retain source artifacts. | Application route, request-cache policy, actual workload overlap, correctness or permission to invoke inference. |
| Shared client delivery owner | Existing admitted registration directory/lease and independently verified attachment; obtain exact snapshot bytes, verify provenance/digests and same-instance association, return immutable evidence or a typed failure. | A digest alone authenticates its author; evidence availability issues a permit or ReadyClient. |
| Existing application qualification harness | Exact route, request-byte references, request/workload observations and existing scoring/human-review receipts; assemble the canonical qualification record from the host snapshot and these inputs. | Host startup intent proves request behavior; identity completeness means task PASS. |

Schema rules stay in connect-contracts. The host does not maintain a second
qualification schema. A future closed companion-publication schema is a delivery
format, not a competing qualification-record format; it must reference the
canonical observation definitions rather than copy their constraints.

`inspect_record` remains the offline cross-artifact conformance oracle. The later
implementation contract must name one production semantic-validation owner and
its exact raw-byte inputs, test it against that oracle and reuse the fixtures.
Do not import a test-only helper as production admission or scatter semantic
checks through host/client/apps. Any required language port is an explicit,
reviewed difference, not an independent rule set. Source parser constraints belong
in closed types/schema; parsing and cross-artifact comparisons have named owners.

## Proposed delivery: companion publication beside registration

Keep the current closed `server.json` bytes and protocol unchanged. Deliver host
evidence through a separately versioned companion publication in the same admitted
private registration directory. This is a proposed file delivery mechanism,
not a new HTTP endpoint or an implemented API. Old clients continue to read only
their existing registration; capture-aware clients explicitly request evidence.
Missing evidence never silently switches routes or changes production readiness.

The companion publication is a small closed manifest selecting immutable,
content-addressed host-snapshot and verified-instance evidence objects. It binds
their exact byte digests, the reviewed source-binding-table digest, and the
registration identity it belongs to. It must contain no arbitrary filesystem
paths, URLs, credentials, document text or embedded application request bodies.
Derived leaf names come only from validated fixed-format digests under a retained
directory descriptor; aliases are labels, not instructions to open a path.

The host snapshot carries only host-owned profile/runtime/model/platform/tier
identity and device/server observations. It is not a fabricated full qualification
record: request/workload/application fields are supplied later by their owners.
The canonical record's `instance_id` remains the digest of exact retained
verified-instance evidence bytes. That artifact binds the already verified
registration, host/server process identities and profile/artifact association;
never use a PID alone or derive trust from the candidate record's own hash.
The client independently verifies this association against its attached instance.
Local file ownership and hash checks preserve the existing attachment trust
boundary; they are not a new cryptographic issuer or proof against an attacker
already controlling that user account. The separately accepted trust design owns
any stronger enrollment/permit authority.

The follow-up interface contract must fix the companion's filename, closed wire
schema/version, canonical instance-artifact encoding, digest derivation, byte caps,
retention rules and public/private asset closure before implementation. These
are delivery design gates, not engine selection or live-budget defaults. This
proposal fixes the mechanism and invariants; it does not pretend those artifacts
already exist or permit implementation against an unreviewed shape. New shared
client code/assets must originate in its canonical repository and satisfy the
[U1 distribution closure](PR-Shared-Runtime-U1.md#complete-allowed-public-source-and-asset-closure),
never be edited only in the host's vendored copy.

## Capture lifecycle and immutable evidence

1. Acquire the existing admitted directory/lease and independent instance binding.
   A starting/unverified server has no verified snapshot. Do not manufacture a
   digest of unverified identity to satisfy the record shape.
2. Collect only under separately authorized capture execution, with owned finite
   I/O/cancellation limits supplied by its caller. This contract sets no numbers,
   starts no process and adds no automatic startup probes. Bound raw input before
   parsing; reject duplicate members and non-JSON numeric constants at ingestion.
3. Bind each observation to the selected source table, raw artifact bytes and
   verified instance. Preserve intended profile/request references separately.
   Recheck the instance around collection/publication and reader acquisition;
   a process restart, PID reuse, changed peer or registration replacement rejects
   that capture as mixed/stale evidence, never fills holes from another instance.
4. Seal complete immutable objects before atomically publishing their manifest.
   Readers see the old complete publication or the new complete publication,
   never partial bytes. A manifest switch is not a multi-file transaction: every
   reference must already resolve and hash correctly; retain acquired objects
   while readers own them. Reject symlinks, wrong ownership, nonregular objects,
   malformed/oversized bytes and digest mismatches at the file admission owner.
   Use the existing descriptor-relative file primitives, not path-based reopens.
   Crash durability and concurrent-reader retention need explicit future proof;
   the current `Records::write` rename alone does not prove them.
5. Capture-aware readers verify same-instance association before accepting the
   snapshot and retain its exact bytes/digests in their run snapshot. A later
   publication cannot mutate that historical snapshot. Capture sequence/time and
   evidence interval belong to the future delivery format: a still-running
   process alone is not proof that mutable settings stayed fixed for a run.
   The selected source binding must establish immutability or define recapture
   and interval checks. A stale interval cannot substantiate current settings.
6. On shutdown/restart, a current publication ceases to be eligible for new live
   bindings. Historical evidence stays historical; retain failures, incomplete
   observations and task receipts. Do not erase prior receipts as cleanup.
   Cancellation or interrupted publication must leave no accepted partial
   snapshot, leak no owned handles/work, and trigger no inference retry/fallback.

Distinguish unavailable observations from invalid provenance. For a verified
instance, source absence/error produces the canonical `not_collected`,
`not_reported` or `source_error` alternative where applicable. Wrong identity,
invalid schema, tampered artifacts or a restart invalidates the capture; it is
not a benign unavailable field. Preserve a bounded failure receipt separately.
An invalid capture does not erase any already retained application task result.
Neither outcome changes production admission policy while issue #88 is open.

## Source-binding obligations; no engine selected

Every later observed value needs a reviewed mapping: exact source revision and
symbol, reporting surface/field path, type/units, supported values and conversion,
source error/unavailable behavior, retained raw-evidence hash/alias and same-instance
proof. `binding_sha256` identifies that mapping, not merely this proposal.
The mapping also specifies the credential-free reporting input it retains: bearer
headers, keys and document/prompt bodies must never enter capture artifacts.
Use the source owner's bounded reporting surface; do not copy whole private logs
and rely on a later redaction pass. If no safe source is available, retain an
explicit unavailable observation rather than a secret-bearing artifact.

The following allocation comes from the canonical schema, not a claim that a
particular engine endpoint reports these values:

| Canonical observation | Evidence owner / required source kind | Binding status |
| --- | --- | --- |
| `effective_settings.context_per_slot`, `slots`, `logical_batch`, `physical_micro_batch`, `context_checkpoints`, `flash_attention`, `kv_cache_type_k`, `kv_cache_type_v`, `offloaded_layers` | Host capture / `server` reports for the verified instance | Exact reporting path, units and supported conversions OPEN until selected-source inspection. `Settings.n_ctx` alone does not establish per-slot semantics. |
| `concurrency.slots` | Host capture / `server`; same slot observation as effective settings | Must agree, never independently guess from total context. |
| `effective_settings.prompt_cache_reuse` | Qualification harness / `request` evidence | Actual request policy/meaning, not startup default. Unknown omitted-field semantics remain unavailable. |
| `concurrency.requests_overlap` | Qualification harness / `workload` evidence | Actual observed schedule/interval; two offered requests or configured slots alone do not prove overlap. |
| CUDA `device.name`, `compute_capability`, `nvidia_driver_version`, `cuda_runtime_version` | Host capture / `device` evidence tied to the server-selected device | OPEN; build-tool version is not observed CUDA runtime version. |
| Vulkan `device.name`, `physical_device_identity`, `api_version`, `driver_implementation`, `driver_version` | Host capture / `device` evidence tied to the server-selected device | OPEN; CUDA fields are forbidden here. |

Never fill an observation from argv, documented defaults, hardware support lists
or fixture values. Preserve valid zero and false without truthiness fallback.
An ambiguous source meaning is unavailable until a reviewed mapping resolves it;
unsupported encodings may require a separate schema proposal, not a guessed
boolean/string conversion. Do not pick a runtime because it has convenient fields.
No endpoint, flag, tokenizer, model or GPU probe is authorized by this document.

## Compatibility and authority boundaries

Capture and record assembly must not reserialize, reorder or project application
inference requests or their response schemas. Preserve the existing byte transport
and frozen native-wire comparison; capture references hash the exact original
request bytes. The gateway defect [EW#317](https://github.com/canfieldjuan/eom-email-watcher/issues/317)
must not be recreated in a logging/normalization layer. Metadata serialization
does not authorize request serialization changes. App serializers and full C9
parity retain their own proof obligations.

Complete identity, server ready, task PASS, human quality approval, qualification
permit and production enrollment remain distinct. No record or companion manifest
issues an approval, admits an unqualified device, changes a canary binding, or
unlocks generation. The separate U1b trust/permit design still must establish
its issuer and reachability boundaries before its implementation.

Windows ships in the first release under ADR-0012. Shared evidence semantics must
cover both platform identities; Linux descriptor/process examples do not prove
Windows ACL/handle/process or publication behavior. Native Windows proof runs
later on Juan's own Windows box, not a VM. Platform-specific implementation and
profile migration remain explicit deliverables; no Linux-only release is inferred.

## Differences from validated work

The proposed additions are the host-owned snapshot, separately versioned companion
delivery and qualification-harness assembly, with source provenance and interval
checks. They are not yet implemented. Existing registration, profiles, runtime
pins, prompts, templates, thinking mode, sampling, request bytes, response-schema
order, output limits, validators and task expectations stay unchanged.

The future companion reader/writer, canonical delivery schema and instance-artifact
encoding require new offline proof. Any semantic-validator language port and
public-client asset change must be listed in its own contract. No inherited
quality result qualifies a different execution identity, and no historical
test result is reported here as a new test run.

## Verification plan

This documentation PR: check every source symbol/link against the pinned inventory,
read the complete one-file diff, resolve repository links, run `git diff --check`,
and prove source, schemas, fixtures, profiles and dependencies did not change.
No code tests, engine builds or model calls are needed for this documentation edit.

Before later implementation sign-off, require offline tests on both sides:

- Reuse PR92 complete/incomplete CUDA/Vulkan fixtures and schema-only corruption
  checks; retain missing observations and failing/pending task receipts without
  promotion. Valid zero/false pass; wrong types, duplicate members, unknown versions,
  mixed backends and each individual binding corruption fail at their origin.
- A source-to-value test per reviewed mapping using retained sanitized source
  bytes; missing/unknown/malformed/overflow values, ambiguous units and unsupported
  semantics cannot silently become measured defaults. No invented engine fixture
  is evidence that the selected engine reports a field.
- Fresh-process/fake-peer tests for restart during collection, publication and
  acquisition; PID reuse, changed registration, wrong device, stale intervals,
  artifact tampering and two readers spanning a publication switch. Assert the
  specific failure, not any downstream error. Same-instance valid controls pass.
- Crash/interruption tests around object sealing and manifest replacement;
  partial files, symlinks, wrong owner, traversal-shaped labels, directory swaps,
  overread/short read and cancellation cannot publish or admit invalid evidence.
  Probe each reviewed byte cap at its boundaries. No live budgets are implied.
- Legacy registration/attach behavior unchanged when the companion is absent;
  capture-aware readers return evidence-unavailable without manufacturing a
  ReadyClient. Preserve lease/drop semantics and typed errors.
- Replay existing exact request-byte fixtures through any changed delivery seam;
  compare bytes, not parsed JSON. No observer may mutate requests or task results.
  Native Windows equivalents remain separately required on the operator's machine.

These are future proof obligations, not executions or test results of this PR.

## Assumptions, blockers and landing boundary

After review, obtain exact-revision acceptance of the proposed capture/delivery
semantics. Before capture implementation, settle the closed companion/interface
contract and its limits/asset closure and selected runtime/source-binding annex.
Profile migration remains a gate for affected G0 bindings, not a requirement to
edit the shipped profile during independent preparation. Offline interface
preparation can proceed
without selecting a runtime; concrete engine mappings cannot be frozen meanwhile.
Live capture additionally requires its explicit phase authorization and budgets.

Doc Sum's full G0 still needs the reviewed app/host/profile tuple, candidate
artifacts, native request owner, capture interface, immutable run snapshot and
store/sidecar bindings under U1b. This document supplies none of those binaries,
permits or measurements. Other application ports/qualifications are separate PRs.
Issue #88 remains the operator's decision before dependent enforcement/enrollment;
this proposal makes no refusal/warning/record-only product choice.

Explicit non-scope: implementation, new schemas/fixtures, dependency installation,
profile/argv/runtime selection, tokenizer/model/engine/host calls, GPU allocation,
engine builds, live budgets, benchmarks, app changes, service changes, Ollama,
production, cutover, arithmetic sandbox, kernel changes or forks. No issuer or
enrollment design is silently folded into evidence capture.

## Implementation summary and cold diff audit

One new planning document only. It inventories the existing record/host/client
owners, proposes compatible companion delivery, separates host observations from
request/workload assembly, and states future provenance/lifecycle/parity proof.
All runtime-specific sources remain unresolved; no accepted source or policy
definition is edited. Durable source/verification receipts live outside worktrees.

## Gap audit

DONE: documentation preparation and source-grounded scope proposal.
NOT DONE: independent review/exact acceptance, delivery wire/interface contract,
selected-source bindings, capture implementation, profile migration, G0, trust
design, live observation, task qualification, human review or production enrollment.
Runtime choice, issue #88 and live budgets remain OPEN.
