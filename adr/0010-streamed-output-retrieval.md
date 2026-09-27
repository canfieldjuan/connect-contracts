# ADR-0010: Connect v3 streamed output retrieval

**Status:** Proposed (accepted when this decision merges)

**Date:** 2026-09-27

## Context and scope

ADR-0002 requires every v2 completed output to contain canonical base64 and
limits it to 2 MiB. Both OCR consumers enforce that shape and cap. Keeping the
source scan can exceed it even when OCR succeeds. The early retained-source
budget check saves work, but cannot deliver a larger artifact. Raising the
inline cap would enlarge the JSON/base64 allocation and break strict decoders.

This decision revises ADR-0002 by adding a separate protocol, and extends the
ADR-0009 OCR profile for that protocol. V1 and v2 wire contracts remain frozen.
There is no broker, queue, cloud storage, shared filesystem path, new service,
model change, image recompression, page splitting, or multi-input workflow.
Email classification and Email Watcher migration are outside the initial rollout.

## Version, discovery, and compatibility

V3 uses `protocol_version: 3`, transport kind `http-loopback-v3`, and:

```text
GET  /v3/manifest
POST /v3/jobs
GET  /v3/jobs/{job_id}
GET  /v3/jobs/{job_id}/outputs/{artifact_id}
```

Its registrations live in `$XDG_RUNTIME_DIR/local-connect/v3/providers/` on
Unix and `%LOCALAPPDATA%\LocalConnect\runtime\v3\providers\` on Windows.
ADR-0005's owner-private placement, no-fallback rule, and verification apply.
V3 keeps ADR-0002's exact-loopback endpoint validation, authenticated manifest
attribution, durable instance identity, rotating process token, primitive
parameters, single streamed input, effects policy, and job idempotency.
All routes require the current registration bearer token and existing Connect
entitlement. Browser-Origin requests are refused. Proxy environment settings,
redirects, remote hosts, and provider-supplied retrieval URLs are not used.

A provider may publish v2 and v3 registrations for the same durable instance
and process. They share ownership, durable job identity and one OCR admission
lane; publishing a second protocol never adds a second OCR worker. Each job
records its admitted protocol and exact request. Conflicting reuse of its ID,
including a change of protocol, is refused. Status and output reads through
the wrong protocol return `JOB_NOT_FOUND`; they never translate a stored job.

Consumers prefer a supported v3 profile before new submission and may use v2
when only v2 is available. Once a job is admitted or its admission is uncertain,
recovery stays with the selected app, durable instance, protocol, job ID and
request. No timeout, failed download or provider restart triggers an automatic
resubmission through v2, another provider or a new job ID.

## Wire documents and bounds

The files under `schemas/v3/` are the executable shape authority. Registration,
manifest, request and error fields retain their v2 meanings, with the protocol
and transport constants above. Job states remain `accepted`, `processing`,
`completed`, and `failed`. Unknown members remain invalid.

A completed output contains exactly these members:

```json
{
  "artifact_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "media_type": "application/vnd.local-connect.ocr-pdf",
  "display_name": "scan.ocr.pdf",
  "byte_size": 3000000,
  "sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
}
```

This is a shape example, not an artifact or integrity receipt. The complete
status still binds the job, capability, provider and input provenance. There
are one through eight outputs, with distinct IDs that never alias an input.
Every v3 output is retrieved through the output route, including small and
zero-byte generic outputs. There is no inline/stream union or `payload_base64`,
path, URL, header credential, or additional delivery field in the descriptor.
The caller constructs the path from schema-validated lowercase UUIDs and the
already-validated registration origin, never from `display_name`.

The generic per-output limit is **37,748,736 bytes (36 MiB)**. This is the
existing OCR 32 MiB input allowance plus a bounded 4 MiB serialized text and
structure allowance. It is a chosen output budget, not a proof that all legal
OCR structures or source rewrites fit it. Final output validation remains
required. The existing 2 MiB inline cap is unchanged on v2.

Before JSON decoding, v3 bounds registration files to 16 KiB, manifests to
128 KiB, request JSON to 64 KiB, and status/error bodies to 64 KiB. Providers
must emit documents within those byte bounds as well as schema bounds. JSON
decoders reject duplicate members and non-finite numbers; before recursive
decoding they reject nesting deeper than 16 containers. Strings do not count
as nesting. There is exactly one streamed input, with the selected capability's
declared input cap and existing multipart framing bound.

## Retrieval and integrity

Only a completed job's recorded output ID is retrievable. A GET has no request
body, query, fragment, range, or conditional request semantics. Unsupported
range/conditional headers are refused with HTTP 400 `MALFORMED_REQUEST`.
Canonical route UUIDs are required; encoded separators, traversal, and supplied
filesystem names never select a file. Authentication and Origin checks precede
job lookup. Artifact IDs are identifiers, not bearer credentials.

A successful response is HTTP 200, `Content-Type: application/octet-stream`,
one decimal `Content-Length` exactly equal to the descriptor size, and
`Cache-Control: no-store`. No content encoding, transfer encoding, redirects,
or provider-authored filename headers are permitted. Bytes are streamed from
the provider's immutable stored artifact, not rebuilt or re-OCR'd on GET.
The consumer requests identity encoding and disables automatic decompression.
The descriptor's media type controls later interpretation, never HTTP guessing.

Before receiving a body, a consumer validates schema, app/instance, job,
capability, input provenance, distinct artifact IDs, declared media types and
profile size bounds. It validates HTTP framing and reads the body into an
owner-private temporary file in chunks no larger than 64 KiB, incrementally
counting bytes and hashing SHA-256. It stops on the first excess byte visible
in the HTTP body, enforces the advertised size and local cap, and rejects a
short body, conflicting length, digest mismatch or unsupported encoding.
It does not concatenate chunks into an unbounded response buffer. After full
body completion, actual length and SHA-256 must both equal the descriptor.

Unverified files are never parsed, rendered, exported, imported, indexed or
made lineage sources. If a profile requires paired outputs, all required
outputs must pass integrity and profile validation before any pair is
published. Verified files may then feed the existing bounded parser/storage
interfaces; their allocations must be covered by the new declared cap. This
does not require a streaming PDF parser or a new storage system.

## Completion, retries, and concurrency

Before committing `completed`, the provider atomically publishes all validated
artifacts and their stable IDs, sizes and hashes in its existing durable job
store. A completion record must never reference temporary or incomplete bytes.
After completion the descriptors and artifact bytes are immutable. Concurrent
GETs, status polls and restarts return the same committed bytes. GET never
acknowledges, consumes, deletes, changes job status or starts inference.

The provider retains artifacts for as long as their completed job record is
retained. Cleanup cannot leave a completed record with intentionally removed
outputs. An active reader holds a stable opened artifact or an equivalent
retention reference; cleanup cannot replace its bytes mid-response. A transfer
does not hold a database write transaction or the OCR admission lock.

At most two output bodies stream concurrently per provider process across its
v3 routes. Additional reads get HTTP 429 `OUTPUT_BUSY`, `retryable: true`, and
`Retry-After: 1`, without occupying a slot or altering the completed job. Slots
are released on success, disconnect, timeout and every error. Job status and
manifest reads remain available while a download or OCR job is active.

Each artifact transfer has a total 60-second deadline, including connection
and body I/O; the provider also bounds its writes to that deadline. Consumers
fetch a job's outputs sequentially. At most three GET attempts per artifact
are allowed per retrieval cycle, with a one-second delay for a transient
failure and any stricter parent deadline honored. Transport loss, timeout and
`OUTPUT_BUSY` can retry the same descriptor from byte zero after removing the
partial file. Range resume is deferred. Oversize, bad framing and integrity
mismatch are not transient: discard the partial pair and surface a failed
retrieval/review outcome without rerunning OCR or delivering partial data.

After restart or a rejected stale token, rediscover only the same durable
instance and validate its manifest and completed status. Resume only if the
descriptors still match the saved ones exactly, using the new registration
token. Otherwise preserve the failure for reconciliation. A source deletion
does not remove already-admitted recovery bytes under ADR-0008. A process
crash discards incomplete temporary downloads on recovery; verified siblings
may be reused only after rechecking their bytes and the current descriptors.

Retrieval errors use the v3 standalone HTTP error envelope and never rewrite
the completed job as failed:

| HTTP | Code | Retryable | Meaning |
|---|---|---|---|
| 400 | `MALFORMED_REQUEST` | false | Invalid route, body, or unsupported range/conditional request |
| 404 | `JOB_NOT_FOUND` | false | Unknown job or wrong admitted protocol |
| 409 | `OUTPUT_NOT_READY` | true | Job is accepted or processing; poll status within the parent deadline |
| 404 | `OUTPUT_NOT_FOUND` | false | Failed job, or artifact ID not in this completed job |
| 429 | `OUTPUT_BUSY` | true | Both transfer slots are occupied |
| 500 | `OUTPUT_UNAVAILABLE` | false | A recorded completed artifact is missing, corrupt, or unreadable |

Existing authentication, entitlement and Origin refusal policy also applies.
After response headers are sent, a read failure aborts the connection; a JSON
error is never appended to artifact bytes. Consumers detect a failed transfer
by body completion, size or digest validation. This is a per-user local
transport; it does not introduce cross-user authentication or a business queue.

## OCR profile 1.1 and downstream ownership

Protocol 3 advertises `document.ocr` version `1.1`. All ADR-0009 1.0 semantic
requirements apply except v2/base64 delivery and its 2 MiB PDF bound. Profile
1.1 requires v3 descriptors/retrieval and a nonempty PDF at most 37,748,736
bytes. It retains exactly one PDF input at most 33,554,432 bytes, 1..100 pages,
exactly the PDF/text output pair, nonempty canonical UTF-8 text at most 262,144
bytes, the tagged structure, source appearance, geometry, canonical text
equivalence, no truncation, no parameters and both effect flags false.
It must not be advertised as 1.0 or offered through v2. Existing v2 1.0 jobs
retain their original output bounds and behavior.

The retained-source preflight and final PDF guard must use the budget of the
job's admitted profile through one shared owner. The preflight keeps 262,144
bytes of bounded headroom and reports non-retryable
`OUTPUT_PDF_BUDGET_EXCEEDED` before rendering/OCR when that budget is exceeded.
The final cap still produces `OUTPUT_PDF_LIMIT_EXCEEDED`; neither guard claims
all admitted sources can complete. A failed profile emits neither artifact.

Invoice Processor and DocSum own their v3 OCR clients, paired validation,
private files and ADR-0008 recovery/lineage. Each must continue withholding
unverified OCR and preserve its existing identity holds, warning/review paths,
extraction checks, summary validation and model settings. A downloaded PDF is
not qualified OCR evidence merely because its hash matches.

The larger derived PDF must also fit its eventual parser, import path and
selected downstream capability. Supporting v3 discovery alone is insufficient.
Invoice's current Connect manifest advertises 32 MiB for both native PDFs and
OCR PDFs; its follow-up must explicitly support 36 MiB for the OCR media type
where that path is claimed, leaving native PDF admission unchanged. DocSum's
OCR pair guard is 2 MiB while its generic input default is 100 MiB; its
follow-up must trace every actual configured bound. Consumers reject an
incompatible downstream handoff before creating a child job and never relabel
an OCR PDF as a native PDF to bypass a cap or source-kind check.

## Conformance and landing gates

This repository supplies v3 schemas, descriptor fixtures and offline semantic
checks. Those checks prove shape/metadata rules only. They do not implement or
prove socket streaming, filesystem isolation, OCR quality, or installed apps.
App implementation PRs must pin the merged contract revision and demonstrate:

1. Old v1/v2 fixtures and jobs still work; strict old consumers never discover
   a v3 descriptor. Wrong-protocol job reads and conflicting resubmission fail.
2. Metadata rejects missing/extra fields, inline payloads, supplied URLs/paths,
   duplicate or input-aliased IDs, provider/job/input mismatches, invalid UUIDs,
   bad hashes and sizes. Generic empty output is valid; OCR empty output is not.
3. Streamed output crosses 2 MiB successfully; 36 MiB minus one and equality
   pass, plus one fails. Text retains its own 256 KiB boundary. Include mixed
   valid/invalid pairs, false/empty sizes, negative sizes and over-limit metadata.
4. Missing/duplicate/conflicting length, short and excess bodies, wrong digest,
   compression, redirects and untrusted paths fail before any parser/import.
   Probe both good and bad inputs through the actual transport and caller.
5. Two simultaneous downloads are correct; a third is busy. Slow/disconnected
   readers release slots within the deadline. Status and OCR admission work
   concurrently. Cleanup/restart races never change a reader's bytes.
6. Lost connection, restart/token rotation and consumer crash recover the same
   completed outputs without OCR, duplicate ledger import or a second summary.
   Partial pairs never create a derived child; missing/corrupt stored artifacts
   and changed descriptors stop with a visible failure.
7. Fresh production OCR of the 15 size-refused corpus entries retains all
   attempts, input/output hashes, verified runtime identity and terminal reasons.
   Follow them through both consumers with the frozen chosen model settings.
   Keep native invoices/summaries and previously successful OCR as regression
   lanes. Report admission/delivery separately from extraction/summary quality;
   passing this contract is not model or handwriting qualification.

Land the shared ADR/schemas/fixtures first. Then use one bounded provider PR
and separate Invoice Processor and DocSum consumer PRs, keeping existing v2
paths during rollout. Only claim the large-output slice complete after both
consumers demonstrate production delivery. Multi-input jobs, ranged resume,
acknowledgement/expiry protocols and other consumer migrations remain deferred.
