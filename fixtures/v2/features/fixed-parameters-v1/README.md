# fixed-parameters-v1 shared conformance slice

## Contract and origin

ADR-0013 landed at d2d3b7baf053377e2e4b78ee3569bde7a389da94.
This slice supplies the negotiated manifest schema and canonical declarative
response/request/admission vectors that do not yet exist. Without them each
app could implement a private fixed-parameter dialect or bypass replay rules.

## Required surface and one owner

- An extended manifest schema derived from the unchanged legacy schema;
  a derivation guard rejects divergence outside the parameter extension.
- Closed fixture-context schemas for exchange, admission and ordered event
  traces. These envelopes describe test inputs, not additional wire fields.
- A canonical golden fixture index with expected validity and decision output.
- A feature conformance oracle under tests, composing the existing
  tests.test_contracts.semantic_errors and primitive-type owner. It does not
  copy their legacy validation rules. One admission oracle also owns event
  trace submission decisions.
- Focused fixture, mutation, boundary and derivation checks, plus the existing
  shared conformance suites. Public README links the executable command.

## Observable behavior

An exact supported request and acknowledgment choose the extended decoder.
Missing acknowledgment or an unsupported request falls back to the unchanged
legacy decoder. Every response must have no-store and Vary, preserving any
existing Vary members. Neither cache order permits response reuse. Rotation
and mismatch recovery discover the current bundle immediately.

Fixed declarations require required=true and their declared primitive type
and existing request-parameter bounds. Presence preserves empty strings,
zero and false; booleans are not integers. Missing/wrong caller values are
invalid requests, not invented fixed-mismatch refusals. Well-typed conflicting
fixed values yield the exact FIXED_PARAMETER_MISMATCH/409/retryable=false
refusal when starting new or failed-restart work.

Admission context resolves immutable job identity before comparing against
a newly rotated bundle. Identical accepted/processing/completed work replays
its admitted identity. A changed request conflicts. Failed restarts and new
jobs use the current declaration; serialized rotate/admit orders have distinct
expected decisions. Header, equality, ordering and conflict mutations must
change golden outcomes or validity. Existing legacy schemas/fixtures remain
byte-identical; a manifest-schema derivation check guards their single owner.

## Non-scope and proof limits

No app, HTTP server/client, connect-automate implementation, model, database,
queue, entitlement, scanned extraction, deployment or existing app contract
change. Ordered event traces are a deterministic conformance model, not a
running transaction or thread scheduler. Request-invalid is a model decision,
not a new HTTP error code. Existing canonical request/error bodies retain
their wire owners. These fixtures do not prove authorization, semantic
classification, real cache behavior or runtime concurrency. Both app owners
must independently replay the published pin and later prove their real paths.

## Gates and plan

Commit this contract before conformance implementation. First run a declared
fail-first schema probe for a valid required fixed value; it must initially
fail with the legacy additional-property rejection. Then derive the extension,
exercise golden fixtures and negative/mutation checks, and run the repository's
existing documented conformance suites. Record exact commit and content hashes
outside worktrees. Publish a separate reviewable PR; no merge is authorized by
this start. Dependent app work stays blocked on shared review/landing, joint
declarations, a later assigned connect-automate owner/pin and accepted app slices.

Status: implementation and verification pending.
