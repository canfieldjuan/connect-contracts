# U1 contract: shared Rust host client and Doc Sum attachment

Status: PROPOSED; no executable work is accepted by this document.
Owner: connect-runtime. Parent: [accepted unification work order](PR-Shared-Runtime-Unification.md),
merged in [PR81](https://github.com/canfieldjuan/connect-contracts/pull/81) as
`95a98c8e937799976f5392bbb08bcc60d392a461`.
Juan's direct "We can start implementation" advances this slice within the
parent's gates. This exact slice contract still requires review and acceptance
before runtime edits. No U2 cutover, live inference or retirement is included.

Operator distribution decision, relayed at 2026-10-29 16:05:06 UTC:
"Public client with amended contract". This selects a public client and its
necessary shared primitives, not private CI credentials or publication of the
host implementation. This amendment is contract-only; no source extraction,
public repository/release creation, credentials, runtime edits or merge is
performed or authorized by publishing it. Exact-revision acceptance follows
independent delta review.

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
responsibility. Its owner confirms there is NO approved Doc Sum per-instance
shared-host canary. U1 defines only the interface and fail-closed behavior;
ds-qualify-c9 proposes the request/expected pair within its 32k qualification
contract. Neither the C7 thinking diagnostic nor synthesis parity calls qualify.

Preserve the owner's historical receipt alias
`native-message-boundary-repair-20261007/production/receipt.json`, SHA-256
`6848dd2dabcd5b60c78052c065227d3e7aac7d680089cf81554b9938c145c520`, source
`456fa8aa9ee5e677997a3c46132c86e583777326`. These are relayed evidence bindings,
not a new replay or rehash in this contract amendment. Historical settings were
cache_prompt=true, n_predict=1500, temperature=0, seed=4294967295 and
message_delimiters framing. Bind/verify the complete existing receipt before
parity execution. Raw artifacts stay heldout; elsewhere use aliases and hashes.
List every U1 runtime/profile/effective-setting difference explicitly. Shared-host
results must not be labelled as this historical baseline.

## Delivery and required change surface

Sequential implementation PRs, one owner and one app per PR. Keep the shared
primitive extraction separate from the new client behavior. If U1b exceeds about
1,000 changed lines, split native-request extraction/transparency from route and
snapshot integration; each remains independently reviewable and preserves gates.

**U1a — public primitives, then public Rust client.** The canonical source home
is a proposed public repository `canfieldjuan/local-connect-model-client`, with
Rust packages at `crates/model-primitives/` and `crates/model-client/`. This replaces
the initial plan to depend on the private host package. No repository is created
by this amendment. Public release/creation needs the accepted boundary, licensing
clearance and reviewed implementation; never expose private Git history by
changing host visibility or pushing its branch/history to the public repository.

The private host consumes the exact reviewed shared-primitives release and
removes the extracted implementations from its former owners. During a staged
extraction, no consumer release is ready until host and client use the same
canonical implementation. Vendored release copies are byte-identical distribution
artifacts, not independently maintained implementations. No app-private forks.
Host changes are limited to those extraction seams, dependency/lock entries,
provenance and adjacent regression tests; admission, idle and execution policies
remain unchanged. The public crates MUST NOT depend on `local-connect-model-host`,
its workspace, build scripts, private Git/registry sources or private assets.

The public source/asset closure and consumer distribution are defined below;
that allowlist replaces permission to expose arbitrary host helpers.

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

Consumer manifests use only the complete vendored public release described below;
no dependency points to a developer checkout, private Git URL or private registry.
No Python implementation, engine plugin abstraction or proxy service in U1.

## D1 origin, public boundary and distribution

The original contract commit `f3f906e8114bcdd57514fe18d46e7c2260c589e7`
introduced D1 by making the client depend on the private host crate while leaving
consumer distribution unspecified. The empty follow-up commit changed no bytes.
GitHub reports host PRIVATE, Doc Sum and Email Watcher PUBLIC. At host base
`f97f2da`, Cargo.toml has one `publish=false` package and lib.rs includes profile,
leases, ELF/runtime files, GPU and process execution. Publishing only a client
folder would retain that private dependency. Doc Sum's pinned
[public CI](https://github.com/canfieldjuan/document-summarizer/blob/7911f4375772fbc2e6c063a4e4a82aea7d638751/.github/workflows/rust.yml)
runs locked Cargo tests/clippy and platform release builds. This amendment fixes
the dependency owner, not CI by adding credentials.

### Complete allowed public source and asset closure

This is a symbol-level extraction allowlist, not permission to export entire
private source files. Public module names below are planned locations under the
new repository; each extracted symbol records its original file/revision/hash.
Any required source/asset outside this list stops extraction for Juan's explicit
boundary decision. Never broaden it implicitly to make a build pass.

| Public unit | Allowed contents / source seam | Required private remainder |
|---|---|---|
| `crates/model-primitives/src/profile.rs` | Pure canonical profile decoding, hash identity, data structs and read-only tier metadata/accessors from host `src/profile.rs`; no alternative profile policy. | `Tier::prepare_runtime`, `RuntimeSet::prepare`, `PreparedRuntime`, descriptor sealing and executable/library preparation remain host-owned. Host uses the shared parsed metadata through a private preparation function. |
| `crates/model-primitives/src/files.rs` | Generic no-follow absolute/component traversal (`open_regular`, `open_private_directory`, its owner-directory helper, `open_absolute`, `walk`, `open_at`) and bounded size/hash reading from `src/files.rs`. Hash/copy has an explicit per-read budget callback; host passes its existing check at the same read boundary. | Model/store runtime admission, memfd sealing, `VerifiedRuntime`, library-directory construction and thread-local `AdmissionBudget` remain private. Do not drop or duplicate host cancellation/deadline checks while separating hashing. |
| `crates/model-primitives/src/lease.rs` | Registration-directory admission, safe lock opening, low-level flock/unlock and client shared-lease acquisition/RAII (`RegistrationDirectory::open/lock_file/acquire_client`, `ClientLease`, CLIENT_WAIT) from `src/coordination.rs`. Host election consumes these helpers rather than keeping copies. | `try_elect` orchestration, `HostLease`, `IdleWindow`, `HostedServer`, `HostEvent`, idle grace/probe policy, shutdown and server spawn remain private. |
| `crates/model-primitives/src/identity.rs` and `wire.rs` | Read-only process/boot identity (`Process`, `Identity`, `process`, `boot`) and server/failure wire data types from `src/host.rs`, matched to public schemas. | Record mutation/cleanup, logs and failure-tail collection, signal handling, health/probe execution and `run_host` remain private. |
| `crates/model-primitives/src/start_request.rs` | `HostConfig` path/profile/start-id validation and argument encoding only. | Host startup composition, GPU selection and server execution remain private. |
| `crates/model-client/src/start.rs` | The existing `launch_transient` client-side service invocation only, adapted to shared request/lease types. It requests the separately installed host service; it does not implement or bundle that service. | No `probe_entry`, `probe_store`, `run_host`, executable main, GPU/device code or runtime loader. Private callers needing the same launch helper consume the canonical client helper without a dependency cycle. |
| `crates/model-client/src/{lib,attach,transport,canary,error}.rs` | New ADR-0011 attach/readiness, verified Unix HTTP transport, canary interface and client errors; no business payloads. | No Invoice implementation extraction here, app validators, prompts, business actions or installed configuration. |
| `crates/model-primitives/src/{lib,error}.rs` | Module exports and common I/O/profile/integrity/lease error subset only; private host errors map at its adapter. | Runtime/GPU/supervision error internals stay private. |
| Public profile/wire assets | Exact bytes from public connect-contracts `runtime/v1/profile.json` and `schemas/runtime/v1/{profile,server,failure}.schema.json`, with origin pins and hashes. Package them under `crates/model-primitives/assets/`; include paths remain within the release. | No runtime binaries, shared libraries, model weights, private host checkout/vendor tree, keys, local records or logs. |
| Package/build/release closure | Root and crate Cargo manifests, lockfile, README, LICENSE/NOTICE, provenance and release manifests, public CI workflow, release verifier script, and sanitized client/primitives unit tests and synthetic local-socket fixtures. Every path/byte is listed in the release manifest. | No private fixture corpus, test helper that spawns a private host executable, hidden workspace dependency or build-time download/generated input from private source. |

`src/{gpu,elf,process,model}.rs` and executable host supervision are excluded in
full. Private file names above are provenance pointers only. No model/runtime
artifact is made public through this client decision. The full exported set is
reviewed before publication, including test/build dependencies, all features and
all supported target graphs. A directory-only copy or a cargo-package listing
without its dependency/assets closure is insufficient.

### Distribution for each consumer

The canonical public repository publishes a reviewed source archive containing
the complete Rust client/primitives workspace, license/provenance, lockfile and
assets. It is pinned by immutable public source commit plus archive SHA-256 and
per-file manifest. Tags/URLs alone are insufficient. Release creation is a later
reviewed action; no placeholder download may be presented as an available release.

| Consumer | Required distribution and build rule |
|---|---|
| Doc Sum (public, U1b) | Vendor the complete reviewed Rust release at `src-tauri/vendor/local-connect-model-client/`; use repository-relative path dependencies into it, with committed Cargo.lock. CI verifies the entire vendor tree, including extra/missing files, against the pinned public release. No developer absolute path or private fetch. |
| Private model host (U1a integration) | Vendor the same shared-primitives release under `vendor/local-connect-model-client/`; compile those exact canonical bytes and remove former duplicate owners. If its service-launch helper is used, consume the canonical client module too. The dependency direction is private host to public primitives/client, never the reverse. |
| Email Watcher (public, U3) | Vendor the complete future public Python client source release at `vendor/local-connect-model-client-python/`, with hash/provenance and a locally built/importable package pinned by its existing dependency lock mechanism. Its release must include its entire public source/assets closure and no dependency on private Invoice/host code. U3 defines the Python extraction in its own accepted contract; no Python code is exported by U1. |
| Invoice (U4) | Adopt that same reviewed Python release with byte-equality and transport-transparency proof. A local host-sidecar build pin is not evidence that the public client is distributable. |
| Future apps/automation packs | Consume the matching immutable public language release through the parent checklist and their own qualification; no per-app edits to vendored client code. |

### Licensing, provenance and clean public build gate

No tracked LICENSE/COPYING/NOTICE file was found at the inspected host, Doc Sum
or Invoice source pins. Public repository visibility is not a license grant.
Before publishing extracted code, record rights/attribution for each origin,
obtain the operator's license decision, retain notices and verify dependency/asset
license compatibility. Do not claim exclusive ownership of inherited code or
invent a license. License clearance blocks publication, not this contract review.

The extraction receipt records original commit/symbol spans and content hashes,
new canonical public commit, package versions, exact public asset origins/hashes,
license identifiers/notices, archive SHA-256, file manifest, dependency graph and
artifact hashes. Private ancestry is referenced only by approved provenance;
it is never copied into the public Git history. All consumers verify identical
release bytes, and fixes go to the canonical source before a new pinned release.

Before U1 client or consumer-build readiness, run fresh public-consumer CI at the
exact release pin, with no private credentials, SSH agent, credential helper,
private registry config, pre-populated private Cargo cache or local host checkout.
Checkout must not persist credentials; release/dependency fetch and build steps
must succeed without repository tokens. Fetch only public sources. Record the
resolved normal/dev/build/target dependency graph and reject private URLs,
workspace escapes or undeclared generated inputs. A private Linux-only dependency
is still a failure even if another target happens to compile without it.

Prove: public release download/hash/complete vendor equality; standalone client
and primitives locked tests/build; then Doc Sum's required locked test/clippy and
normal release build at its exact consumer revision on supported CI platforms.
Run the analogous public Email build gate when U3 supplies Python. Include
negative verifier probes for a modified source or asset, missing/extra file and
a disguised private dependency, plus a valid pristine release. Record cold-cache
CI evidence and output artifact hashes; a developer's authenticated build is not
substitute proof. No model/GPU or production service is needed for these gates.

This gate proves public source/client and consumer builds, not host installation
or model readiness. A release build must not secretly fetch a private host
sidecar: keep the prepared/installed-host precondition explicit until a separately
authorized host artifact/setup distribution is bound. If packaging cannot build
without exposing another host asset, stop for Juan's decision; neither publish
that asset nor inject credentials. No full app/runtime rollout claim until the
host delivery and real consumer qualification gates are separately satisfied.

## Shared client and transport invariants

The client owns bounded attach, safe registration/key access, lease lifetime,
profile/instance admission and authenticated transport. The application owns
paths, canary payload/expected result, scheduling, prompts and task validation.
Reuse ADR-0011 deadlines and file/identity rules. Never terminate or replace a
foreign-profile host, and never terminate the shared server on app Drop/error.
Hold the lease while model work is queued/active; close only the client's own
handles when work ends. This differs from keeping an app-private model resident:
with no other leases, current host idle grace is 10 seconds with a 2-second probe
interval (`coordination.rs:15-17`), so idle reclamation is approximately 10–12
seconds, not an inference measurement. The next job may pay model reload cost;
U2 must measure cold attach/model load/canary separately from warm requests.
Do not change idle policy or hold a dummy lease to hide that cost.

The canary interface runs after verified profile/instance attachment and before
any document request. Its persisted binding includes consumer/client/profile,
canary request/expected-result identity and server PID/start time/boot identity.
Missing approved pair, mismatch, failed or interrupted canary never grants
readiness. Test-only synthetic callbacks are labelled as such; the approved
request/expected pair remains a separate ds-qualify-c9 qualification decision.

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
changes before implementation proceeds. Only the public primitives' Unix/Linux
code is platform-gated; no target may depend on the private host crate. Existing
Windows routes must still build; this does not implement
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

Before code: exact amended U1 review/acceptance and confirmed host-client
integration base. Before public source/release publication: explicit boundary and
license clearance and reviewed extraction. Publish only a reviewed candidate at
that gate; clean unauthenticated public CI then proves readiness before consumer
adoption. Before app attachment readiness/live qualification: reviewed U1a release,
Doc Sum canary request/expected result and native request receipt, exact artifact
pins and prepared-store/sidecar binding. Those values must come from the existing
qualification owner or an explicitly accepted new qualification; no placeholder
canary can be labelled qualified. No current blocker authorizes a scope expansion.

## Implementation summary, cold diff audit and gap audit

This PR changes only this proposed U1 contract, including the public-client
distribution amendment addressing D1 at its originating dependency boundary.
No runtime/client code, dependencies,
application settings, model files, test inputs or services change. Validate source
citations and docs-only diff; no application/model tests are needed for prose.

NOT DONE: exact amended-contract review/acceptance, license/publication clearance,
implementation, clean unauthenticated builds, release binding,
canary readiness, application qualification and cutover. Parent PR81 is merged;
that does not mark these U1 gates complete.
