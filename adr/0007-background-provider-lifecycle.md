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
package upgrade, package reinstall, and a successful manager stop do not
trigger a restart. Disable, rebind, package upgrade, package removal, or package
reinstall during backoff cancels a pending restart before binding access or
publication.
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

Every installed package declares one immutable artifact scope. Per-user scope
is conforming only when its executable, launch artifacts, operation record, and
manager entry points are not shared with or reusable by another OS user; the
per-user control authority is then also its package authority. If any executable
or launch artifact is shared, the package provides a protected package-wide
operation authority and durable barrier outside the mutable package. Every
installer, launcher, foreground and background entry point, and affected user
manager participates in that authority.

For per-user artifacts, enable, disable, and rebind take the combined per-user
and package authority exclusively once. For shared artifacts, each of those
control operations first takes the package authority in shared mode and then
takes its per-user authority exclusively. Package upgrade, removal, and
reinstall take the package authority exclusively, then take every affected
user's per-user authority exclusively in canonical user identity order. Before
any manager or package mutation, a shared-scope package operation durably closes
admission to new session launches, enumerates every affected user, records that
participant set and each prior enabled choice, cancels every retry, suppresses
every manager, stops every provider process tree, and proves every provider
ownership and exact registration ended. Failure to enumerate, suppress, or
quiesce any participant leaves the package barrier incomplete and changes no
package artifact. The barrier remains through package admission and each
participant's disabled, deferred-enabled, or authenticated-successor settlement.
A package that cannot provide this coordination must use per-user artifacts.

Foreground and independently started background provider acquisition take the
package authority in shared mode and then the per-user control authority in
shared mode before reading or validating the selected binding and before their
nonblocking provider-ownership attempt. When both scopes use the same per-user
authority it is acquired once. A failed ownership attempt releases shared
authority before any wait or backoff and reacquires it before a new attempt. A
successful attempt retains both shared authorities through opened-state
revalidation, job recovery, endpoint binding, atomic registration publication,
and authenticated attribution to the selected state. It releases them after
that startup commits; provider ownership and publication locks continue to
guard steady-state serving.

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
The fixed acquisition order is package authority, per-user control authority,
provider-ownership lock, then any protocol publication lock. A conflicting
operation fails fast without manager mutation, binding access, state recovery,
endpoint binding, or registration.

The background entry point started inside an enable, rebind, package-upgrade,
or package-reinstall transition does not reacquire shared authority only while
the controller's correctly ordered package and per-user authority continuously
covers its startup. In shared artifact scope, enable and rebind hold package
shared plus that user exclusive; package upgrade and reinstall hold package
exclusive plus every participant user exclusive. In per-user scope the combined
authority is held exclusively once. The controller retains or delegates every
required scope without a gap through authenticated publication or complete
failed-start cleanup and child exit. A controller return, crash, or readiness
deadline does not authorize a surviving child to continue uncovered. Before
exclusive per-user coverage can end, the child must already retain delegated
package coverage and complete a gap-free handoff to both shared authorities, or
exit before binding state access, recovery, endpoint binding, or publication.
The child still takes the provider-ownership lock. This closes the
check-then-start race without introducing a lifecycle queue.

### State binding and privacy

The service entry point reads one application-owned, owner-private binding to
the provider's durable state. Rebind takes exclusive control authority and
validates the target while the old binding remains authoritative. It cancels
pending manager retry, stops every possibly live publisher for the application
across foreground and background modes, protocol modes, and durable-state
bindings, then proves the old endpoint dead, its exact registration absent, and
provider ownership released before replacing the binding. If a publisher cannot
be stopped or those facts cannot be proved within the control deadline, rebind
fails, preserves the old binding, and starts no target publisher.

Only after that proof may rebind atomically and durably replace the binding,
read back its opened identity, and start the target under continuous control
coverage. Binding replacement is the crash commit point: a crash before it
leaves the old binding authoritative; a crash after it leaves the target
authoritative, and later acquisition may use only the complete binding that
durably survived. If target readiness fails, the controller first stops the
target process tree and proves its endpoint dead, exact registration absent,
and ownership released. It then atomically and durably restores and rereads the
old binding before any old-state publisher may restart. If rollback cannot be
proved, it starts no publisher and reports the selected state unavailable. No
path leaves a publisher for one binding live while another binding is committed
or restored.

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

Every package-operation record and removal receipt is a bounded, non-link
regular file outside the mutable installed package. For per-user artifacts it
is owner-private. For shared artifacts it is protected at package-operation
scope and cannot be replaced, cleared, or consumed under only one participant's
authority. Each shared-scope operation record binds the bounded exact
participant set and generation-bound prior enabled choice and settlement state
for every affected user; singular user, choice, process, registration, and
receipt language below applies to every recorded participant.

After complete-package admission, each upgrade disposition or reinstall that
leaves a package installed settles a recorded enabled choice according to the
participant's actual service-session state. If that user's manager is available
and can launch in the current session, the controller starts the successor under
continuous authority coverage and records settlement only after authenticated
readiness. If no service session capable of that user's startup exists, the
controller durably restores the enabled manager choice without starting a
process, claiming readiness, or waiting for login, records `deferred-enabled`
settlement, and keeps the operation barrier through that commit. The next
platform session trigger performs ordinary package-shared and per-user-shared
acquisition after the package operation clears. Session absence is not failed
package admission, failed rollback, or justification for removal. A recorded
disabled choice remains disabled and starts nothing.

Package upgrade takes exclusive control authority before suppressing manager
startup or changing launch artifacts. Before either mutation, it atomically and
durably writes the package-operation record. The record names package upgrade
and contains a unique operation generation, immutable source and target package
identities, any verified rollback material or reference, every prior enabled
choice, and an incomplete state whose initial disposition is forward. While
holding exclusive authority, the upgrader cancels every pending manager retry,
prevents new shared acquisition, performs the bounded stop of every complete
process tree, waits for every provider ownership to end, and removes only each
exact dead process registration. It keeps automatic manager launch suppressed
while any launch artifact or executable may be incomplete.

An upgrade controller that starts with an incomplete record takes exclusive
authority and recovers that exact generation before any provider can acquire
shared authority. It verifies package state and resumes or safely restarts the
recorded disposition; it never infers completion merely from files being
present. It does not replace or clear an existing record with a new operation
generation, different target, or unverified state.

Exact-generation recovery may durably advance the same upgrade record only from
forward to rollback, forward to removal, or rollback to removal; it never
reverses a disposition. It never changes record kind, generation, artifact
scope, participant set, source identity, or failed target, and never installs a
third target. Each disposition is committed before its first package mutation.
Rollback restores only the recorded source from verified material, passes full
package, binding, and entry point admission, and settles every prior choice
through the service-session rule above before exact clear.

If forward recovery cannot pass admission and verified rollback is unavailable
or cannot settle, exact recovery advances the same generation to the absorbing
removal disposition before removal mutation. It suppresses every affected
manager, proves all process trees, ownership, and exact registrations ended,
removes source, target, and partial artifacts, leaves durable jobs untouched,
and durably writes generation-bound removal receipts preserving every prior
enabled choice before exact clear. A user removal request may ask the exclusive
recovery controller to advance that incomplete upgrade to removal; it does not
create, overwrite, retarget, or clear the record. Crashes resume the recorded
disposition idempotently. An unreadable, malformed, wrong-scope, wrong-target,
or unverifiable record remains a fail-closed barrier and permits no automatic
package mutation.

For forward or rollback settlement, only after the complete installed package,
each selected durable-state binding, and the background entry point pass the
same admission checks as a new enable may recovery restore manager choices. It
then applies the service-session settlement rule above and clears only after
every recorded participant is disabled, deferred-enabled, or authenticated on
the expected durable state.

For every participant started in an available service session, the ready
successor must retain delegated control coverage that survives controller exit
before the controller clears the record. The controller then clears only its
exact upgrade generation, atomically and durably, and every started successor
completes a gap-free downgrade or handoff to shared authority before the
controller releases its own coverage. A controller crash after the clear
therefore leaves each complete, authenticated successor covered; each successor
finishes the handoff or exits with normal exact-registration cleanup before
another acquisition can proceed. Participants settled as disabled or
deferred-enabled have no process to cover; their durable manager choices must
already match the record before clear.

An installation or readiness failure completes failed-start cleanup, keeps
manager launch suppressed and the upgrade record incomplete, preserves durable
job state and every prior enabled choice for exact-generation forward, rollback,
or removal recovery, and reports the provider visibly unavailable. A crash
before the exact clear leaves the durable admission barrier rather than an old
or partial installation that a new provider entry point can start.

Package removal takes exclusive control authority before disabling manager
startup or changing launch artifacts. Before either mutation, it atomically and
durably writes the package-operation record, naming package removal, a unique
operation generation, the target installed package, every prior enabled choice,
and an incomplete state. While holding exclusive authority, the remover cancels
every pending manager retry, prevents new shared acquisition, stops every
complete provider process tree without the ordinary job drain, waits for every
ownership to end, and removes only each exact dead process registration. It
removes launch artifacts and the executable only after no old process can serve
or publish.

A removal controller that starts with an incomplete removal record takes
exclusive authority and finishes that exact generation; it does not replace or
clear the barrier based on absent or partially removed files alone. It clears
only its exact generation, atomically and durably, after manager launch is
suppressed, the complete process tree and provider ownership have ended, the
exact registration is absent, and the target launch artifacts and executable
are absent. Before that clear it leaves provider durable job state untouched
and atomically and durably writes either an owner-private per-user removal
receipt or a package-operation-protected bounded receipt set outside the removed
package. Each receipt binds the exact removal generation and participant and
preserves that participant's prior enabled choice for a later reinstall. A
crash after any receipt but before the complete receipt set and exact clear
leaves the barrier in place and lets exact recovery reuse completed receipts
idempotently. The controller then clears the incomplete record and releases
control authority.

A crash before the clear leaves ordinary acquisition blocked until exclusive
recovery completes removal. A failed removal keeps manager launch suppressed
and the record incomplete, reports failure, and preserves durable job state and
every prior enabled choice.

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
completed removal-receipt generation and participant set, every copied prior
enabled choice, and an incomplete state. Failure to persist that new record
leaves the package absent, every receipt unconsumed, and manager launch
suppressed. A reinstall controller that starts with an incomplete reinstall
record takes exclusive authority, validates and recovers that exact generation,
and rolls it forward or safely
restarts it without inferring completion from partial files. It accepts an
already-consumed marker only when the receipt generation, package target,
participant set, choice map, and incomplete reinstall record all match; it then
uses the enabled choices copied into the record and does not consume a receipt
again.

The installer holds the same exclusive authority across removal recovery,
reinstall-record persistence, new-package installation, and new-enable
admission. The reinstall generation then follows the upgrade generation's
enabled or disabled successor start, authenticated readiness, delegated
coverage, exact clear, and shared-authority handoff ordering. Before the exact
reinstall clear, it atomically and durably marks only every matching participant
receipt consumed; after the complete matching receipt set is marked, the
still-incomplete reinstall record is the sole owner of the copied enabled
choices. Installation or readiness failure keeps manager launch suppressed and
the reinstall record incomplete for exact recovery. It never treats a receipt
as readiness and never restores manager launch while the removal barrier remains
incomplete or before the new package passes admission. The reinstall barrier
remains until every disabled choice is settled and every enabled choice is
either served by an authenticated successor under continuous coverage or
durably deferred because no capable service session exists.

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
   package reinstall or intentional stop during backoff do not restart;
7. a v1 provider proves the private state-binding and serving-generation
   correlation before state-specific readiness or takeover succeeds;
8. malformed, linked, non-private, oversized, mismatched, and changed state
   bindings fail closed before service start;
9. control and acquisition attempts raced before binding access, before and
   after ownership, during recovery, and between endpoint binding and
   authenticated registration prove both exclusion directions, clean unwind,
   and release after success, failure, and process exit; shared-scope enable,
   disable, and rebind prove package-shared then per-user-exclusive ordering,
   while an ownership waiter releases both shared scopes before backoff;
10. a controller return, crash, or readiness deadline during child startup
   leaves no uncovered package or per-user authority interval, late publisher,
   overlapping control mutation, or foreground restoration before the child has
   stopped;
11. rebind raced against foreground and background publishers stops every
    current publisher and proves its endpoint dead, exact registration absent,
    and ownership released before committing the target binding; a stop timeout
    preserves the old binding and starts no target, while crashes before and
    after the binding commit recover only the binding that durably survived;
    target-readiness failure stops and proves the target absent before restoring
    the old binding, rollback failure starts neither state, and crashes during
    rollback never produce readiness attributed to the wrong durable state;
12. two distinct OS users exercise both artifact scopes: per-user artifacts
    operate independently, while a shared-artifact package mutation by user A
    races user B's enable, disable, rebind, live provider, startup, backoff,
    login, and logout under package-first authority and one package barrier; no
    new control or acquisition succeeds after barrier persistence and every
    recorded participant's manager, process tree, ownership, and exact
    registration end before artifact mutation. Failure to enumerate, suppress,
    or quiesce user B leaves artifacts unchanged and the barrier incomplete. An
    enabled user B kept logged out through mutation and crash recovery settles
    as deferred-enabled after package admission, claims no readiness, does not
    force rollback or removal, and starts through ordinary acquisition only on
    a later session trigger. Crashes after participant discovery, a subset of
    manager stops, mutation, package admission, deferred settlement, active-user
    settlement, and exact clear preserve the exact participant and choice map;
    malformed scope or participant data fail closed before automatic mutation;
13. package removal raced against manager backoff, binding access, recovery,
    endpoint binding, publication, and steady-state serving cancels every retry
    and leaves no live or late publisher before launch artifacts or the
    executable are removed; controller crashes after barrier persistence,
    manager suppression, old-owner stop, partial removal, each participant
    receipt, and artifact deletion preserve the exact incomplete generation and
    block ordinary acquisition, while a crash after the exact clear observes
    complete removal. Generation A cannot clear, overwrite, or repair generation
    B, malformed or wrong-target records remain fail closed, durable job state
    remains untouched, and the bounded receipt set preserves every participant's
    prior enabled choice. Upgrade cannot replace an incomplete removal, and
    reinstall completes and exactly clears that removal before creating a new
    package artifact while retaining manager suppression through admission;
14. package upgrade raced against manager backoff, binding access, recovery,
    endpoint binding, publication, and steady-state serving launches neither an
    old nor partial installation; enabled participants authenticate only after
    complete-package admission, disabled participants start nothing, and durable
    jobs and all prior choices survive failure. A permanently invalid target
    exercises exact-generation rollback to the verified source for both enabled
    and disabled choices, including an enabled logged-out participant that
    settles as deferred without making the valid rollback fail; unavailable or
    failed rollback durably advances that same generation to removal, deletes
    source, target, and partial artifacts, preserves jobs and choices in
    participant receipts, and exactly clears only after removal settles. Crashes
    after disposition persistence, partial rollback, rollback admission,
    removal selection, partial deletion, each
    receipt, successor readiness, and before or after exact clear resume only the
    recorded disposition. A new upgrade cannot overwrite or retarget it, a user
    removal request can only advance its recovery to removal, and malformed,
    wrong-scope, wrong-participant, or wrong-target records remain barriers;
15. package reinstall persists a new exact generation after removal clear and
    before the first replacement artifact, copies the exact participant and
    choice map, and consumes only its matching receipt set; crashes after removal
    clear, record persistence, partial installation, package admission, a subset
    of receipt consumption, participant settlement, and before exact clear leave
    either no new artifact or the exact durable barrier, never an acquirable
    partial installation. After exact clear they leave a complete admitted
    package with each enabled active-session successor authenticated under
    continuous coverage, each enabled sessionless participant durably deferred,
    and every disabled manager suppressed; an old removal generation cannot
    delete the new package, malformed or conflicting records fail closed, a
    consumed receipt without its matching incomplete reinstall fails closed,
    and matching recovery reuses consumed markers idempotently;
16. a job consuming its maximum drain still leaves enough of the 35-second
    graceful-stop budget for durable cancellation classification, endpoint
    shutdown, exact-registration removal, ownership release, and exit before
    force termination at 40 seconds; forced termination leaves durable job
    state recoverable by the next owner and is followed by exact-registration
    removal by the 45-second control deadline before success or replacement;
    and
17. Linux systemd-user and Windows per-user-task artifacts preserve the stated
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
