# Runtime qualification-record schema contract

Status: PROPOSED; documentation only. Owner: connect-runtime.
Operator authorization covers preparing this proposal, not implementing it.

Authority remains [ADR-0015](../adr/0015-runtime-accuracy-qualification-identity.md).
This is the schema-contract preparation for step 1 of the
[accepted U1b delivery sequence](PR-Shared-Runtime-U1b-Consumer-Approval.md#required-change-surface-and-sequence),
not a replacement sequence or a production approval format. ADR-0015's acceptance
was recorded with [PR70](https://github.com/canfieldjuan/connect-contracts/pull/70);
its retained Proposed heading is not a new grant of implementation authority.

## Root cause and inspected inventory

Contracts main `098e79b8c928c85cfc2f1ef141211e7a2aea6fde` has runtime schemas for
profile, server registration and failure, but no accuracy qualification record.
`server.schema.json` describes availability/instance identity. Extending its
meaning to imply task accuracy would confuse registration with qualification.

| Existing owner | Evidence to reuse; limit |
| --- | --- |
| `schemas/runtime/v1/{profile,server,failure}.schema.json` at the contracts revision above | Existing closed runtime shapes; preserve them in this slice. |
| `tests/test_runtime_contracts.py::{load,profile_semantic_errors}` and `requirements-dev.txt` at that revision | Existing JSON Schema draft 2020-12 validation and separate semantic-check pattern; no new dependency or runner framework needed. |
| Host `bc8f46168cde990a9601fd6f0df61e0509c7d6ec`, vendored `model-client/src/transport.rs::{Props,Settings,verify_identity}` | Checks context, model, build and template. `Settings` models only `n_ctx`; this is not complete ADR-0015 settings capture. It does not prove other fields are absent from the engine. |
| Same host, vendored `model-client/src/canary.rs::{Binding,Definition::admit}` | Existing private approval and per-instance readiness owners; an evidence record must not bypass or extend their authority. |
| U1b validated-work inventory and its frozen native-wire receipt | Reuse the inventory, payload/source bindings, original framing baselines and existing corpus references. Do not recreate corpus inventories or treat synthetic wire tests as task-quality qualification. |

The existing profile records Qwen3.5-9B-Q4_K_M and runtime commit
`c1d0e7a004015f23bc0233470b747b596f29b264`. These are inventory facts, not selection
of the next engine, a loaded-instance observation or transferable accuracy proof.
Shipping the shared host with Qwen 9B is the product direction; exact engine
selection remains the separate U1b Runtime Identity Selection gate.

## Required change surface

This PR adds only this document. After its exact-revision acceptance, the next
schema implementation proposes one canonical qualification-record schema under
`schemas/runtime/v1/`, public synthetic fixtures under `fixtures/runtime/v1/`,
and focused offline checks following the existing conformance pattern. No second
schema copy in the host or applications may become an independent authority.
The host's later capture contract consumes this record contract and names the
registration delivery mechanism; this PR adds no fields to `server.json`.

### Identity and evidence semantics

ADR-0015 Decision 1 owns the identity. The record must require the following
concepts; schema names/types and source-dependent encodings are reviewed in the
schema/capture changes before their consumers are implemented:

| Concept | Constraint and owner |
| --- | --- |
| Record version | Closed version; unknown versions are invalid evidence, not silently interpreted as the current version. |
| Profile, archive and model SHA-256 | Required identities; use the existing lowercase hexadecimal SHA-256 constraint. Resolve the selected tier against the supplied exact profile bytes. A digest-shaped string alone is not identity verification. |
| Platform and tier/backend | Platform comes from the final platform profile. Closed `cuda` / `gpu-cuda` and `vulkan` / `gpu-vulkan` branches; archive/model must belong to that profile and tier. Do not guess platform from the GPU or host OS. |
| CUDA device | Device name, compute capability, NVIDIA driver version and CUDA runtime version, with their observation sources. No fabricated version from build intent. |
| Vulkan device | Device name, physical-device identity, Vulkan API version and driver implementation identity/version, with their observation sources. CUDA-only fields are forbidden in this branch. |
| Effective settings | Every Decision 2 setting below, explicitly observed or explicitly unavailable; never filled from intended argv or remembered defaults. |
| Concurrency | Observed slot count and whether requests overlapped in the recorded qualification workload. Configured capacity is not evidence of actual overlap. |
| Application route | Application, capability, request profile or prompt version, as ADR-0015 defines them. U1b artifact manifests and checker/corpus bindings remain separate provenance, not a substitute route identity. |

The future schema uses closed objects and discriminated variants with required
fields, `const`/`enum` and native JSON Schema constraints. Wrong types, unknown
fields and mixed backend records must fail offline evidence validation. This
does not choose installed-product behavior for an unqualified identity.

An unavailable observation is a distinct typed alternative with a required
reason and no observed value. Each required observation has a place in the
record: omission, empty strings, null placeholders, fabricated zeroes and an
arbitrary extra-fields bag must not stand in for that alternative. An observed
zero or false remains valid where the selected source's semantics permit it;
no truthiness default may replace it. Source errors, unreported values and
not-yet-collected values must remain distinguishable, without private log text.

Evidence completeness and task outcome are separate. Any unavailable required
observation makes the execution identity incomplete; it cannot substantiate a
qualified PASS. A complete identity does not mean correct answers. Retain task
failures, wire/output mismatches and pending human review under the existing
application scoring owner, including when identity evidence is incomplete.
Schema acceptance alone never issues a qualification PASS, an enrollment, a
permit or a ReadyClient. No hardware allow/deny behavior is introduced here.

### Intended settings, observations and capture ownership

Decision 2 requires context per slot, slots, logical batch, physical micro-batch,
context checkpoints, prompt-cache reuse policy, flash attention, both KV cache
types and offloaded layers. Record intended settings separately, by reference
to the exact profile/request inputs. They cannot populate the observed fields.

The separately reviewed host capture slice must supply a source-binding table
for every observation: selected source revision and symbol, reporting surface,
field path, type/units, supported values, unavailable behavior, and a retained
raw-evidence reference. Use the running server's actual reports for effective
server settings; distinguish configured policy from measured state. Per-request
controls and workload overlap need their request/harness evidence as well;
the host must not infer them from startup configuration. GPU/driver observations
must identify the device actually selected for the same server instance.

The collector must bind observations to the verified instance and reject a
mixed-instance record; a restart during capture cannot splice old and new state.
Public fixtures use synthetic values and source aliases. Private raw evidence
stays outside repositories; reports reference bounded artifacts by hash/alias.
No credentials or document content belong in this record.

Exact reporting paths and backend-specific encodings are unresolved until
source inspection establishes them for the chosen candidate. Do not assert that
`/props` reports everything, invent an endpoint or run the engine to fill this
proposal. Independent shape design and synthetic fixtures may proceed without
selecting a production build; a concrete capture binding must not be frozen
before runtime selection. Unsupported observations remain explicitly incomplete.

### Validation ownership and request-order preservation

Schema-expressible constraints belong in the canonical schema. Cross-artifact
comparisons that JSON Schema cannot express have one named semantic validator
in the later conformance/capture implementation: profile bytes versus profile
digest, selected tier versus backend/archive/model, consistent instance and
consistent slot-count observations. Review its exact inputs before code. It
validates evidence; it is not the production admission-policy owner.

This record is not the model's response schema. It must not rewrite, project,
sort or canonicalize inference requests. The shared client's existing
`ReadyClient::exchange` -> `VerifiedSession::exchange` -> `Attached::exchange`
passes caller bytes into `Full::new(body)` without JSON reserialization.
`real_unix_stream_replays_all_frozen_requests_without_reserialization` compares
captured request-body byte arrays. Preserve that guard; parsed-object equality
cannot detect the gateway defect tracked by
[EW#317](https://github.com/canfieldjuan/eom-email-watcher/issues/317).
App serializers/projections and full structured C9 parity retain their own
proof obligations before adoption. This document claims neither new test results
nor end-to-end application parity.

## Differences from validated work

The only proposed future addition is a canonical evidence record and its offline
validation. Existing profiles, requests, schemas sent to the model, prompts,
framing, sampling, scoring, original outputs and per-instance checks are unchanged.
No historical proof is promoted to cover a new execution identity. Backend
branches describe evidence; they do not add product support or hardware policy.

## Verification plan

For this documentation PR: inspect the one-file diff, resolve relative links,
check the cited source owners and existing schema inventory, and check whitespace.
No builds, code tests, tokenizer, model or host calls.

For a later accepted schema implementation, require offline fixtures for complete
CUDA and Vulkan records, explicit incomplete evidence, unknown versions/backends,
mixed variants, missing/extra/duplicate fields and mismatched profile/tier/artifact
bindings. Duplicate JSON object members must fail at the ingestion owner before
ordinary parsing can discard them. Cover partial records and each observation's
unavailable alternative; preserve task failures and pending review independently.
Exercise minimum/maximum boundaries and valid zero/false versus invalid empty or
wrong-type values according to the reviewed field definitions. Both an otherwise
valid record and each single-field corruption must be exercised. Tests must
consume the canonical schema rather than reimplement its lexical constraints.
These are future proof obligations, not tests executed or authorized by this PR.

## Assumptions, blockers and explicit non-scope

- Exact-revision acceptance of this proposal is pending. It does not dispatch
  schema implementation, host capture, the trust design or any application port.
- Runtime selection, source-bound capture encodings and final platform-profile
  migration remain necessary before the affected G0 bindings. The
  [ADR-0012 coordinated migration](../adr/0012-shared-local-model-runtime-windows.md#profile)
  still combines platform and explicit settings in one revision per platform.
- [Issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88) remains
  open before dependent real admission/enrollment enforcement. No refusal,
  warning or record-only policy is selected. Independent offline evidence design
  does not wait for that policy.
- U1b still owns trust/issuer/permit design, consumer integration, G0 delivery,
  then separately accepted numeric G1/G2 annexes. Do not request those live
  annexes before runtime selection or reuse another identity's time ceilings.
- No executable schemas, fixtures, code, dependencies, runtime builds, profile
  or argv changes, live observations, tests, installations, app routing, service
  changes, Ollama changes, production adoption or arithmetic investigation.

## Implementation summary, cold diff audit and gap audit

This proposal adds one Markdown contract. It changes no executable behavior.
The diff must remain limited to this file; authorities are linked rather than
edited. Documentation verification is recorded in the PR evidence packet.

DONE for proposal preparation only after that documentation verification.
NOT DONE: review/acceptance, executable schema and fixture proof, source-bound
capture, complete G0 tuple, live qualification and production enrollment.
