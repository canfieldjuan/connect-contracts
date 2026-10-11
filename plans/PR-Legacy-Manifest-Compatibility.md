# Legacy manifest compatibility amendment proposal

Status: PROPOSED, separately reviewed shared-contract amendment. No protocol change is accepted, no executable schema/fixture/runtime changes are made, and no merge or implementation is authorized.

## Root cause and evidence

The landed ADR0013:47-53 at8a9a44c5d4a040c75849a93ded82e6c98ff242e9 requires every response to emit no-store plus feature Vary. The shared exchange oracle applies those producer requirements as consumer admission requirements even when acknowledgment is absent. Dependency PR2's matrix inherits this rule, so opting in can lose otherwise compatible invoice/certificate discovery from a provider lacking feature Vary.

Actual checked source: frozen Invoice Processor62d7b4d85cc1947626f77f4a5a65ebdbe4829281, connect/server.py:427, and primary8efb0ccf68b9a1836748ed502b860e63f5e5cd88:429 send Cache-Control:no-store. No feature acknowledgment/Vary handling was found in their connect source. The claim that these revisions lack no-store is contradicted; arbitrary installed historical versions were not examined. Connect-automate d68b25f discovery performs fresh streamed authenticated GET and strict legacy decoding (:1193-1214); no manifest cache is present there.

The compatible legacy response does not advertise classifier identity. Losing invoice.extract/certificate.extract is a provider-wide compatibility failure, not a reason to invent document.classify identity. ADR0013's unchanged missing-ack fallback and existing idempotency owners still apply.

## Wire-observable policy proposed at the canonical owner

Amend ADR0013's Negotiated manifest section at its freshness definition; do not add a consumer-side exception while the landed rule remains in force. Exact proposed replacement for the freshness paragraph:

> Feature-aware providers MUST emit Cache-Control:no-store and Vary:Local-Connect-Manifest-Features on both legacy and negotiated manifest responses, preserving other Vary fields. Consumers never store or reuse manifest responses; every discovery and rediscovery uses a fresh authenticated response bound to the registration's app and instance.
>
> An exactly requested and exactly acknowledged negotiated response MUST satisfy both freshness headers and the extended schema. Missing or invalid freshness headers reject that response. Wrong, malformed, ambiguous or unsolicited acknowledgment rejects negotiation; it is not treated as an absent acknowledgment.
>
> A genuinely absent acknowledgment selects the strict legacy decoder. Consumer admission of that legacy response does not require freshness headers to exist: absent Cache-Control is permitted; if Cache-Control is present it must contain a valid no-store directive. Explicit storage/reuse directives without no-store, including max-age or s-maxage, are incompatible. A present malformed freshness header is rejected. Legacy Vary may be absent or may omit the feature member; this does not authorize storage or reuse. Authentication, registration attribution, bounded duplicate-safe parsing and strict legacy body validation remain mandatory. Fixed-identity capabilities are unavailable, document.classify is not exposed, and fixed identity is never synthesized or replaced with editable parameters. Compatible invoice.extract and certificate.extract remain usable.
>
> An unacknowledged provider that predates the feature and a feature-aware provider that declines it are not distinguishable by these headers. The consumer uses the same legacy admission policy for both, without inferring support from app names, versions, labels or installation history. A feature-aware producer still owes the response-header requirements above; failure of that producer's emission conformance does not by itself remove compatible legacy capabilities from a direct-read consumer.

Valid no-store retains its HTTP precedence over storage directives; mixed headers are not a licence to reuse a response. Header parser obligations reuse canonical HTTP semantics and reject duplicate/ambiguous negotiation or malformed values. No new support marker, registration field, extra network route or app-version heuristic is introduced.

## Required change surface

After separate acceptance, update ADR0013 at its owning definition, feature fixture-context documentation, and shared exchange schema/oracle/tests as required to distinguish the obligation under test. Existing producer-conformance fixtures retain their meaning; new consumer-admission fixtures specify observable legacy compatibility. Fixture context may name producer-conformance versus consumer-admission; this is test metadata, not a new wire field or inferred server generation. One exchange policy owner must compose existing bounded header/schema/context validation; do not add a later filter that makes invalid extended discovery usable.

Existing exchange-reject-legacy-no-store-missing (Cache-Control:max-age=60) remains a producer rejection and also rejects consumer reuse policy. Existing exchange-reject-legacy-vary-missing remains a producer-conformance rejection; a new consumer case with valid no-store but missing feature Vary is accepted under the proposed legacy policy. This distinction is explicit; do not silently change old fixture interpretation or claim current artifacts already prove the proposal.

Connect-automate PR2 must then adopt the accepted revised shared pin and retain compatible legacy DTOs for invoice/certificate while classifier discovery remains unavailable. Provider and Watcher declarations reconcile separately; no frozen app head is edited by this proposal.

## Explicit non-scope

No current ADR/schema/oracle/fixture mutation, dependency implementation, provider or Watcher runtime adoption, manifest cache, classifier/model/OCR work, immutable-request/digest change, stored-job migration, entitlement bypass, fallback from bad acknowledgments or malformed extended bodies, deployment or merge authority. Existing identity and replay semantics remain settled.

## Assumptions and blockers

Oversight proposed retaining compatible advertised legacy invoice/certificate capabilities during opted-in discovery. Exact-wording operator acceptance of this shared policy is pending. Provider concurrence is review evidence, not that acceptance or unilateral consumer permission. Both owners and shared review must accept exact wording and executable contract vectors before dependency implementation. The new producer/consumer distinction must not be guessed from an unacknowledged wire response. Historical absence of all freshness headers is a synthetic version-skew test, not a verified deployed-build claim.

## Verification contract and mutation proposal

Record immutable baseline and revised pins, source/fixture hashes, exact validation role and fail-before/pass-after results when implementing the shared amendment. No test is run against an unimplemented proposal to claim success.

1. Opted-in request, no acknowledgment, no freshness headers: fresh authenticated strict legacy invoice/certificate accepted; classifier unavailable (synthetic old-provider case).
2. Actual source shape: no acknowledgment, no-store, no feature Vary: compatible legacy accepted. Wrong app/instance or invalid legacy body still rejects.
3. Feature-aware producer deliberately declines: producer emission must include freshness; consumer sees the same unacknowledged legacy rules. Do not pretend it can distinguish feature knowledge.
4. Negotiated acknowledgment: both freshness headers required; empty/malformed/missing headers reject. Exact token plus valid extended body succeeds. Wrong/duplicate/malformed/unsolicited acknowledgments reject rather than falling back.
5. Legacy Cache-Control:max-age=60 without no-store rejects; absent Cache-Control is distinct. no-store is not defeated by an extra cache hint and never permits reuse. Malformed present cache/Vary values reject.
6. Both request orders and rotate-then-rediscover issue fresh direct reads. A stale stored response is rejected in every role. Retain older accepted immutable job bytes; no rebinding or digest normalization.
7. Functional consumer boundary: selecting compatible legacy invoice.extract/certificate.extract still constructs and hands off bounded selected artifacts under existing entitlements/confirmation; attempting classifier selection without acknowledged fixed identity cannot dispatch. Schema-only catalog assertions do not prove usability.
8. Mutations: apply producer-only Vary requirement to all legacy consumers (valid legacy lost); let negotiated response bypass freshness (bad negotiated accepted); treat absent ack as malformed or malformed ack as absent; expose classifier/editable identity in legacy; reuse response; ignore conflicting cache directive; rewrite saved request. Detect each at the correct owner.

## Implementation summary

None. This PR adds one proposal document only. Accepted ADR0013 and current fixtures remain unchanged until a separate accepted amendment implementation.

## Cold diff audit

Only this planning document is new. The response definition is proposed for its one canonical owner; dependency plans link here rather than inventing a conflicting local rule. No code tests are rerun for this documentation-only proposal; current shared tests cannot prove a rule they do not implement.

## Gap audit

NOT DONE: shared/owner acceptance of this wording; revised executable shared vectors and independent review; dependency plan adoption; provider/Watcher separate acceptance AND builds; any application implementation or merge. Existing connect-automate restoration finding is a separate dependency-plan blocker and is not resolved by this proposal. All three adoption surfaces must be accepted AND built before checking-pipeline work.
