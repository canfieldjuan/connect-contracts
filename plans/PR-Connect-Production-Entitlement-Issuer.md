# PR: Connect production entitlement issuer

## Why this slice exists

Local Connect entitlement v1 defines how applications verify a signed bearer
license, but the repository currently contains only schemas and conformance
fixtures. Those fixtures are explicitly test-only. There is no release-owned
tool that can create a protected production Ed25519 key, publish its public
verification key, or issue a production entitlement without hand-assembling
security-sensitive JSON.

The root cause is the missing release authority between the accepted contract
and application verifiers. This slice supplies that authority without moving
private-key custody into any application or changing the entitlement format.

## Scope (this PR)

1. Add a release-only issuer CLI that:
   - creates an encrypted Ed25519 private key with owner-only permissions;
   - publishes the matching entitlement-v1 public keyring;
   - signs strict entitlement-v1 claims with an active feature list;
   - refuses unsafe private-key files, duplicate features, invalid validity
     intervals, unknown key IDs, output replacement, and repository-local
     private-key destinations.
2. Support either an interactive passphrase or Linux Secret Service custody;
   never accept the passphrase as a command-line argument or print it.
3. Add both-direction boundary tests for initialization and issuance.
4. Document the release workflow and the separation between public build input
   and private issuer custody.

### Files touched

- `tools/entitlement_issuer.py`
- `tests/test_entitlement_issuer.py`
- `entitlements/v1/release/keyring.json`
- `requirements-dev.txt`
- `README.md`
- `plans/PR-Connect-Production-Entitlement-Issuer.md`

## Mechanism

`init` creates an Ed25519 key in memory, encrypts its PKCS#8 representation,
and writes it exclusively with mode `0600`. The passphrase is either entered
twice through a no-echo prompt or generated and stored under a key-id-scoped
Secret Service item. The corresponding public keyring contains only the
contract's `key_id`, `Ed25519` algorithm, and unpadded base64url public key.

`issue` reopens only an owner-private, regular, non-symlink private-key file,
retrieves the passphrase through the selected custody mechanism, verifies that
the private key matches the selected public-keyring entry, serializes strict
claims, signs those exact payload bytes, self-verifies the result, and creates
the requested entitlement without replacing an existing file.

## Intentional

- Production public keys are publishable build inputs; their trust comes from
  the official application package, not secrecy.
- The private key remains outside Git and application packages.
- Secret Service support is optional and Linux-specific. Interactive
  passphrases remain the portable path.
- Entitlements remain offline bearer licenses with the limits already recorded
  in ADR-0003.

## Deferred

- Billing, checkout, renewals, online activation, revocation, machine binding,
  and account UI remain deferred.
- Hardware-token custody and offline recovery ceremonies remain release
  operations outside this CLI.
- Application packaging and installation are owned by each application repo.

## Verification

- `python3 -m unittest tests.test_entitlement_issuer`
- `python3 -m unittest tests.test_contracts`
- `python3 -m unittest`
- `python3 -m ruff check tools/entitlement_issuer.py tests/test_entitlement_issuer.py`
- `python3 -m ruff format --check tools/entitlement_issuer.py tests/test_entitlement_issuer.py`
- Focused manual initialization and issuance under a temporary home, followed
  by schema and signature verification.

Results:

- `python3 -m unittest tests.test_entitlement_issuer` passed 13 tests.
- `python3 -m unittest` passed 19 tests.
- Ruff lint passed, and both new Python files passed Ruff's format check.
- `python3 -m compileall -q tools tests` passed.
- `init --secret-service` created `local-connect-prod-2026-01` with an
  owner-only encrypted private key outside Git, one matching Secret Service
  item, and the public release keyring in this repository.
- `issue --secret-service` created an active entitlement and a second isolated
  smoke entitlement; both completed without exposing the passphrase.
- The release public key was compared with the canonical test fixture and is
  distinct.
- Locked Secret Service collections now interpret the API's dismissal result
  correctly and verify that the collection is unlocked before key access;
  regression tests cover success, dismissal, and a still-locked collection.
- The operator guide distinguishes the already-completed production bootstrap
  from issuance and points future `init` runs at new, non-existing staging
  destinations.
- Type-invalid public keys and non-UTC claim datetimes fail through the issuer's
  stable `IssuerError` contract rather than escaping as raw Python exceptions.
- Fractional claim datetimes are rejected before they can collapse to the same
  serialized second. FIFO inputs cannot block the issuer before regular-file
  validation, unsupported private-key algorithms remain inside the safe error
  contract, and Secret Service query failures are normalized on both command
  paths. Numeric-limit and recursion failures during JSON decoding are also
  normalized instead of escaping as raw tracebacks. Passphrases are bounded at
  the backend limit on both init and issue paths, and key-generation backend
  failures use the same safe operator error contract.
- Interactive passphrase EOF, cancellation, terminal failure, and encoding
  errors are normalized through one prompt helper on both command paths.

## Estimated diff size

Approximately 1,000 added lines across the issuer, boundary tests, plan, public
keyring, and release documentation. The private-file admission and atomic
creation code accounts for the larger-than-initially-estimated surface. The
security-sensitive init/issue lifecycle is one indivisible slice; splitting it
would leave either an unusable signer or an untested key-generation path.
