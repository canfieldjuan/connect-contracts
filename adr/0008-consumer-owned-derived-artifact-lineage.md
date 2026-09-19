# ADR-0008: Consumer-owned derived artifact lineage

**Status:** Proposed

**Date:** 2026-09-17

**Decider:** Pending

## Context

Connect v2 identifies one submitted input and every completed output, but it does
not link an output to a later job that consumes those bytes. An automatic OCR to
analysis path therefore needs durable causal identity and replay behavior across
two otherwise independent jobs.

Adding `derived_from` to a v2 request or status would break existing strict v2
decoders even if the field were optional. The downstream provider also does not
need ancestry to process the immediate artifact: its request already carries the
selected capability, artifact identity, media type, size, digest, source
application, parameters, and exact bytes.

The consumer selects providers, admits user-initiated and automatic work,
retains job records, and reconciles uncertain submissions. It is therefore the
authority that can record the relationship without changing the provider wire
protocol or introducing a shared runtime.

## Decision

### Consumer-owned lineage edge

Connect v2 remains unchanged. A consumer that submits one retained provider
output as another job's input, through either a user-initiated in-app action or
automatic execution, stores a durable, application-private lineage edge before
the downstream submission.

The logical edge identifies:

- the consumer's immutable execution or admission identity;
- the producer provider app and durable instance, producer job, and selected
  output artifact;
- the downstream provider app and durable instance and downstream job; and
- creation time.

Provider, capability, request, artifact, and integrity metadata may remain in
the referenced durable job records instead of being duplicated in the edge.
The complete logical identity must still be recoverable after restart. A bare
job ID or bare output artifact ID is insufficient because job ownership is
provider-instance scoped and output identity is unique only within one
completed job.

Each downstream job has exactly one parent edge. Repeating the same admitted
execution step resolves to the same downstream job and edge. Reusing that
identity with a different producer output, downstream provider app or durable
instance, capability, parameters, source application, or input integrity
metadata is a conflict.

### Admission and integrity

The consumer selects the retained completed producer row and output, validates
the producer status against its saved request and selected provider, proves the
output exists exactly once, and validates its bytes inside the same
deletion-excluding transaction or critical section that admits the downstream
step. The downstream request reuses that output's artifact ID, and its input
media type, decoded byte size, SHA-256 digest, and bytes exactly match the
output. Missing, malformed, ambiguous, or conflicting producer state fails
before any downstream network request.

That admission atomically persists the lineage edge, the exact downstream
request and stable job identity, its dispatch record, and exactly one durable
recovery source before `POST /v2/jobs`. The recovery source is either the
existing producer-output payload protected transactionally from deletion or a
bounded owner-private child snapshot of the selected bytes; a consumer does not
retain both for the same downstream step. Deletion and admission use the same
serialization boundary: if deletion commits first, no descendant is admitted;
if admission commits first, deletion preserves the lineage, metadata, and the
selected recovery source. The recovery bytes are read back and revalidated
before every first submission or replay. The original root artifact and
producer job remain the audit identity; a child snapshot is a recovery copy,
not a new source.

The selected recovery source remains available until downstream admission is
impossible or all uncertainty and replay have reached a terminal result.
Deleting a source message, file, rule, or completed producer row cannot remove
bytes or metadata needed by an admitted or replayable descendant. After
terminal settlement, the consumer may remove payload bytes under its retention
policy but retains the lineage edge and integrity metadata needed to audit the
chain. Referenced producer, downstream, and root-input identity records remain
while the edge remains, or are compacted atomically into an equivalent immutable
lineage record before their job rows are removed.

### Crash and control behavior

A crash before the admission transaction commits creates no downstream job. A
crash after commit recovers the same exact request, bytes, job identity, and
edge. When provider acceptance is uncertain, the consumer reconciles status
against the edge's immutable downstream provider instance before replay and
relies on that instance's existing v2 same-request idempotency rule. It never
submits that job or edge to a replacement instance when the selected instance
is missing or unreachable; uncertainty remains durable rather than creating a
second owner. It never reruns the producer under the old edge to replace missing
or corrupt bytes.

Disabling or deleting the rule prevents creation of a downstream step that has
not yet been admitted. Once a provider may own the downstream job, the consumer
retains and reconciles it to a terminal result; rule deletion does not turn
uncertain provider-owned work into a fresh submission or erase its audit edge.

### Source application and provider knowledge

`source_app_id` continues to name the immediate consumer submitting each v2
job. It is fixed by that consumer, not copied from the producer output or
accepted from a caller, rule, or imported lineage record. The same consumer
therefore uses the same value across a derived handoff, and a persisted mismatch
fails before network activity. Providers treat it only as unauthenticated
attribution; authorization and entitlement never depend on it.
The downstream request preserves the selected output's exact media type. A
versioned capability profile may reserve a distinct media type to tell the
downstream provider the immediate transform or source class it must record. For
example, an OCR profile can emit `application/vnd.local-connect.ocr-pdf`; a
provider that explicitly accepts it records OCR-derived input instead of native
PDF text. Substituting `application/pdf` would be an integrity conflict, not a
compatibility fallback.

That media type is not ancestry. The downstream provider is not told the root
document, producer job, initiating action or automation rule, mailbox message,
or filesystem source, and provider behavior or entitlement must not depend on
that private history. The consumer-owned edge remains the authority that joins
the downstream record back to the exact producer output and root input.

A later use case that requires lineage to cross an independent consumer boundary
needs a new versioned wire contract. It must not extend strict v2 objects in
place.

### Explicit user import

A user may export an output and later select that file as a new root input. That
explicit import starts a new lineage root and does not claim a derived edge to
the earlier provider job. A direct in-app action on the retained output is a
derived handoff and uses the consumer-owned edge above.

## Required acceptance evidence

Each consumer that offers a derived handoff must prove these boundaries against
durable storage and a restarted process:

1. a valid completed output commits one edge, one exact downstream request, one
   dispatch, and exactly one durable recovery source before the first network
   request; both a protected existing payload and a child-owned snapshot are
   exercised when the consumer supports both choices;
2. crashes before and after admission produce zero or exactly one downstream
   job respectively;
3. a lost acknowledgement reconciles by status before same-identity replay and
   never creates a second provider job; when the selected instance disappears
   and a replacement instance appears, the old job remains pinned and no request
   using its identity or edge is sent to the replacement;
4. provider, job, output and input artifact, capability, parameter, media type,
   size, digest, byte, execution-identity, downstream app/instance, and
   `source_app_id` mismatches fail before network activity; caller-, rule-, and
   producer-supplied source application values are rejected, and a provider
   cannot use that field for authorization or entitlement;
5. missing or corrupt producer payload cannot be replaced by rerunning the
   producer under the old edge;
6. source or rule deletion cannot remove an admitted descendant's recovery bytes
   or audit edge, while no unadmitted descendant is created after disable;
   a concurrent deletion/admission race proves both outcomes, with deletion
   winning before admission producing no child and admission winning first
   retaining the exact lineage and bytes;
7. terminal payload cleanup retains enough edge and integrity metadata to trace
   the downstream job to the exact producer output and root input; and
8. strict current v2 request and status validators continue to reject an
   undeclared `derived_from` field; and
9. a profile-defined derived media type is preserved from producer output to
   downstream input, while substitution with its native media type fails before
   network activity and the downstream record uses the derived source class.

## Consequences

- OCR and later analysis remain separately attributable and independently
  idempotent without a v2 wire change.
- Every consumer that offers a derived handoff needs a durable lineage edge and
  exactly one bounded recovery source integrated with its existing job
  transaction.
- Providers remain unaware of consumer-local workflow, root source, and
  retention policy while a profile-defined media type may identify the immediate
  transform class they must record.
- A shared broker, shared private storage, and synchronized provider upgrades
  are not introduced.

## Deferred

- OCR capability behavior and deterministic OCR output selection;
- shared workflow or rule grammar;
- multi-input, multi-parent, branching, and join graphs;
- lineage transmitted between independent consumers;
- automatic scheduling, compensation, and user-facing graph visualization; and
- a later wire version if a provider must receive ancestry.
