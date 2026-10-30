## Acceptance record — 2026-10-29

Juan accepted the exact reviewed work order at
`7adfab16c2cbb3dbd6766a00100090e9767e0648`, directly in the
`connect-runtime` session: "I accept".
Oversight also relayed his decision verbatim: "Accept 81 do the guarded merge yourself";
oversight clarified that "Accept 81" accepts this revision and the merge phrase
referred to document-ocr #71, not this PR.
[Oversight CONTRACT REVIEW PASS](https://github.com/canfieldjuan/connect-contracts/pull/81#issuecomment-6489218149)
applies to that exact revision. This acceptance record changes no work-order
requirements. The reviewed body below is retained byte-for-byte as the proposal
that was accepted; its historical PROPOSED/NOT DONE labels describe that revision.
Each implementation slice retains its own contract/review gates.

---

# Shared runtime unification work order

Status: PROPOSED, docs only. No implementation or route retirement is accepted.
Tracking: [connect-contracts #80](https://github.com/canfieldjuan/connect-contracts/issues/80).
Owner: the existing `connect-runtime` session, across the host and all three apps.

## Decision and acceptance boundary

The operator selected the ADR-0011 shared model host (`llama-server`, Qwen3.5-9B)
as the common target, and directed Doc Sum's 32k qualification to that host.
The [04:37 decision](https://github.com/canfieldjuan/connect-contracts/issues/80#issuecomment-6488081716)
and [04:44 ownership amendment](https://github.com/canfieldjuan/connect-contracts/issues/80#issuecomment-6488166313)
select the target and sole runtime owner; they do not accept this contract.
The earlier runtime choice is recorded in
[invoice-processor #70](https://github.com/canfieldjuan/invoice-processor/issues/70).

This proposal needs oversight CONTRACT REVIEW and Juan's acceptance of the exact
reviewed commit. Each implementation slice needs its own committed contract,
review and acceptance gates. No executable migration, live model/GPU run,
installation, promotion, merge or deletion is authorized by this document or by
publishing its PR. The operator's subsequent permission to open PRs is limited to unification and
deprecation; concurrency experiments remain local-only. The docs-only proposal is separate from the local-only
concurrency investigation; it does not publish or adopt experimental kernels.

## Root cause and verified inventory

Runtime selection has separate owners in each app. Accepted host design alone
has not ported those selectors, request semantics, saved jobs or setup flows.
The gap is at app construction/configuration and attachment, not a requirement
to replace the model engine. Source below was inspected at exact remote-main
revisions on 2026-10-29, independent of dirty/local checkout heads. Installed
artifacts were not re-bound in this work order; current deployment state remains
UNKNOWN and must be captured before a cutover claim.

| Owner / inspected revision | Confirmed source behavior and owning symbols |
|---|---|
| connect-contracts `f00aad8aa3d53285c5b96afd34ecc5ec59030991` | [ADR-0011 attach and lease rules](../adr/0011-shared-local-model-runtime.md#attaching); [canonical profile](../runtime/v1/profile.json): llama.cpp `c1d0e7a004015f23bc0233470b747b596f29b264`, context 32768, one slot, thinking off, authenticated local socket. Current profile contains CUDA and Vulkan GPU tiers, both Qwen3.5-9B-Q4_K_M; older ADR CPU prose does not add a tier to these bytes. |
| local-connect-model-host `f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b` | [host.rs `launch_transient` / `run_host`](https://github.com/canfieldjuan/local-connect-model-host/blob/f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b/src/host.rs#L107-L143) owns server lifecycle; this is also the [Invoice sidecar build pin](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/scripts/build_desktop_sidecar.py#L24-L39). A newer local checkout is not evidence of a newer installed host. |
| document-summarizer `7911f4375772fbc2e6c063a4e4a82aea7d638751` | [model_settings.rs](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/model_settings.rs#L854) `runtime_from_settings`, `runtime_from_snapshot`, `StageRuntime`: direct Ollama or in-process llama.cpp, plus gateway selection. Default preset at line30 remains the older 30B preset. [gateway_runtime.rs:22-25](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/gateway_runtime.rs#L22-L25) binds task@1 to 8192. [llama_cpp.rs `completion`](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/llama_cpp.rs#L577-L600) sends token-array `/completion`, temperature0, request seed, cache_prompt true and json_schema. |
| eom-email-watcher `3edcae19de0fff45ebc808aa5650e17a411a2e45` | [runtime.py](https://github.com/canfieldjuan/eom-email-watcher/blob/3edcae19de0fff45ebc808aa5650e17a411a2e45/src/eom_email_watcher/runtime.py#L184-L198) chooses `GatewayModel` or `LocalModel`. [model.py](https://github.com/canfieldjuan/eom-email-watcher/blob/3edcae19de0fff45ebc808aa5650e17a411a2e45/src/eom_email_watcher/model.py#L344-L377) sends chat/schema requests at 0.1 with no seed; gateway generation at line 781 also uses0.1. [config.py](https://github.com/canfieldjuan/eom-email-watcher/blob/3edcae19de0fff45ebc808aa5650e17a411a2e45/src/eom_email_watcher/config.py#L483-L529) defaults to loopback and 20000 body characters, maximum 100000; gateway uses its task label instead of the configured model name. |
| invoice-processor `f7281d71e050fd5e9c746bb5e45c55862af12c26` | [model.py `build_runtime`](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/model.py#L784-L796) chooses gateway explicitly, otherwise `SharedHostModel` only when [setup/scope.py `in_scope`](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/scope.py#L26-L35) accepts package defaults on Linux x64; overrides and other platforms still reach loopback. [setup/attach.py](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/attach.py#L177) owns lease, identity verification and app canary. Host integration is existing code, not universal deployment proof. |
| local-inference-gateway `f105bfd0fba0c8f0866902751c0ec7018171ea39` | [worker.py](https://github.com/canfieldjuan/local-inference-gateway/blob/f105bfd0fba0c8f0866902751c0ec7018171ea39/src/local_inference_gateway/worker.py#L75) contains `OllamaWorker`, `LMStudioWorker`, `FallbackWorker`; schema serialization at223 conditionally sorts fields. [app.py](https://github.com/canfieldjuan/local-inference-gateway/blob/f105bfd0fba0c8f0866902751c0ec7018171ea39/src/local_inference_gateway/app.py#L350-L360) owns a single active lane. [contracts.py:18-19,60-61](https://github.com/canfieldjuan/local-inference-gateway/blob/f105bfd0fba0c8f0866902751c0ec7018171ea39/src/local_inference_gateway/contracts.py#L18-L19) distinguishes document task@2/32768 from v1's absent context guarantee. None of this is a host adapter. |

INFERRED: porting these app selectors to the existing host removes multiple
engine ownership from the supported app route. It does not establish faster
inference, more runtime slots or equivalent task quality.

## Reuse of validated work, before any port

The existing canonical profile remains the source of model, archive, template
and argv identity. Vendor its exact bytes and derive PROFILE_ID, never hand-copy
selected settings. Do not promote the diagnostic runtime or sandbox v0.7.0.
The host lease, file verification, descriptor loader, socket peer verification,
canary and failure semantics are reused, not redesigned in each app.

Qualification planning must bind and reuse the existing 301-file source receipt,
the 25-case pre-production evaluation `20261004T175816Z-24660385746b`, issue-73's
33-invoice corpus and existing corpus manifest/real validators. These are prior
inventory references, not newly executed or re-certified here. Before a live
request, each qualification owner supplies exact existing receipt aliases and
hashes, app/source/runtime bindings, request bytes, framing/template, schemas in
property order, model pin, output budgets, settings, inputs and recorded scores.
Missing evidence is an explicit blocker; do not rebuild a replacement synthetic
suite or substitute JSON validity for extraction/summary quality.

Prior concurrency evidence remains separate and unresolved. Durable aliases:

| Report alias | SHA-256 |
|---|---|
| seeded-corpus-concurrency-20261013T010124Z/RESULTS.md | `8ccd8f94c7ce94ea4e71bc9ecd0a090c20aa47bd2dfd1cf4bc008f48467bc51a` |
| paired-token-projection-trace-20261025T001307Z/RESULTS.md | `35de12175c8e3fd7d9ea2ada14dc2fd9f9f50f935a913347841c0af5cd0501bc` |
| beta-projection-isolation-20261027T061238Z/RESULTS.md | `b573aa44ae5f4c32538dfc0e13d48a742e2a4efc183efa848c989e2a51350250` |

Those reports do not qualify a new app route. The beta experiment is parked;
no claim of complete arithmetic root cause, safe multi-slot deployment or speedup
is a prerequisite or an outcome of this unification proposal.

## Required change surface and sole ownership

`connect-runtime` owns the host and all app-side attachment, runtime selection,
setup, migration and retirement work in their respective repositories. Other app
sessions retain their product work. `ds-qualify-c9` owns Doc Sum's 32k criteria,
corpus, evidence and live-run request, against the delivered host route; runtime
ownership does not take over its quality decisions.

Before app edits, oversight records non-overlapping files/branches and the exact
integration base. DS #116 (`f48bb5035612c11747385ef7a553d915ec7da6a0`) and #126
(`e12ac4a72330bb6eb000119e77806ecce313d591`) are open proposals, not main. DS #155's
r6 repair precedes its qualification work order per #80. EW #145 was verified as
a CLOSED polling issue, not an active PR. Oversight clarified that the EW work is
isolated installed qualification on merged `3edcae19`, not an open code branch;
its reported open PR is #237. At U3 contract drafting, oversight must confirm the
exact integration base and non-overlapping ownership with `ew-cutover-255`; this
coordination report is not an installed-artifact binding. Dirty checkouts remain
untouched.

| Ordered slice | Runtime owner's work | Required gate before advancing |
|---|---|---|
| U0: this docs-only work order | Resolve ownership/default/deprecation decisions and freeze the source inventory. | Oversight CONTRACT REVIEW and Juan's exact-commit acceptance; no implementation bundled. |
| U1: Doc Sum host attach | Deliver the shared Rust host-client crate and add its host contract as a `ModelRuntime` route; bind settings and immutable run snapshots, setup/store pins, app canary, native tokenization/request framing and lease ownership. Reuse useful transport code, remove no route yet. | Focused attach/error/race tests; source-bound request equivalence for the transport-only port. Deliver an exact app/host/profile revision tuple to ds-qualify-c9. |
| U2: Doc Sum 32k qualification and proposed cutover | Runtime owner repairs route defects at their origin. ds-qualify-c9 runs its separately accepted qualification on the U1 host route. Gateway@2 and the in-process #126 child are not substitutes for this target. | Independently scored whole-writer/task evidence, human review, explicit route/default differences, separate live-run authority and exact-revision promotion acceptance. The complete contention matrix below must pass before U2 cutover; unavailable peer routes block cutover, not independent preparation. No automatic cutover on a canary. |
| U3: Email Watcher host attach, qualification, proposed cutover | Extract the behavior-preserving shared Python host-client package from Invoice before Email attaches; route runtime factory/config/setup and job leases through that client; preserve Email analysis and scheduling contracts, persistence, retries and result identity. Runtime owner also owns its qualification binding and deprecation. | Real pre-production Email cases and the complete contention matrix below before U3 cutover; transport-only 0.1 behavior first, then a separately accepted default-alignment comparison. No mailbox sends/calendar writes to benchmark. |
| U4: Invoice consolidation | Move its already-existing host attach onto the same released Python client and profile; close remaining product gateway/TCP selection bypasses. Preserve canary, grammar/schema order, extraction and retry semantics. | Prove extraction transparency against the original Invoice client, including request bytes, outputs, errors, tier request limits and lease/canary behavior; reuse issue-73/other existing pre-production scoring; no claim that a source pin proves every installed document correct. Test-only explicit TCP harness remains outside product selection. |
| U5: staged retirement | After each app's own route passes and cutover is accepted, remove its superseded product selectors, fallback paths and setup guidance. Retire gateway engine workers only after all app consumers are migrated and pending jobs are settled. | Per-route dependency/usage inventory, exact-version acceptance, focused positive/negative route tests, reviewed rollback and no data loss; recorded operator hardware-support-floor decision and affected-user transition proof below. No service uninstall or stored-model deletion. |

The order is delivery order, not permission to cut over each app immediately.
U2 may deliver task-quality evidence and remain pending cutover while U3/U4
deliver the peer clients needed for the full contention gate. Later delivery
requires its own accepted slice contract; a pending cutover does not waive it.
Slices may share read-only preparation. Executable changes remain sequential at
the host/profile boundary, one app per PR; do not make app sessions race the
runtime owner. Rebase of the inventory means re-checking affected evidence, not
assuming the proposal's old line numbers still identify the current owner.

## Compatibility invariants and proposed migration behavior

- One per-user host, one server and one loaded model. Preserve ADR-0011 lease,
  start race, parent-death, stale registration, profile mismatch, file pinning,
  socket peer/key and timeout rules. No app kills another profile's host.
- Keep context 32768 and one slot in the canonical profile. Multiple clients may
  attach and queue; that is not parallel generation. Bound waits, cancellation,
  retryability and retry-after propagation at the actual owning boundary.
- Preserve each app's prompt framing, tokenization, reasoning-off handling,
  schema property order, grammar features, budgets and validators. DS's native
  token-array `/completion` must not silently become a chat-template request.
  Schema-valid output alone is insufficient; reasoning-only output is not final
  content. Verify endpoint support on the exact pinned runtime before live use.
- Port transparency requires identical serialized generation inputs and recorded
  native/application outputs under matched settings; log every mismatch and its
  score effect. Where a route necessarily changes serialization (Ollama/gateway
  versus native), list that difference before implementation and independently
  score it. Do not relabel changed input bytes as transparent transport parity.
- Bind new DS runs to the host profile in immutable snapshots. Existing runs
  retain their recorded route identity; never rewrite an old run as host-backed.
  Proposed retirement policy: allow completion before withdrawal where supported;
  otherwise preserve results/checkpoints and require an explicit new run on the
  accepted host route. Do not delete history or silently resume under new numerics.
  This user-visible transition needs explicit acceptance in U2/U5 contracts.
- Preserve gateway request IDs, encrypted result replay, acknowledgement and
  ambiguous-outcome handling while draining outstanding work. A migration must
  not rerun a completed business action because its old endpoint disappeared.
- Each app gets its own host-instance canary; canary PASS is readiness, not a
  substitute for corpus qualification. Missing host/profile/readiness fails
  visibly and retryably where appropriate, without falling back to another engine.
- Existing language/runtime boundaries stay: deliver the shared Rust and Python
  host clients specified below against one contract; do not create a general engine/plugin
  framework or an unreviewed proxy to avoid native socket verification.

## Shared host clients and adding a consumer

CONFIRMED at the inventory revisions: Invoice owns the app-side attachment in
[setup/attach.py](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/attach.py#L17-L32),
with `profile.py`, `fetch.py`, `extract.py`, `records.py`, socket verification and
store helpers. The host repository delivers the host; the inventory does not
establish an existing reusable app-client release. The original work order's
reference to established client interfaces did not specify this missing owner.

PROPOSED, owned by `connect-runtime`: one released host client per language.
Extract a Python package from Invoice's setup implementation without changing
observable behavior; derive the Rust crate from U1's Doc Sum attachment work.
The slice contracts name package locations, exact extraction boundaries and
release/dependency pins before code changes. Keep application prompts, validators,
canary payloads, data paths and scheduling policy in explicit consumer adapters;
keep common lease, profile/identity verification, authenticated transport and
attachment behavior in the shared clients. No private client forks or copied
attachment implementations in apps or automation packs. This is reuse of the
single ADR-0011 host contract, not a general architecture/plugin framework.

Each client release pins the canonical profile by hash. Client version, source
revision, built artifact hash and profile hash belong to each consumer's
qualification identity. U4 must prove Invoice's move is transparent before its
private implementation is removed; any unavoidable difference is listed and
qualified separately, never hidden in the extraction. Reuse Invoice's existing
attachment tests and real request/scoring evidence as the regression guard.

Adding an app or Connect Automate pack requires all of the following:

- Record the licensor's express product designation in the versioned external
  designated-products record defined by the [proposed client terms](PR-Shared-Client-Proprietary-Terms.md#external-designated-products-record),
  once those terms and that record are accepted. Bind its revision/hash and entry
  in that consumer's permission evidence; do not edit the immutable client release
  or other consumers' client pins to add a product. This proposed checklist
  amendment grants no designation or distribution authorization by itself.
- Depend on the released shared client for its language and vendor the exact
  profile by hash; verify the registration and instance rather than discovering
  or selecting another engine. A new language requires a separately accepted
  client contract, not a private fork or an ad hoc proxy.
- Take a lease while model work is queued or active, including retries that still
  need the model; release it when that consumer's queue is empty, according to
  ADR-0011's foreground/background lifecycle rules.
- Run a consumer-owned canary per verified server instance and preserve peer,
  profile, model and template identity checks. Canary success is only readiness.
- Declare effective request/queue deadlines, retry and cancellation semantics,
  scheduling guarantees and observation points in the contention model below.
- Qualify that consumer's real inputs, outputs, validators and business-action
  idempotency separately; bind installed artifact/client/profile identities.
- Treat a different model or additional slots as a new canonical profile and
  requalification for every consumer before adoption. No local override bypass.

## Shared-slot contention gate

Before either U2 or U3 cutover, exercise the complete matrix on the proposed
shared clients, pinned one-slot host and real app request paths. Earlier
Email/Invoice overlap alone cannot qualify Doc Sum's interference. Preserve
actual app budgets; no live business actions. A missing peer implementation or
unaccepted scheduling requirement is an explicit blocked gate, not a waived row.

| Participants | Required schedule coverage |
|---|---|
| Doc Sum × Email Watcher | Both arrival orders; Email arrives during a long Doc Sum prefill and generation; reverse the holder and waiter. |
| Doc Sum × Invoice Processor | Both arrival orders; long holder and queued extraction, including a queued timeout and recovery. |
| Email Watcher × Invoice Processor | Both arrival orders, repeated offers and recovery after a holder completes or is cancelled. |
| All three | Each app as initial holder, simultaneous and staggered queued offers, timeout/retry/cancel, then continued arrivals to test progress. |

Source-bound timeout inventory (configuration is not installed-state proof):

- Email defaults to 60 seconds, configurable from 1 to 300, in
  [config.py](https://github.com/canfieldjuan/eom-email-watcher/blob/3edcae19de0fff45ebc808aa5650e17a411a2e45/src/eom_email_watcher/config.py#L483-L496).
  `runtime_from_config` passes this to either route; HTTPX request-phase timeouts
  are not proof of a total end-to-end deadline.
- Invoice's generic model timeout is 300 seconds, but its existing shared-host
  path [overrides it](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/attach.py#L408-L414)
  with [82 seconds for CUDA / 89 for Vulkan](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/profile.py#L104-L105).
  [LoopbackModel](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/model.py#L318-L325)
  applies HTTPX phase limits with a separate 3-second connect timeout. Do not
  qualify the shared-host route as if its request limit were 300 seconds.
- Doc Sum gateway timeout and request lifetime are each 900 seconds in
  [model_settings.rs](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/model_settings.rs#L41-L42).
  Its native path also has a 900-second request timeout and a separately bounded
  [slot-acquisition wait](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/llama_cpp.rs#L674-L680).
  These are separate boundaries, not a proven 900-second end-to-end cap.

For each qualified app revision record configured and effective boundaries,
including attachment, local admission, host queue, transport, retry/backoff,
request lifetime and cancellation. Keep every offer and stable job/request ID;
record queue delay separately from inference where observable and label missing
boundaries unknown. Preserve timeout/rejection classification and retry hints
through the app scheduler: retryable remains retryable, with no lost or duplicated
work or repeated business actions after an ambiguous response. Demonstrate
progress without starvation beyond each app's accepted scheduling contract. If
that contract lacks a bound, surface and settle it explicitly before cutover;
do not invent a passing threshold or assume server FIFO/fairness. Any timeout,
queue, retry or scheduling-policy change is a named default-alignment item with
its own accepted behavior and comparison. This gate does not authorize changing
production admission or adding runtime slots.

## Default alignment: explicit differences, not incidental fixes

| Item | Port baseline / proposed disposition | Acceptance or evidence owed |
|---|---|---|
| Host/profile/model identity | Exact canonical profile bytes across apps; no per-app model auto-selection. Current GPU 9B only. | Setup, attach, alias/build/template verification and installed artifact binding for every release. |
| DS context and default | Existing gateway@1 / 8192 and older direct preset become a proposed host-bound 32768 default for NEW runs. | This is an intentional behavioral difference, qualified by ds-qualify-c9; no presumption that larger context produces prose or better summaries. |
| Email temperature/seed | Preserve 0.1/no seed for route port; propose 0 only as a later named alignment change. Seeded controls must retain real temperatures and be identified as controls. | Exact-revision operator decision and same-fixture task scoring before default 0 adoption. No universal seed added by this work order. |
| Schema order/grammar | Preserve source request order and supported strict grammar. Do not import gateway sorting into host requests. | Capture request bytes; adversarial/order-sensitive Invoice cases; gateway #35 remains a separately tracked defect until that route retires. |
| Body/token/output budgets | Preserve app limits during transport port; measure tokenizer-backed fit against effective 32768. | Email 20000/100000 character limits are not token guarantees. Reject over-budget input explicitly; do not silently truncate or homogenize every app's output cap. |
| Prompt cache, batches, KV, attention, checkpoints | Keep pinned effective behavior; do not copy sandbox q8_0 or diagnostic settings. | Record effective values. Any changed default is a new comparison identity; cache-off is not silently adopted. |
| Timeout / queue / retry policy | Preserve the route-specific boundaries in the contention inventory, including Invoice tier limits; bind actual configured values for each installed consumer. | Complete all contention rows before U2/U3 cutover. Any change to deadlines, fairness, retry/backoff or admission needs a named operator-accepted alignment comparison, not an incidental transport fix. |
| Stale installed settings | Classify configured model names as used/unused per route; preserve user config until accepted migration. | Binding receipts and migration tests; no live settings edited during contract work. |

## Retirement boundaries and rollback

After accepted cutovers, app inference uses the shared host. Explicitly cover:
Doc Sum's direct Ollama and in-process llama.cpp owner; its gateway task route;
Email Watcher's gateway and loopback/LM Studio paths; Invoice's gateway bypass
and product TCP override; and gateway `OllamaWorker`, `LMStudioWorker` and engine
fallback as app inference paths. Test-only TCP fixtures must be impossible to
select through normal product defaults; no automatic fallback remains.

Do not uninstall third-party runtimes, stop unrelated sessions, erase models,
credentials, stored results or private evidence. Retiring code/routes is distinct
from deleting services or data. Proposed rollback uses the last qualified app
release/config snapshot through an explicit operator action, preserving saved
run identities; it is never an automatic alternative-engine retry. Each U5
contract identifies the rollback artifact and proves no database downgrade or
result loss is required before removing the route.

### U5 hardware support decision

The current [canonical profile](../runtime/v1/profile.json) has only `gpu-cuda`
and `gpu-vulkan`; both require a memory floor of 7373 MiB for the pinned 9B model.
This is a profile admission floor, not a blanket claim that any GPU of that size
is supported: the other device/driver/platform requirements still apply. There
is no CPU tier. Retiring every old route would leave machines outside those
requirements with no app inference route.

U5 is blocked until a recorded operator decision names the supported hardware
and platform floor, the affected existing-user inventory, and the accepted
transition/communication and rollback policy for users outside that floor.
Do not silently withdraw their working route. Until the decision and its
transition proof are accepted, retain affected routes and mark retirement
incomplete; do not add an automatic fallback or pretend those machines passed
host qualification. A decision to retain broader hardware support requires a
separate accepted profile/qualification work order before the corresponding
retirement. This proposal does not add a CPU tier or another model.

## Qualification and platform dependencies

[ADR-0015 / PR70](https://github.com/canfieldjuan/connect-contracts/pull/70)
remains proposed at `664f3f7bed43c7a0542a248203a147f2e378868b`. Its identity/effective
settings/independent-answer rules inform this work order; they are not merged
requirements or authorization to edit schemas. The record schema and host capture
work follow its accepted landing order, owned by this runtime session. Before
qualification, settle that dependency or accept an explicit versioned evidence
contract; never claim effective fields from argv or document defaults alone.

Record app and installed build identity, shared-client release/source/artifact hash,
vendored profile hash and PROFILE_ID, runtime archive/library and
model/template hashes, GPU/driver/runtime, effective per-slot context, slots,
batch/ubatch, checkpoints/cache, attention, offload and KV precision. Mark missing
observability unknown. Keep input preparation, native output and interpretation
as separate first-divergence boundaries. Retain offers/errors/rejections and
correct completed jobs, queue delay separately from inference where observable;
never derive token timing from nonstream replies or compare unequal work as speed.

[Windows ADR-0012 / PR58](https://github.com/canfieldjuan/connect-contracts/pull/58)
is OPEN at `a7d93f585119c614f88e9191001610716f109c2e`. Windows adoption is blocked
until its exact accepted revision, implementation, platform measurements and
app route proof exist. Linux-only success cannot authorize a Windows release or
removal of Windows' current path. Do not hide the dependency with TCP fallback.

[LAN gateway role #16](https://github.com/canfieldjuan/connect-contracts/issues/16)
is a later product/transport decision: if selected, it fronts the same host,
not a second engine. No LAN serving, endpoint redesign or gateway-host proxy is
implemented or implicitly accepted here. Connect capabilities/automation APIs,
entitlements and business-action semantics remain unchanged; audit their app
runtime callers within each app slice rather than expanding this into a new API.

## Verification plan and explicit non-scope

For this PR: review source pins/permalinks, dependencies and slice gates; check
Markdown links, `git diff --check`, and prove only this work-order document is
changed. No new tests that merely assert prose, no dependency installation, and
no duplicated application or model suites for a docs-only diff.

For accepted implementation slices: focused fail-before/pass-after tests at the
actual owner; attach race, incompatible profile, stale peer, lease release,
timeout/cancel, order-sensitive schema, pending-result replay, resumed-run
identity, token boundaries and retry tests. Both normal and rejected routes must
be exercised. Qualification preserves real validators, independent labels and
human summary review. Performance thresholds remain for agreement after matched
baseline measurements. No full-corpus parity or speed gate is waived.

Non-scope: engine fork/upgrade, diagnostic kernel adoption, additional models or
hardware, CPU-tier restoration, more slots, production admission tuning, eight-hour
soak, automatic route retirement, installs, service changes, promotion or merges.

## Implementation summary, cold diff audit and gap audit

This PR adds only this proposed work order. Runtime/profile/schema bytes,
applications and live services are unchanged. Inventory links are pinned source,
not installed-state claims. Source snapshots and evidence digests are retained
outside worktrees under the runtime owner's durable evidence root.

NOT DONE: oversight CONTRACT REVIEW, exact-revision operator acceptance,
coordination-base confirmation, shared-client delivery, app attach/migration,
full contention qualification, hardware-floor decision, live qualification,
Windows dependency, default alignment decisions and retirement. Publishing this
proposal does not satisfy any of those gates.
