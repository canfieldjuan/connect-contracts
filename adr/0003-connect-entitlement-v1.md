# ADR-0003: Connect entitlement v1

**Status:** Accepted

**Date:** 2026-08-31

## Context

Connect capability exchange is a paid product feature. Provider installation,
runtime registration, and authenticated reachability prove availability, but
none proves that the local user is commercially entitled to exchange artifacts
between applications. Email Watcher's Gmail authorization is private mailbox
access and must not become a Connect account or license.

The first sellable boundary needs deterministic offline behavior without adding
a billing provider, cloud account, broker, or workflow service to either
standalone application.

## Decision

### Independent commercial contract

Entitlement format version 1 is independent of Connect protocol versions 1 and
2. No entitlement, customer identity, or signature is placed in a capability
manifest, job request, result, or runtime registration.

Both the caller and provider independently verify the same local entitlement
before participating:

- a consumer returns no discovered capabilities and rejects new invocation
  attempts while unentitled;
- a provider does not return its manifest and rejects job submission and status
  access while unentitled; and
- standalone application behavior and already persisted user-owned results stay
  available.

This defense in depth prevents a stale registration or a modified consumer from
turning one missing check into free provider admission.

### Signed bearer license

The entitlement file is a bounded JSON envelope containing:

- `format_version`;
- an issuer `key_id`;
- unpadded base64url payload bytes; and
- an unpadded base64url Ed25519 signature over those exact payload bytes.

The decoded payload is a strict JSON object containing a UUIDv4 entitlement ID,
an opaque subject, a unique feature list, and UTC `issued_at`, `not_before`, and
`expires_at` timestamps. Capability exchange requires the exact feature
`connect.capability_exchange`.

Signing the encoded bytes rather than a reconstructed JSON object avoids
cross-language canonicalization. Verifiers bound and decode the payload, verify
the signature with a compiled public-key ring, then strictly validate claims.
Unknown key IDs, unknown fields, duplicate JSON object member names, malformed
encoding, invalid signatures, invalid intervals, missing features, and
unsupported versions fail closed.

An entitlement is active exactly when:

```text
issued_at <= not_before <= now < expires_at
```

There is no implicit offline grace period. Replacing an expired license
atomically with a valid signed license takes effect on the next discovery or
provider request; application restart is not required.

### Local placement and trust

The initial Ubuntu implementation reads:

```text
$XDG_CONFIG_HOME/local-connect/entitlement-v1.json
```

or, when `XDG_CONFIG_HOME` is unset:

```text
$HOME/.config/local-connect/entitlement-v1.json
```

The directory and file must be owned by the current OS user, must not be
symlinks, and must not grant group or other permissions. Tests may inject an
isolated path and key ring; production runtime code cannot replace compiled
issuer keys through an environment variable.

Public verification keys are compiled into official packages. Private issuer
keys are never shipped or committed. Key IDs permit additive rotation. The
canonical key and licenses under `entitlements/v1/fixtures/` are explicitly
test-only.

## Security boundary

This is an offline signed bearer license. It prevents editing or fabricating an
entitlement without an issuer key, but it is not machine-bound and has no online
revocation. A user who copies a valid license may copy its commercial rights.
Clock rollback and stronger device/account binding require an activation
service or trusted platform component and remain deferred.

The entitlement never grants mailbox, database, or filesystem authority.
Email Watcher still hands off only explicitly selected artifact bytes and
bounded metadata. Document Summarizer never receives Gmail credentials.

## Rejected alternatives

### Environment or unsigned feature flag

Rejected because the user or any same-user process could manufacture paid
status without an issuer decision.

### Reuse Gmail OAuth

Rejected because mailbox authorization belongs only to Email Watcher and would
couple unrelated providers to Google identity.

### Add entitlement fields to Connect v1 or v2

Rejected because it would leak commercial state into interoperability payloads
and break frozen strict decoders.

### Require an online broker now

Deferred. It would add account, lifecycle, availability, and packaging work
that the two-application offline proof does not need.

## Consequences

- Connect can be sold independently of either standalone application.
- Missing, malformed, expired, or not-yet-valid licenses deterministically hide
  capabilities and deny live jobs.
- License delivery and production issuer-key custody are release operations,
  not application runtime behavior.
- Billing checkout, account UI, renewal UI, revocation, machine binding,
  Windows/macOS placement, and grace policy remain deferred.
