# ADR-0007: Background provider lifecycle

**Status:** Accepted

**Date:** 2026-09-17

**Decider:** Juan Canfield

## Context

Connect availability currently requires a running, authenticated provider.
ADR-0001 defers launch on demand and a broker, while ADR-0002 makes a v2
`instance_id` the durable provider state identity rather than a process
identity. ADR-0005 defines safe Windows registration ownership, but none of
those decisions says how a provider remains available after its desktop window
closes.

ADR-0006 assigns unattended rule admission and provider submission to a
consumer. That feature cannot run unattended when its provider exists only as
part of an open desktop window. Providers have begun solving this independently,
which risks incompatible consent, ownership, takeover, shutdown, and Windows
lifecycle rules.

This decision standardizes provider process lifecycle. It does not add a
broker, change either wire protocol, or move application-private state into a
shared service.

## Decision

### Opt-in per-user service

A background provider is an application process supervised for the current
operating-system user. It serves the same capabilities and opens the same
provider-owned durable state as that application's foreground provider.

Background operation is off after first install. The application exposes one
explicit user control that turns it on or off. Turning it on persists the
choice in the user's service manager and starts the provider. Turning it off
stops the provider and removes automatic start. A desktop window may display
manager and authenticated serving state, but window memory is never the source
of truth for whether background operation is enabled.

No entitlement silently enables a background provider. Entitlement permits
Connect or Automate behavior; it does not grant process-lifecycle consent.

"Unattended" in this decision means that no provider window must remain open
while the user's service session is available. It does not promise pre-login,
post-logout, or machine-wide execution. A platform may separately keep a user
manager alive after logout, but Connect does not require or enable that policy.

The platform adapters are:

- Linux: one packaged systemd user unit enabled for the current user and
  started by that user's service manager. It is not a system service.
- Windows: one packaged per-user Task Scheduler task with an at-logon trigger.
  It runs only as the same user, stores no password, requests no elevation, and
  launches the package's exact background-provider entry point. It is not a
  machine-wide service or startup task.

The enabled choice survives application upgrades. Package removal must make a
running provider stop and remove its registration. A later reinstall may
restore the prior per-user enabled choice only after the installed executable
and provider state pass the same admission checks as a new enable operation.

macOS launchd integration remains a later platform adapter governed by the
same consent and ownership rules.

### One durable provider, one live publisher

The foreground and background entry points are two process modes of one
provider. They share application-private durable job state and, for v2, the
same durable `instance_id`. They do not clone, copy, or migrate accepted jobs
during takeover.

ADR-0002 continues to require a new bearer token, endpoint, process identifier,
and start time for every publisher process. V1 keeps its frozen per-process
`instance_id`; its foreground and background processes instead serialize on
the one v1 `app_id` publication slot. The background contract does not change
either registration schema.

Exactly one process may own the provider state and publish a registration at a
time. Every provider entry point takes the same application-private exclusive
provider-ownership lock before it recovers jobs, binds an endpoint, or writes a
registration. It holds that lock until its registration is safely removed and
serving has ended. Windows providers also obey ADR-0005's protocol-specific
publication locks; those locks do not replace the application-private state
lock.

A background process may wait for provider ownership while it remains enabled.
Foreground startup never waits invisibly: the desktop either observes the
existing authenticated provider and starts no publisher, or reports that
another process owns serving. Neither process deletes or replaces another live
process's registration.

### Deterministic selection and takeover

The current authenticated live owner wins unless the user changes background
mode:

- When a window opens and the enabled background provider is already live for
  the same durable state, the window starts no foreground provider.
- When a window opens and no authenticated provider is live, it may start its
  foreground provider. An enabled background process may wait for the same
  ownership lock and takes over after the foreground process ends.
- When the user turns background operation on while that window owns the
  provider, the window stops its publisher, then the service manager starts or
  resumes the background entry point. The control succeeds only after an
  authenticated registration attributes serving to the expected durable
  state. If readiness fails within the control deadline, the application
  reports failure and restores its foreground provider when the window is
  still open.
- When the user turns background operation off, the service manager stops and
  disables the background entry point. An open window starts its foreground
  provider only after the old registration is gone and ownership is available.
- A live provider for a different durable state is never treated as this
  window's provider and is never displaced. The application reports the state
  mismatch and starts no competitor until that owner ends or the user selects
  the matching state through an application-owned operation.

Provider selection uses a successful authenticated manifest whose attribution
matches the registration and expected durable state. Service-manager states
such as starting or active do not by themselves prove that a provider is
serving.

Background control and provider acquisition share one application-private
control authority. An enable, disable, or rebind operation takes it exclusively
from manager preflight through final authenticated state. Foreground and
external provider acquisition take it in shared mode around their nonblocking
provider-ownership decision. A conflicting operation fails fast without
manager mutation, state recovery, endpoint binding, or registration. The
background entry point started inside an exclusive enable transition does not
re-enter that control authority; it still takes the provider-ownership lock.
This closes the check-then-start race without introducing a lifecycle queue.

### State binding and privacy

The service entry point reads one application-owned, owner-private binding to
the provider's durable state. Enable or rebind validates the selected state,
stops any possibly live background process while the old binding remains
authoritative, writes the new binding atomically, reads it back, and only then
starts the service. A stop failure preserves the old binding. A write failure
after a successful stop starts neither the old nor new state.

Bindings must be bounded regular files, must not be links or reparse points,
and must contain only the minimum application-private state locator. They are
not stored under a Connect registration directory, are not visible to
consumers, and carry no bearer token. Implementations compare durable state by
opened filesystem identity where path aliases could otherwise make one state
look different.

Linux bindings live in the application's private user configuration. Windows
bindings live in the application's private Local AppData, separate from the
shared `%LOCALAPPDATA%\LocalConnect\runtime` registration tree in ADR-0005.

### Bounded stop and recovery

On ordinary stop, a provider stops admitting new work while retaining
authenticated status for its admitted job, and gives that job at most 30
seconds to finish and commit a terminal status. It then removes only the
registration it published and exits. At the deadline it cancels local work and
first persists a recoverable nonterminal or explicit retryable failure
according to the provider's existing durable-job contract.

The service-manager stop deadline is at least 40 seconds and strictly longer
than the provider drain. After that deadline it terminates the complete process
tree. Manager actions and readiness probes are independently bounded; no
desktop control waits indefinitely.

After a crash or forced stop, the next owner recovers the same durable v2 job
state before publishing availability. It never converts an uncertain admitted
job into a fresh submission under the same identity. Consumers retain the
ADR-0006 reconciliation rules.

If the running package executable is removed or replaced, the provider stops
serving and removes its own registration without waiting for the ordinary job
drain. This prevents an uninstalled artifact from remaining discoverable. Its
durable job state remains available for a safely installed successor.

### User-visible state

Applications distinguish these facts:

- background start is enabled or disabled according to the service manager;
- a background process is starting, stopping, or unavailable; and
- an authenticated provider is serving the selected durable state.

Only the last fact proves Connect availability. Controls admit at most one
background mutation at a time and refresh both manager state and authenticated
provider state after success or failure.

### Required acceptance evidence

Each provider implementation must exercise both sides of these boundaries:

1. first install is disabled; explicit enable persists and serves after the
   window closes;
2. foreground and background attempts never recover or publish concurrently;
3. a live background provider prevents a window publisher, while a window
   provider hands off after explicit enable;
4. delayed readiness succeeds only after authenticated attribution, and a
   readiness deadline restores the still-open window provider;
5. disable drains or bounds the admitted job, removes the exact registration,
   and permits one foreground replacement;
6. crash or forced-stop recovery reuses the v2 durable identity and reconciles
   accepted work without duplicate submission;
7. malformed, linked, non-private, oversized, mismatched, and changed state
   bindings fail closed before service start;
8. concurrent control and provider-acquisition attempts prove both exclusion
   directions and release after success, failure, and process exit;
9. package removal makes the old process undiscoverable, and reinstall can
   safely restore the prior enabled choice and durable state; and
10. Linux systemd-user and Windows per-user-task artifacts preserve the stated
    user, privilege, startup, stop, and process-tree bounds.

Installed-artifact evidence is platform-specific. A Linux proof does not
establish Windows behavior, and package construction alone does not establish
installed service behavior.

## Rejected alternatives

### Enable background operation during installation

Rejected because installing or licensing an application is not consent to keep
it running in the user's session.

### Machine-wide service

Rejected because current providers and registrations are per-user and a
machine service would add multi-user state, token, and authorization policy.

### Leave one provider process behind when the window closes

Rejected because an unsupervised child has no durable enabled state, restart
policy, bounded stop owner, or reliable package-removal behavior.

### Launch on demand or a shared broker

Deferred. A per-user provider service satisfies unattended availability without
adding a third runtime, shared private state, or a new transport authority.

### Foreground always displaces background

Rejected because closing and opening a window would interrupt admitted work and
create avoidable ownership races. The current authenticated live owner remains
stable until it ends or the user explicitly changes background mode.

## Consequences

- Unattended consumers can rely on an explicitly enabled provider without an
  open provider window.
- Each provider needs a platform service adapter, an application-private state
  and control lock, durable recovery, and user-visible lifecycle state.
- V2 durable identity and existing wire schemas remain unchanged.
- Windows and Linux implementations have independent installed acceptance
  gates.
- Launch on demand, a broker, machine-wide serving, and macOS packaging remain
  separate decisions.
