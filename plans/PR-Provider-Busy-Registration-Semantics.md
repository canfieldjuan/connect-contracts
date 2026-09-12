# Enforce PROVIDER_BUSY and registration URL semantics

## Why this slice exists

Release-blocker issue #10 found three admission gaps in the executable Connect
contracts: both error schemas admit `PROVIDER_BUSY` with `retryable: false`, v1
lacks v2's TCP port-range semantic check, and the registration URL regex accepts
a terminal line feed under validators whose `$` anchor matches before that
character. Exact-head review also found the same error code admitted inside a
failed job status even though ADR-0006 defines it as a pre-admission refusal.

### Problem-derived contract

Root cause: error semantics are duplicated across standalone HTTP errors and
nested job-status errors without one disposition for the pre-admission-only
busy code. Registration admission also relies partly on a regex and partly on a
v2-only parsed-URL check, after a parser may normalize control characters.

The correct fix must:

1. couple the `PROVIDER_BUSY` code to `retryable: true` in both versioned error
   schemas;
2. reject `PROVIDER_BUSY` from failed job-status errors because such a job was
   already admitted;
3. inspect raw registration URLs for controls before parsing and apply the same
   TCP port-range semantics to v1 and v2;
4. make the schema's end-of-string admission independent of `$`'s terminal-LF
   behavior;
5. add positive and negative executable contract evidence for both protocol
   versions; and
6. tell downstream implementations which checks remain semantic obligations
   beyond JSON Schema validation.

The fix must not change the accepted exact-loopback URL shapes, couple generic
error codes to a retry policy, change routes or wire fields, add an executable
runtime library, or modify any application repository.

### Closure declarations

- Busy-policy code set: **CLOSED**, **ENUMERATED** from ADR-0006's sole
  pre-admission busy code, `PROVIDER_BUSY`. Other codes retain their declared
  retryability. Standalone HTTP errors require it to be retryable; job-status
  errors reject it because admission has already happened. An unknown or future
  code receives no implicit busy semantics.
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

1. Tighten v1 and v2 standalone and nested error schemas plus registration
   schemas without changing any valid fixture.
2. Extend the shared conformance semantic path to both protocol versions.
3. Add indexed invalid fixtures and boundary-focused tests.
4. Document the runtime checks every downstream implementation must perform.

### Files touched

- `schemas/v{1,2}/{error,job-status,registration}.schema.json`
- `fixtures/v{1,2}/index.json` and focused fixtures under each `invalid/`
- `tests/test_contracts.py`
- `README.md`
- `plans/PR-Provider-Busy-Registration-Semantics.md`

### Review Contract

Acceptance criteria:

1. Both error schemas reject an indexed `PROVIDER_BUSY` fixture whose
   `retryable` field is false and continue accepting the existing true fixture,
   settled by `python3 -m unittest tests.test_contracts`.
2. Both job-status schemas reject `PROVIDER_BUSY` for either retryable value,
   while their existing non-busy failed-job fixtures remain valid.
3. `semantic_errors()` applies raw-control and numeric port checks to v1 and v2;
   direct boundary tests cover port 1, 65535, 0, and 65536 plus terminal and
   embedded controls.
4. The registration schemas reject terminal-LF inputs without depending on a
   validator-specific `$` interpretation, settled by the indexed fixtures and
   the Python conformance suite.
5. Every new negative member is indexed for both versions, while all existing
   exact-loopback valid fixtures remain green in the full suite.
6. README conformance guidance identifies raw-control rejection and numeric
   port validation as runtime obligations that occur before parser
   normalization.

Affected surfaces: v1/v2 standalone and job-status error schemas, v1/v2
registration schemas, executable fixtures, semantic tests, downstream guidance.

Risk areas: cross-validator regex behavior, frozen-v1 compatibility, error
retry semantics, parser normalization, boundary completeness.

Triggered reviewer rules: R1, R2, R3, R5, R10, R11, R14.

Reachability proof: `python3 -m unittest tests.test_contracts` loads every
indexed fixture through its versioned schema and, after schema admission, calls
the shared semantic checker. A zero-failure run proves the executable contract
rejects each negative fixture and preserves every positive fixture.

## Mechanism

Each error schema gains a conditional rule: when `error.code` is
`PROVIDER_BUSY`, `error.retryable` must be the constant `true`; each job-status
schema rejects that pre-admission-only code. Registration patterns use an actual
end-of-input assertion after the existing canonical URL grammar. The semantic
checker rejects raw controls before `urlsplit`, then validates the parsed port
for both versions. Fixtures and focused tests probe both error directions.

## Intentional

- V1 receives only rejecting-side corrections for documents that violate the
  already accepted ADR semantics; no valid v1 wire shape changes.
- The repository remains language-neutral and ships no runtime validator.
  Schemas, fixtures, and normative guidance remain the integration surface.
- Retryability for codes other than `PROVIDER_BUSY` remains explicit and
  unconstrained because no canonical policy couples those codes.
- A failed job status cannot use `PROVIDER_BUSY`; ADR-0006 reserves it for a
  request the provider did not admit.

## Deferred

Parking predicate: changes inside application repositories, alternative
transports, new error-code policies, and broader URL canonicalization are
parked unless this contract correction cannot be exercised without them.

Parked hardening: downstream application conformance updates remain separate
per-repository slices if their current implementations fail the new fixtures.

## Verification

- `python3 -m unittest tests.test_contracts` -- 9 tests, OK.
- `python3 -m unittest` -- 25 tests, OK.
- `python3 -m pytest -q` -- 25 passed and 165 subtests passed.
- JSON parse sweep -- 66 schema and fixture files parsed.
- Node registration-regex boundary probe -- 16 cases passed.
- `ruff check tests/test_contracts.py` -- all checks passed.
- `git diff --check` -- clean.

## Estimated diff size

Actual after review: 18 files, +469 / -28 (497 changed lines), including 152
plan lines and 317 non-plan additions. The indivisible root class spans both
error shapes, both protocol versions, indexed fixtures, and shared tests.
