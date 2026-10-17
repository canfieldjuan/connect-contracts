# ADR-0014: Invoice amount-due capability version agreement

**Status:** Accepted; contract only. Juan: **"Accept (Recommended)"**, relayed
verbatim by oversight in mail `2caefb53` and [acceptance comment
6228607997](https://github.com/canfieldjuan/connect-contracts/pull/69#issuecomment-6228607997).
Accepted text: `694faaa17076fe819653b7b419380b3b6afbe6c5`. The selected option:
"The agreement is accepted as written; the invoice processor continues its
offline build, and nothing switches over until the Email Watcher follow-up
(#278) is also done and tested." This document does not activate a provider
or consumer cutover. Exact-head oversight review remains a separate merge gate.

**Date:** 2026-10-17

## Problem and ownership

Invoice Processor's single total role cannot faithfully represent both current
charges and the amount still payable after previous balances, payments, deposits
and credits. Its accepted [AMOUNT-DUE revision 2 + R1][amount-due] assigns those
roles to InvoiceRecord 2.0 and changes the record shape. Publishing that shape
under the existing capability identity would silently change a consumer's
contract. The record semantics remain owned by Invoice Processor, not copied
into this generic transport repository.

The operator authorized this contract-only agreement through oversight, verbatim
"Go ahead (Recommended)": "IP session drafts the connect-contracts agreement PR
(contract only); I file the Email Watcher follow-up issue, scheduled after #261.
Nothing switches over until both are agreed and tested."
This authorizes drafting, not acceptance of this ADR or implementation elsewhere.

## Existing canonical contract: no schema or registry change needed

Inspected base: `0f77f8a77e6fb014f0d563645ebdbb83ce6dbc3b`.

- [ADR-0002](0002-connect-v2-generic-capabilities.md), Generic capability
  declarations and Compatibility and matching, already gives each capability
  an independent `major.minor` version and requires request/declaration matching.
- [Manifest](../schemas/v2/manifest.schema.json) and
  [request](../schemas/v2/job-request.schema.json) schemas both admit version
  strings such as `2.0`. Neither enumerates invoice capability versions.
- The existing [unsupported-version fixture][unsupported] is schema-valid but
  invalid against its selected provider declaration. The context validator
  `tests/test_contracts.py::_job_request_errors` matches the entire `(id, version)`
  pair; a protocol/schema parse alone is not admission.
- Generic output artifacts carry integrity-checked bytes; there is no canonical
  InvoiceRecord JSON schema or invoice-version registry here. Existing invoice
  entries in fixed-parameter fixtures are synthetic conformance examples, not
  a registry that must be rewritten for every product upgrade.

**No canonical JSON schema, registry, executable code or fixture change is
needed for this identity agreement.** This ADR and its index entry are the
entire change. It does not claim that an installed SDK or consumer has passed
cutover qualification. If a decoder change is discovered, report it to its
owner; this agreement does not authorize an SDK patch.

## Proposed identity and breaking-change rule

| Layer | Identity after the separately gated cutover |
| --- | --- |
| Connect wire protocol | `2`, unchanged |
| Provider app | `invoice-processor`, unchanged |
| Invoice capability | `invoice.extract`, version `2.0` |
| Invoice JSON payload | `record_version: "2.0"` |
| Invoice JSON media type | `application/vnd.local-connect.invoice+json`, unchanged |
| Certificate capability | `certificate.extract`, version `1.0`, unchanged |

The invoice payload and financial-role invariants are defined once by
[AMOUNT-DUE AD-1 through AD-5][amount-due]. There is no lossy 1.0 adapter: current
charges must never be renamed as payable to satisfy an old reader. A newly
executed 2.0 extraction must not be returned under a 1.0 capability promise.
The payload's version must match the agreed record contract; the media type
alone does not distinguish historical from new records.

This does not activate Invoice Processor's separate classifier/fixed-parameter
proposal, change the model/runtime profile or add a Connect wire version.

## New admission, recorded replay and retained work

Authentication, entitlement, bounded parsing, artifact integrity and provider
instance attribution remain mandatory. The durable job owner distinguishes
recorded work from work that would execute, preserving [ADR-0002][jobs] and
[ADR-0013's admission/replay ordering][replay].

- A **new** `invoice.extract` 1.0 submission to a provider admitting only 2.0
  receives the existing unsupported-capability refusal; it is not translated
  or silently resubmitted as 2.0. For Invoice Processor this is HTTP 400,
  `UNSUPPORTED_CAPABILITY`, `retryable: false`, in the existing v2 error envelope
  ([provider code/flag owner][errors]). The generic invalid fixture establishes
  version rejection, not a new global HTTP error enum.
- An identical **completed** 1.0 request returns its retained job identity and
  original artifact bytes, sizes and hashes, with its original capability and
  record identities. No re-extraction, record rewriting or migration of those
  artifact bytes occurs. Existing result-retention/purge rules still apply.
- A consumer verifies a retained outcome against its recorded admission
  identity, not a substituted current 2.0 declaration. The canonical
  `_job_status_errors` comparison intentionally rejects a status paired with
  the wrong manifest; do not weaken it to make old/new identities match.
  The consumer/provider proof must show how the recorded context is retained
  across reopening and rediscovery.
- Changed immutable request data under an existing job identity remains a
  conflict. A failed-job restart that would execute is new execution and must
  satisfy current admission. Accepted queued/running work must retain its
  admitted semantics; an upgrade must not execute it using the new record
  contract. Cutover must settle this at the provider lifecycle/job owner.

A stale saved selection is an explicit consumer refusal/reselection case, not
permission to rewrite a queued request, job identity or selected version.
Visible recovery requires selecting a currently compatible capability. Completed
historical output remains readable/exportable under its original identity.

## Certificate isolation

Certificate capability identity, prompt, schema, output fields and provenance
remain unchanged. Invoice Processor remains Email Watcher's certificate
provider. Invoice Processor's standing same-input COI gate applies to its
implementation; this contract-only PR does not substitute a schema check for
that runtime proof.

## Owners, evidence and landing order

1. Review this draft agreement and obtain explicit operator acceptance. Record
   the accepted exact head; no boundary implementation before acceptance.
2. Email Watcher's owner handles [issue #278][watcher], scheduled after #261:
   visible saved-selection refusal/reselection, retained completed-output
   replay, version-preserving decoder proof and planned-adoption documentation.
   No Email Watcher edits belong to this PR. Acceptance and testing of that
   consumer work remain a separate cutover prerequisite.
3. Invoice Processor implements [PR #178][invoice-pr] at its existing owners,
   preserving immutable historical records and completed jobs. Its real-HTTP
   tests must cover old/new requests, wrong record identities, changed-request
   conflicts, restart/replay and accepted work at upgrade. All failure paths
   retain their existing auth/integrity gates.
4. Run the accepted Invoice Processor offline, migration, mutation, native/UI
   and COI parity gates with frozen inputs and approved budget. No live call,
   consumer cutover or boundary merge before both owner agreements and their
   prerequisite tests. Installation/promotion is a later decision.

### Verification and limits

For this text-only PR, inspect the schema and context-validator owners and run
an offline in-memory identity probe: matching 2.0 declaration/request accepted;
old 1.0 request against that declaration rejected; the existing unsupported
fixture remains rejected; recorded 1.0 status validates only with its recorded
1.0 context. The probe is an audit of existing generic conformance, not a live
provider or SDK proof. Check relative links and `git diff --check`; verify the
diff contains only this ADR and the README index. No broad runtime suite is
justified by text-only changes.

**Gap audit: NOT DONE.** Canonical agreement acceptance, consumer agreement and
product implementation/qualification are pending. No product is installed,
promoted or qualified by this proposal.

[amount-due]: https://github.com/canfieldjuan/invoice-processor/blob/a48dd72a416841f90ef424c31b8909b890cf4ba0/docs/contracts/AMOUNT-DUE.md
[unsupported]: ../fixtures/v2/invalid/job-request-unsupported-capability-version.json
[jobs]: 0002-connect-v2-generic-capabilities.md#jobs-and-artifacts
[replay]: 0013-fixed-compatibility-parameters.md#admission-refusal-and-replay
[errors]: https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/connect/errors.py#L52-L58
[watcher]: https://github.com/canfieldjuan/eom-email-watcher/issues/278
[invoice-pr]: https://github.com/canfieldjuan/invoice-processor/pull/178
