# Enforce PROVIDER_BUSY and registration URL semantics

## Why this slice exists

Release-blocker issue #10 found three admission gaps in the executable Connect
contracts: both error schemas admit `PROVIDER_BUSY` with `retryable: false`, v1
lacks v2's TCP port-range semantic check, and the registration URL regex accepts
a terminal line feed under validators whose `$` anchor matches before that
character.

### Problem-derived contract

Root cause: independent schema fields do not express the coupled busy-error
invariant, while registration admission relies partly on a regex and partly on
a v2-only parsed-URL check. A parser may normalize control characters before
the semantic layer sees them.

The correct fix must:

1. couple the `PROVIDER_BUSY` code to `retryable: true` in both versioned error
   schemas;
2. inspect raw registration URLs for controls before parsing and apply the same
   TCP port-range semantics to v1 and v2;
3. make the schema's end-of-string admission independent of `$`'s terminal-LF
   behavior;
4. add positive and negative executable contract evidence for both protocol
   versions; and
5. tell downstream implementations which checks remain semantic obligations
   beyond JSON Schema validation.

The fix must not change the accepted exact-loopback URL shapes, couple generic
error codes to a retry policy, change routes or wire fields, add an executable
runtime library, or modify any application repository.

### Closure declarations

- Busy-policy code set: **CLOSED**, **ENUMERATED** from ADR-0006's sole
  pre-admission busy code, `PROVIDER_BUSY`. Other codes retain their declared
  retryability. An unknown or future code receives no implicit busy semantics.
- Registration host set: **CLOSED**, **ENUMERATED** from ADR-0001's exact
  numeric-loopback transport: `127.0.0.1` and `::1`. Every other parsed host is
  rejected by the schema grammar and must also be rejected by implementations.
- Raw URL input: **OPEN**, sourced from registration documents. Admission has
  one fail-closed conjunction: control-free raw text, the canonical lexical
  shape, successful parsing, and a port in `1..65535`; malformed, normalized,
  or unrecognized values reject. The schema closes representation to a scalar
  string, so container variants reject before URL admission.
- TCP port range: **CLOSED**, **DERIVED** by numeric comparison with the
  protocol's `1..65535` invariant. Values outside the range reject.

## Scope (this PR)

Ownership lane: connect-contracts-release-boundaries
Slice phase: first-public-release blocker

1. Tighten v1 and v2 error and registration schemas without changing any valid
   fixture.
2. Extend the shared conformance semantic path to both protocol versions.
3. Add indexed invalid fixtures and boundary-focused tests.
4. Document the runtime checks every downstream implementation must perform.

### Files touched

- `schemas/v{1,2}/{error,registration}.schema.json`
- `fixtures/v{1,2}/index.json` and focused fixtures under each `invalid/`
- `tests/test_contracts.py`
- `README.md`
- `plans/PR-Provider-Busy-Registration-Semantics.md`

### Review Contract

Acceptance criteria:

1. Both error schemas reject an indexed `PROVIDER_BUSY` fixture whose
   `retryable` field is false and continue accepting the existing true fixture,
   settled by `python3 -m unittest tests.test_contracts`.
2. `semantic_errors()` applies raw-control and numeric port checks to v1 and v2;
   direct boundary tests cover port 1, 65535, 0, and 65536 plus terminal and
   embedded controls.
3. The registration schemas reject terminal-LF inputs without depending on a
   validator-specific `$` interpretation, settled by the indexed fixtures and
   the Python conformance suite.
4. Every new negative member is indexed for both versions, while all existing
   exact-loopback valid fixtures remain green in the full suite.
5. README conformance guidance identifies raw-control rejection and numeric
   port validation as runtime obligations that occur before parser
   normalization.

Affected surfaces: v1/v2 error schemas, v1/v2 registration schemas, executable
fixtures, semantic conformance tests, downstream guidance.

Risk areas: cross-validator regex behavior, frozen-v1 compatibility, error
retry semantics, parser normalization, boundary completeness.

Triggered reviewer rules: R1, R2, R3, R5, R10, R11, R14.

Reachability proof: `python3 -m unittest tests.test_contracts` loads every
indexed fixture through its versioned schema and, after schema admission, calls
the shared semantic checker. A zero-failure run proves the executable contract
rejects each negative fixture and preserves every positive fixture.

## Mechanism

Each error schema gains a conditional rule: when `error.code` is
`PROVIDER_BUSY`, `error.retryable` must be the constant `true`. Registration
patterns use an actual end-of-input assertion after the existing canonical URL
grammar. The semantic checker rejects raw control code points before calling
`urlsplit`, then validates the parsed port for both versions. Indexed fixtures
exercise the portable public contract, while focused unit cases probe all
boundaries and both error directions.

## Intentional

- V1 receives only rejecting-side corrections for documents that violate the
  already accepted ADR semantics; no valid v1 wire shape changes.
- The repository remains language-neutral and ships no runtime validator.
  Schemas, fixtures, and normative guidance remain the integration surface.
- Retryability for codes other than `PROVIDER_BUSY` remains explicit and
  unconstrained because no canonical policy couples those codes.

## Deferred

Parking predicate: changes inside application repositories, alternative
transports, new error-code policies, and broader URL canonicalization are
parked unless this contract correction cannot be exercised without them.

Parked hardening: downstream application conformance updates remain separate
per-repository slices if their current implementations fail the new fixtures.

## Verification

- `python3 -m unittest tests.test_contracts` -- 8 tests, OK.
- `python3 -m unittest` -- 24 tests, OK.
- `python3 -m pytest -q` -- 24 passed and 159 subtests passed.
- JSON parse sweep -- 64 schema and fixture files parsed.
- Node registration-regex boundary probe -- 16 cases passed.
- `ruff check tests/test_contracts.py` -- all checks passed.
- `git diff --check` -- clean.

## Estimated diff size

Actual before commit: 14 files, +371 / -27 (398 total changed lines), including
143 plan lines and 228 non-plan additions; below the 400 LOC soft cap.
