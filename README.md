# Local Connect Contracts

This repository is the canonical, language-neutral contract authority for
interoperability between independently installed local desktop applications.

It intentionally contains no broker, executable runtime, application-private
code, or workflow engine. Applications remain independently useful and own
their private state.

Current decisions:

- [ADR-0001: Connect v0 local capability interoperability](adr/0001-connect-v0.md)
- [ADR-0002: Connect v2 generic capability participation](adr/0002-connect-v2-generic-capabilities.md)
- [ADR-0003: Connect entitlement v1](adr/0003-connect-entitlement-v1.md)
- [ADR-0004: Connect entitlement activation v1](adr/0004-connect-entitlement-activation-v1.md)
- [ADR-0005: Windows Local Connect placement](adr/0005-windows-local-placement.md)

The first provider's standalone summary artifact is implemented and verified,
so Connect v1 remains frozen as executable JSON Schemas and conformance
fixtures under `schemas/v1/` and `fixtures/v1/`.

Connect v2 is the generic capability successor. Its schemas and fixtures live
under `schemas/v2/` and `fixtures/v2/`. V2 adds native action metadata,
bounded primitive parameters, explicit effect/confirmation declarations, and
generic integrity-checked output bytes. It does not modify v1.

Run `python3 -m unittest tests.test_contracts` after installing the development
dependency in `requirements-dev.txt`.

Commercial Connect authorization is a separate, signed local contract under
`entitlements/v1/`. It does not add fields to either Connect wire protocol.
The key and licenses under `entitlements/v1/fixtures/` are conformance fixtures
only and must never be used as a production issuer. The separately named
`entitlements/v1/release/keyring.json` is the publishable production public
keyring consumed by official application builds; it contains no private key.

The current production authority is already bootstrapped. Release operators
issue licenses against its committed public keyring through the offline issuer:

```bash
python3 tools/entitlement_issuer.py issue \
  --key-id local-connect-prod-2026-01 \
  --private-key /absolute/private/path/issuer.private.pem \
  --keyring "$PWD/entitlements/v1/release/keyring.json" \
  --subject customer-or-installation-reference \
  --expires-at 2027-09-02T00:00:00Z \
  --output /absolute/private/path/entitlement-v1.json \
  --secret-service
```

`init` is reserved for bootstrapping a new authority or rotation candidate and
requires both destinations not to exist. Never point it at the committed
current keyring. For example, stage the next public keyring separately, review
it, then intentionally publish its public entry through the normal release
process:

```bash
python3 tools/entitlement_issuer.py init \
  --key-id local-connect-prod-2027-01 \
  --private-key /absolute/private/path/issuer-2027.private.pem \
  --keyring /absolute/release/staging/keyring-2027.json \
  --secret-service
```

Without `--secret-service`, both commands prompt locally for the encryption
passphrase without echoing it. The CLI never accepts a passphrase argument.
Private-key parents must be owner-only, and the CLI refuses to place a private
key anywhere inside this repository. Official application packages embed only
the public keyring. Entitlements are created owner-private and are installed by
an application's ADR-0004 activation adapter.

Activation is an app-local operation governed by ADR-0004. Either application
may securely install the same signed entitlement, but no application becomes
the owner of another application's settings or private data.

ADR-0005 extends discovery and entitlement placement to Windows without
changing the wire transport: Windows uses exact-loopback HTTP and per-user
files rooted under `%LOCALAPPDATA%\LocalConnect\`. Named pipes remain deferred.

Both versions use the same intentionally small HTTP shape under their own
versioned routes:

- `GET /v{n}/manifest` returns the authenticated manifest.
- `POST /v{n}/jobs` accepts multipart fields `request` (the job-request JSON)
  and `artifact` (one streamed artifact).
- `GET /v{n}/jobs/{job_id}` returns the current job-status document.

All routes require the runtime-registration bearer token. The registration
itself is an owner-only, atomic runtime file and is availability evidence only
while its exact-loopback endpoint answers with the same instance ID.

V2 output payloads are base64-encoded bytes with declared size and SHA-256.
Implementations must validate those integrity fields after decoding. Known
media types may be rendered by consumer-owned code; unknown types may only be
saved/exported safely and must never be executed automatically.
