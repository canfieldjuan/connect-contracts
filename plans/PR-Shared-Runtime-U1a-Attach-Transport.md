# U1a: verified attachment, byte transport and canary readiness

Status: PROPOSED, contract preparation only. Owner: connect-runtime.
Parent: [accepted U1](PR-Shared-Runtime-U1.md). Immediate prerequisite:
[canonical bounded service start](PR-Shared-Runtime-U1a-Service-Start.md).
This is the second sequential client slice, not permission to implement both
in one unreviewed change. Independent review and Juan's exact-revision acceptance
precede implementation. No app route, live canary, release or cutover is included.

## Root cause and verified inventory

CONFIRMED at local client `adae73240c99f0e5329e6038f09d63309e13301d`:
there is no client transport or readiness owner. The extracted primitives are
necessary inputs, not proof of readiness:

| Source owner | Confirmed scope / gap |
|---|---|
| `model-primitives/src/lease.rs:34,41,66,88` | Registration/lock admission and a non-cloneable RAII client lease; acquisition waits at most 10 seconds. |
| `model-primitives/src/profile.rs:30,47,50,56,112,123` | Exact canonical profile admission and read-only build/context/tier/template/model accessors; no socket identity check. |
| `model-primitives/src/identity.rs:19-41` | Process start-time and boot observations. The parser does not reject zombie state; calling it alone is not the ADR liveness check. |
| `model-primitives/src/wire.rs:10-45` | Record decoding and failure serialization. Record state is a String, several required nullable fields are Option, and Failure has no owned deserialization form. Serde decoding alone does not enforce the authoritative schema/semantic rules. |
| private host `src/host.rs::launch_transient` at `3a2e3a439afb56267207b30e40c8439b5784dee1` | Service launch only; the preceding contract makes it a canonical bounded client operation. |

These gaps are confirmed in checked-out source; they are not a diagnosis of the
installed applications. No primitive is reclassified as a ready client merely
because its extraction tests passed.

Doc Sum candidate `46daeffeffd9cb1952fe54d0fadbd3abeecae139` is separately
under review in [PR157](https://github.com/canfieldjuan/document-summarizer/pull/157).
`src-tauri/src/pipeline/native_request.rs::{PromptFraming,CompletionResponse}`
owns framing/request bytes and raw response content; `FramingPolicy`'s qualified
constructor remains test-only. Its saved receipt is
`u1b-native-framing-implementation-20261030/implementation-receipt.json`, SHA-256
`bfc8eefceed2ee95fbdb22782a8731222e723aa0c58d39582ea5aa5c5c7c87ff`.
That receipt reports 18 wire cases/108 payloads, 23 typed-response cases and 10
mutation checks. They are existing offline evidence, not newly executed tests
or merged/live qualification. Full structured C9 parity remains pending.

Reuse those exact synthetic payloads, property order, response bytes and scoring
outcomes for transport transparency. Preserve parent U1's existing runtime/model,
template, prompt/settings and corpus bindings. Do not rebuild the 301-file receipt,
issue-73 inventory or pre-production corpus, and do not copy private data into this
client. Invoice attachment is behavioral reference under U1, not code to extract
here; its Python adoption remains a separate slice.

## Required change surface

In the canonical local client, add `crates/model-client/src/{attach,transport,canary}.rs`
and extend `lib.rs`/`error.rs` from the preceding startup slice. Put private record
admission and state types in `attach.rs`; transport cannot consume unadmitted wire
structs. Add synthetic attachment/socket/canary tests and exact byte fixtures.

At the existing primitive identity parser, add a read-only state observation and
liveness operation using that one parser. Preserve `process`'s existing behavior
for old callers and all extracted wire bytes; no second `/proc` parser in the
client. The added state is read-only identity metadata within U1's allowlist,
not process control. Existing `Identity`/`Process` serialization stays unchanged.
Registration schema admission belongs at the new client read boundary, not in
every consumer or in host wire serialization.

Update only necessary manifests/lock entries, source/provenance manifests,
README and synthetic test support. Reuse these versions already present in Doc
Sum's inspected lock: hyper 1.11.0, hyper-util 0.1.20, http-body-util 0.1.5,
tokio 1.53.1, bytes 1.12.1, http 1.5.0, time 0.3.55. The primitive UUID pin is
1.27.0 whereas this Doc Sum lock has 1.25.0: do not claim lock identity or silently
update the app. Resolve the client graph offline from available locked public
packages and record feature/transitive differences before coding. A necessary
unavailable/new dependency is an explicit contract amendment, not an install.

Linux runtime support is gated. Other supported targets expose typed unsupported
behavior and must build without importing Linux-only primitives. This is not
ADR-0012 Windows implementation. Existing Windows application routes must pass
their later consumer build gate; Linux results cannot waive it.

## Admission and lifetime contract

Use closed internal states: lease-held attachment, identity-verified session,
then canary-ready client. The public generation operation requires the last
state. Constructors/fields that confer admission remain private; no boolean
`ready`, unchecked Record, free-form endpoint or cached success can manufacture it.

1. **Acquire:** resolve caller-supplied ADR paths, admit the registration directory
   with the existing descriptor traversal, then acquire the shared lease before
   reading or requesting startup. No fallback directory or new path resolver.
   Retain it through queueing, startup, identity, canary and active requests.
2. **Read:** open trusted literal record/key names relative to the admitted
   directory using no-follow descriptors. Require same-user, regular, single-link,
   mode-0600 files. Refuse symlinks, directories, FIFOs and unsafe modes without
   blocking. Bound reads during reading, including file growth, not just by stat.
   Proposed client ceilings: registration/failure 16 KiB each; bearer key exactly
   the host's 64 ASCII hexadecimal bytes. No trimming or secret Debug/log output.
   These are explicit client admission rules, not new host wire schema fields.
3. **Validate:** implement the exact public server/failure schema shapes using
   closed Rust models, enum states/codes and validated scalar types, with one
   named admission function for cross-field rules. Required nullable fields must
   be present; reject missing/extra/duplicate keys, invalid UUID versions, invalid
   timestamps, out-of-range numbers and partial unselected-runtime groups.
   Use a date parser, path components and typed numbers, not parallel regex
   substitutes. Keep a rule-to-schema/semantic-test mapping against
   `schemas/runtime/v1/{server,failure}.schema.json` and
   `tests/test_runtime_contracts.py::{server_semantic_errors,failure_semantic_errors}`
   at contracts `57421c5fb6d126146b5e2e4137e7cc3e2b8ba114`.
   Runtime semantics include socket byte length and resolved-path equality,
   tier/device consistency, and aggregate failure-tail bytes. Never infer model
   readiness from schema validity alone.
4. **Attach:** follow ADR-0011's state machine, not an app-specific loop. Check
   boot, PID/start identity and non-zombie state. Ready requires both host and
   server alive. Preserve starting/unselected states as waiting only. On an
   absent/stale/stopping host, start at most once through the canonical helper;
   a live different-profile host is refused without stop/replacement. Correlate
   failure by own start ID or the host identity being awaited; ignore unrelated
   old failures. Dead awaited host ends the attach with its failure or explicit
   exited-without-record outcome. A malformed/untrusted record is an admission
   error, not permission to delete it or replace the host.
5. **Time:** use one initial 15-second publication window shared with launch;
   then the observed starting record's `ready_by` plus 10 seconds. Parse wall
   time once to a checked monotonic bound, never extend it on record refresh or
   wall-clock jumps. A deadline claiming more than ADR's 300-second startup
   budget cannot grant extra time. Client/canary/request deadlines can shorten
   waits, never extend the ADR bounds. Lease acquisition retains its existing
   10-second primitive ceiling. Cancellation before/after that synchronous call
   is checked; immediate interrupt inside it is NOT claimed. Any blocking worker
   stays owned until the bounded acquisition ends; late acquisition is dropped
   without launch/send. Report cancellation and cleanup time separately.
6. **Bind:** require exact admitted canonical profile, tier, model, context,
   build and template identities. Store an immutable verified-instance tuple
   including host boot/identity and server PID/start identity. Compare later
   peers to this tuple, never to whichever record is newest.

Dropping, failing or cancelling a client closes only its exchanges/handles and
lease. It never unlinks records, signals the host, changes idle grace, holds a
dummy lease or retries a generation automatically. Distinguish retryable not-ready,
profile incompatibility, invalid registration, peer change, deadline, caller
cancellation, recorded host failure, protocol failure and canary mismatch.
Do not label unknown-delivery requests safe to replay; caller owns retry policy.

## Verified transport and readiness

Use an actual connected `tokio::net::UnixStream`. Before HTTP handshake or any
authorization/request byte, verify peer UID/PID plus process start and boot
against the bound instance. Hand that same stream to Hyper; no verify-one/send-
another race. Each reconnect repeats the check. Peer change invalidates readiness
and returns to attachment; do not replay an interrupted model request. No TCP,
proxy, redirects, arbitrary URL or silent fallback.

Identity probes use authenticated `/v1/models` and `/props` on that verified
stream, requiring ADR-0011's single pinned model alias, exact context/build and
template hash. Missing or unsupported response shapes fail closed. The retained
Phase 0 source at runtime `c1d0e7a004015f23bc0233470b747b596f29b264`,
`sources/llama/tools/server/server-context.cpp::get_res_model_info` (4416) and
`get_res_props` (4471), emits model `id`, `meta.n_ctx`, `meta.n_ctx_train`,
`default_generation_settings.n_ctx`, `chat_template` and `build_info`.
Doc Sum's inspected `llama_cpp.rs::verify_started_model` (1843) checks the model
identity fields; it does not supply a `/props` build parser. The exact
`llama_build_info()` encoding and its binding to the full admitted build commit
remain to be source-bound before the identity parser is implemented. A commit
substring match is not proof. Hash the returned template's exact UTF-8 bytes,
without trimming. Do not compare the model's descriptor pathname.
The registration socket path must equal the caller's resolved ADR socket path.

The byte transport takes a closed endpoint/method choice for these identity probes,
`/tokenize` and `/completion`; it does not parse or reserialize application JSON.
Use Hyper's HTTP parser and bounded bodies/headers. Proposed header budget is
16 KiB and 64 fields; identity bodies are capped at 4 MiB. The later Doc Sum
adapter supplies its existing 512 KiB tokenize and 4 MiB completion caps from
`native_request.rs:8-9`. Request bodies have an explicit finite byte cap supplied
by the consumer; zero, overflow or an expired deadline cannot mean unlimited.
Test chunked/unknown-length bodies and early Content-Length rejection with actual
received-byte enforcement. Preserve raw body bytes, status and relevant retry
metadata; never derive token timings from a nonstream response. SSE/application
streaming support is not introduced or removed from an existing route here.

Expose a consumer-owned canary definition/checker under the verified session,
with consumer/client/profile, request-definition and expected-result identities.
It may need a bounded tokenize/completion sequence: do not hard-code a single
preformatted request, invent an independent formatter, force an answer with a
grammar, or compare the app's trimmed final response. The consumer's reviewed
native owner supplies framing and raw decoding. A canary callback's reviewed
code/definition and exact expected raw result are bound by the qualification
receipt; a mutable label or arbitrary success boolean is insufficient.

Only a successful comparison for that tuple and the current server instance
can construct a ready handle. Missing approval binding, mismatch, whitespace
change, timeout or cancellation does not. Concurrent canary attempts coalesce
only for the identical tuple; failure never populates a success cache and one
consumer cannot inherit another's qualification. A persisted success is never
trusted without current instance verification. The app owns any persistence;
this slice adds no settings/database or generic qualification store.

No approved Doc Sum canary is asserted here. Use labelled synthetic callbacks
only. The real pair remains ds-qualify-c9's separately reviewed decision. The
later Doc Sum adapter will bind the qualified framing constructor to admitted
profile metadata and build the synchronous-trait bridge; neither lives here.

## Verification plan

Use real isolated Unix listeners and fresh child processes for lifecycle/peer
tests; synthetic payloads only, no user service manager or model. Keep every
receipt, rejected offer and failure. Before each origin fix declare its exact
fail-first probe, then show pass-after and commit that reproduction. Reuse U1a
startup/lease probes and the saved native byte corpus instead of a new serializer.

| Gate | Required proof, including both directions |
|---|---|
| File/schema admission | Valid records/keys admitted; malformed/partial/mixed fields, missing nullable keys, duplicate keys, wrong types, unknown state/code, symlink/FIFO/owner/mode/link errors refused before any network byte. Reuse public runtime fixtures and cross-field oracle. |
| Boundaries | Empty/single/max-1/max/max+1 bodies and headers, UTF-8 byte-vs-character length, growing/truncated files, 0/false/empty/oversized limits, checked time overflow, past/maximum/over-budget timestamps and clock jumps; no default defeats. |
| Liveness/peer | Live same instance succeeds; zombie, missing process, wrong boot/start/PID/UID, socket replacement and record replacement fail closed. A real socket proves bad peers receive zero auth or model bytes. Root-dependent UID evidence must be isolated and recorded or remain an unmet gate. |
| State/races | Absent, live starting selected/unselected, ready, stopping, foreign profile, matching/unrelated failure; simultaneous attaches, launcher exit race, one start per attach, host death, lease held while queued. No foreign stop/delete or replacement side effect. |
| Transport | Replay all saved request bytes, including schema order/omission, through the real HTTP stream; exact raw responses/status/retry metadata retained. Header/body caps, malformed HTTP, disconnect, cancellation, no unchecked reconnect or automatic request replay. |
| Canary | Exact raw success; leading/trailing difference, wrong consumer/profile/client/definition/expected binding, changed server, failure/cancel, concurrent same/different tuples; no early business request or stale success reuse. |
| Resource/error | Deadlines at every blocking boundary; owned workers/drivers finish or bounded cleanup failure is reported; no detached worker, leaked lease, swallowed failure, post-cancel send or host signal. Queue/attach/probe/canary/request boundaries recorded separately. |
| Negative controls | Deliberately bypass peer verification, compare against a refreshed record, drop schema order, trim canary output, omit a cache-tuple member, remove a body cap or cancel guard. Named tests must detect each mutation for its intended cause. |

Focused tests, fmt/clippy, complete vendor/source manifest identity and Linux plus
unsupported-target compilation are implementation gates. Review includes
`boundary-probe` and `effect-trace`. Public anonymous dependency/build checks and
complete release equality remain mandatory before publication/consumer adoption;
local synthetic success is not a substitute. No broad model tests in this slice.

## Explicit non-scope and downstream contracts

No Doc Sum `SharedHost` selector, `shared_host.rs`, settings/snapshot version,
database, qualification receipt schema or app dependency/vendor change. No
Invoice/Email changes, schema projection repair, prompts, inference kernels,
models, cache precision, slots, production admission, live canary, installs,
remote client repository, release publication or performance claims.

After both client slices pass, prepare the separate Doc Sum opt-in adapter and
immutable snapshot contract against the reviewed client and merged framing owner.
It must preserve historical snapshots and existing routes, bind the admitted
profile/thinking mode and exact release, and include the bounded sync adapter.
G0/G1 needs full C9 schema-order parity, approved canary and combined artifact/
effective-setting evidence; G2 needs the separately accepted live budget. The
ADR-0015/qualification-schema prerequisite is not silently implemented here.

## Assumptions/blockers

The preceding service-start slice must be reviewed and integrated first. This
contract's proposed caps, closed state API, process-state observation and strict
record admission are explicit new client behavior requiring acceptance. Exact
native build-info encoding, final dependency graph, client build receipt
and downstream source revisions must be bound before their dependent code.
No missing pin may be replaced with an assumed value or mutable label.

Doc Sum's framing PR is an inspected candidate; its review/merge and full C9
parity are separate gates. Public license adoption/rights, clean public release
builds, host provisioning and approved consumer canary remain pending, but do
not prevent offline contract review. The generic client can be tested with
synthetic inputs without pretending the real consumer is ready.

## Implementation summary

This is a contract-only proposal for the missing shared attachment owner, with
explicit boundaries and test gates. It implements no client or app behavior.

## Cold diff audit

Only this plan and the service-start plan are added. Preserve the accepted U1,
ADR/profile/schema/fixtures and all code. Verify source citations, internal links,
the sequential dependency and the complete list of intentional differences.
No application suite is rerun for this prose-only change.

## Gap audit

NOT DONE: independent review and exact-revision acceptance, bounded startup,
client implementation and offline security/byte/resource proofs are outstanding.
Publication, Doc Sum integration, real canary/task quality, concurrency and speed
qualification remain later work; none is implied by a completed contract draft.
