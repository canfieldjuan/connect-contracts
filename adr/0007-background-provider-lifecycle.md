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
  started by that user's service manager. It is not a system service. The unit
  uses manager-owned restart-on-failure with bounded backoff and rate limiting.
- Windows: one packaged per-user Task Scheduler task with an at-logon trigger.
  It runs only as the same user, stores no password, requests no elevation, and
  launches the package's exact background-provider entry point. It is not a
  machine-wide service or startup task. The task uses manager-owned restart on
  unexpected failure with bounded delay and a bounded retry rate.

While background operation remains enabled, an unexpected provider exit asks
the service manager to launch a recovering owner without requiring a desktop
window. Each platform adapter declares a positive minimum retry delay, a finite
maximum time to its first retry, and a finite attempt budget over a finite
window so a persistent startup fault cannot spin. A successful authenticated
serving interval resets that budget only after the adapter's declared stability
period. Exhausting the budget leaves background operation enabled but visibly
unavailable; the next platform session trigger or explicit control operation
may start a new bounded retry sequence. Intentional disable, package removal,
package upgrade, and a successful manager stop do not trigger a restart.
Disable, rebind, or package upgrade during backoff cancels a pending restart
before binding access or publication.
Every retry follows the same control-authority, provider-ownership, recovery,
and publication requirements as an initial background start.

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

Because the frozen v1 wire has no durable-state identity, a v1 provider that
supports background mode also exposes application-private lifecycle status to
its own desktop host. That status correlates the current serving process with
the exact durable-state binding and serving generation. It is bounded,
authenticated or carried over same-application IPC, and never exposed through
Connect discovery. A v1 implementation without this private correlation may
report same-app availability, but it cannot claim state-specific readiness,
automatic takeover, or mismatch recovery. V2 implementations correlate the
expected state through their durable `instance_id` and may use the same private
status seam for manager diagnostics.

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
matches the registration. State-specific readiness additionally requires the
expected v2 durable `instance_id` or the v1 application-private lifecycle
correlation defined above. Service-manager states such as starting or active do
not by themselves prove that a provider is serving.

Background control and provider acquisition share one owner-private, per-user,
per-application control authority. The same authority covers every foreground
and background entry point, every supported protocol mode, and every durable
state binding that the application may select. It is not keyed by process,
process mode, protocol instance, or state path.

An enable, disable, rebind, package-upgrade, package-removal, or
package-reinstall operation takes the authority exclusively from manager
preflight through final authenticated state, complete failed-start cleanup, or
completion of the package operation.
Foreground and independently started background provider acquisition take it
in shared mode before reading or validating the selected binding and before
their nonblocking provider-ownership attempt. A failed ownership attempt
releases shared authority before any wait or backoff and reacquires it before a
new attempt. A successful attempt retains shared authority through opened-state
revalidation, job recovery, endpoint binding, atomic registration publication,
and authenticated attribution to the selected state. It releases shared
authority after that startup commits; provider ownership and publication locks
continue to guard steady-state serving.

Before binding access, every shared acquisition also checks under control
authority that no package-operation record exists. An incomplete, unreadable,
malformed, or wrong-target record is a durable barrier and fails closed before
manager mutation, state recovery, endpoint binding, or publication. Only a
package operation holding exclusive control authority may recover that record
and resume or safely restart the recorded operation.

An existing package-operation record's kind, generation, and target are
immutable. A requested upgrade, removal, or reinstall that encounters a
different recorded kind, generation, or target fails before manager or package
mutation. It cannot clear, overwrite, convert, or claim to repair the existing
operation; an exclusive recovery must finish or safely restart the exact
recorded kind and generation first.

Startup failure removes any endpoint and exact registration created by that
attempt before releasing provider ownership and then shared control authority.
The fixed acquisition order is control authority, provider-ownership lock, then
any protocol publication lock. A conflicting operation fails fast without
manager mutation, binding access, state recovery, endpoint binding, or
registration.

The background entry point started inside an exclusive enable, rebind,
package-upgrade, or package-reinstall transition does not reacquire shared
authority only while that same exclusive authority continuously covers its
startup. The controller retains or delegates that authority without a gap
through authenticated publication or complete failed-start cleanup and child
exit. A controller return, crash, or readiness deadline does not authorize a
surviving child to continue uncovered. Before exclusive coverage can end, the
child must already retain delegated coverage, complete a gap-free handoff to
shared authority, or exit before binding state access, recovery, endpoint
binding, or publication. The child still takes the provider-ownership lock.
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
authenticated status for its admitted job. Its entire graceful-stop sequence
has a 35-second maximum. Within that total budget it gives an admitted job at
most 30 seconds to finish and commit a terminal status; at the job deadline it
cancels local work and persists a recoverable nonterminal or explicit retryable
failure according to the provider's existing durable-job contract. The
remaining total budget covers cancellation-state persistence, endpoint
shutdown, removal of only the registration this process published, release of
provider ownership, and process exit. Implementations shorten the job drain as
needed to preserve that cleanup budget; they do not begin a full 30-second
drain after consuming earlier stop time.

The service manager force-terminates the complete process tree 40 seconds after
the stop request if the process has not exited, preserving five seconds beyond
the complete 35-second graceful-stop budget. The controlling adapter then has
until 45 seconds after the original stop request to observe termination, prove
provider ownership ended, and safely remove only the exact dead process's
registration. It leaves durable job state unchanged and recoverable by the next
provider owner. If it cannot prove the old endpoint dead, ownership ended, and
the exact registration absent by that deadline, the control operation fails and
no foreground replacement starts. Manager actions and readiness probes are
independently bounded; no desktop control waits indefinitely. When a newly
started provider misses its readiness deadline, the controller stops its
complete process tree and waits until startup activity and provider ownership
have ended before releasing exclusive control authority or restoring a
foreground provider. A timed-out child may not publish late.

After a crash or forced stop, the next owner recovers the same durable v2 job
state before publishing availability. It never converts an uncertain admitted
job into a fresh submission under the same identity. Consumers retain the
ADR-0006 reconciliation rules.

Package upgrade takes exclusive control authority before suppressing manager
startup or changing launch artifacts. Before either mutation, it atomically and
durably writes a bounded, owner-private, non-link regular-file record outside
the installed package. The record names package upgrade and contains a unique
operation generation, the target package identity, the prior per-user enabled
choice, and an incomplete state. While holding exclusive authority, the
upgrader cancels every pending manager retry, prevents new shared acquisition,
performs the bounded stop of the complete process tree, waits for provider
ownership to end, and removes only the exact dead process registration. It
keeps automatic manager launch suppressed while any launch artifact or
executable may be incomplete.

An upgrade controller that starts with an incomplete record takes exclusive
authority and recovers that exact generation before any provider can acquire
shared authority. It verifies package state and rolls that operation forward or
safely restarts it; it never infers completion merely from files being present.
It does not replace or clear an existing record with a new operation generation,
different target, or unverified state.
Only after the complete installed package, selected durable-state binding, and
background entry point pass the same admission checks as a new enable may it
restore manager launch. If the recorded prior choice was enabled, it explicitly
starts that generation's successor under the still-held exclusive authority and
succeeds only after authenticated readiness for the expected durable state. If
the choice was disabled, it leaves manager launch disabled and starts no
provider.

For an enabled upgrade, the ready successor must retain delegated control
coverage that survives controller exit before the controller clears the record.
The controller then clears only its exact upgrade generation, atomically and
durably, and the successor completes a gap-free downgrade or handoff to shared
authority before the controller releases its own coverage. A controller crash
after the clear therefore leaves the complete, authenticated successor covered;
that successor finishes the handoff or exits with normal exact-registration
cleanup before another acquisition can proceed. For a disabled upgrade, the
controller clears its exact generation only after the complete installation
passes admission and manager launch remains disabled, then releases authority.

An installation or readiness failure completes failed-start cleanup, keeps
manager launch suppressed and the upgrade record incomplete, preserves durable
job state and the prior enabled choice for a later successful repair, and
reports the provider visibly unavailable. A crash before the exact clear leaves
the durable admission barrier rather than an old or partial installation that a
new provider entry point can start.

Package removal takes exclusive control authority before disabling manager
startup or changing launch artifacts. Before either mutation, it atomically and
durably writes the same bounded, owner-private package-operation record, naming
package removal, a unique operation generation, the target installed package,
the prior per-user enabled choice, and an incomplete state. While holding
exclusive authority, the remover cancels every pending manager retry, prevents
new shared acquisition, stops the complete provider process tree without the
ordinary job drain, waits for ownership to end, and removes only the exact dead
process registration. It removes launch artifacts and the executable only
after no old process can serve or publish.

A removal controller that starts with an incomplete removal record takes
exclusive authority and finishes that exact generation; it does not replace or
clear the barrier based on absent or partially removed files alone. It clears
only its exact generation, atomically and durably, after manager launch is
suppressed, the complete process tree and provider ownership have ended, the
exact registration is absent, and the target launch artifacts and executable
are absent. Before that clear it leaves provider durable job state untouched
and atomically and durably writes an owner-private removal receipt outside the
removed package. The receipt binds the exact removal generation and preserves
the prior per-user enabled choice for a later reinstall. A crash after the
receipt but before the clear leaves the barrier in place and lets exact recovery
reuse the receipt idempotently. The controller then clears the incomplete
record and releases control authority.

A crash before the clear leaves ordinary acquisition blocked until exclusive
recovery completes removal. A failed removal keeps manager launch suppressed
and the record incomplete, reports failure, and preserves durable job state and
the prior per-user enabled choice.

A reinstall takes exclusive control authority before it inspects or changes
package files, launch artifacts, manager state, the operation record, or the
removal receipt. If an incomplete removal record exists, the installer validates
and completes that exact removal generation through its receipt and exact clear
while manager launch remains suppressed. It does not overwrite the record,
start a new package generation, or create any new package artifact first. A
malformed, wrong-target, or conflicting receipt or record fails closed before
mutation. A consumed receipt with no matching incomplete reinstall record also
fails closed before mutation.

After exact removal clear and proof that the old target artifacts are absent,
but before creating the first new package artifact, the installer atomically
and durably writes a new package-reinstall operation record outside the package.
It has a unique generation, the new target package identity, the matching
completed removal-receipt generation, the copied prior enabled choice, and an
incomplete state. Failure to persist that new record leaves the package absent,
the receipt unconsumed, and manager launch suppressed. A reinstall controller
that starts with an incomplete reinstall record takes exclusive authority,
validates and recovers that exact generation, and rolls it forward or safely
restarts it without inferring completion from partial files. It accepts an
already-consumed marker only when the receipt generation, package target, and
incomplete reinstall record all match; it then uses the enabled choice copied
into the record and does not consume the receipt again.

The installer holds the same exclusive authority across removal recovery,
reinstall-record persistence, new-package installation, and new-enable
admission. The reinstall generation then follows the upgrade generation's
enabled or disabled successor start, authenticated readiness, delegated
coverage, exact clear, and shared-authority handoff ordering. Before the exact
reinstall clear, it atomically and durably marks only the matching removal
receipt consumed; after that mark, the still-incomplete reinstall record is the
sole owner of the copied enabled choice. Installation or readiness failure keeps
manager launch suppressed and the reinstall record incomplete for exact
recovery. It never treats the receipt itself as readiness and never restores
manager launch while the removal barrier remains incomplete or before the new
package passes admission. The reinstall barrier remains until a disabled choice
is settled or the enabled successor is authenticated under continuous coverage.

If an executable is removed or replaced outside that serialized package
operation, a running provider still stops serving and removes its own
registration without waiting for the ordinary job drain. This is a defense
against external replacement, not the package-removal synchronization path.

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
6. crashing an enabled provider causes the Linux or Windows user manager to
   launch a recovering owner within the declared first-retry bound and without
   an open window; that owner uses new process credentials, reuses the v2
   durable identity, and reconciles accepted work without duplicate submission;
   repeated failure exercises the delay, attempt/window ceiling, and stable
   serving reset, while disable, rebind, package upgrade, package removal, and
   intentional stop during backoff do not restart;
7. a v1 provider proves the private state-binding and serving-generation
   correlation before state-specific readiness or takeover succeeds;
8. malformed, linked, non-private, oversized, mismatched, and changed state
   bindings fail closed before service start;
9. control and acquisition attempts raced before binding access, before and
   after ownership, during recovery, and between endpoint binding and
   authenticated registration prove both exclusion directions, clean unwind,
   and release after success, failure, and process exit; an ownership waiter
   releases shared authority before backoff;
10. a controller return, crash, or readiness deadline during child startup
   leaves no uncovered publication interval, late publisher, overlapping
   control mutation, or foreground restoration before the child has stopped;
11. package removal raced against manager backoff, binding access, recovery,
    endpoint binding, publication, and steady-state serving cancels every retry
    and leaves no live or late publisher before launch artifacts or the
    executable are removed; controller crashes after barrier persistence,
    manager suppression, old-owner stop, partial removal, and artifact deletion
    preserve the exact incomplete generation and block ordinary acquisition,
    while a crash after the exact clear observes complete removal; generation A
    cannot clear, overwrite, or repair generation B, and malformed or
    wrong-target removal records remain fail-closed; a successful removal leaves
    durable job state untouched and a generation-bound receipt from which an
    admitted reinstall can restore the prior enabled choice; an upgrade request
    cannot mutate or replace the incomplete removal operation; a reinstall that
    encounters an incomplete removal takes exclusive authority, completes and
    exactly clears that generation before creating a new package artifact,
    retains manager suppression through new-package admission, and cannot let
    old removal recovery delete the new installation or restore manager launch
    while the barrier exists; and
12. package upgrade raced against manager backoff, binding access, recovery,
    endpoint binding, publication, and steady-state serving launches neither an
    old nor partial installation; an enabled installation restarts and proves
    authenticated readiness only after the complete successor passes admission,
    a disabled installation starts nothing, and a failed upgrade keeps manager
    launch suppressed while preserving the prior enabled choice and recoverable
    durable job state; controller crashes after marker persistence, manager
    suppression, old-owner stop, partial replacement, package admission, and
    manager restoration preserve the exact incomplete generation, block
    ordinary acquisition, and let only an exclusive repair finish or safely
    restart it; after successor readiness, delegated coverage survives a crash
    before or after the exact clear and prevents an uncovered publisher before
    the shared-authority handoff or clean exit; generation A cannot clear,
    overwrite, or repair generation B, and malformed or wrong-target upgrade
    records remain fail-closed barriers; a removal request cannot mutate or
    replace the incomplete upgrade operation; and
13. package reinstall persists a new exact generation after removal clear and
    before the first replacement artifact; crashes after removal clear, after
    reinstall-record persistence, during partial installation, after package
    admission, after receipt consumption, during manager restoration, and
    before exact clear leave either no new artifact or the exact durable barrier,
    never an acquirable partial installation; after exact clear they leave a
    complete admitted package with either an authenticated successor under
    continuous coverage or manager launch disabled; enabled and disabled choices
    follow the upgrade successor ordering, an old removal generation cannot
    delete the new package, malformed, wrong-target, and conflicting receipts or
    reinstall records fail closed before mutation, a consumed receipt without a
    matching incomplete reinstall record fails closed, and matching recovery
    accepts the consumed marker idempotently from the copied enabled choice; and
14. a job consuming its maximum drain still leaves enough of the 35-second
    graceful-stop budget for durable cancellation classification, endpoint
    shutdown, exact-registration removal, ownership release, and exit before
    force termination at 40 seconds; forced termination leaves durable job
    state recoverable by the next owner and is followed by exact-registration
    removal by the 45-second control deadline before success or replacement;
    and
15. Linux systemd-user and Windows per-user-task artifacts preserve the stated
    user, privilege, automatic-restart, bounded-backoff, stop, and process-tree
    bounds.

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
