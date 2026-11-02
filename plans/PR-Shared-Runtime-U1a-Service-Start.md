## Acceptance record — 2026-10-30

Juan accepted this exact reviewed contract at
`ef1713d4b2a56981a5f42658188f7fd122ccfdac` with the verbatim reply
"accept 86 at ef1713d" in the oversight chat. Oversight relayed that decision
in message `2c715485` at 2026-10-31 00:12:01 UTC.
[Oversight CONTRACT REVIEW PASS](https://github.com/canfieldjuan/connect-contracts/pull/86#issuecomment-6536123630)
applies to that revision.

The accepted body below is preserved byte-for-byte, SHA-256
`a90167447c7b9843c9a39e97f1e05b7abe70a0d2d07777a558e9f69d601a6bf5`. This record adds no requirements.
Its historical PROPOSED and pending-acceptance labels describe the proposal
now accepted. Acceptance covers the sequential offline service-start and
attachment/transport/canary contracts, including the shared 15-second publication
window; the service-start slice comes first after acceptance-delta review and
guarded contract merge. It does not authorize live service/model execution,
public release, application adoption, installation or cutover.

---

# U1a: canonical bounded service-start client

Status: PROPOSED, contract preparation only. Owner: connect-runtime.
Parent: [accepted U1](PR-Shared-Runtime-U1.md). Follow-on:
[verified attachment and transport](PR-Shared-Runtime-U1a-Attach-Transport.md).
Base of this proposal: connect-contracts
`57421c5fb6d126146b5e2e4137e7cc3e2b8ba114`.
Independent review and Juan's exact-revision acceptance precede implementation.
Neither this proposal nor its publication authorizes a service/model run,
public client release, application adoption, runtime upgrade or cutover.

## Root cause and verified inventory

CONFIRMED: the canonical local client workspace at
`adae73240c99f0e5329e6038f09d63309e13301d` contains only
`crates/model-primitives` (`Cargo.toml:2`). Its
`start_request::HostConfig::{validate,args}` already owns startup validation and
argument encoding (`crates/model-primitives/src/start_request.rs:19,71`). It
does not launch a service. There is no `crates/model-client` implementation at
that revision. These are local source pins, not published client releases.

CONFIRMED: private host checkout `1bacdd0a11aa0512703cc6ac5074c90779820677`
and merged revision `3a2e3a439afb56267207b30e40c8439b5784dee1` have identical
`src/host.rs`, coordination and client-vendor contents. The merged source's
[launch_transient](https://github.com/canfieldjuan/local-connect-model-host/blob/3a2e3a439afb56267207b30e40c8439b5784dee1/src/host.rs#L59-L87)
owns the service command, but waits through synchronous `Command::status()`
without a deadline. `src/main.rs:67` calls it for the host's attach entry;
`src/lib.rs:21` exports it. Extracting that wait unchanged would not provide
the bounded attachment required by ADR-0011. This is a code-observed unbounded
wait, not a claim that a deployed launch has hung.

Reuse the existing startup-request provenance and synthetic probes, rather than
rebuilding the runtime/model inventory. The source-bound baseline includes:

- `model-primitives/tests/start_request.rs`: original validation and argv rules;
- host `tests/executable.rs::unavailable_bus_actor`: no-manager typed refusal,
  with isolated bus endpoints, and its fresh-process caller;
- host `tests/coordination.rs`: existing lease/election invariants;
- host `tests/native_host.rs`: read-only reference for real launch callers;
  its live tests are NOT authorized by this contract.

No prompts, token budgets or generation settings belong to this extraction.
The parent model/runtime/profile inventory stays binding and unchanged.

## Required change surface

1. Add canonical `crates/model-client/{Cargo.toml,src/lib.rs,src/start.rs,src/error.rs}`
   in the local client repository. `start.rs` becomes the sole service-command
   owner; it consumes the existing primitive `HostConfig` and borrowed
   `ClientLease`. Keep package publication disabled.
2. Add focused startup tests under `crates/model-client/tests/`. Use a fresh
   subprocess and synthetic launcher for spawn/wait/cancel tests; no real user
   service manager. Test injection is private/test-only, never a public arbitrary
   command-launch API or an environment override in production.
3. Update the root workspace and necessary lock entries, provenance, complete
   source manifest and vendor-verifier expectations. Reuse already locked
   dependencies; no unrelated dependency upgrade. This slice needs no HTTP
   dependency and no new framework.
4. In a dependent private-host integration commit, vendor the exact complete
   reviewed local candidate, add its repository-relative client dependency and
   route `host::launch_transient` through it with the existing host error mapping.
   Remove the old command construction and wait; retain the host's public wrapper
   and private service execution. Bind the canonical candidate commit, archive
   and complete file hashes before integration. A local vendored candidate is
   not a public or consumer-ready release.

No private-host dependency enters either public crate. This uses only the
accepted `model-client/src/start.rs` allowlist; runtime admission, probing,
election, records, GPU choice and supervision remain private. Reuse the same
canonical helper from the new client and the private host, without a cycle.

## Preserved behavior and explicit differences

Preserve exact command/argument order, `OsString` path bytes, service unit naming,
stdin/stdout/stderr policy and validation-before-launch from the source above:
`systemd-run --user --collect --quiet --property=Type=exec
--property=KillMode=control-group --property=TimeoutStopSec=8`, unit derived from
the validated start ID, `--`, installed host executable, then `HostConfig::args`.
No shell, download, app child-server fallback, enabled unit or login startup.
The helper requests the separately installed host; it never starts llama-server.
Keep the lease borrowed throughout the operation and close-on-exec.

The deliberate difference is a bounded wait at this originating command owner:

- Accept an absolute monotonic deadline and cancellation signal. Reject an
  expired deadline/cancellation before spawning. Use checked time arithmetic.
- The attach caller shares one 15-second startup-publication window across
  launch and observation of a live starting record, rather than granting a new
  15 seconds after launch. This is the proposed operational interpretation of
  ADR-0011's initial wait, explicitly subject to contract review.
- The historical host wrapper supplies a 15-second launch deadline and a
  noncancelled signal. This changes only the previously unbounded manager wait;
  the host's 300-second admission/start budget and idle policy do not change.
- Spawn at most once. On timeout/cancel, close and reap only the owned launcher
  process, never the transient service, host, server, or another client's work.
  Do not detach an unbounded wait task. Account for bounded cleanup separately;
  inability to complete cleanup is an explicit error, not claimed success.
- A service may already have started when the launcher times out. Return a typed
  uncertain-launch outcome carrying the start ID; do not automatically launch
  again in this attach. Releasing this client's lease lets existing host policy
  decide idle reclamation. A later attach must rediscover identity normally.
- Preserve existing missing-manager and unsuccessful-exit errors; distinguish
  cancellation, deadline and I/O outcomes at the client owner. The host wrapper
  maps them explicitly, without conflating a deadline with invalid input.

No measured startup-time or inference-speed claim follows from this change.

## Explicit non-scope

No attachment state machine, HTTP transport, canary, application dependency or
route/settings change in this first slice. No host election, record mutation,
server supervision, idle policy, profile/schema, model, inference arithmetic,
concurrency, production installation or public release change. Preserve the
existing private runtime preparation and all unrelated manifests/tests. The
following attachment contract cannot be bundled into this extraction's proof.

## Verification plan

Before editing, capture original command arguments and typed results in an
isolated test process, including spaces and non-ASCII path bytes. Bind those
captures to the original source hash. Declare the new bounded-wait test as an
expected failing-before probe, with a supervising test deadline so the original
unbounded behavior cannot hang the suite. Then prove the corrected behavior and
retain the reproduction as a regression.

- Both sides: valid config launches exactly once; invalid path/profile/start ID,
  expired deadline and pre-cancel launch zero times. Assert exact error variants.
- During launch: normal success, nonzero exit, missing manager, hung launcher,
  cancellation, exit racing deadline, and uncertain service-start outcome.
  Prove owned launcher cleanup and no signal/service-stop sent to the synthetic
  host. Preserve original argument bytes and original completed-call results.
- Lease: a separately spawned lock contender cannot take the exclusive lock
  while launch is pending; after this client ends it can. No lease descriptor
  passes to the synthetic executable. Never substitute a process listing for
  this isolation proof.
- Boundary: zero/expired budget, just-before/at/after deadline, cancellation
  before spawn and while waiting; arithmetic overflow refuses input. No falsy
  value silently selects an unlimited/default wait.
- Mutation proof: remove cancellation/deadline enforcement, reorder an argument,
  bypass config validation, duplicate launch or leak the lease; named tests must
  fail for the intended cause, not merely fail to compile.
- Run focused client and host callers, fmt and applicable clippy checks. Reuse
  required CI for broader suites. Linux behavior and unsupported-platform builds
  are separate gates: no Linux-only imports/dependencies may break existing
  Windows consumers; no Windows shared-host functionality is claimed.

Record `boundary-probe` and `effect-trace` in the implementation review. Evidence
lives outside worktrees, directories 0700/files 0600; PRs cite alias and SHA-256.
No host secrets, private documents or live endpoints enter fixtures or logs.

## Assumptions/blockers

- The accepted parent permits the symbol boundary, but this deadline/cancellation
  refinement needs review and exact-revision acceptance before code changes.
- Installed host provision and store preparation are caller preconditions.
  This contract neither installs nor discovers alternate executables.
- Public publication remains blocked on the separately accepted
  [terms proposal's operative-license and rights gates](PR-Shared-Client-Proprietary-Terms.md).
  Juan Canfield's owner designation does not itself satisfy those remaining gates.
- A changed source base or newly required dependency is inventoried and reviewed
  before implementation; stale checkout identity is never treated as installed
  behavior. This work makes no installed-deployment claim.

## Implementation summary

This document proposes startup extraction plus the explicitly listed bounded-wait
change. No executable code, dependency, service or runtime has been changed by
the proposal. The attachment contract consumes this result sequentially.

## Cold diff audit

Only this new plan and its sibling attachment plan are in the contract change.
The accepted parent, ADR, profile, schemas, fixtures and application code remain
unchanged. Validate links, exact source pins, declared differences and docs-only
diff; application/model tests are not required for a prose-only proposal.

## Gap audit

NOT DONE: implementation is not authorized by preparation alone. Exact-revision
review/acceptance, startup regression/parity proof, reviewed canonical candidate
and dependent host integration remain. Public release, app attachment and live
qualification are independent later gates.
