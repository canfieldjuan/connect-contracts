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
of truth for whether background operation is enabled. When no background-mode
transition record exists, the service manager is the source of truth. While an
incomplete record exists, that record owns the exact transition and the manager
state is only an intermediate effect until exact recovery settles and clears it.

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
may start a new bounded retry sequence. Intentional disable, rebind,
durable-state reset or replacement, package removal, package upgrade, package
reinstall, and a successful manager stop do not trigger a restart. Disable,
rebind, durable-state reset or replacement, package upgrade, package removal,
or package reinstall during backoff cancels a pending restart before binding
access or publication.
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
  provider, the controller first persists the enable transition, stops the
  window publisher, then the service manager enables and starts or resumes the
  background entry point. The control succeeds only after an
  authenticated registration attributes serving to the expected durable
  state. If readiness fails within the control deadline, the application
  records rollback, stops the background entry point, restores the recorded
  prior manager choice, reports failure, and lets a still-open window restore
  its foreground provider through ordinary acquisition after exact clear.
- When the user turns background operation off, the controller first persists
  the disable transition, stops the background entry point and proves its
  endpoint, registration, and ownership gone, then disables automatic start.
  An open window starts its foreground provider only after the exact transition
  record is settled and cleared.
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

For per-user artifacts, enable, disable, rebind, and durable-state reset or
replacement take the combined per-user and package authority exclusively once.
For shared artifacts, each of those control operations first takes the package
authority in shared mode and then takes its per-user authority exclusively.
Package upgrade, removal, and reinstall take the package authority exclusively,
then take every affected user's per-user authority exclusively in canonical user
identity order. Before
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

Before binding or manager access, every shared acquisition and every enable,
disable, rebind, or durable-state reset or replacement control operation checks
under its required authority for both the package-operation and
application-private background-mode-transition and durable-state-reset records.
An incomplete, unreadable, malformed, or wrong-target record is a durable
barrier and makes an unrelated request fail closed before manager mutation,
state recovery, endpoint binding, or publication. It cannot clear, overwrite,
or order itself around that record. Only the recorded lifecycle operation
holding its required exclusive control authority may recover the record and
resume or safely restart the exact operation, except after the explicit
package-removal ownership handoff defined below makes that exact package
generation the sole recovery authority.

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

The background entry point started inside an enable, rebind, durable-state
reset or replacement, package-upgrade, or package-reinstall transition does not
reacquire shared authority only while
the controller's correctly ordered package and per-user authority continuously
covers its startup. In shared artifact scope, enable, rebind, and durable-state
reset or replacement hold package shared plus that user exclusive; package
upgrade and reinstall hold package exclusive plus every participant user
exclusive. In per-user scope the combined authority is held exclusively once.
The controller retains or delegates every
required scope without a gap through authenticated publication or complete
failed-start cleanup and child exit. A controller return, crash, or readiness
deadline does not authorize a surviving child to continue uncovered. Before
exclusive per-user coverage can end, the child must already retain delegated
package coverage and complete a gap-free handoff to both shared authorities, or
exit before binding state access, recovery, endpoint binding, or publication.
The child still takes the provider-ownership lock. This closes the
check-then-start race without introducing a lifecycle queue.

### Crash-recoverable background-mode transition

Enable and disable are durable control transitions, not two unrelated service
manager commands. Before either transition changes a publisher, registration,
retry, or manager state, its controller atomically and durably writes one
owner-private, bounded, regular non-link background-mode-transition record
outside the mutable package and provider state. The record immutably binds its
format version, `enable` or `disable` kind, unique operation generation,
installed package identity and artifact scope, selected binding and opened
identity, expected v2 durable `instance_id` or v1 private lifecycle correlation,
the bounded observed publisher/process-tree and exact registration identities,
prior manager choice, and target manager choice. Kind and target must agree:
`enable` targets enabled and `disable`
targets disabled. A malformed, wrong-package, wrong-scope, wrong-binding,
wrong-state, or wrong-generation record fails closed before automatic mutation.

Before writing a new transition record, the controller holds its required
package and per-user authority and requires that no package-operation,
background-mode-transition, or durable-state-reset record already exists. An
existing record authorizes only its own exact recovery; a new control request
cannot infer completion from partial manager, process, or registration state.
Durable record commit is also an admission barrier: every still-live publisher
for the selected application/state checks it before each job creation and
returns pre-admission `PROVIDER_BUSY` until exact clear. This prevents a crash
between intent persistence and the first stop signal from admitting new work.
The check is linearized through one application-private transition-admission
gate: a job-creation route holds it shared from barrier checks through accepted
job commit, while the controller holds it exclusively only across durable
transition-record or package-handoff commit. The controller releases this gate
before it waits for process exit or provider ownership. A job committed before
the barrier is drained under the existing stop contract; no job can commit
after the barrier and before exact clear.
An ordinary foreground/background entry point that encounters a valid record
exits before binding access or publication. An application recovery entry point
may release any shared acquisition authority, reacquire package-shared then
per-user-exclusive authority (or the combined per-user authority exclusively),
validate the exact generation, and become its recovery controller. It does not
hold shared authority while waiting for exclusive recovery.

An enable record starts with a durable `forward` disposition and advances
monotonically through `intent-recorded`, `source-stopped`, `manager-enabled`,
and `successor-ready`. Readiness failure may durably advance once to an
irreversible `rollback` disposition, after which recovery may only stop the
target, restore the immutable prior manager choice, and settle failure. A
disable record advances monotonically through `intent-recorded`,
`publisher-stopped`, and `manager-disabled`. Exact-generation recovery under the
same package and per-user exclusive authority idempotently resumes only the
recorded kind, target choice, phase, and disposition. An opposite toggle,
rebind, reset, package operation, or ordinary provider acquisition cannot
overwrite, clear, retarget, or order itself around the record; it must first let
exact recovery settle and clear that generation, except for the explicit
package-removal ownership transfer defined below.

Before each distinct stop phase issues its first stop request, the record
durably binds that phase's immutable stop-attempt identity and original
graceful, force, and control deadlines. The phases are enable-source,
enable-rollback-target, and disable-background; a transition records only the
phases it reaches. Recovery never grants an existing phase a new drain or
deadline. It uses only that phase's provable remaining budget; after reboot,
clock rollback, or missing timing evidence makes the remaining budget uncertain,
recovery treats its graceful budget as exhausted and proceeds to the forced-stop
classification and exact cleanup required below.

For enable, the controller persists intent before stopping a foreground owner.
It proves that owner's endpoint dead, exact registration absent, and provider
ownership released before enabling and starting the background entry point. The
transition child remains under the continuous retained or delegated coverage
defined above and may publish only for authenticated readiness. Every job
creation route returns pre-admission `PROVIDER_BUSY` while the enable record
exists, so rollback cannot abandon accepted work. After exact-state readiness,
the controller durably records `successor-ready` before it clears the exact
record; the exact authenticated successor may admit jobs only after durable
clear under the gap-free authority handoff. If forward readiness cannot be
proved, rollback stops the complete target process tree,
proves its endpoint, exact registration, and ownership gone, restores and reads
back the prior manager choice, and clears the record. A still-open foreground
host may restore its publisher only afterward through ordinary acquisition.

Before exact clear, the transition child also remains bound to a bounded,
authenticated controller-liveness channel or equivalent application-private
lease. Loss of its controller before clear makes the child keep returning
pre-admission `PROVIDER_BUSY`, remove only its exact registration, exit, and
release provider ownership plus every delegated shared scope within the existing
startup-cleanup bound. Exact recovery never waits behind a surviving pre-clear
child. After clear, the same child may complete the ordinary gap-free handoff to
steady-state shared authority.

For disable, the controller persists intent before its first stop or manager
mutation. It cancels pending retry, stops every background publisher tree for
the application, and proves every endpoint dead, exact registration absent, and
provider ownership released before recording `publisher-stopped`. It then
durably disables automatic manager launch and records `manager-disabled` before
clearing the exact record. Holding exclusive authority prevents a concurrent
publisher acquisition; after a controller crash, the durable record prevents a
manager retry or independently started child from recovering, binding, or
publishing. An open window may start a foreground provider only after the record
is absent and the manager's disabled choice is read back.

The record's settlement choice is its target choice for forward enable and
disable, and its immutable prior choice after enable selects rollback. The
controller clears only its own exact generation after that settlement choice
and the disposition's required publisher/registration outcome are both proved.
A crash before clear therefore leaves a record that owns completion; a crash
after durable clear observes the fully settled manager choice. A controller
return, deadline, or crash never authorizes its transition child to continue
uncovered, and service-manager state alone never clears or completes an
operation record.

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

### Durable-state reset and replacement

The explicit v2 durable-state reset or replacement operation governed by
ADR-0002 takes the same package-shared then per-user-exclusive control authority
as rebind for shared artifacts, or the combined authority exclusively for
per-user artifacts. It validates that the selected binding and opened state
carry the recorded old `instance_id`. A live publisher for a different durable
state makes the operation fail before mutation and is not displaced. Windows
also applies ADR-0005's placement-specific registration cleanup.

Before writing its record or making its first state, identity, manager, or
registration mutation, the controller requires under its package-shared and
per-user-exclusive authority that no package-operation or
background-mode-transition or durable-state-reset record exists. Any
incomplete, unreadable, malformed, or conflicting record makes reset fail
closed without writing a reset record or changing manager, state, identity, or
registration data; reset cannot clear or advance that other operation.
The controller then writes an owner-private, bounded, regular non-link durable
reset record outside both source and target state. Its operation generation,
installed package identity and declared artifact scope, source binding and opened
identity, old `instance_id`, expected source registration identities, target
identity, allocated new `instance_id`, and prior manager choice are immutable.
Its phase advances only through `source`,
`target-prepared`, `target-committed`, then either irreversible `forward-only`
or `rollback`; rollback may advance to absorbing `removal-handoff`, while a
successfully recovered side advances to `settled`. No later phase reverses. The
record is the acquisition barrier described above. Only exact-generation
recovery under the same exclusive authority may advance or clear it. Unreadable,
malformed, wrong-package, wrong-scope, wrong-binding, wrong-state,
wrong-registration, wrong-identity, or wrong-generation data fail closed before
automatic mutation.

While holding exclusive authority, reset cancels manager retry, suppresses
manager launch, and stops every foreground and background publisher tree that
can serve the selected source across protocol modes. It first proves every old
endpoint dead and provider ownership released. In the fixed acquisition order
it then takes provider ownership and every applicable v1 and v2 publication
lock, validates and removes only each exact dead publisher's registration and
temporary, and only then proves those registrations absent. On Windows the old
v2 destination and temporary use ADR-0005's exact cleanup; other platforms use
their existing protocol publication and exact-registration rules.

Reset does not proceed while the source retains any accepted job still covered
by its existing query, reconciliation, or retention contract, including a
terminal result that a consumer may still retrieve. It aborts before state or
identity mutation, restores the prior manager choice and source publisher as
applicable, and reports that retained work blocks reset. It never forces a
terminal classification to bypass that boundary and never copies, reinterprets,
or freshly submits an old accepted job under the new identity.

The controller prepares and admits the complete target state and persisted new
`instance_id` while retaining verified source rollback material, then records
`target-prepared`. An atomic, durable application-private binding or
state-descriptor replacement is the reset commit point and records
`target-committed`. Before it, only the source and old identity are
authoritative; after it, only the target and new identity are authoritative. An
implementation may not destroy or mutate the source in place when a crash could
pair one state epoch with the other identity.

If the prior manager choice is enabled or a foreground host requires serving,
the controller starts the target under continuous control coverage. The child
takes provider ownership and every applicable publication lock, may publish for
authenticated readiness, but returns only pre-admission `PROVIDER_BUSY` from
every job-creation route while the record remains `target-committed`. A
disabled choice needs no child. Before forward becomes irreversible, target
readiness failure stops the target, removes only its exact registrations, proves
it absent, durably selects `rollback`, atomically restores and rereads the
source binding and old identity, and only then may restart the source. Rollback
failure starts neither side and leaves the record as a barrier. Exact recovery
may retry only the same rollback while its immutable source material remains
valid.

After rollback failure, an explicit package-removal request may ask exact reset
recovery to durably advance that generation to absorbing `removal-handoff`.
This phase makes neither state authoritative, starts neither publisher, and
permits only the matching package-removal barrier transfer below; it does not
permit enable, rebind, another reset, upgrade, reinstall, or ordinary provider
acquisition. A corrected source may repair rollback before this marker, but no
state repair or forward recovery is allowed later in that reset generation or
before package removal completes. After completed removal, only a new reinstall
generation carrying this exact immutable predecessor may perform the explicit
state resolution defined below; an upgrade or ordinary reinstall cannot.

After authenticated target readiness, or complete local target admission for a
disabled choice, the controller durably advances to irreversible
`forward-only`. Only then may the target admit a job. Recovery after that marker
may resume or finalize only the target and never select rollback or reactivate
the source. A crash before the marker therefore cannot strand a target job, and
a crash after it cannot abandon that job by restoring the old identity.

Crash recovery is exact-generation and monotonic. Before the reset commit it
may complete forward or restore only the source; after commit but before
`forward-only` it may resume the target or select rollback while verified source
material remains. The controller clears only its exact record after one side is
settled, every opposing endpoint and exact registration is absent, ownership
matches that side, and the prior manager choice is restored. A controller crash,
return, or deadline never leaves a child outside continuous authority coverage.

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

Each package-operation record, removal receipt, and receipt-retirement
tombstone is a bounded, non-link regular file outside the mutable installed
package. A per-user artifact is owner-private. A shared artifact is protected
at package-operation scope and cannot be replaced, cleared, or consumed under
only one participant's authority. Each shared-scope operation record binds the bounded exact
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

Before any package upgrade, removal, or reinstall writes a package-operation
record or mutates a manager or package artifact, its package-exclusive and
participant-user-exclusive authority checks every participant's
application-private background-mode-transition and durable-state-reset records.
Any such record makes upgrade, reinstall, and unrelated removal fail closed
without writing a package record or changing manager or artifact state. Those
operations cannot clear, advance, or order themselves ahead of it; exact
per-user recovery must settle and clear it first.

The sole exception is an explicit removal whose complete participant map names
every matching predecessor as exactly one of `ordinary`,
`background-control-handoff`, or `reset-handoff`. A control handoff may copy a
valid incomplete background-mode-transition record. A reset handoff may copy
only a valid record already in `removal-handoff`. Every predecessor must match
the bounded exact package participant set, installed package, artifact scope,
and participant identity. A participant with both record kinds, a missing or
duplicate predecessor, a reset in another phase, or unreadable, malformed, or
mismatched data blocks removal before mutation. For a control handoff, the
canonical `preserved_manager_choice` is derived only from immutable choices and
durable disposition: `disable` preserves disabled, a forward `enable` preserves
enabled, and an enable record in irreversible `rollback` preserves its recorded
prior choice. A reset handoff preserves its recorded prior choice; an ordinary
participant preserves the stable manager choice observed with no per-user
record. The package choice map, typed predecessor, removal receipt, and later
reinstall choice map MUST all contain that same canonical value. A mismatch or
an attempt to use a transitional manager bit fails before mutation.

Under package-exclusive and every affected participant's user-exclusive
authority, the remover copies every matched handoff into its normal package
removal record. For each reset handoff it copies the participant, type, reset
generation and phase, package target and artifact scope, source binding and
opened identity, old `instance_id`, expected source registration identities,
target identity, new `instance_id`, and prior manager choice. For each control
handoff it copies the participant, type, transition kind, generation, phase and
disposition, package and scope, binding/opened/state identity, expected
publisher/process-tree and registration identities, prior and target manager
choices, canonical preserved choice, and the complete stop-attempt/deadline set.
It durably commits that complete typed predecessor set and canonical package
choice map as the atomic ownership handoff under the transition-admission gate
exclusively before it idempotently clears any matched per-user record.
Before that commit, each per-user record is the sole recovery authority. After
that commit, the exact package-removal generation is the sole recovery
authority; any still-present matching per-user record is inert predecessor
evidence that only this package generation may clear. Exact control or reset
recovery encountering the matching committed package record exits without
mutation. A crash before the package commit leaves only the per-user
authorities; a crash after it leaves only package recovery authority regardless
of how many inert predecessor files remain. No executable, manager, state,
registration, or package artifact changes before every transferred record is
cleared under that ordered barrier transfer, and upgrade or reinstall cannot
perform this transfer.

From package-record commit until every inherited publisher tree has ended, the
package barrier also inherits each transferred control record's pre-admission
gate. Every job-creation route in such a publisher returns `PROVIDER_BUSY` even
after its per-user transition record is cleared. The remover then cancels its
coverage, stops the tree, and proves endpoint death, ownership release, and
exact-registration absence before package mutation.

Under that same authority and before writing a new package-operation record, a
package controller also recovers any completed reinstall receipt-retirement
tombstone. A valid tombstone binds the exact completed reinstall generation,
outcome, target, participant set, predecessor receipt producer identities, and
predecessor receipt filenames. Recovery deletes only those bound consumed
predecessor receipts idempotently and deletes the tombstone last. An unreadable,
malformed, mismatched, or unbound consumed receipt fails closed before a new
package record or artifact mutation. A valid completed tombstone is cleanup
authority, not an incomplete lifecycle barrier, and does not block ordinary
provider acquisition.

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
successor remains covered by the controller's package and user authorities while
the package record is incomplete. Pre-clear blocking authority is never
inherited by or delegated to the child. Controller death therefore releases
those process-scoped authorities without child cooperation. The child watches an
authenticated controller-liveness channel; on loss before exact clear it stops
serving, removes only its exact registration, releases provider ownership, and
exits within the startup-cleanup bound. A hung child cannot block acquisition of
exclusive control: exact recovery acquires the controller-owned authorities,
force-stops that recorded process tree within the existing control deadlines,
proves endpoint death, ownership release, and exact-registration cleanup, and
then resumes the generation.

The atomic durable commit that clears the exact package generation replaces
controller coverage with one post-clear successor-handoff barrier per started
participant. Each barrier is bound to the package generation, participant,
exact child process credentials, durable state, binding, serving generation, and
one persisted nonrenewable handoff attempt and deadline. Crashes never reset the
deadline; uncertain remaining time is treated as expired. The barrier is
universally checked by provider acquisition, background control, durable-state
control, and every package operation under the normal package-first authority
order. It is not a manager choice and grants no job admission by itself.

The named, already-ready child first CASes `pending` to `child-claimed` before
acquiring shared package/user authority. After acquisition it revalidates the
same claim and deadline, then consumes the barrier while still holding shared
authority; job admission remains `PROVIDER_BUSY` until that durable consumption
commits. If consumption wins, shared authority covers the first instant without
the barrier. If the child crashes or freezes after claiming or after acquiring
shared authority, the still-durable barrier continues to block every competing
path.

The controller releases its own coverage only after the barrier commit. A crash
after commit therefore leaves durable mutually exclusive coverage while the
exact child finishes shared acquisition; a crash before commit leaves no barrier
and recovery handles the pre-clear child as above. On child death, liveness loss,
or handoff-deadline expiry, exact barrier recovery CASes `pending` or
`child-claimed` to `recovery-claimed` before waiting on package/user authority.
That durable claim revokes the child's handoff permission: every child route
continues returning `PROVIDER_BUSY`, it cannot consume the barrier, and it must
release shared authority and exit if it resumes.

`recovery-claimed` is an absorbing phase owned by the immutable package/barrier
generation, not by the process that won the CAS. It authorizes exact-generation
recovery to force-stop the named complete process tree before exclusive lock
acquisition. Any later recovery controller that validates the same package,
generation, participant, child credentials, binding, durable state, and serving
generation idempotently resumes that stop; it does not need or attempt a second
claim transition.

After the stop releases any child-held shared locks, recovery acquires exclusive
package/user authority, revalidates the unchanged `recovery-claimed` barrier,
proves endpoint death, ownership release, and exact-registration cleanup, and
CAS-deletes only that barrier. Crashes after the recovery CAS, force-stop,
exclusive acquisition, cleanup proof, or immediately before deletion resume the
same phase; a crash after exact deletion observes no barrier and performs no
stale cleanup. If barrier consumption beat the recovery CAS, no recovery claim
exists and the child's already-held shared authority remains the ordinary
coverage. Malformed, mismatched, duplicate, expired-but-unclaimed, or unowned
barriers remain fail-closed. Participants settled as disabled or deferred-enabled
have no child or handoff barrier; their durable manager choices must already
match the record before clear.

An installation or readiness failure completes failed-start cleanup, keeps
manager launch suppressed and the upgrade record incomplete, preserves durable
job state and every prior enabled choice for exact-generation forward, rollback,
or removal recovery, and reports the provider visibly unavailable. A crash
before the exact clear leaves the durable admission barrier rather than an old
or partial installation that a new provider entry point can start.

Package removal takes exclusive control authority before disabling manager
startup or changing launch artifacts. Before either mutation, it atomically and
durably writes the package-operation record, naming package removal, a unique
operation generation, the target installed package, the canonical preserved
manager choice map, the optional complete typed lifecycle-predecessor set
transferred above, and an
incomplete state. A transferred participant's preserved choice comes from its
reset or background-mode-transition predecessor, never the already-suppressed
manager. While holding exclusive authority, the remover cancels
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
package. Each receipt binds its participant and the exact package-operation kind
and generation whose removal or absorbing removal disposition produced package
absence, and copies that participant's canonical `preserved_manager_choice` for
a later reinstall. For a participant with a transferred predecessor, the receipt also
carries that participant's complete immutable typed predecessor copied into the
package record. A reset predecessor leaves both state epochs and every durable
job untouched; a background-control predecessor changes no provider state or
job. That producer identity is the completed removal generation for
receipt validation even when the immutable operation kind is upgrade or
reinstall. A
crash after any receipt but before the complete receipt set and exact clear
leaves the barrier in place and lets exact recovery reuse completed receipts
idempotently. The controller then clears the incomplete record and releases
control authority.

A crash before the clear leaves ordinary acquisition blocked until exclusive
recovery completes removal. A failed removal keeps manager launch suppressed
and the record incomplete, reports failure, and preserves durable job state and
the complete canonical preserved-manager-choice map.

A reinstall takes exclusive control authority before it inspects or changes
package files, launch artifacts, manager state, the operation record, or the
removal receipt. If an incomplete removal record exists, the installer validates
and completes that exact removal generation through its receipt and exact clear
while manager launch remains suppressed. It does not overwrite the record,
start a new package generation, or create any new package artifact first. A
malformed, wrong-target, or conflicting receipt or record fails closed before
mutation. A consumed receipt with neither its matching incomplete reinstall
record nor its matching completed receipt-retirement tombstone fails closed
before mutation; a matching tombstone is recovered through the cleanup rule
above before any new reinstall generation begins.

After exact removal clear and proof that the old target artifacts are absent,
but before creating the first new package artifact, the installer atomically
and durably writes a new package-reinstall operation record outside the package.
It has a unique generation, the new target package identity, the matching
completed removal-receipt producer kind and generation and participant set,
the exact copied preserved manager choice map, every carried typed lifecycle
predecessor, and an incomplete state. Failure to persist
that new record leaves the package absent, every receipt unconsumed, and manager
launch suppressed. A reinstall controller that starts with an incomplete reinstall
record takes exclusive authority, validates and recovers that exact generation,
and rolls it forward or safely
restarts it without inferring completion from partial files. It accepts an
already-consumed marker only when the receipt producer kind and generation,
package target, participant set, choice map, and incomplete reinstall record all
match; it then uses only the preserved choices copied into the record and does
not consume a receipt again.

The installer holds the same exclusive authority across removal recovery,
reinstall-record persistence, new-package installation, and new-enable
admission. The reinstall generation then follows the upgrade generation's
enabled or disabled successor start, authenticated readiness, delegated
coverage, exact clear, and shared-authority handoff ordering.

For a participant carrying a background-control-handoff predecessor, the
reinstall record validates the copied predecessor and uses only its derived
preserved manager choice. It does not recreate or resume the old transition,
infer a choice from manager state, or start a provider before complete-package
admission. After admission it settles that enabled or disabled choice through
the ordinary service-session rule.

For each participant carrying a reset-handoff predecessor, installed package
bits do not settle that participant. The reinstall controller keeps manager
launch suppressed and provider acquisition blocked until an explicit
state-resolution choice selects either the predecessor's exact source binding,
opened identity, and old `instance_id`, or its exact target identity and new
`instance_id`. Before binding mutation it durably records that immutable choice
in the reinstall record, validates and admits the selected state without
reinterpreting or deleting durable jobs, and proves the opposing publisher and
registrations absent. Only then may it apply the predecessor's recorded prior
manager choice and perform ordinary disabled, deferred-enabled, or authenticated
settlement. It cannot invent a new state, infer a choice from package presence or
manager state, or clear, tombstone, or retire the predecessor while unresolved.

Installation or readiness failure keeps manager launch suppressed and the
reinstall record incomplete for exact recovery. It never treats a receipt or
tombstone as readiness and never restores manager launch while the removal
barrier remains incomplete or before the new package passes admission. The
reinstall barrier remains until every disabled choice is settled and every
enabled choice is either served by an authenticated successor under continuous
coverage or durably deferred because no capable service session exists.

For a forward disposition, every participant settlement above completes before
tombstone publication or predecessor receipt consumption. For an absorbing
removal disposition, before the first predecessor-consumption/replacement pair
described below, the controller atomically publishes and durably commits a
completed receipt-retirement tombstone outside the package. The tombstone names
this exact reinstall generation, its forward or removal outcome, target,
participant set, and complete predecessor receipt set. The controller then
atomically and durably marks only every matching participant receipt consumed.
After the complete matching set is marked, the still-incomplete reinstall
record is the sole owner of the copied enabled choices and the tombstone is the
sole authority to retire those predecessor receipts after clear.

Only after settlement and complete matching predecessor consumption may the
controller clear that exact reinstall record. It then deletes the tombstone's
bound predecessor receipts idempotently and durably commits every bound
receipt's absence. Only after those absences are durable does it atomically
remove and durably commit the tombstone's absence. A crash before clear resumes
the active reinstall through its record; a crash after clear resumes only
receipt retirement through the tombstone. No order can leave a consumed
predecessor receipt without one of those two exact authorities, and no later
package operation writes its own record until retirement completes.

Exact-generation recovery may durably advance the same reinstall record only
from forward to the absorbing removal disposition before any receipt-retirement
tombstone for that generation is durable and after either deterministic
complete-package admission failure that exact recovery cannot repair without
changing the recorded target or an explicit user package-removal request. Once
a tombstone is durable, its recorded disposition is frozen. A removal request
after a forward tombstone must let that already-settled forward generation
complete exact clear and predecessor receipt retirement; only then may normal
package admission start a fresh removal generation. A
retryable installation or readiness failure, a readiness timeout, an unavailable
service session, or a deferred-enabled participant does not authorize removal.
Recovery never reverses that disposition or changes the record kind, generation,
artifact scope, participant
set, copied choice map, completed-removal predecessor, or failed target. A user
removal request may ask the exclusive recovery controller to make that advance;
a request for a corrected reinstall target cannot. The disposition is committed
before its first removal mutation. Recovery then keeps every manager suppressed,
proves all target process trees, ownership, and exact registrations ended,
removes the failed target and partial artifacts, and leaves durable jobs
untouched. For each recorded participant, it atomically and durably pairs that
participant's matching predecessor-receipt consumption with a replacement
removal receipt outside the package, bound to this reinstall generation and
preserving the exact choice and any unresolved reset-handoff predecessor.
Completed participant pairs are idempotent under
the still-incomplete reinstall record. Only after every target artifact is
absent and the complete replacement receipt set is durable may recovery clear
that exact reinstall generation. The package is then absent, manager launch
remains suppressed, and a corrected target requires a new reinstall generation
that consumes only that replacement receipt set. A crash resumes only the
recorded disposition; it cannot make the failed or corrected target acquirable.

If an executable is removed or replaced outside that serialized package
operation, a running provider still stops serving and removes its own
registration without waiting for the ordinary job drain. This is a defense
against external replacement, not the package-removal synchronization path.

### User-visible state

Applications distinguish these facts:

- background start has a stable enabled or disabled choice only when no
  transition record exists;
- an exact enable or disable generation is incomplete and requires recovery;
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
4. delayed readiness succeeds only after authenticated attribution. Enable
   durably records intent before foreground stop or manager mutation, and
   crashes after intent persistence, source stop, manager enable, target
   publication, authenticated readiness, rollback selection, and exact clear
   recover only that generation. Before clear every target job-creation route
   returns `PROVIDER_BUSY`; a readiness deadline stops the target and restores
   the recorded prior manager choice before exact clear, then a still-open
   window may restore its provider through ordinary acquisition. Success clears
   before the target admits work. Controller loss after target publication or
   readiness makes the pre-clear child remove its exact registration, exit, and
   release delegated scopes before exclusive recovery proceeds. The source-stop
   and rollback-target-stop phases use distinct persisted attempts and deadlines;
   repeated crashes never reset either phase's clock;
5. disable durably records intent before its first stop or manager mutation,
   drains or bounds the admitted job, removes the exact registration, proves
   ownership released, and persists the manager's disabled choice before exact
   clear and one foreground replacement. Crashes immediately after record
   persistence, publisher stop, manager disable, and clear resume or observe
   only the recorded disabled outcome; a retry or child cannot publish through
   the barrier, and a still-live old publisher returns `PROVIDER_BUSY` after
   record commit. Repeated controller crashes reuse the record's original stop
   attempt and never reset its drain or control deadlines; uncertain remaining
   time is treated as expired. Unreadable, malformed, wrong-package, wrong-scope,
   wrong-binding, wrong-state, and wrong-generation records fail closed before
   unrelated control, acquisition, or package mutation;
6. crashing an enabled provider causes the Linux or Windows user manager to
   launch a recovering owner within the declared first-retry bound and without
   an open window; that owner uses new process credentials, reuses the v2
   durable identity, and reconciles accepted work without duplicate submission;
   repeated failure exercises the delay, attempt/window ceiling, and stable
   serving reset, while disable, rebind, durable-state reset or replacement,
   package upgrade, package removal, package reinstall, or intentional stop
   during backoff do not restart;
7. a v1 provider proves the private state-binding and serving-generation
   correlation before state-specific readiness or takeover succeeds;
8. malformed, linked, non-private, oversized, mismatched, and changed state
   bindings fail closed before service start;
9. control and acquisition attempts raced before binding access, before and
   after ownership, during recovery, and between endpoint binding and
   authenticated registration prove both exclusion directions, clean unwind,
   and release after success, failure, and process exit; shared-scope enable,
   disable, rebind, and durable-state reset or replacement prove package-shared
   then per-user-exclusive ordering, while an ownership waiter releases both
   shared scopes before backoff;
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
12. durable-state reset or replacement raced against foreground and background
    acquisition, manager retry, source job recovery, endpoint binding,
    publication, and steady serving persists its exact reset record and cancels
    retry before mutation. A forced-stop stale registration is cleaned only
    after endpoint death and ownership release, under every applicable protocol
    publication lock, and registration absence is proved afterward on Linux and
    Windows. Any source job still inside its query, reconciliation, or retention
    contract aborts reset and remains queryable under the source identity.
    Crashes after record persistence, old cleanup, target and new-ID preparation,
    the atomic reset commit, target publication or readiness, immediately before
    and after `forward-only`, rollback selection or commit, and exact clear
    recover exactly one paired state and identity with the prior manager choice.
    A concurrent job creation before `forward-only` receives `PROVIDER_BUSY` and
    persists no job; one after the marker may be accepted and recovery can no
    longer roll back. No old accepted job is lost, duplicated, copied, or
    submitted under the new identity; no new-ID publisher appears before commit
    and no old-ID publisher appears after forward settlement. Target failure
    before the marker proves it absent before restoring the source, rollback
    failure starts neither side, and exact recovery can retry the same rollback.
    Explicit removal requests after rollback failure persist
    `removal-handoff`; with two or more handoff participants and an ordinary
    third participant, one matching package remover validates the complete
    handoff set and durably copies every immutable state/identity field and prior
    choice into its removal record before clearing any reset record. Crashes
    before and after each clear retain a complete authority with no prior package
    mutation, and every affected removal receipt retains its exact predecessor.
    Upgrade, unrelated removal, ordinary acquisition, and state repair cannot
    consume the handoff; reinstall copies it, keeps launch blocked, and requires
    an explicit exact source-or-target resolution before settlement. A live
    different-state owner is not displaced,
    and malformed or mismatched records remain barriers. After a reset
    controller crash, unrelated enable, disable, rebind, and package operations
    fail before mutation until exact reset recovery clears the record;
13. two distinct OS users exercise both artifact scopes: per-user artifacts
    operate independently, while a shared-artifact package mutation by user A
    races user B's enable, disable, rebind, durable-state reset or replacement,
    live provider, startup, backoff, login, and logout under package-first
    authority and one package barrier; no new control or acquisition succeeds
    after barrier persistence and every
    recorded participant's manager, process tree, ownership, and exact
    registration end before artifact mutation. Failure to enumerate, suppress,
    or quiesce user B leaves artifacts unchanged and the barrier incomplete. A
    crash-persisted reset record for user B prevents creation of a package record
    and all manager or artifact mutation until exact reset recovery clears it. An
    enabled user B kept logged out through mutation and crash recovery settles
    as deferred-enabled after package admission, claims no readiness, does not
    force rollback or removal, and starts through ordinary acquisition only on
    a later session trigger. Crashes after participant discovery, a subset of
    manager stops, mutation, package admission, deferred settlement, active-user
    settlement, and exact clear preserve the exact participant and choice map;
    malformed scope or participant data fail closed before automatic mutation;
14. package removal raced against manager backoff, binding access, recovery,
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
15. package upgrade raced against manager backoff, binding access, recovery,
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
    wrong-scope, wrong-participant, or wrong-target records remain barriers.
    Controller loss after successor readiness but before exact clear makes each
    child remove its registration and release ownership, while controller-owned
    package/user locks disappear without child cooperation and exclusive
    recovery can force-stop a hung child. Loss after the atomic clear leaves the
    exact universally checked successor-handoff barrier until the named child
    completes shared acquisition and durable consumption or exact recovery CASes
    `recovery-claimed`, force-stops it before exclusive acquisition, then proves
    cleanup. Freeze/crash cuts at `pending`, `child-claimed`, after shared lock
    acquisition but before consumption, `recovery-claimed`, and immediately
    after consumption leave the barrier or shared lock as complete coverage. No
    competing acquisition or package mutation crosses either cut. Recovery
    crashes after its CAS, force-stop, exclusive acquisition, cleanup proof, and
    immediately before or after exact barrier deletion are resumed by a new
    controller from the same generation-owned phase without resetting the
    deadline or requiring the prior recovery process;
16. package reinstall persists a new exact generation after removal clear and
    before the first replacement artifact, copies the exact participant and
    choice map plus every carried typed lifecycle predecessor, and consumes only
    its matching receipt set. A participant with a reset predecessor remains
    blocked after package admission until an explicit exact source-or-target choice is
    durably recorded, admitted without deleting jobs, and authenticated to the
    selected durable state;
    package presence or manager state cannot select it. Crashes before and after
    that choice preserve the same unresolved or selected identity, and an
    absorbing removal carries an unresolved predecessor into the replacement
    receipt rather than retiring it. Other crashes after removal
    clear, record persistence, partial installation, package admission,
    forward participant settlement, atomic receipt-retirement tombstone
    publication, a subset of receipt consumption, exact clear, a subset of
    predecessor receipt deletion, durable receipt absence, atomic tombstone
    removal, and durable tombstone absence leave either the exact active barrier
    or a recoverable completed-retirement authority, never an acquirable partial
    installation or an unowned consumed receipt. Removal disposition publishes
    its tombstone before its first predecessor-consumption/replacement pair.
    After forward exact clear the generation leaves a complete admitted package
    with each enabled active-session successor authenticated under
    continuous coverage, each enabled sessionless participant durably deferred,
    and every disabled manager suppressed; an old removal generation cannot
    delete the new package, malformed or conflicting records fail closed, a
    consumed receipt without its matching incomplete reinstall or completed
    retirement tombstone fails closed, and matching recovery reuses consumed
    markers and deletes predecessor receipts idempotently with the tombstone
    last. A remove, reinstall, remove, reinstall cycle consumes only the current
    producer's receipt set and is never blocked by or attached to the retired
    predecessor generation. A removal request immediately before tombstone
    persistence may advance the same generation to removal. The same request
    immediately after a forward tombstone cannot change that generation: forward
    settlement, exact clear, and retirement finish first, then a fresh removal
    generation starts under normal package admission. Crashes on either side of
    this boundary never create a tombstone/outcome mismatch. A permanently invalid
    target advances that exact generation from forward to absorbing removal before
    mutation, while retryable installation or readiness failure,
    readiness timeout, and session absence remain forward-recoverable and never
    authorize removal; the transition never retargets the record, stops any
    target publisher, removes every target and partial artifact, preserves jobs
    and choices, and
    replaces the complete predecessor receipt set with reinstall-generation-bound
    removal receipts before exact clear. Crashes after disposition persistence,
    partial deletion, each predecessor-consumption/replacement-receipt pair,
    and before or after exact clear resume only removal or observe a fully absent
    package. A corrected target starts only as a new generation consuming the
    replacement set; a new reinstall cannot overwrite the failed generation,
    and malformed, wrong-scope, wrong-participant, wrong-choice, wrong-producer,
    or wrong-target recovery remains a barrier. Active, disabled, and
    deferred-enabled participants preserve their exact choice without requiring
    a logged-out user to become ready, and retirement deletes only predecessor
    receipts, never the replacement set. Reinstall successor children exercise
    the same controller-loss cuts immediately before and after atomic clear:
    controller-owned pre-clear scopes release without child cooperation and a
    hung child is force-stopped, while only a child named by the committed
    post-clear successor-handoff barrier may survive to finish shared
    acquisition. Frozen-child races before shared acquisition and after shared
    acquisition but before durable consumption prove recovery claims the barrier
    before force-stop and that the barrier blocks every competing package,
    control, and provider acquisition until exact consumption or cleanup. The
    same recovery crash cuts after claim, stop, exclusive acquisition, cleanup,
    and before/after deletion resume idempotently under the reinstall generation;
17. a job consuming its maximum drain still leaves enough of the 35-second
    graceful-stop budget for durable cancellation classification, endpoint
    shutdown, exact-registration removal, ownership release, and exit before
    force termination at 40 seconds; forced termination leaves durable job
    state recoverable by the next owner and is followed by exact-registration
    removal by the 45-second control deadline before success or replacement;
    and
18. Linux systemd-user and Windows per-user-task artifacts preserve the stated
    user, privilege, automatic-restart, bounded-backoff, stop, and process-tree
    bounds; and
19. a shared-scope explicit removal races mixed ordinary participants,
    background-control handoffs, and reset handoffs across at least two users.
    Durable commit of its complete typed predecessor and canonical choice maps
    is the atomic ownership handoff: before commit the per-user record owns
    recovery; after commit only the exact package generation owns it and any
    uncleared predecessor is inert evidence. Crashes before and after commit and
    each predecessor clear leave one complete recovery authority. A transferred
    forward enable from prior-disabled reinstalls enabled, enable rollback
    reinstalls the prior disabled choice, and disable from prior-enabled
    reinstalls disabled; the package map, receipt, reinstall map, and typed
    predecessor agree exactly. A ready enable child continues to return
    `PROVIDER_BUSY` from package commit through process termination even after
    its per-user record is cleared. Same-user duplicate or mixed predecessors,
    missing participants, malformed data, and wrong package, scope, binding,
    state, generation, or choice fail before manager or artifact mutation.
    Reinstall consumes only matching receipts and retains the explicit
    source-or-target resolution boundary for reset predecessors.

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
