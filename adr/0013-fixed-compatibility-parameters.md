# ADR-0013: negotiated fixed compatibility parameters

**Status:** Proposed

**Date:** 2026-10-10

## Context and scope

A capability version describes an interface, not the provider's changing
classification decision bundle. Email Watcher #231 and Invoice Processor #140
require a bundle identity before dispatch. Their accepted agreement direction
is Email Watcher #236, canonical issue-body UTF-8 SHA256
`6209b41e31a598388d7f9829bd134b259269a4cc349b21fbf19df84527e411a0`.

ADR-0002's manifest names parameter types but cannot advertise fixed values.
Its closed schema and deployed strict readers reject an added field. Extending
the default manifest would hide existing invoice/certificate capabilities.
This ADR owns negotiation, fixed-parameter semantics and admission refusal.
Application selection, consent, entitlement, queue and classification rules
remain their existing owners. No application implementation is included.

## Negotiated manifest

An authenticated consumer requests the exact feature token
`fixed-parameters-v1` in `Local-Connect-Manifest-Features` on
`GET /v2/manifest`. HTTP header names are case-insensitive; this feature token
is case-sensitive. This revision negotiates that one token, not arbitrary
feature lists. Absent, unsupported or different tokens receive the legacy
manifest without the response feature header.

A supporting provider acknowledges the feature with the same response header
and token and returns the negotiated manifest. Only a response with that
acknowledgment is decoded under the extended manifest schema. An unacknowledged
response uses the legacy decoder. Both responses remain authenticated and
bound to the registration's app and durable instance identity.

The default v2 manifest schema and its existing fixtures stay byte-identical.
The extended schema will have its own identifier and fixture family under
`schemas/v2/features/fixed-parameters-v1/` and
`fixtures/v2/features/fixed-parameters-v1/`. It adds only the parameter
member defined below; all existing closed-object and contextual rules remain.
The legacy response omits capabilities that require fixed identity. For this
slice it omits `document.classify`, while retaining the existing invoice and
certificate declarations. It must not publish classifier parameters as
editable substitutes in that response.

No v1/v3 schema, route, registration, entitlement or artifact format changes.
Feature-aware providers MUST emit Cache-Control:no-store and Vary:Local-Connect-
Manifest-Features on both legacy and negotiated manifest responses, preserving other
Vary fields. Consumers never store or reuse manifest responses; every discovery and
rediscovery uses a fresh authenticated response bound to the registration's app and
instance.

An exactly requested and exactly acknowledged negotiated response MUST satisfy both
freshness headers and the extended schema. Missing or invalid freshness headers reject
that response. Wrong, malformed, ambiguous or unsolicited acknowledgment rejects
negotiation; it is not treated as an absent acknowledgment.

A genuinely absent acknowledgment selects the strict legacy decoder. Consumer admission
of that legacy response does not require freshness headers to exist: absent Cache-
Control is permitted; if Cache-Control is present it must contain a valid no-store
directive. Explicit storage/reuse directives without no-store, including max-age or
s-maxage, are incompatible. A present malformed freshness header is rejected. Legacy
Vary may be absent or may omit the feature member; this does not authorize storage or
reuse. Authentication, registration attribution, bounded duplicate-safe parsing and
strict legacy body validation remain mandatory. Fixed-identity capabilities are
unavailable, document.classify is not exposed, and fixed identity is never synthesized
or replaced with editable parameters. Compatible invoice.extract and certificate.extract
remain usable.

An unacknowledged provider that predates the feature and a feature-aware provider that
declines it are not distinguishable by these headers. The consumer uses the same legacy
admission policy for both, without inferring support from app names, versions, labels or
installation history. A feature-aware producer still owes the response-header
requirements above; failure of that producer's emission conformance does not by itself
remove compatible legacy capabilities from a direct-read consumer.

## Fixed parameter owner

A parameter declaration may include `fixed_value`. Its presence requires
`required=true`. The value has exactly the declared string/integer/boolean
type and the existing request-parameter bounds from ADR-0002 and
`schemas/v2/job-request.schema.json`. JSON integers include mathematically
integral numeric forms; booleans are not integers. Numeric equality is used
only within the integer type: false never equals zero.

Presence, not truthiness, decides whether a value is fixed. Empty strings,
zero and false remain admitted values when they satisfy the declared type.
Null, arrays, objects and out-of-bound values are invalid. No fixed value
means the existing user-supplied parameter behavior.

One declaration supplies advertisement, consumer public DTO, request
validation and provider admission. Consumers copy fixed values into the
immutable request and never prompt for them. Missing or conflicting caller
values cannot silently override the declaration; a request builder may fill
an omitted fixed value from the explicitly selected declaration before
freezing the request. Once frozen, the request contains every required value
and is never rewritten because discovery changes.

For `document.classify` 1.0, the two required string parameters are
`record-version` fixed to `1.0`, and `classifier-version` fixed to the
provider's admitted lowercase 64-hex decision-bundle SHA256. The bundle
composition and classifier id are owned by the pinned provider contract in
Invoice Processor #140, not by this ADR. Labels, descriptions, app version
and filenames are never compatibility identity.

## Admission, refusal and replay

Authentication, authorization, bounded parsing and request/artifact integrity
still apply to every request. Durable job identity decides whether a request
would start work before current fixed-value equality is imposed:

- An identical already accepted, running or completed request returns its
  recorded job identity/outcome after a provider upgrade. It is checked
  against its recorded admission identity, never rebound to the new bundle.
- Reusing an existing job id with a different immutable request remains
  `JOB_CONFLICT` under the existing idempotency owner.
- A new submission, or a failed-job restart that would execute, must match the
  currently admitted fixed declaration. The durable admission owner performs
  this check atomically with deciding and recording that execution. Bundle
  replacement uses the same serialization boundary. Advisory preflight cannot
  override a valid recorded replay or authorize work across a bundle change.
- Work that was accepted retains the immutable bundle it was admitted under;
  execution cannot substitute the newly advertised bundle. The provider owns
  that bundle's availability for its accepted work.

A fixed-value mismatch that would start work returns HTTP 409 and the existing
v2 error envelope with `code=FIXED_PARAMETER_MISMATCH` and `retryable=false`.
No job is accepted, no classification executes, and no permanent document
result is fabricated. The message is descriptive, not a machine-parsed field.
`retryable=false` forbids blindly repeating the same immutable request.
Mismatch recovery immediately rediscovers the current bundle under the
negotiated-manifest response rule above, even after bundle rotation. Explicit
selection of compatible identity may authorize a new attempt; this does not
mutate the refused request or an owned job.

Email Watcher's classifier integration maps this code to `deferred`
(`classifier_bundle_unavailable`) until an admitted bundle is selected.
That mapping requires a separately reviewed amendment to #231 I-state; the
accepted head is not silently edited. Other consumers own their compatible
rediscovery policy rather than repeatedly retrying the old request.

## Required fixtures and evidence

Before application implementation, the shared schema/fixture follow-up must
cover legacy discovery and acknowledged extended discovery, unsupported
feature fallback, unknown-member rejection, missing acknowledgment, required
fixed values, mismatched types, false versus zero, empty string, integer and
string limits, missing/conflicting frozen request values, and the exact
HTTP refusal envelope. Response fixtures check both required headers on
both legacy and negotiated variants, including preservation of existing Vary
fields. Cache fixtures cover both orders (negotiated then legacy, and legacy
then negotiated) and bundle rotation followed by mismatch recovery and immediate
rediscovery, using the negotiated-manifest response rule above. Neither request
order permits reuse of a manifest response, and recovery observes the current
bundle without a cache-expiry window.

Contextual admission vectors must distinguish prepared old bundle/new POST,
accepted old-bundle replay, changed-request conflict, failed old-bundle
restart, and bundle rotation concurrent with admission. Provider and consumer
replay the same fixtures through their own owners; test artifacts name the
exact shared and application revisions. No production/concurrency effect is
proven by a schema-only check.

Existing shape evidence at provider `62d7b4d` and consumer `1386e6f` accepted
19 valid and rejected 20 invalid canonical shapes, with four mutation oracles.
The provider independently reproduced that replay. This is evidence for the
existing request/result agreement, not for this negotiation implementation.

## Landing order and gaps

1. Review and accept this ADR, including shared refusal and replay semantics.
2. Land its negotiated schema and shared conformance fixtures in a separate
   shared-contract commit/PR, with legacy schemas preserved.
3. Review the provider and consumer declarations together against that pin,
   including the separately reviewed #231 refusal-mapping amendment.
4. Accept each owner's implementation slice before application code; prove
   discovery, admission/replay and concurrency effects at their source owners.

**NOT DONE:** negotiated schemas/fixtures, joint declaration review and
application implementation/runtime proof. This PR is the shared agreement
text only. The operator's no-code-before-agreement gate remains in effect.
