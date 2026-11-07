# Summary offline replay identity contract

## Authority, root cause and required surface

Status: PROPOSED, documentation only; owner: connect-runtime. This refines
[migration plan section B](PR-V1-Profile-Migration-Replay.md#b-scorer-environment-and-retained-answer-parity).
It authorizes no implementation, fixture construction, native build, dependency
installation, scorer replay, tokenizer/model call or production change.
Exact-revision acceptance and independent review are required before separately
authorized implementation. The preceding Summary evidence review must also pass;
its submission is evidence, not a completed gate.

Fresh ingestion creates a document UUID, changing normalized block identities
in the first prompt. A fresh run UUID also changes the generation seed. The
retained exact-request guard correctly refuses the answer association. This
occurs before inference and is separate from concurrent inference arithmetic.

The repair owner is the offline fixture's initial application state. Preserve
archived document/run identities through existing typed store APIs. Do not
rewrite prompts or answers, ignore identifiers, weaken request equality,
monkeypatch UUID generation or change production identity policy.

Required documentation surface: this annex and a parent section-B pointer.
Future executable surface: a test-only overlay in a disposable copy of the
pinned archived Summary crate, an offline transcript controller and boundary
proof. No dirty/current app checkout is an implementation target.

## Validated inventory and limits

Reuse existing inventories and packet alias
summary-scorer-parity-20261107T171602Z:

| Artifact | SHA-256 |
| --- | --- |
| REPORT.md | 6ff10355c74fc078e40cb3b0f52add23ff833f50453425b52a275f85a52bf82a |
| binding.json | fe771c8fd524b8baf3982bca7408e36463c0c2956017cec896588b94cb2244ef |
| execution.json | 7f4177a5080d8f6d8532cf4275336a5cc6b59a99f109f3e930064d952b4401b7 |
| origin-trace.json | 9be17aa20dafccba789c387ce024888f85c913955c305f6c73e7cf0653630bc0 |
| SHA256SUMS | 1d2e894adc43e3ff1bc92c5240f6ac09210f32683705338365bc4edc1830041e |

The previous packet reports one byte-identical score, **FAILED to FAILED**,
one request attempted and none of five saved responses consumed. Nine wrapper
tests passed normally and under optimized Python. It proves no successful
Summary chain or summary fidelity. Preserve that verdict and every byte.

Independent review alias summary-scorer-parity-review.md, SHA-256
3d2db4f799bc22689b5cfeac922700e6074ce3ed624bc49da503162e1d59f9d4,
passes those provenance/refusal/cause claims. It explicitly leaves Summary
output parity and section B unmet. This satisfies the preceding evidence-review
gate only, not review or acceptance of this new contract.

The 301-file receipt pins archived sources, not the compiled driver. The
pre-production manifest/build receipt separately binds 83 compiled source files
and the driver. Archived Summary revision:
2e7fc4ef503ea1868a413f337b8acdd8936e1e3d; driver binary SHA-256:
993da0663759dc9828039fd36dbcbef97957ac84b10dd4f1674c5e71fecf56e6;
evaluation driver source SHA-256:
0d818411fd71051dda6fbb501ac443f8f10e20a4d1fbbd4037a0a38d4c0a2b37.

Control inventory is pre-production evaluation
20261004T175816Z-24660385746b, Summary case synthetic_service_agreement.
Its stored driver status is complete. Its recorded observation is general
profile, coherent presentation, one claim, two evidence items, no warnings,
durable reopen true and semantic fidelity unreviewed. Its transcript contains
five generation records and 31 preflight records: 19 complete and 12 failed
with context_exceeded. Original, retained serial and recent scorer runs used
the same PDF bytes.

Supplemental receipt alias
summary-replay-identity-contract-20261107T173556Z/source-evidence.json,
SHA-256 4a35eaf76953376ec6ac7ff983eb811da6c70d99328d94bf2626f1a4a390d053,
binds the eight cited source files and 45 original-control artifacts. This adds
the required original DB/PDF/result/wire/preflight bindings; it does not rebuild
source/corpus inventories. Raw documents, identities and DB contents remain
private; these references do not authorize uploading them.

## Source-grounded mechanism

References are relative to the pinned archived Summary source,
src-tauri/src/pipeline/, unless noted otherwise.

| Owner | Confirmed behavior and consequence |
| --- | --- |
| ingest.rs:88/:139, prepare_pdf_ingestion_with_source_type | Creates a document UUID. Production behavior stays intact. |
| ingest.rs:153, prepare_received_run | Creates a run UUID and defines Received/version-1 initial state. |
| normalize.rs:53/:117, deterministic_block_id | Hashes document ID, normalizer version, page and block index. |
| summary/pages.rs:649/:781, prompt_candidates / selection request | Includes block ID in the first prompt. |
| summary.rs:218, generation_seed_for_run | Derives seed from run ID; document identity alone is insufficient. |
| contracts.rs:149, continuation_checkpoint; service.rs:205/:421 | Complete runs cannot continue; retry requires Failed and creates a new run. A terminal DB is not a pre-call checkpoint. |
| db.rs:1793/:1801, persist_ingestion / persist_ingestion_with_profiles | Typed owner requires matching document ID and Received/version 1; transactionally creates ingestion state. Visibility is pub(super)/pub(crate), unavailable to an external example driver. |
| service.rs:475, process_ingested_to_summary | Processes stored identity without re-ingesting the PDF. |

Retained score.py::Replay.complete, lines 46–54, normalizes model alias and seed,
then compares reconstructed requests and refuses inequality before returning an
answer. harness-source/eval_summary.py::bridge routes preflight into token
counting. Both operations need an offline association; replacing generation
alone is insufficient.

The future adapter must reuse the archived evaluation driver's ModelRequest
serialization and Python request_body/admission/failure mapping. A necessary
test-module port is a byte-audited, explicitly listed driver-overlay difference;
it must not recreate prompts, schemas or scoring rules through a new adapter.

## Identity fixture at the existing store owner

Use a fresh, exclusively created database and verified private PDF copy. Do not
write the original/installed DB or rewind a terminal DB clone by editing/deleting
rows. This fixture is explicitly reconstructed initial state, **not a captured
historical pre-call checkpoint**.

The future test-only module lives in the copied crate's pipeline namespace,
allowing access to the existing store owner without widening production APIs.
Permitted overlay: one cfg(test) module declaration and its test module. Keep
production function bodies, Cargo manifest/lock and dependencies byte-identical.
No runtime feature, CLI override or production restoration endpoint. Audit
cfg(test) differences; this is offline app replay, not production-binary,
entitlement or installer qualification.

A closed fixture descriptor selects only the bound original case and the two
lanes below. Use existing typed models/enums, required descriptor members and
unknown-field rejection. One named fixture validator owns cross-file hash and
association rules. No regex substitutes, parallel ID scrubber, dependency or
framework. Identities come from authenticated records, never caller overrides.
Bind artifact sizes/counts before execution and reject oversized/unlisted data;
do not make an arbitrary database/path/identity import tool.

Required construction:

- Verify original manifest, build/source pins, complete driver result, DB, PDF
  and ordered wire/preflight records before fixture writes. Use SQLite read-only
  APIs; refuse unaccounted journal/WAL state so a main-file hash cannot hide pages.
- Obtain the one original IngestedDocument and associated run via typed getters.
  Cross-check IDs, content digest/size, profiles and creation metadata against the
  bound driver result and initial event. Never select by recency or list position.
- Preserve document ID, original filename, file/source type, content hash/size
  and creation timestamp. Only local_source_path changes to the verified private
  PDF copy; record that relocation and retain any request difference it causes.
- Construct PipelineRun with the archived run ID and document ID. Follow
  prepare_received_run: Received/version 1; pipeline version 1.0;
  created_at/updated_at equal the verified original creation instant;
  started_at/completed_at/current_stage/failure absent; zero progress, empty
  warnings, cancellation false, resumable true. Check the source's first event
  supports this initial state. Do not copy terminal state or delivered outputs.
- Call persist_ingestion_with_profiles with the original model-profile
  presence/value and Summary profile, including genuine absence of a model
  profile. Do not substitute current defaults. Reopen and verify stored
  identity/profile associations before processing.
- Call process_ingested_to_summary with the archived parser, normalizer,
  interpreter and chunker and the offline ModelRuntime seam. New event IDs and
  execution timestamps stay new; no clock freezing. Preserve run identity so
  production seed derivation remains unchanged.

If the existing typed owner cannot express this, stop for a contract amendment;
do not insert arbitrary SQL rows or widen production visibility.

## Offline transcript and request association

Bind each occurrence by lane, case, ordered operation ordinal and exact request
identity. The control uses the complete ordered generation/preflight transcript,
including context rejections. No searching ahead, response reassignment, skipped
refusals or automatic retry.

For generation, compare the generated request to its corresponding frozen request
before returning the saved response. Preserve messages, output limits,
temperature, response format and schema property order. Bind the run-derived
seed to its recorded value; do not carry the old scorer's seed omission into new
acceptance. Only the existing explicit evaluation-candidate model-alias mapping
is permitted and reported separately from raw equality; it cannot hide a profile
or model change.

Preserve all original buffers. Where native request.raw bytes exist, retain them
exactly and report literal-byte comparison separately from generated-request and
ordered-member comparison. Original pre-production wire files are structured
records, not proven original HTTP bytes. Do not claim historical wire equality
from reserialization. No schema sorting, ID rewrite, generic canonicalization
or ignored-key list.

Return each recorded preflight outcome only after matching its complete request,
context/output reserve and occurrence. Preserve the 12 context_exceeded refusals
and existing ModelRuntimeFailure mapping, not blanket admission. Token counts
are historical observations, not new measurements or authority for another prompt.
An unrecorded preflight/generation is a retained association failure and stops
that lane. No real tokenizer/model/external-network fallback.

The later controller uses fresh processes, kernel network isolation, private
outputs and bounded cleanup of owned processes only. Any bridge is accessible
only inside that namespace. Deadlines, limits, native build identity and exact
commands require a separately approved execution packet. No live hardware budget
is allocated here.

## Later lanes and gates

**C0 — original-answer identity control.** Use reconstructed identity and the
original pre-production answers/preflights. Require the complete ordered
transcript, no missing/extra calls, matching seeds and schema order. Invoke
unchanged app validators and reproduce the original run_summary return payload:
input digest, relative driver-artifact path and full summary_observation,
including unreviewed fidelity. The app must complete and pass existing
source-unchanged/durable-reopen checks. A matching failure does not pass C0.

Preserve and diff full driver, Summary and citation artifacts as well, including
timestamps and integrity fields. The existing score payload is the scorer-parity
object; this contract grants no Summary clock exception or full-artifact
equivalence claim. Any additional artifact comparison rule needs its own amendment.

**C1 — retained serial-answer diagnostic.** Only after C0 passes, use a separate
fresh fixture with the same original identity and serial-2 native answers for
pre-24. Those request bodies came from the original fixed workload; changed
answers can make later dynamic requests diverge. Each request/preflight must
match its bound occurrence before its response/count can be reused. Retain a
divergence and stop the lane; never force remaining answers through or mutate
the transcript.

Report old FAILED verdict, new C0 result and C1 result separately. A C1 success
would be a changed harness outcome under this fixture, not byte-identical parity
with the failed baseline. No perfect accuracy, installed-app compatibility,
summary fidelity or inference-performance claim. Human review and platform/app
qualification stay independent.

## Every deliberate departure

| Departure | Reason / required proof |
| --- | --- |
| Random fresh ingestion replaced by typed initial state in a new DB | Repair identity at its origin; prove original IDs and derived block ID/seed before dispatch. Production ingestion unchanged. |
| In-crate test overlay replaces cached external example | Store API is not public; bind new build/source and cfg(test) scope, with no binary-equivalence claim. |
| PDF path relocated | Protect originals; preserve bytes/filename and retain any request difference. |
| Original-answer C0 before serial-answer C1 | Distinguish fixture/adapter defects from changed-answer branches. |
| Recorded preflight replaces live counting | Exact ordinal/request/outcome association, including refusals; no invented admission. |
| Validate seed instead of ignoring it | Original run identity permits the actual derived seed; never rewrite a seed to pass. |

All other algorithms, schemas, settings, validators, source pins and saved
answers remain unchanged. Another departure requires a revised contract.

## Required later proof and acceptance

Reproduce the old fresh-UUID failure before implementation. Probe the valid exact
fixture and independent refusals: changed PDF/source/DB/receipt; wrong doc/run
association; absent/present profile mismatch; unknown descriptor fields;
duplicate/missing/reordered transcript; changed seed, block ID, schema order,
output reserve, context or response association; non-Received/stale state;
nonempty output DB; escaping/aliased paths; missing/changed preflight rejection;
extra generation and unused responses. Zero/false/empty cannot select defaults.
Prove the downstream app consumes verified objects, not unchecked parallel values.

Mutate fixture/occurrence checks individually and retain all survivors with
reasons. Reuse app store/validator tests and the retained control, not a new
summary-quality heuristic. Preserve outputs, refusals, errors and differences
in a new sealed packet. Never overwrite saved evidence.

Gates: prior Summary evidence review; oversight and connector review at this
exact head; Juan's exact-revision acceptance; guarded merge. These approve the
contract only. Implementation, native test build and offline execution each need
separate authorization. Production UUID policy, selected runtime, issue 88,
live budgets, installed adoption and human quality remain unchanged/open as
previously applicable.

## Gap audit

Documentation/source mapping DONE when this annex and parent pointer are checked.
Fixture implementation, test driver, build and C0/C1 replay are **NOT IMPLEMENTED /
NOT RUN**. Existing failed-verdict parity is not successful Summary-chain or
overall section-B qualification.
