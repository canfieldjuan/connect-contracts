# ADR-0006: Consumer-owned admission and the Automate feature

**Status:** Proposed (accepted when this decision merges)

**Date:** 2026-09-11

**Decider:** Juan Canfield

## Context

ADR-0001 states that Connect v0 "has no callback, queue, scheduler, or
automatic retry service. A provider processes at most one job at a time and
returns a retryable busy error for additional work." That sentence has been
read two ways: as "no one queues" and as "the provider does not queue". Only
the second reading was ever intended, and Email Watcher has since implemented
the first consumer-owned admission queue against the unchanged v2 wire
contract (its `docs/CONTRACTS.md`, durable provider-admission queue). Three
decisions that every future consumer needs now live only in that one
consumer's documentation.

Separately, the entitlement format (ADR-0003) types `features` as a bounded
list of pattern-matching strings and names exactly one feature,
`connect.capability_exchange`. Email Watcher enforces a second feature,
`connect.automations`, that no shared document defines. The offline issuer
validated features by pattern only, so a misspelled tier could be issued as a
valid licence that no application would honour. ADR-0004 also states that
"activation grants only `connect.capability_exchange`", which was true of
its scope and is no longer a complete description of what an installed
licence can carry.

## Decision

### Consumers own admission, ordering, and retry

ADR-0001's sentence is amended to: *v0 and v2 have no callback and no
provider-side queue, scheduler, or retry service; a provider processes at
most one job at a time and returns a retryable busy error for additional
work; the caller owns admission, ordering, and retry.* Direction is not
inverted: consumers poll and re-POST; providers never call back.

The normative consumer pattern is:

- one admission lane per `(protocol version, provider app id, provider
  instance id)`, shared by every capability that instance exposes, because
  capacity is a property of the provider process, not of a capability;
- `PROVIDER_BUSY` with `retryable: true` is an authoritative pre-admission
  refusal: the job was not accepted and may be resubmitted with the same
  `job_id`;
- `JOB_NOT_FOUND` proves non-retention only when the job has never returned
  authoritative `accepted` or `processing`; after acceptance it is
  contradictory evidence and the consumer reconciles rather than resubmits;
- a consumer's unattended trigger layer (rules, schedules) is consumer-local
  data and behaviour. It requires no protocol change, and a provider needs
  nothing beyond ADR-0002 to be used by it.

### The feature registry

`entitlements/v1/features.json` is the enumerated registry of feature
identifiers. Today it lists exactly:

- `connect.capability_exchange` (ADR-0003): discovery and invocation;
  enforced independently by consumers and providers.
- `connect.automations` (this decision): unattended automation in a consumer,
  meaning rule evaluation, admission of automation work, and its provider
  submission. It is additive to `connect.capability_exchange` and grants no
  discovery or invocation on its own. It is enforced by the consumer only:
  the wire deliberately carries no entitlement (ADR-0003), so no provider is
  expected to check it, and a provider cannot distinguish an automation job
  from a click.

The claims schema is unchanged. The registry is a vocabulary, not a schema
enum, so adding a feature is additive and does not invalidate installed
licences. The issuer refuses to issue a feature that is not registered. Every
conformance fixture licence uses only registered features, and a signed
fixture carrying both features exists so applications assert the second key
from the shared fixture instead of minting one locally.

ADR-0004's sentence "Activation grants only `connect.capability_exchange`" is
corrected to: *activation installs the licence's whole feature list; an
application honours the registered features it implements.* The activation
admission rule is unchanged: a candidate must be `active` for
`connect.capability_exchange` to be installed, so an automations-only licence
is not installable, which keeps the additive relationship.

## Rejected alternatives

### Enumerate features in the claims schema

Rejected because a schema enum would make every new feature a breaking
change to installed verifiers, which validate the claims document strictly.

### Provider-side enforcement of `connect.automations`

Rejected because it would require entitlement data on the wire, which
ADR-0003 rejects, and because the provider cannot tell an automation job
from an interactive one; the consumer that owns the trigger owns the gate.

### Provider-side queue

Rejected again: the provider contract refuses excess work by design and
assigns retry policy to the caller (ADR-0001, Invoice Processor's S5-JOB-2).

## Consequences

- Every consumer implementing a queue or an automation has one shared place
  to read the admission and feature rules.
- A misspelled feature cannot be issued.
- `connect.automations` is sellable as a named tier and testable from a
  shared fixture.
- Nothing about rules, events, or actions is added to this repository; the
  action vocabulary remains the v2 manifest.
