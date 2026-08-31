# ADR-0004: Connect entitlement activation v1

**Status:** Accepted

**Date:** 2026-08-31

## Context

ADR-0003 defines how independently installed applications verify the same
signed offline entitlement. It does not define how a user installs that
entitlement. Requiring manual placement would make the commercial boundary
fragile: either application could write a partial file, follow an unsafe path,
or report activation before the shared durable entitlement is valid.

Activation must remain application-local. It must not add entitlement data to
Connect manifests or jobs, introduce a broker, or let one application modify
another application's private persistence.

## Decision

### App-local activation boundary

Each participating application exposes two commands through its own trusted UI
adapter:

- **status** evaluates the shared entitlement using ADR-0003 and returns only a
  stable state and whether Connect is active; and
- **install** accepts a user-selected source file, installs its exact bytes at
  the ADR-0003 shared path, and returns the newly evaluated status.

These commands are not Connect wire-protocol routes. They are local application
operations and remain independently implemented by each application.

The status states are:

```text
active
authority_unavailable
missing
invalid
not_yet_valid
expired
feature_missing
```

Only `active` sets the active flag. Status output does not expose entitlement
IDs, subjects, timestamps, key material, or decoded claims to the frontend.

### Admission before mutation

Install reads the selected source as bounded bytes without following a final
symlink. The source must be a regular file. Before any destination mutation,
the application applies the same strict envelope, signature, claim, feature,
and time checks used for live authorization. Only an entitlement that is
`active` at install time is admitted.

The source path is never used to derive the destination. The destination is
always the shared path from ADR-0003. Source bytes are not rewritten or
deleted.

### Serialized atomic replacement

On the initial Unix implementation, installers in every participating
application coordinate on this persistent lock file:

```text
$XDG_CONFIG_HOME/local-connect/.entitlement-v1.lock
```

with the same `HOME` fallback as ADR-0003. The application:

1. safely creates or opens the owner-private `local-connect` directory;
2. opens the lock as an owner-only regular file without following symlinks;
3. obtains an exclusive, non-blocking advisory lock;
4. re-evaluates the candidate at the commit-time clock;
5. writes the exact candidate bytes to a unique same-directory temporary file
   created exclusively with mode `0600` and without following symlinks;
6. flushes and syncs the complete temporary file;
7. atomically replaces `entitlement-v1.json` with that file;
8. syncs the containing directory; and
9. evaluates the installed entitlement before returning success.

The directory must be owned by the current user, must not be a symlink, and
must not grant group or other permissions. Existing destination and lock files
must meet the same ownership, regular-file, no-symlink, and owner-only
requirements. A lock held by another installer fails fast as busy; callers do
not wait indefinitely.

Validation, admission, lock, write, and pre-replacement failures leave an
existing entitlement byte-for-byte unchanged. Temporary files are removed on
recoverable pre-replacement failures. Atomic replacement ensures readers see
either the prior complete file or the new complete file, never partial JSON.
If the platform reports a durability failure after replacement, the operation
returns a storage failure and must not claim a successfully durable activation;
hardware-level recovery beyond normal filesystem guarantees is deferred.

### Stable local failures

Applications preserve their existing structured error envelopes and map
activation failures to these stable codes:

```text
CONNECT_ENTITLEMENT_AUTHORITY_UNAVAILABLE
CONNECT_ENTITLEMENT_SOURCE_INVALID
CONNECT_ENTITLEMENT_NOT_ACTIVE
CONNECT_ENTITLEMENT_STORAGE_UNAVAILABLE
CONNECT_ENTITLEMENT_ACTIVATION_BUSY
CONNECT_ENTITLEMENT_INSTALL_FAILED
```

UI copy may differ by application, but it must not turn a failed install into
an active state. Cancellation is a UI outcome and does not invoke install.

### Availability and restart behavior

Successful replacement is visible to both applications on their next
entitlement-gated operation. No process restart or private-database mutation is
required. Expiry, removal, corruption, or replacement also takes effect on the
next operation.

Applications without a compiled trusted key report `authority_unavailable` and
cannot install or activate a license. Test and development builds may compile a
test public key explicitly; no build or runtime path may embed a private key.

## Security boundary

The file picker is only a user-consent surface. The backend independently
enforces bounded regular-file reads, cryptographic admission, a fixed
destination, permissions, serialization, and atomicity. A caller cannot use
the command to write an arbitrary path or install unsigned content.

Activation grants only `connect.capability_exchange`. It grants no mailbox,
credential-store, application database, or general filesystem access.

## Rejected alternatives

### Frontend copy

Rejected because frontend code cannot safely own destination derivation,
signature admission, permissions, locking, or atomic replacement.

### One application owns all activation

Rejected because either application must remain independently installable and
usable. Requiring a named peer would recreate direct application coupling.

### Runtime public-key override

Rejected because an environment or settings override would let the same local
user replace the commercial authority and mint paid status.

### Install inactive renewals

Deferred. Version 1 installs only a currently active entitlement. Advance-dated
renewal staging needs an explicit product policy for overlap and selection.

## Consequences

- Either installed application can activate the same local Connect purchase.
- Concurrent app installers cannot interleave writes.
- Invalid, inactive, partial, or unsafe sources cannot replace a working
  entitlement during expected failure handling.
- Both applications still function standalone when activation is absent or
  fails.
- License acquisition, billing UI, production issuer custody, online
  revocation, machine binding, and non-Unix placement remain deferred.
