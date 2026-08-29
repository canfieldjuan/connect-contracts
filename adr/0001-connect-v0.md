# ADR-0001: Connect v0 local capability interoperability

**Status:** Accepted

**Date:** 2026-08-29

**Decider:** Juan Canfield

## Context

Email Watcher and Document Summarizer are independent Tauri desktop
applications. They must remain independently useful and must not read one
another's databases, import private implementation modules, or rely on private
filesystem layouts.

The first interoperability proof lets Email Watcher discover a running
provider for `document.summarize`, explicitly hand it a PDF attachment, and
display the returned plain-text summary. The design must allow a differently
named application to provide the same capability without changing Email
Watcher.

Connect v0 targets Ubuntu first, operates without cloud services, and accepts
the local same-OS-user trust boundary. Workflow composition, launch-on-demand,
and multi-provider selection are outside this decision.

## Decision

### Discovery and availability

Providers advertise capabilities, not application-specific integrations.
Each running provider binds an ephemeral loopback HTTP endpoint and atomically
writes an owner-only runtime registration under:

```text
$XDG_RUNTIME_DIR/local-connect/v1/providers/
```

If `XDG_RUNTIME_DIR` is unavailable, Connect is unavailable. There is no
fallback to a shared temporary directory.

A provider is available only when its registration has a supported protocol,
its endpoint is an exact loopback address, and its authenticated manifest is
reachable. Installation alone does not imply availability. Stale
registrations are ignored.

### Transport and authentication

Connect v0 uses HTTP over exact loopback addresses because both Rust and
Python can implement streaming requests, bounded timeouts, and polling without
a third resident process.

Every provider process creates a new random instance identifier and bearer
token. The token is stored only in its owner-readable runtime registration.
Consumers disable environment proxies, refuse redirects, and reject
non-loopback endpoints. Providers reject browser `Origin` requests and enforce
bounded request sizes.

This authenticates possession of the per-user registration, not application
identity. `app_id` is attribution metadata, not cryptographic proof. Defending
against a hostile process running as the same OS user requires a future trusted
broker or OS package-identity mechanism.

### Artifacts and ownership

Connect exchanges typed artifact descriptors and streamed bytes. It never
exchanges private filesystem paths.

The caller provides media type, byte size, SHA-256 digest, and untrusted
display metadata. The provider streams the input into a generated owner-only
temporary file, validates it, flushes it, and atomically promotes it into
provider-owned durable storage before accepting the job.

Document Summarizer retains a Connect-imported PDF as a normal durable
document with Connect provenance. Email Watcher retains its returned summary
with the source email. Purging the email may remove Email Watcher's copy but
does not delete the independently owned Document Summarizer document.

The default provider input limit is 100 MiB and is configurable. Email sender,
subject, mailbox identifiers, OAuth credentials, and other mailbox state are
not transferred.

### Jobs and results

The caller creates the job identifier. Provider states are:

```text
accepted -> processing -> completed | failed
```

`accepted` means the provider durably owns the validated input and has
committed its job-to-pipeline mapping. Callers poll status; v0 has no callback,
queue, scheduler, or automatic retry service. A provider processes at most one
job at a time and returns a retryable busy error for additional work.

Repeating a job identifier with the same declared input is idempotent.
Repeating it with different input is a conflict. Email Watcher reuses an
existing completed result for an attachment and capability version; an
explicit re-summarize action is deferred.

The first output is versioned JSON containing plain UTF-8 summary text,
warnings, and input-artifact provenance. It contains no HTML, Markdown,
citations, or provider-private document identifiers.

### UI contribution

Email Watcher understands the capability `document.summarize` and presents a
contextual `Summarize` action for compatible PDF attachments. It does not
branch on a provider app identifier.

Zero compatible providers yields no action. One yields the action. More than
one yields an `ambiguous_provider` diagnostic rather than silent provider
selection. Discovery is refreshed with inbox refresh, window focus, and again
immediately before job submission.

## Options considered

### Tauri command invocation

Rejected because Tauri IPC joins a WebView to its own application core; it is
not an independently installed cross-application contract.

### Direct executable invocation

Rejected because executable discovery, input-derived execution, asynchronous
status, and lifecycle ownership create unnecessary coupling and security risk.

### Unix sockets and Windows named pipes

Deferred. They offer strong OS-level access controls but require different
cross-platform transports and language implementations. The protocol retains
a transport discriminator so they can be added without changing capability,
artifact, or job contracts.

### Local broker

Deferred. A broker would simplify launch-on-demand, leases, provider policy,
and package identity, but it creates a third installed service and failure
domain before the two-application proof needs one.

### Custom URI handler

Deferred for possible launch signaling. A URI handler is not the artifact and
asynchronous job channel.

## Consequences

- Both applications keep private databases and credential stores.
- Connect can disappear without disabling either standalone application.
- A third application can provide `document.summarize` without Email Watcher
  code changes when it is the only compatible provider.
- Providers must already be running in v0.
- Same-user malicious-process impersonation is not prevented.
- Multiple-provider selection, Windows packaging, and alternate transports
  require later decisions.

## v1 contract freeze

The first executable contract uses protocol integer `1`; application and
capability versions remain independent strings. Provider availability is not a
mutable manifest flag: it is proven by a supported runtime registration plus
an authenticated `GET /v1/manifest` response carrying the same instance ID.

`POST /v1/jobs` uses two multipart fields: a bounded `request` JSON part and
one streamed `artifact` part. `GET /v1/jobs/{job_id}` carries the polling state
and, when complete, the inline versioned summary artifact. The JSON descriptor
contains a display name, media type, byte size, SHA-256 digest, and source-app
attribution but cannot contain a filesystem path or mailbox metadata.

The schemas constrain wire shape. Implementations must additionally parse and
validate URLs, enforce port and body limits, authenticate before accepting
bytes, compare the streamed size and digest with the descriptor, sanitize the
display name before provider-owned storage, and verify idempotent job reuse.
Those checks cannot safely be delegated to JSON Schema alone.

## Implementation gates

1. Email Watcher must independently persist, display, and retrieve attachment
   bytes.
2. Document Summarizer must independently produce and reload a durable summary
   through a UI-neutral application service.
3. Only then are v1 JSON Schemas and conformance fixtures frozen.
4. The provider is implemented before the consumer UI.
5. Completion requires a real installed Ubuntu handoff plus provider removal
   and restoration with the same Email Watcher build.
