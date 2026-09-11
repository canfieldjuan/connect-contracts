# PR: Automate feature registry and ADR-0006

## Why this slice exists

Email Watcher enforces a second entitlement feature, `connect.automations`,
that exists in no shared document: the claims schema types `features` as
free-form pattern strings, the issuer validates by pattern only, and the only
signed fixture carries the single exchange feature. A misspelled tier can be
issued as a valid licence that no application honours, and every application
that wants to test the second key must mint its own licence. ADR-0001's
"no queue" sentence and ADR-0004's "grants only capability exchange" sentence
also no longer describe the shipped consumer queue and the two-feature
licence. This is the shared-contract prerequisite (section 8.3 of the Email
Watcher rule-engine contract) for implementing the Automate rule engine.

## Scope (this PR)

1. `entitlements/v1/features.json`: the enumerated feature registry with
   exactly `connect.capability_exchange` and `connect.automations`.
2. Two new signed conformance fixtures under `entitlements/v1/fixtures/valid/`:
   `active-automations.json` (both features, entitled) and
   `automations-only.json` (second feature alone, not entitled for
   exchange), signed by a new additive test key
   `connect-test-automations-2026-01` in `test-keyring.json`, because the
   original test signing key was never committed.
3. `tools/entitlement_issuer.py`: validate every `--feature` against the
   registry, not only the pattern.
4. `adr/0006-consumer-admission-and-automate-feature.md`: consumers own
   admission, ordering and retry; the feature registry; corrections to the
   ADR-0001 and ADR-0004 sentences.
5. Tests: registry validity, every entitled fixture licence uses only
   registered features (the existing `missing-feature` negative fixture
   deliberately carries an unregistered one), index feature expectations,
   issuer rejects an unregistered feature and issues both registered ones.
6. `README.md`: list ADR-0006 and the registry.

### Review Contract

- The claims schema and both wire protocols are unchanged: `git diff` touches
  no file under `schemas/` and not `entitlements/v1/claims.schema.json`.
- The production keyring `entitlements/v1/release/keyring.json` is unchanged.
- Every fixture in `entitlements/v1/fixtures/index.json` still passes the
  existing conformance test; the two new cases are entitled exactly as their
  `features` field says.
- The issuer refuses `--feature connect.automation` (unregistered) and
  accepts `--feature connect.capability_exchange --feature
  connect.automations`.

### Files touched

- `entitlements/v1/features.json` (new)
- `entitlements/v1/fixtures/test-keyring.json`
- `entitlements/v1/fixtures/index.json`
- `entitlements/v1/fixtures/valid/active-automations.json` (new)
- `entitlements/v1/fixtures/valid/automations-only.json` (new)
- `tools/entitlement_issuer.py`
- `tests/test_contracts.py`
- `tests/test_entitlement_issuer.py`
- `adr/0006-consumer-admission-and-automate-feature.md` (new)
- `README.md`
- `plans/PR-Automate-Feature-Registry.md` (new)

## Mechanism

The registry is a strict JSON object read by the issuer with the same bounded
regular-file reader and duplicate-key-rejecting parser it uses for keyrings.
`issue_entitlement` loads it after the pattern check and refuses any feature
not listed. The conformance test loads the registry, checks identifier
validity and uniqueness, decodes every fixture's claims, and asserts its
features are a subset of the registry; index cases may carry an expected
`features` list that must equal the decoded claims. The new fixtures were
signed once with a freshly generated Ed25519 key whose public half is added
to the test keyring; the private half was discarded, as with the existing
test key.

## Intentional

- A registry file rather than a schema enum, so adding a feature is additive.
- The test signing key is new and additive; the original fixtures and key are
  untouched.
- ADR-0006 is `Proposed` in the file and becomes accepted by the merge, as
  the earlier ADRs did.
- `connect.automations` is consumer-enforced only; nothing is added to the
  wire.

## Deferred

- Rule, event, or action schemas: consumer-local by ADR-0006.
- A registry schema file: the issuer and the test validate its shape; a
  schema can follow if a second reader appears.
- Provider awareness of automation origin: rejected by ADR-0006.

## Verification

- `python3 -m unittest`
- `python3 -m ruff check tools/entitlement_issuer.py tests/test_contracts.py tests/test_entitlement_issuer.py`
- `python3 -m ruff format --check tools/entitlement_issuer.py tests/test_contracts.py tests/test_entitlement_issuer.py`
- Manual: decode both new fixtures and verify their signatures against the
  test keyring; run the issuer against a temporary authority with an
  unregistered feature (refused) and with both registered features (issued).

## Estimated diff size

About 350 lines including the ADR and plan; roughly 60 lines of code in the
issuer and 90 in tests.
