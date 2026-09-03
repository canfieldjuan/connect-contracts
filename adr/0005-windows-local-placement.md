# ADR-0005: Windows Local Connect placement

**Status:** Accepted

**Date:** 2026-09-03

## Context

ADR-0001 deliberately started with Ubuntu and deferred Windows transport and
packaging. ADR-0003 and ADR-0004 likewise define only Unix placement and file
handling for the shared entitlement. The wire contracts themselves do not rely
on Unix: registrations advertise exact-loopback HTTP endpoints and bearer
tokens, and all capability, job, artifact, and entitlement documents are
language-neutral JSON.

Participating applications now ship or are preparing Windows packages. Without
one shared Windows placement decision, a provider can run but a consumer cannot
discover it, and neither side can independently verify or activate the same
commercial entitlement.

## Decision

### Preserve the existing transport

Windows uses the existing `http-loopback-v1` and `http-loopback-v2` transports,
including exact-loopback endpoint validation, per-process bearer-token rotation,
authenticated manifest attribution, bounded requests and responses, and refusal
of browser-Origin requests. No registration, manifest, job, artifact, or error
schema changes.

Named pipes remain deferred. They are not required to establish per-user
discovery because the registration file carries the authentication secret and
availability still requires a live authenticated loopback endpoint.

### Shared Windows root

Windows implementations derive the shared root from the process's absolute
`LOCALAPPDATA` directory:

```text
%LOCALAPPDATA%\LocalConnect\
```

When `LOCALAPPDATA` is absent, relative, or unusable, Connect is unavailable.
There is no fallback to the working directory, a machine-wide directory, or a
shared temporary directory.

V1 and v2 runtime registrations are stored under:

```text
%LOCALAPPDATA%\LocalConnect\runtime\v1\providers\
%LOCALAPPDATA%\LocalConnect\runtime\v2\providers\
```

The shared entitlement and persistent activation lock are stored at:

```text
%LOCALAPPDATA%\LocalConnect\entitlement-v1.json
%LOCALAPPDATA%\LocalConnect\.entitlement-v1.lock
```

Application-private databases, job artifacts, logs, and settings remain outside
the interoperability contract and use each application's own per-user state
location.

### Windows owner-private boundary

The current user's Local AppData profile ACL is the owner-private boundary.
Implementations establish a protected current-user/SYSTEM/Administrators DACL
on each directory they newly create, then verify the effective DACL on that root
and every Connect-owned directory, published registration, installed
entitlement, temporary, and lock file before trusting it. Existing unsafe paths
are rejected rather than silently rewritten. A null or unreadable DACL fails
closed. The owner must be the current user,
SYSTEM, or the built-in Administrators group. An access-allowed ACE that grants
file content/list, mutation, deletion, DACL, ownership, generic-read,
generic-write, or generic-all rights to any other principal fails closed;
OWNER RIGHTS is treated as the already-validated concrete owner, while Creator
Owner is permitted only on inherit-only ACEs. Connect-owned descendants must
remain inside that absolute root and must not be symlinks, junctions, or other
reparse points. Protection from a hostile process already running as the same
user remains deferred.

A user-selected activation source may originate in Downloads or another
non-private directory. It must still be a bounded regular non-reparse file and
must pass signature, feature, and time admission; its ambient ACL is not used as
authority and does not need to match the installed private destination.

Implementations reject registration and entitlement candidates that are not
bounded regular files or that are reparse points. Security checks apply again
to an opened candidate before its content is trusted. Failure to establish the
per-user boundary fails Connect closed while leaving standalone application
behavior available.

### Atomic publication and serialization

Windows registration and entitlement writers create a unique same-directory
temporary regular file, write and flush the complete bounded content, and
atomically replace the fixed destination. A registration becomes availability
evidence only after publication. A failed write must not be reported as a
successful registration or activation.

Readers keep registration and entitlement handles bounded and short-lived.
Writers retry Windows sharing violations for a bounded interval before
replacement or owned-file cleanup fails; they never wait indefinitely or report
an uncommitted write as successful. A Windows v2 provider derives one
collision-safe registration filename from its `app_id` and durable
`instance_id`; restarting the same durable instance replaces that same path
rather than publishing another candidate.

A Windows v1 provider permits exactly one active publisher for each `app_id`
under the current Windows user. Because schema-valid IDs can equal reserved
Windows device basenames, it publishes `local-connect-v1-<app_id>.json` and
holds an exclusive non-blocking lock on
`.local-connect-v1-<app_id>.lock` in the same protocol-specific providers
directory. The fixed `local-connect-v1-` prefix plus the v1 `app_id` character
and length constraints produces a non-reserved, collision-safe Windows
filename. The provider acquires that lock before it binds or publishes, holds
it through its complete serving lifetime, removes the registration only when
its current bearer token still matches the file, and releases the lock last. A
second process for the same `app_id` fails Connect startup as busy; it does not
replace the active registration. A crash leaves fixed registration and
lock-file paths for the next process to reuse even though the v1 registration
document's process-scoped `instance_id` rotates.

Registration publication temporaries end in `.tmp`, not `.json`, under an
ASCII-case-insensitive comparison. The writer removes its own temporary after
successful replacement or any handled failure. A process crash may leave that
non-candidate temporary behind, but consumers never count, parse, or probe it as
a registration; stale-temporary scavenging remains optional storage hygiene.

For each protocol-specific Windows providers directory, consumers examine at
most 256 direct child entries whose names end in `.json`, compared
ASCII-case-insensitively. Every such name counts before file type, security, or
content admission; other names, including persistent `.lock` files, do not
count. Encountering a 257th candidate or an enumeration error fails discovery
closed for that directory before any candidate endpoint is probed. These
requirements do not change the registration document or bearer-token contract.

Provider-state ownership and entitlement activation use non-blocking Windows
file locks. Every shared Connect lock covers byte offset `0` for length `1`.
Implementations initialize a zero-length lock file with one byte before taking
that range; the persistent byte has no semantic value. A held lock fails fast
as busy; callers do not wait indefinitely. Candidate admission is repeated
while the activation lock is held before replacement. The installed entitlement
is re-read and verified before activation reports success. Expected
pre-replacement failures leave the prior entitlement unchanged.

Windows has no portable directory-`fsync` equivalent. Implementations flush the
temporary file before replacement and rely on the platform's same-volume atomic
replacement guarantee. They must not claim stronger crash durability than the
platform provides.

### Persistent runtime directory

Unlike `XDG_RUNTIME_DIR`, Local AppData survives reboot. Providers remove their
own registration on graceful shutdown only after verifying its bearer token.
V1 crash/restart cycles reuse the prefixed `app_id` slot's fixed registration
and lock paths, and v2 cycles reuse the durable instance's fixed path. Consumers treat
registrations as candidates only, enforce the 256-entry Windows scan above, and
ignore stale files whose exact endpoint is unreachable, whose bearer token
fails, or whose manifest attribution differs. Therefore a stale file alone
never proves availability or causes unbounded discovery work.

## Security boundary

The Windows decision does not strengthen same-user process identity. A hostile
process running as the user can read per-user registrations just as it can on
the initial Unix trust model. A future trusted broker, package identity, or
named-pipe ACL design would be a new transport decision.

The shared entitlement remains a signed offline bearer license. Windows
placement grants no mailbox, application database, generation-model, or general
filesystem authority.

## Rejected alternatives

### Machine-wide ProgramData placement

Rejected because it creates multi-user token and entitlement sharing and would
require a service or broker to mediate ownership.

### Shared temporary-directory fallback

Rejected because a fallback can expose bearer tokens to other local users and
makes discovery depend on ambient process state.

### Windows named pipes in this slice

Deferred because exact-loopback HTTP already supplies the bounded streaming job
contract. Replacing the transport would add two implementations without fixing
the missing shared placement and entitlement lifecycle.

### Windows Registry discovery

Rejected because runtime registrations are ephemeral process evidence, contain
rotating secrets, and require atomic file-like cleanup and enumeration. A
per-user filesystem directory keeps both applications aligned with the existing
consumer model.

## Consequences

- Windows providers and consumers can share one deterministic registration and
  entitlement location without a broker.
- Existing v1/v2 wire documents and Linux behavior remain unchanged.
- Windows packages must implement and test Windows-native locking, bounded
  regular-file handling, reparse-point refusal, and atomic replacement before
  claiming Connect support.
- V1 and v2 crash/restart cycles cannot accumulate one registration per process;
  v1 admits one active publisher per `app_id`, and Windows consumers apply the
  common 256-entry stale-candidate scan.
- Named pipes, brokered identity, code signing, installers, auto-update, and
  macOS placement remain deferred.
