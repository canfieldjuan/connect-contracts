# Offline companion-schema implementation contract

Status: PROPOSED; documentation only. Owner: connect-runtime.
Juan authorized preparing this contract, not implementing it. Exact-revision
acceptance and a separate implementation go precede executable changes.
Runtime choice, [issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88)
and live budgets remain OPEN. No builds, model calls, Ollama or production changes.

This is the independent offline schema preparation permitted by the accepted
[companion interface](PR-Shared-Runtime-Companion-Interface.md#assumptions-blockers-and-gap-audit),
not dispatch of its reader, semantic-validator port or capture implementation.
It preserves [ADR-0015](../adr/0015-runtime-accuracy-qualification-identity.md)
and the [U1b landing order](PR-Shared-Runtime-U1b-Consumer-Approval.md#required-change-surface-and-sequence).
This document cannot deliver G0, an approval capability or a live qualification.

## Root cause and source inventory

CONFIRMED at contracts base `bc95f3a6248a8062a9bfd5755180e3a2ef04a86e`:
the companion's wire shapes are specified in prose but have no executable
schemas. `schemas/runtime/v1/` contains qualification, profile, registration and
failure schemas only. Applying the qualification-record schema to a host snapshot
would require app-owned facts the host must not supply. The missing contract
artifacts originate here, not in an application or inference arithmetic path.

| Existing source / symbol | Reuse; limitation |
| --- | --- |
| [Companion interface](PR-Shared-Runtime-Companion-Interface.md#exact-publication-and-host-snapshot-shapes) | Exact manifest, instance and snapshot shapes, raw-byte rules and owner boundaries; no executable implementation. PR94's historical Proposed heading does not undo its recorded exact-revision acceptance. |
| [Qualification schema](../schemas/runtime/v1/qualification.schema.json), `$defs/{sha256,alias,platform,positive_count,settings,concurrency,cuda_device,vulkan_device}` | Canonical identity and observation constraints. Reuse by reference; do not copy the observation definitions. |
| [Offline reader](../tests/runtime_qualification.py), `inspect_record` | Existing raw-profile digest, expected-instance, tier/backend and observed-slot comparisons. It validates qualification records, not companion bundles or authenticated process state. Preserve it unchanged. |
| [Qualification tests](../tests/test_runtime_qualification.py), `QualificationContractTests` | Schema-only discriminator probes, valid/incomplete inputs, typed observation negatives and retained task references. Reuse these cases and run their existing checks later without changing expectations. |
| [Fixture inventory](../fixtures/runtime/v1/qualification/README.md) and its `index.json` | Synthetic CUDA/Linux and Vulkan/Windows comparison surfaces; not bootable profiles or hardware qualification. Original bytes remain unchanged. |
| [Runtime tests](../tests/test_runtime_contracts.py), `RuntimeContractTests.test_fixture_inventory_is_complete` | One exhaustive runtime fixture inventory owner. Its current `*/*.json` scan must explicitly account for new companion fixtures, not skip that directory. |
| [Development requirements](../requirements-dev.txt) | Existing `jsonschema==4.25.1`; no dependency installation, upgrade, new runner or workflow in this slice. Actual test environment versions must be recorded in a later authorized run. |

Reuse the [host capture inventory](PR-Shared-Runtime-Host-Capture.md#root-cause-and-current-source-inventory)
and [U1b validated-work inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port)
by reference: Qwen3.5-9B-Q4_K_M profile/model/runtime/template pins, original and
qualified framing, prompts, sampling, request bytes and output budgets, frozen
wire results, the 301-file receipt, issue-73 and pre-production corpus manifests.
Do not recreate those inventories, copy private documents, rerun tasks or change
their scores. Their historical pins are not selection of the next runtime.
PR92's pinned-dependency replay caveat and human task-quality review remain open.

INFERRED: executable schemas will make later wire-format drift detectable.
UNKNOWN: future engine reporting surfaces, live source validity, current installed
identity and task/performance results. This slice supplies no new evidence for them.

## Required change surface

This PR adds only this document. The later, separately authorized implementation
is limited to the following files and responsibilities:

| Path | Required change |
| --- | --- |
| `schemas/runtime/v1/companion.schema.json` | Closed manifest shape and bounded object references. |
| `schemas/runtime/v1/instance.schema.json` | Closed platform/process shapes and tier/backend pairing; lexical identity constraints only where specified below. |
| `schemas/runtime/v1/host-snapshot.schema.json` | Closed host-only observation shape, referencing qualification definitions with the two exact unavailable placeholders. |
| `fixtures/runtime/v1/companion/{README.md,index.json,*.json}` | Flat, explicitly inventoried public synthetic wire-shape fixtures, raw-byte digests and expected schema outcomes; exact leaves enumerated in the implementation diff. |
| `tests/test_runtime_companion.py` | Schema-only conformance and frozen-fixture tests; test-local, offline reference registry. No new production or bundle-validation entry point. |
| `tests/test_runtime_contracts.py::RuntimeContractTests.test_fixture_inventory_is_complete` | Include the companion index and every listed JSON fixture in the existing exhaustive inventory. Preserve existing inventory coverage and all legacy validation behavior. |

No other source, existing schema or fixture modification is required. If source
inspection exposes a necessary expansion, state and review the contract revision
before implementing it; do not quietly turn this slice into a validator port.

### Canonical schema ownership and local references

Use JSON Schema draft 2020-12 with stable `$id` values under
`https://local-connect.invalid/schemas/runtime/v1/` and the filenames above.
These are identifiers, never network fetch destinations. Register the three new
schemas and the unchanged qualification schema from an explicit local allowlist;
resolve all `$ref` targets through that complete registry. Missing/unregistered
resources must fail without any network retrieval. Test the closed closure and
an unregistered-reference negative; do not disable reference validation.
Use the existing jsonschema reference-registry support and its available
dependencies. If it is unavailable in the pinned environment, report the blocker;
do not install a dependency or substitute a permissive resolver.

Keep `Digest`, `Alias`, `Seq` and platform definitions in qualification's
`$defs/sha256`, `alias`, `positive_count` and `platform`. Put new U64Text and
process/UUID lexical definitions in instance's `$defs`; snapshot references those
for capture-window counters. Companion owns ObjectRef, with reference-specific
size refinements. This establishes one owner per lexical rule without adding a
fourth schema or editing qualification's existing definitions.

All objects are closed with required members and explicit types. Use `const`,
`enum`, `oneOf`, `allOf`, array counts and numeric/string bounds in the schemas.
Use patterns only for the specified closed lexical tokens and test end-of-string
behavior, including a terminal newline. No parallel regex or truthiness defaults
in Python may compensate for a missing schema constraint. Referenced observation
objects stay closed; composition narrows existing members without opening extras.

### Manifest and declared sizes

Require exactly `companion_version`, `sequence`, `instance_id`, `instance`,
`snapshot`, `bindings`, `sources`. Version is integer constant 1; sequence is Seq.
Instance id is Digest. Each ObjectRef has exactly `sha256` and integer `bytes`.
The positive declared-byte maximum is 16384 for instance, 65536 for snapshot,
262144 for bindings and each raw source. Sources is an array of 0..32 closed
entries containing `kind` (`server` or `device`), Alias `alias` and `object`.

These are declared-size constraints, not proof of retained bytes, byte length,
hash, aggregate budget or file safety. Alias uniqueness by key and manifest
instance-id equality remain semantic checks; `uniqueItems` is not a substitute
for alias uniqueness. A schema-valid manifest is not an admitted bundle.

### Instance variants

Implement the exact members in the accepted interface's
[instance artifact table](PR-Shared-Runtime-Companion-Interface.md#exact-instance-artifact-and-hash).
Require integer version 1, canonical lowercase UUID-v4 start id, all Digest
fields, lowercase 40-hex build commit and matched CUDA/gpu-cuda or
Vulkan/gpu-vulkan pairs. Platform chooses the process shape, independently of
backend. Do not invent a Linux-only CUDA or Windows-only Vulkan restriction.

Linux host/server objects require `pid`, `start_ticks`, `boot_id` and forbid
Windows members. Windows objects require `pid`, `creation_filetime` and forbid
Linux members. Boot id is the OS UUID's lowercase hyphenated lexical shape,
not a requirement that the boot UUID be version 4. PIDs and Windows FILETIME
are positive U64Text; Linux start ticks may be zero. U64Text is the ASCII decimal
lexical form from PR94, at most 20 characters, with no leading zeros except `0`.

The interface explicitly assigns unsigned-64 overflow comparison to the named
semantic validator. Numeric PID ceilings and FILETIME interpretation also remain
there. Schema success on a lexically valid but numerically oversized string is
not full instance validity. Do not encode an alternative arithmetic policy in a
range-shaped regex. JSON member order, literal number spelling and exact final LF
are raw-byte canonicalization obligations, not JSON-object schema assertions.

### Host snapshot and incomplete evidence

Require exactly `snapshot_version`, `instance_id`, `binding_sha256`, `sequence`,
`capture_window`, `device`, `effective_settings`, `concurrency`. Version is integer
constant 1; digests and Seq reuse their canonical definitions. Capture window is
closed `clock`, `start`, `end`: clock is `linux-boottime-ns` or
`windows-uptime-ms`; counters use U64Text. Ordering and platform association need
the separately supplied instance and remain semantic obligations.

Device is exactly one of qualification's closed CUDA or Vulkan device shapes.
Snapshot has no platform/backend members, so selecting the shape matching an
independent instance belongs to bundle validation, not an invented discriminator.
Both clock alternatives are schema-valid with either device shape; this does not
qualify either platform/backend combination for execution.

Reference the existing `settings` and `concurrency` definitions and narrow
`prompt_cache_reuse` and `requests_overlap`, respectively, to exactly
`{"state":"unavailable","reason":"not_collected"}`. Observed false is forbidden
in those host-only positions just as observed true is. Other observations retain
every canonical unavailable reason, and observed zero/false remain valid where
their canonical types allow them. Do not require all host observations to exist
as measured values. Forbid `application_route`, `intended`, `task_evidence`,
approval flags and any additional field in the snapshot.

### Explicit proof boundary

The future test result is named **schema conformance**, never CheckedBundle,
AttachedEvidence, qualified, authenticated or task PASS. It does not introduce
an offline duplicate of `local-connect-model-client::evidence` or extend
`tests.runtime_qualification.inspect_record` to another format.

| Obligation beyond schema conformance | Later owner / evidence |
| --- | --- |
| UTF-8/BOM/duplicate-member/nonfinite rejection, parser depth and actual byte caps | Bounded raw parser in the separately authorized shared-client evidence implementation. The existing qualification parser remains unchanged. |
| Instance serialization order, escaping, final LF and SHA over exact bytes; numeric overflow and PID bounds | Shared semantic validator and canonical-instance vectors. Fixture hashing here proves only fixture preservation. |
| Object sizes/digests, expected instance/profile/source bindings, alias uniqueness, source use, backend/clock association, slot equality and capture-window ordering | Shared `evidence::validate_bundle`, with independently supplied expectations, under its later contract. |
| Source validity across independently required intervals; observed request/workload facts; qualification-record assembly | Selected-engine source annex, shared record-binding validator and existing app harness owners. Unavailable values stay incomplete. |
| Symlinks, ownership, retained handles, process replacement, cancellation, atomic publication, races, quotas and memory acquisition limits | Shared reader/private publisher and native-platform proofs; no filesystem security or concurrency claim from JSON validation. |

Test descriptions and README must preserve these distinctions. Include explicit
schema-only counterexamples: equal-shaped but mismatched instance hashes, reversed
window counters and an oversized 20-digit counter may pass shape checks while
remaining invalid for later bundle admission. Do not add post-schema rejection
in this slice that hides those missing later proofs.

## Fixtures, differences and parity requirements

Reuse PR92's synthetic device/settings observations and valid/incomplete cases as
input values; record their source filenames and hashes. New documents need their
own declared shape outcomes because a host snapshot omits app fields and fixes
the two host placeholders. Do not edit or reserialize original fixture files.
Use synthetic process identities, digests and aliases only; no corpus text,
credentials, real registrations, private source tables or reports.

The companion index enumerates every fixture leaf, target schema, raw SHA-256,
expected schema validity and named constraint under test. For negative cases,
record the intended failing JSON path and schema keyword; a resolver/import
error or an unrelated earlier rejection does not satisfy the case. Recursive
`oneOf` diagnostics must expose the relevant branch error without depending on
unstable human-readable library wording. No paths/URLs supplied by fixtures are
followed: fixture and schema selection use the fixed repository allowlist.

Keep fixtures flat so the existing runtime inventory can remain exhaustive.
Include Linux and Windows instances for each backend, both device shapes with
both clocks, complete host-owned observations and individually/all unavailable
host-owned observations. Test all three schemas independently before any later
semantic checks. Exact bytes are retained and hashed before parsing; tests must
not rewrite files or sorted-key serialize app inputs. No new scoring is added.

Differences from validated work are limited to the three new evidence schemas,
synthetic companion fixtures, their local-reference test support and inventory
extension. No production Python-to-Rust port, public client release/asset
vendoring, executable profile, engine conversion, request framing or model
behavior is part of this slice. Preserve the existing wire byte-order guard by
leaving its code and frozen requests unchanged; do not claim it was rerun here.

## Explicit non-scope

No edits to qualification/profile/server/failure schemas, canonical profile,
legacy fixtures, qualification oracle, host/client/app code, transport, native
registration migration, public release manifests, workflows or dependencies.
No bundle validator, collector, source adapter, reader, file opener, new attach
path, permit/issuer, ReadyClient constructor, health check, tokenizer, model
invocation, engine build or GPU use. No enrollment, unqualified-hardware policy,
runtime selection, live budgets, installation, service or Ollama changes.
Windows remains in the first release with native proof later on Juan's Windows
box; synthetic JSON is not native proof and does not authorize a VM.

## Verification plan

For this documentation PR only: inspect the one-file diff against the pinned
base; check source symbols, relative links, ownership and constraint traceability;
run whitespace checks and preserve the diff/input hashes in a durable packet.
No executable schema, fixture or test is written or run by this PR.

After exact acceptance and a separate implementation go, require:

1. Declare a fail-first schema-presence/conformance probe before adding schemas;
   record the intended missing-artifact assertion, not an accidental import error.
   Then prove the same probe passes with the schema implementation. Keep the
   probe as a regression test, with exact commit and command evidence.
2. Check every schema with `Draft202012Validator.check_schema`; prove every local
   reference resolves and an unknown resource fails without retrieval. Exercise
   schemas directly so a later semantic helper cannot mask a missing constraint.
3. For every closed object/member: good input, missing member, unknown member,
   mixed variant and wrong type. Test unknown versions/backends/platforms, both
   tier-pair directions, process-field mixing, UUID/hex/decimal lexical near-misses
   including empty strings, whitespace/newlines, escapes in parsed values and
   non-ASCII digits. Valid wire-shape objects must not be rejected by accident.
4. For each declared size, count, length and Seq limit: min-1/min/max/max+1;
   zero, empty string, false, null and wrong-type controls. Test empty/single/max
   sources and mixed valid/invalid entries. Keep boolean and integer distinction.
   Do not claim raw file/depth/aggregate quotas have been proved by these tests.
5. Probe both exact unavailable placeholders, each canonical source kind and
   observed/unavailable alternative. Retain valid zero checkpoint/offload counts
   and false flash attention. Reuse unchanged qualification fixtures/checks to
   show the original full record still permits app-owned request/workload facts.
6. Prove frozen fixture hashes and exhaustive inventory, including an unlisted
   companion fixture negative. Record branch-specific rejection paths/keywords.
   Targeted in-memory schema mutations removing a required field, closure, source
   count/byte maximum, pairing constraint or placeholder restriction must be
   caught by the direct conformance tests; no production mutation tooling added.
7. Run the focused commands below in the authorized environment, record Python,
   jsonschema and reference-library versions and exact output, and retain raw
   receipts outside worktrees. If pinned prerequisites are missing, stop that
   verification and report them without installation or substitution. Preserve
   PR92's older environment caveat separately; do not claim a historical rerun.

Future commands, **not run or authorized by this document**:

```text
python3 -B -m unittest tests.test_runtime_companion
python3 -B -m unittest tests.test_runtime_qualification tests.test_runtime_contracts
git diff --check
```

No build, engine, GPU, live host or application is needed. Do not duplicate broad
suites solely for a documentation follow-up. The eventual implementation review
must name `boundary-probe` and `effect-trace` evidence: actual schema rejection
at the named keyword, plus valid-side controls, rather than presence of a keyword
or a generic error. Nothing here claims an already passing conformance test.

## Assumptions, blockers and authorization

The merged companion interface is the specification; no new wire fields,
constants or source semantics are proposed here. Runtime choice and the real
source-binding annex block dependent capture work, not this independent schema
proposal. Issue #88 controls later policy/enrollment; live budgets remain Juan's
later execution decisions. Exact acceptance of this document does not by itself
dispatch implementation, select an engine or authorize testing installed apps.

Raw-byte/parser/semantic/filesystem proof deliberately remains NOT DONE after a
schema-only implementation. The later shared-client contract must cover those
obligations before any artifact is treated as CheckedBundle or AttachedEvidence.
Native Windows registration/profile migration, qualification-only permit design,
G0, task parity and human review remain separate gates. No schema result closes
them or establishes faster inference or multi-user concurrency.

## Implementation summary and cold diff audit

This proposal changes only this document. It names future schemas, fixture/test
ownership, direct-schema proof and deferred owner obligations. No executable
behavior, test input, profile or request byte is changed. The cold diff audit
must verify that every paragraph stays within this documentation-only scope
and the accepted interface; durable evidence records the actual checked base.

## Gap audit

DONE: implementation-contract preparation and source inventory, subject to the
recorded documentation verification receipt.
NOT DONE: independent review, exact-revision acceptance, separate implementation
go, schemas/fixtures/tests themselves, future conformance proof and all deferred
raw-byte/semantic/native/live gates. Stop after publication for contract review;
do not interpret preparation as implementation authority.
