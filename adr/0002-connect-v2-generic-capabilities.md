# ADR-0002: Connect v2 generic capability participation

**Status:** Accepted

**Date:** 2026-08-30

## Context

Connect v1 proved one local handoff, but its wire contract is deliberately
specific to `document.summarize`:

- capability declarations have no safe action label, description, parameter
  declaration, external-effect flag, or confirmation requirement;
- job requests cannot carry declared parameters; and
- completed jobs contain a summary-specific output object.

The existing Python and Rust implementations reject unknown fields. Adding
the missing fields to v1 would therefore break deployed strict decoders even
if JSON Schema marked the fields optional. V1 remains frozen.

Email Watcher now needs to discover and invoke capabilities without binding
its business logic to Document Summarizer or to one output schema.

## Decision

### Version coexistence

Generic participation uses protocol version 2. V1 schemas, fixtures,
registrations, and routes remain unchanged.

V2 providers register under:

```text
$XDG_RUNTIME_DIR/local-connect/v2/providers/
```

and expose:

```text
GET  /v2/manifest
POST /v2/jobs
GET  /v2/jobs/{job_id}
```

The transport remains exact-loopback HTTP with an owner-private per-instance
bearer token. A provider may expose v1 and v2 simultaneously during migration.
Each registration names one protocol version and transport kind, so an older
consumer never receives a document it cannot decode.

### Generic capability declarations

Every v2 capability declares:

- its identifier and independent `major.minor` capability version;
- a bounded action label and description;
- accepted media types and per-type maximum byte sizes;
- produced media types;
- bounded primitive parameter declarations; and
- whether invocation has external effects or requires confirmation.

Labels and descriptions are untrusted text. Consumers render them only with
consumer-owned native components and never interpret them as markup or code.

Accepted media types and parameter names must be unique within a capability,
so one declaration cannot advertise conflicting size limits. Job parameters
may be strings, bounded integers, or booleans. Implementations reject
undeclared parameters, missing required parameters, and values whose primitive
type does not match the declaration. The request capability version, input
media type, and input byte size are also validated against that same provider
declaration before acceptance. V2 intentionally does not embed arbitrary JSON
Schema or provider-authored forms.

Input artifacts may contain zero bytes; accepted-media declarations impose an
upper bound and do not imply a positive minimum. Integer parameters follow JSON
Schema numeric semantics, so mathematically integral forms such as `1.0` are
valid while booleans and fractional values are not. Runtime registration ports
are additionally validated to the TCP range 1 through 65535.

### Jobs and artifacts

V2 retains caller-created stable job and artifact identities. Repeated
submission of the same job identity and request is idempotent; conflicting
reuse is rejected. The first v2 transport accepts exactly one streamed input
artifact per job. Multi-input jobs require a later transport contract rather
than an undocumented multipart convention.

Completed jobs return generic output artifacts. Each output contains:

- artifact identity, media type, and untrusted display name;
- decoded byte size and SHA-256 digest; and
- bounded base64-encoded bytes.

Always carrying bytes gives every output one deterministic integrity rule and
avoids placing provider-private paths in the contract. Payloads use canonical
base64, including the empty string for a zero-byte artifact, and output
artifact identities are unique within a completed job.
Known media types may be decoded and rendered by consumer-owned code after
size and digest checks. Unknown media types may only be saved/exported through
a generated or sanitized filename; they are never executed or interpreted
automatically.

Output artifacts are limited to 2 MiB each and eight outputs per job. The
transport implementation must bound the complete response before parsing.
Larger or streaming outputs require a later versioned retrieval contract.

### Compatibility and matching

Availability still means a supported owner-private registration plus a
successful authenticated manifest response whose app and instance attribution
matches the registration. Installation alone is not availability.

Consumers match declarations using protocol version, capability version,
media type, artifact size, supplied parameters, and effects/confirmation
policy. Application identity is used only for attribution, availability,
provenance, and explicit provider selection.

## Landing order

1. Publish the v2 schemas and fixtures while leaving v1 untouched.
2. Add a dual-stack v2 provider surface to Document Summarizer.
3. Add v2 generic discovery, matching, invocation, and persistence to Email
   Watcher while retaining the working v1 proof until migration is complete.
4. Prove provider removal/restoration, explicit multi-provider selection, a
   second deterministic capability, and unknown-output export.

## Rejected alternatives

### Extend v1 in place

Rejected because both current implementations deny unknown fields. It would
be a breaking wire change disguised as an optional schema edit.

### Provider-authored HTML, forms, or arbitrary JSON Schema

Rejected because Email Watcher owns its UI and trust boundary. The current
proof needs only bounded primitive parameters and native controls.

### Shared paths or provider-private output references

Rejected because applications own private storage and artifacts cross only by
explicit handoff.

### A broker or workflow engine

Deferred. Neither is required to prove generic capability discovery and one
local asynchronous job.

## Consequences

- V1 remains operational and backward compatible.
- V2 adds a small dual-stack migration cost to both applications.
- Generic consumers can present capabilities safely without app-specific
  labels or provider UI.
- Binary and unknown outputs have a deterministic safe export path.
- Large outputs, multi-input jobs, remote transport, launch-on-demand, and
  same-user process attestation remain deferred.
