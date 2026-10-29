# U1 contract: shared Rust host client and Doc Sum attachment

Status: PROPOSED; no executable work is accepted by this document.
Owner: connect-runtime. Parent: [accepted unification work order](PR-Shared-Runtime-Unification.md),
merged in [PR81](https://github.com/canfieldjuan/connect-contracts/pull/81) as
`95a98c8e937799976f5392bbb08bcc60d392a461`.
Juan's direct "We can start implementation" advances this slice within the
parent's gates. This exact slice contract still requires review and acceptance
before runtime edits. No U2 cutover, live inference or retirement is included.

## Root cause and preserved evidence

Doc Sum's current native runtime couples request preparation with ownership of
an app-private server. It has no ADR-0011 shared-host route or released Rust
client. Adding another app-local copy of Invoice attachment would duplicate the
security-sensitive owner. Separate lifecycle/transport at that origin while
preserving the native generation inputs and interpretation.

Confirmed source bases, independently of local checkout heads:

| Repository / base | Owning source and established behavior |
|---|---|
| local-connect-model-host `f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b` | [lib.rs](https://github.com/canfieldjuan/local-connect-model-host/blob/f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b/src/lib.rs) exports lease/profile/launch primitives. [coordination.rs:68-86](https://github.com/canfieldjuan/local-connect-model-host/blob/f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b/src/coordination.rs#L68-L86) owns shared lease acquisition/release. [host.rs:107-143](https://github.com/canfieldjuan/local-connect-model-host/blob/f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b/src/host.rs#L107-L143) owns transient launch. [profile.rs:31-46](https://github.com/canfieldjuan/local-connect-model-host/blob/f97f2da4d8b452ff6cbec4b6bca77ac5c1c94a9b/src/profile.rs#L31-L46) admits the exact vendored profile. |
| document-summarizer `7911f4375772fbc2e6c063a4e4a82aea7d638751` | [model_settings.rs](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/model_settings.rs#L854-L881) owns runtime selection; `runtime_from_snapshot` at974 owns restoration. [contracts.rs:442-468](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/contracts.rs#L442-L468) owns persisted runtime identity; `ModelRuntime` at861 is the consumer interface. [llama_cpp.rs:577-600](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/src-tauri/src/pipeline/llama_cpp.rs#L577-L600) serializes token-array completion with seed, temperature0, cache_prompt true, stop token, schema and output cap. |
| invoice-processor `f7281d71e050fd5e9c746bb5e45c55862af12c26` (read-only reference) | [setup/attach.py](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/attach.py#L177) implements the app-side reference. [setup/socket.py](https://github.com/canfieldjuan/invoice-processor/blob/f7281d71e050fd5e9c746bb5e45c55862af12c26/src/invoice_processor/setup/socket.py) verifies the connected peer before returning the stream to HTTP. Python extraction remains U3; Invoice adoption U4. |

Reuse the parent inventory: canonical profile/runtime/model/template, existing
301-file source receipt, pre-production evaluation and real corpus manifests.
Do not rebuild them. The reference input is Doc Sum's native serializer and
framing, not Invoice's chat payload. Whole-writer quality remains ds-qualify-c9's
responsibility. Its exact canary and qualified native request receipt are pending
coordination and are gates for readiness/live proof, not invented fixtures.

## Delivery and required change surface

Two sequential implementation PRs, separately reviewable, one app per PR:

**U1a — shared Rust client in local-connect-model-host.** Create the package
`local-connect-model-client` at `crates/model-client/` and register it as a workspace
member. It depends on the existing host library's canonical profile and lease
owners on Linux; no copied lease policy, secondary profile schema or app-private
client. Changes are limited to root `Cargo.toml`/`Cargo.lock`, the new crate's
manifest/source/tests and its contract/release documentation. Existing host
library modules may expose the minimum existing identity/file helpers needed by
the client, with focused tests at that owner; no host execution/admission changes.
Extend CI to include the crate's fmt/clippy/tests so workspace defaults cannot
silently omit it. Record client release/source/artifact/profile hashes.

**U1b — Doc Sum adapter on the reviewed U1a client revision.** Add
`src-tauri/src/pipeline/shared_host.rs` and module wiring. Scope of existing
runtime files, including the seven-file coordination intersection:

| File under src-tauri/src/pipeline | Allowed U1 change |
|---|---|
| contracts.rs | Add the shared-host runtime kind and immutable binding described below; preserve old snapshot serialization. |
| model_settings.rs | Explicit shared-host selection, new snapshot creation/restoration, stage dispatch and admission; unchanged default and existing routes. |
| llama_cpp.rs | Extract reusable native request/token framing and bounded response decoding into `native_request.rs`; private-child lifecycle stays on the old route. Both routes consume the same request owner. |
| llama_cpp_framing_tests.rs | Absent at this main pin; if another reviewed branch lands it first, adapt/move only framing tests needed for the common owner, preserving expected bytes and coordinating conflicts. |
| gateway_client.rs | No U1 changes. |
| gateway_runtime.rs | Only a mechanical `None` in historical snapshot construction if required by the additive binding. No request, retry, replay or task-version changes. |
| model.rs | No U1 changes. |

Other allowed files: `pipeline/mod.rs` for module wiring; `src-tauri/Cargo.toml`
and lockfile for the exact reviewed client dependency; focused adapter/request/
snapshot tests; release pin documentation. Mechanical `shared_host: None`
constructor additions may be needed in existing fixtures in `connect/ocr_consumer.rs`,
`connect/provider.rs`, `connect/store.rs`, `desktop.rs`, `pipeline/corrections.rs`,
`pipeline/db.rs`, and `pipeline/service.rs`. No behavior changes in those modules.
Readers in `lib.rs`, `pipeline/ingest.rs`, and `tests/office_acceptance.rs` are
verification targets; source discovery does not grant unrelated write scope.

Do not carry a development filesystem path dependency into the app release.
The Doc Sum dependency pins the reviewed client Git revision or immutable release
artifact; source/build/artifact/profile bindings form the qualification receipt.
No Python implementation, engine plugin abstraction or proxy service in U1.

## Shared client and transport invariants

The client owns bounded attach, safe registration/key access, lease lifetime,
profile/instance admission and authenticated transport. The application owns
paths, canary payload/expected result, scheduling, prompts and task validation.
Reuse ADR-0011 deadlines and file/identity rules. Never terminate or replace a
foreign-profile host, and never terminate the shared server on app Drop/error.
Hold the lease while model work is queued/active; close only the client's own
handles when work ends. A failed canary never grants document readiness.

Use the actual connected Unix descriptor for the peer check. The proposed seam
is `tokio::net::UnixStream`, peer credentials plus registered process start/boot
identity, followed by `hyper::client::conn::http1::handshake(TokioIo(stream))` on
that same verified stream. Authenticate/send only after verification. Every new
connection is checked; no unchecked reconnect, TCP fallback, redirect or proxy.
The shared client exposes bounded byte-oriented requests; it must not parse and
re-serialize application JSON schemas. Use Hyper's HTTP parser, not an ad hoc one.
A dedicated bounded adapter worker can bridge Doc Sum's synchronous trait without
blocking or nesting a Tokio runtime on a caller executor. Cancellation closes the
owned exchange and preserves the app's typed outcome; it never kills the host.

These dependency versions already occur in Doc Sum's pinned Cargo.lock: hyper
1.11.0, hyper-util0.1.20, http-body-util0.1.5, tokio1.53.1, bytes1.12.1 and http1.5.0.
Adding the necessary direct client dependencies/features is an explicit source
manifest/lock change for this slice, not authorization to install/upgrade the
host environment. Reuse locked versions; review any newly resolved transitive
changes before implementation proceeds. The host crate's Linux dependency is
platform-gated. Existing Windows routes must still build; this does not implement
or claim ADR-0012 Windows shared-host support.

## Immutable snapshot and selection contract

Add `InferenceSource::SharedHost` and `ModelRuntimeKind::SharedHost` as explicit
opt-in route values. Existing default/Direct/Gateway behavior remains unchanged;
no settings file is rewritten during development and no UI/default cutover is
part of U1. Expose this route through the existing settings/runtime entry points
for the accepted qualification path, with explicit unsupported-platform refusal.

Proposed snapshot version4 retains the existing analysis/verification stage
fields and adds an optional `sharedHost` binding at the outer snapshot owner.
Its Rust field uses serde default and skip-if-None so versions1/2/3 retain their
serialized bytes. The binding has `profileId`, `clientReleaseId`, `hostBuildId`
and `canaryBindingId`, each identifying exact qualified bytes through the release
receipt. The profile hash is computed from canonical bytes; release/build/canary
IDs are content-bound manifest IDs, never mutable labels or paths. No server PID,
key, socket path or private document data is persisted in the snapshot.

Version4 requires the complete binding and both stages to use the admitted
shared-host kind/profile/model/context/tokenizer tuple. Reject a missing/partial
binding, foreign profile/client/canary binding, mixed route stages, or unknown
version before generation. Versions1/2/3 reject a shared binding and continue to
restore their historical route. Do not reinterpret old IDs or rewrite old runs.
The existing `db.rs::ensure_run_model_profile` equality check remains the durable
owner of immutability; child/retry copies retain the original serialized profile.
No database migration or replacement snapshot store is required.

## Differences, limits and qualification

Intended differences are shared host attachment/lifecycle, explicit new route
identity, verified transport and consumer canary. Preserve native token arrays,
prompt framing, reasoning-off handling, schema property order, seed/temperature,
cache behavior, output cap and response interpretation. Native-request extraction
must pass a byte-transparency gate before using it through the new transport.
The old private runtime and canonical host artifact are separately pinned; equal
serialization does not imply equal numerical execution or qualify a new model
route. List all artifact/effective-setting differences in the U1b handoff.

Keep Doc Sum's existing request/tokenization time budgets and local admission
semantics; attach adds ADR-0011's separately reported bounds. Record boundaries
rather than converting request limits into an invented end-to-end guarantee.
No hidden retries, scheduler fairness changes, new default, extra slot, profile
change or fallback. U2 remains responsible for accepted 32k task quality; full
cross-app contention remains a prerequisite to U2/U3 cutovers.

U1 source implementation may operate against a prepared canonical store for
qualification. Missing store or host package fails explicitly; no automatic
large downloads or fake readiness. A distributable app setup/host sidecar binding
must be recorded and verified before any installed-route or production claim.
That package binding is a handoff gate, not permission for a live install here.

## Verification plan

Use focused fail-before/pass-after probes at the owner, plus adjacent existing
regressions and required fmt/clippy checks. No live model/GPU runs under U1.

- Real local socket fixture: correct peer sends request bytes; wrong UID/PID,
  reused PID/start time, swapped path and stale instance send no auth/model bytes.
  Verify the actual sent connection, not a second observation socket.
- File and identity boundary probes: safe input accepted; malformed, partial,
  symlink/nonregular/unsafe registration/key and mismatched profile refused;
  no foreign-host stop/replacement or fallback; sensitive values never logged.
- Attach races: shared lease retained while queued; per-instance canary binding
  checked; concurrent consumers and canary rejection preserve server ownership;
  failed/cancelled/closed clients release only their handles.
- Deadline, cancellation, bounded body/header and interrupted-response cases:
  typed retryability retained, no swallowed failures, no post-cancel generation,
  no detached unbounded worker or connection leak. Queue delay stays distinct.
- Native-request extraction: byte-identical body/schema/token framing from the
  same existing fixtures, before and after. Port output interpretation separately;
  synthetic tests do not claim real task accuracy or model output parity.
- Snapshot probes: byte-identical old serialized cases; version4 complete binding
  admitted; mixed/missing/mismatched binding rejected; persisted/retried old runs
  unchanged and profile mismatch still refused by the existing DB owner.
- Preserve existing Doc Sum cancellation, prompt-fit and startup-identity tests;
  host lease/race tests remain green. Verify Windows compilation/old-route
  behavior on the applicable CI platform before merge; Linux-only success is not
  a waiver. Do not duplicate broad required CI unnecessarily.

Reference tests already exist in host `tests/coordination.rs`, Invoice
`tests/test_shared_host.py` and Doc Sum `llama_cpp.rs` (including queued
cancellation, framing-reserve fit and startup identity). Reuse these invariants;
add the minimal regression at the new client/adapter seam. Full-corpus quality,
human summary review and performance comparison remain separate later gates.

## Coordination and explicit blockers

Oversight confirmed the Doc Sum main base above. U1 owns runtime-selection seams,
the new route and client dependency. ds-qualify-c9 retains summary verification
and parser work. Open #116/#126 overlap the seven runtime files; held #154/#155
overlap Cargo.toml/lock. Whichever lands second rebases, with conflicts resolved
through oversight and no silent deletion of the other owner's work.

Before code: exact U1 review/acceptance and confirmed host-client integration
base. Before app attachment readiness/live qualification: reviewed U1a release,
Doc Sum canary request/expected result and native request receipt, exact artifact
pins and prepared-store/sidecar binding. Those values must come from the existing
qualification owner or an explicitly accepted new qualification; no placeholder
canary can be labelled qualified. No current blocker authorizes a scope expansion.

## Implementation summary, cold diff audit and gap audit

This PR adds only this proposed U1 contract. No runtime/client code, dependencies,
application settings, model files, test inputs or services change. Validate source
citations and docs-only diff; no application/model tests are needed for prose.

NOT DONE: exact-contract review/acceptance, implementation, release binding,
canary readiness, application qualification and cutover. Parent PR81 is merged;
that does not mark these U1 gates complete.
