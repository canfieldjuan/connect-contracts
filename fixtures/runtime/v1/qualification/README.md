# Offline qualification-record conformance

Implements the accepted [record contract](../../../../plans/PR-Runtime-Qualification-Record.md).
These fixtures are synthetic evidence-shape examples, never approval, a selected
runtime, qualified hardware or permission to run. The implementation go covers
schema/fixtures and offline tests only. Runtime selection, issue #88 and live
budgets remain open. No original profile, registration, request or fixture changes.

## Record and input contract

`qualification.schema.json` owns the record. It has closed version-1 CUDA/Vulkan
variants. Common identity fields are `profile_id`, `platform`, `tier`, `backend`,
`runtime_archive_sha256`, `model_sha256`, `instance_id`, and `application_route`
(application, capability, request_profile). The instance id is the digest of a
capture owner's verified-instance evidence artifact, not a PID or invented claim
that this offline reader authenticates a running process.

`device` and `effective_settings` have required, individually typed observations.
`concurrency` records slots and actual request overlap. Each observed value has
`state: observed`, `value`, and a `source` (kind, binding_sha256, artifact_sha256,
alias, instance_id). Kinds distinguish server, device, request and workload.
Each unavailable value instead has `state: unavailable` and a reason from
`not_collected`, `not_reported`, `source_error`. No observed value or fake source
is permitted on that branch. `binding_sha256` identifies the later reviewed
source-binding table; synthetic fixture bindings do not freeze real encodings.

Normalized count values are integers, with positive context/slot/batch sizes and
nonnegative checkpoint counts/offloaded layers. Counts have a representation
ceiling of 9007199254740991 for exact cross-language JSON integer interchange;
it is not an execution budget. Zero checkpoint count and zero offloaded layers
are legitimate values. Flash attention, cache reuse and overlap are booleans;
KV cache type and backend/device version/identity values are nonempty strings.
CUDA compute capability is a pair of nonnegative integer major/minor values.
These are evidence representations, not assertions about any engine's API.
Unresolved or unsupported source-to-value mappings remain unavailable. A source
using different semantics needs a reviewed capture mapping, not guessed coercion.

`intended` contains only artifact references for profile/request intent, never
fallback observed settings. `task_evidence` is a list of opaque artifact references
for the application's existing scoring/output/human-review receipts. It may be
empty before task work; failures and pending human review remain in those
receipts and are not reclassified by this reader. Neither record nor reader
has an approval/PASS field or an enrollment API.

The only offline entry point will be `tests.runtime_qualification.inspect_record`:

- Takes **raw UTF-8 JSON bytes** for the record and exact profile, plus an explicit
  expected instance-evidence digest supplied by the caller. Parses every object
  with duplicate-member rejection, and rejects non-JSON NaN/Infinity constants.
- Validates the record against the canonical schema before reading its values.
- Validates the profile's comparison surface (platform, distinct selected tier,
  device class, archive/model hashes) against a definition in the same schema.
  This is deliberately NOT a replacement for full canonical-profile admission.
  Other existing profile fields are outside this comparison surface. Production
  must supply the already admitted profile through its later capture integration.
- Compares the SHA-256 of the original profile bytes, platform, selected tier's
  device class/archive/model, all observed-source instance ids against the expected
  instance id, and the duplicated observed slot count. It never follows paths,
  URLs or artifact aliases. The profile intent reference must equal profile_id.
- Returns the validated record and the missing observation paths. `complete`
  means only all required observations are present, never task success. An
  invalid record raises a shape/binding error; an incomplete valid record remains
  available, including all task-evidence references. No record is rewritten.

The synthetic profile inputs exercise a future explicit platform field without
modifying the shipped profile schema or canonical profile. They are only the
comparison surface, not bootable profiles. The coordinated platform/settings
migration and actual runtime/source bindings remain later gates. No real profile
is inferred from a fixture or admitted by this offline helper.

## Verification and scope

Run `python3 -m unittest tests.test_runtime_qualification` for this slice and
`python3 -m unittest tests.test_runtime_contracts` for the unchanged adjacent
runtime documents. No model, GPU, network, installed app or host is used.
Use the existing jsonschema dependency; no new packages or workflow changes.

Cover both backend variants and platforms; incomplete evidence; every required
field/closed object; mixed backend fields; each binding comparison; restart-spliced
sources; duplicates at every input depth; unknown variants; count limits and
falsy/wrong types. Preserve input bytes and task-evidence references. A complete
record with a retained failing task receipt is still complete evidence, not PASS.
The source-binding table and full profile admission are explicitly not proved.

## Root cause / required change surface / gap audit

The missing record is owned by the schema contract, not the application's
response schema. Add the schema, these fixtures and an offline conformance helper
plus tests. No app/host settings, routes, inference-schema ordering, profile bytes,
registration format, trust/permit design or production hardware policy changes.

The existing shared transport byte-order guard is unchanged; this implementation
never imports the apps or transport and does not qualify their output parity.
Exact fixture hashes, test receipts and cold diff audit live in the durable PR
packet. Implementation and independent review are pending at this spec commit.
