# Real-document offline preparation contract

## Authority and root cause

Status: PROPOSED contract, documentation only. Owner: connect-runtime for the isolated
adapter/transport, with Doc Sum's existing input/parser/store/validator owners retained.
Juan selected Doc Sum `e5000cf20fdd65d53804d17f93f6f7683e6e2aad` for this contract:

> Use e5000cf for the offline preparation contract and continue. Keep builds, OCR execution, model calls and production changes on hold.

The subsequent selection answer was “Select e5000cf for the contract”. These select
source, not this final contract revision or implementation/execution. Exact-head
oversight/connector review and Juan's exact-revision acceptance remain required.
Budgets are UNSET. No executable permission follows from acceptance or merge.

This extends [migration section B](PR-V1-Profile-Migration-Replay.md#b-scorer-environment-and-retained-answer-parity)
and preserves [CC112's identity contract](PR-Summary-Offline-Replay-Identity.md).
The archived C0/C1 adapter binds a synthetic case; replacing its PDF would bypass
case-specific identity/request assumptions. The missing proof is full real-document
preparation at the selected source, not an established production app defect.

Required documentation surface: this contract, its [source annex](PR-Real-Document-Offline-Preparation-Source.md)
and the migration pointer. No application, executable schema, fixture or test change
belongs in this PR. The annex inventories all tracked crate files and the complete
lockfile, plus the preparation call paths. It does not claim a compiled dependency
closure or that every inventoried function executes.

## Validated work to reuse

Reuse the accepted R2 real-document plan, its PDF/original-name binding and review
closures. Do not rebuild corpus inventories, rehash models or rerun spent packets.
Source/evidence aliases and hashes are in the annex; raw documents remain private.

- C0/C1 retain their archived source, binary, profiles, seeds, schemas and saved
  request/answer identities. Their unchanged saved answers do not establish human
  quality, changed-answer behavior, current-source parity or inference speed.
- The selected source is distinct from that archived crate. The annex lists every
  file-level difference, including store lifecycle and SQLite dependencies. Carry
  these as selected-source differences; do not port an older dependency to erase them.
- Reuse the corrected root-profile fixture from `c9-ocr-offline-admission-20261027`,
  independently reviewed by `df50d59a`. Its `qualification_profile` returns the
  existing test snapshot; absent/conflicting-profile tests remain mandatory. Synthetic
  profile inheritance is not production model/configuration qualification.
- RD-S01 through RD-S06 are the existing frozen selection, not extra cases. Historical
  RD-S02/RD-S04 receipts remain older-source baselines. RD-S03's older-engine OCR
  failure remains a failure, not an approved current receipt. Tesseract/index snippets
  cannot substitute for app extraction. Human references remain unreviewed.
- Invoice controls remain independent: issue73's single-layout USD scope; native77's
  synthetic portion clearly labelled; received15 under definition revision1. No
  taxonomy/remapping or policy choice is made here. Issue71 decisions remain open.

## Exact future overlay surface

Use a disposable copy of the selected Doc Sum source, retained outside removable
worktrees. Authenticate pristine Git tree and every crate blob before applying an
explicit diff. Production function bodies, visibility, Cargo manifest/lock, assets,
configurations and dependencies remain byte-identical to the selected revision.

The permitted Rust overlay is:

1. A test-only module inclusion in
   `src-tauri/src/connect/ocr_consumer/streamed/tests.rs`, already included only by
   `#[cfg(all(test, unix))] mod tests` in `streamed.rs:717`.
2. New sibling file
   `src-tauri/src/connect/ocr_consumer/streamed/real_document_preparation.rs`, included
   as a child module of those tests. Use the existing lexical test scope to access
   private owners. No production API export, release feature or visibility widening.

This overlay is Unix-only and scoped to the Linux offline preparation lane. Native
Windows qualification needs a separately reviewed test seam; this contract does not
widen the existing platform gate or provide Windows preparation evidence.

The later isolated packet may also contain a bounded launcher/receipt reader and
saved-response fixture server. These are test tooling only, not an OCR engine or
production service. Bind their complete source, exact invocation and environment;
no dynamic import/eval of descriptor-provided code. No tool is implemented now.
All allowed additions must be listed and hashed in the future overlay receipt.
Anything beyond this surface needs a contract amendment before implementation.

## Closed input and resource contract

The future descriptor is a closed tagged type with exactly two variants:
`PrepareNative` and `ValidateSavedOcr`. Both require an independently approved
execution-manifest identity, bound case/occurrence, PDF artifact identity, original
filename identity, selected source/overlay identity, profile binding, exclusive
output root and explicit finite limits. `ValidateSavedOcr` additionally requires the
approved producer/request/status/output receipt and its reconstructed initial-state
identity binding. Missing receipt returns `MISSING_OCR_RECEIPT` before any endpoint.

Use existing typed models plus Serde closed structs/enums (`deny_unknown_fields`),
strict duplicate-member rejection and a single named cross-file association validator.
Unknown/missing/duplicate members fail; no untyped Value/default path may erase them.
Zero/false/empty limits are errors, not defaults. A valid-shaped hash does not prove
approval: the launcher binds the accepted manifest digest from an independently
retained operator receipt, not a digest computed from whichever descriptor it receives.
The adapter consumes verified typed values only. No parallel regex admission.

Private cases are allowlisted by the existing frozen case/digest table, never by a
filename guess or arbitrary path. Synthetic public test fixtures have a separate
explicit test identity and cannot be relabelled real evidence. Bounded descriptor
and file reads, regular-file/no-follow checks, exclusive private output creation and
source size/digest verification occur before app work. If the old analysis writer is
reused, first close its shorter-rewrite and symlink-refusal regression gaps.

Every later execution manifest must state numeric limits for descriptor bytes,
per-file and aggregate input/output bytes, page count, wall time, memory, process
count, local fixture HTTP attempts, logs and cleanup. No implicit unlimited field;
UNSET blocks execution. OCR-plan budgets do not authorize this preparation. Kernel
network isolation and private stores must fail closed, with no host-network fallback.
No environment switch can arm real OCR or any model/tokenizer in this offline adapter.

## PrepareNative

Create a fresh private store through the selected typed store owner, with no installed
DB, corrections or settings import. Use `prepare_pdf_ingestion_with_source_type`,
`prepare_received_run` and `persist_ingestion_with_profiles`; preserve the private
original filename, NativeText source type and independently bound PDF digest. Supply
the explicit profile snapshot, recording whether it is synthetic metadata or a
separately approved application snapshot. Never construct a model client to obtain it.

Run `parse_document` with `PdfExtractParser`, which validates bytes and visits every
page. Preserve exact parsed pages, warnings, parser/version, content hash, state/event
records and `requires_ocr` decision. Empty or mixed pages are not automatically OCR'd:
report `OCR_REQUIRED` and stop. For a non-OCR case report `NATIVE_PREPARED`, preserving
all parse warnings. A parser failure is retained as that failure, not converted to an
empty successful extraction. No pipeline service/run-to-summary call is permitted.

Fresh identities are recorded once per occurrence. Stable identities needed for a
later replay must come from its approved initial-state binding through the same typed
store mechanism as CC112; never rewrite prompts, UUID generation, existing terminal
rows or output IDs downstream. Reopen the fresh store via the selected lifecycle
owner, verify the same persisted source/parse identity, and stop before Normalize,
Analyze, Summarize or model-stage dispatch. Native preparation is not summarization.

## ValidateSavedOcr: same consumer boundary, offline transport

Admit only an independently reviewed same-input OCR receipt with source/producer,
protocol, original request bytes, page scope, profile and output provenance. Missing
or incompatible data refuses. Reconstruct initial Received/version1 root identities
and the approved `NewOcrHandoff` association in a fresh store via typed APIs; preserve
request/job/artifact/root/child IDs and the original display name. Replay identity is
reconstructed initial state, not a claimed captured checkpoint. Parse the original
PDF through the selected native parser; use `db::prepare_ocr_handoff`, then
`validate_saved_request` before dispatch. No direct SQL handoff insertion or copying
terminal DB rows. Any receipt lacking those associations needs its own preparation,
not invented IDs or rewritten response bodies.

**The transport trait alone is insufficient.** `streamed::download_async` creates its
own reqwest client. Therefore the saved-response fixture must be a bounded loopback
HTTP endpoint inside the same fresh, otherwise disconnected network namespace as
the consumer. The endpoint serves only approved saved status and output bodies through
a test-only `OcrTransport` wrapper that delegates submit/status to unchanged
`HttpOcrTransport` but overrides rediscover to refuse and directs temporary output
files to the bounded private root. Keep `run_handoff_until`, strict metadata decoding,
streamed retrieval, pair validation and child admission unchanged. No actual provider process starts.
Use an explicitly supplied private test `LiveOcrProvider`; do not call normal discovery,
`process_scanned_document` or startup recovery. Missing/extra/misassociated requests
are failures. Preserve ordered transcript occurrence, method/path, logical request and
PDF bytes, status/error bodies and all consumed/unconsumed outputs. Compare serialized
request bytes where available; do not claim literal multipart/wire equality when the
original capture lacks it or multipart boundaries change. Report such transport
framing separately from exact request JSON, input and response bodies.

The only provider-envelope substitutions are the fixture's namespace-local endpoint
and fresh ephemeral bearer credential. They are explicit replay transport differences,
not producer identity changes. Provider instance/job IDs, request JSON, descriptors,
output bytes, schema order and provenance stay bound. Secrets never enter evidence.
Refresh/discovery paths must refuse rather than discover a real provider; a receipt
requiring such a path is retained as unsupported until separately contracted. Every
uncertain/retry/status/output request counts against the finite replay budget; never
reset counters, replace failed work or weaken production validators to obtain a pass.

On valid success, retain all original outputs and invoke unchanged canonical pair,
source-page, identity, materialization and child-admission owners, then parse the child
with `TaggedOcrParser`. Require one lineage, matching child digest and inherited root
model/summary profiles. Reopen and revalidate without app startup recovery. Failed
output or admission remains a failure; do not backfill a missing profile after failure.
A later correction uses a new fixture, preserving the failed evidence.

This operation does not qualify live discovery, entitlement, installed applications,
OCR recognition, retry recovery, model behavior or speed. It validates a retained
receipt through the selected consumer. Live capture is NOT a third adapter mode and
cannot be selected via environment. It remains a separate reviewed plan and approval.

## Every intentional difference and parity rule

| Difference from old controls | Owner and required evidence |
| --- | --- |
| Frozen real PDF replaces generated synthetic case | Input owner; digest/original-name binding and full-page extraction; no substitution inside C0/C1. |
| Selected e5000cf replaces archived Summary crate | Complete source/lock inventory and annex; public unchanged-owner regression first. No whole-app parity claim. |
| Fresh store/fixture, reconstructed IDs where receipt requires them | Typed ingest/handoff owners; Received/version1, exact association, no terminal rewind or raw SQL. |
| Offline saved server replaces a live OCR endpoint | Namespace and frozen-response evidence; real HTTP/stream validators retained, endpoint/token differences declared. |
| Stop at parsed native/derived artifact | No summary/model client; record OCR_REQUIRED/failure instead of silently continuing. |
| Explicit initial root profile instead of former defective None fixture | Reuse df50d59a owner and positive/absent/conflicting-profile regressions. |

No other port difference is allowed silently. Same-input source changes must be
reported, including extraction/page ordering and error behavior. Reuse public frozen
controls and review any changed results before private preparation. Do not force
byte equality across intentionally different source versions or call current-source
failure a model regression. Human quality and schema validity remain separate.

## Verification plan and acceptance gates

Future separately authorized implementation must supply an owner-to-test matrix:

| Invariant / boundary | Settling proof before private use |
| --- | --- |
| Identity / file admission | Correct public fixture passes; changed/missing/duplicate/mixed binding, wrong case/name/digest and symlink/alias/nonempty output roots fail before parsing. |
| Closed descriptor / bounds | Unknown/duplicate keys and each required field missing; zero/false/empty, min-1/min/max/max+1, large-valid; limits affect consumed data, not just a precheck. |
| Full native parser | Native, empty and mixed-page controls; parser page signal preserved; no live OCR on OCR_REQUIRED; source unchanged before/after. |
| Root profile / store | Reuse df50d59a positive and absent/conflicting-profile negatives; fail-first ModelProfileMismatch; no partial child or profile overwrite; lifecycle reopen retains data. |
| Saved OCR transport | Namespace-local saved HTTP success; wrong job/instance/input/request/output association fails; unexpected route, discovery, missing response and exhausted budget fail closed. |
| Real stream validators | Bad size/digest/media, malformed/duplicate metadata, oversized/truncated body and mismatched canonical text/page count fail through existing owners. Both valid and invalid boundaries tested. |
| Durable child | Exactly one lineage and inherited profiles, tagged-page equality, repeat admission does not duplicate, reopen identity; no model-stage events. |
| Isolation / ownership | No external/production endpoint or writable production store; no real OCR/model process; concurrent store/path claims refuse; cleanup only owned processes. |
| Evidence writer | Private permissions, exclusive creation, bounded logs, shorter rewrite and symlink refusal if writer reused; failed outputs retained. |

This is a contract, not a passing test report. Native compiler/build flags, dependency
cache hashes, source-copy identity, executable hash, OS isolation, command lines and
numeric limits belong to the separately approved verification/execution packets.
No native code, executable schema, test fixture, build, parser, OCR or replay runs in
this PR. Do not duplicate broad suites for Markdown-only changes.

## Non-scope, unresolved items and gap audit

No production API/config/dependency/schema change; no host/runtime/engine implementation,
GPU use, tokenizer/model call, OCR execution, installed adoption, service/Ollama change,
remote fork, concurrency claim or performance claim. No Invoice mapping/assembly/scoring
or issue71/issue88 decision; no human gold invented. Original seals remain immutable.

Source selection is DONE; final exact-revision contract acceptance is PENDING. The
native/runtime-file receipt for current OCR, human reviewer/reference answers,
implementation, builds/tests, private preparation, live capture and all numeric budgets
remain pending separately. Invoice taxonomy/remapping is its own work order and does
not become a prerequisite to reviewing this independent adapter contract.

Documentation inventory/contract DONE when its checks pass and the PR is submitted.
Implementation/qualification NOT DONE. Merge requires independent exact-head oversight,
connector completion, required checks (or confirmed absence), no unresolved threads/
CHANGES_REQUESTED, clean matching branch and guarded merge; acceptance covers contract
only. Subsequent implementation, build/test, private replay, live OCR and model execution
each require separate explicit authority. No merge is requested before acceptance.
