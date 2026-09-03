# PR: Windows Local Connect placement

## Why this slice exists

Local Connect's wire contract is platform-neutral, but its discovery and
entitlement contracts currently name only XDG paths and explicitly defer
Windows placement. Both participating applications can be packaged for
Windows, yet they cannot find the same registration directory or shared
entitlement there. Building another executable cannot close that gap.

The root cause is a missing shared Windows filesystem contract. This slice
defines that contract while retaining exact-loopback HTTP and the existing
same-OS-user trust boundary.

## Scope (this PR)

1. Define the Windows per-user roots for runtime registrations and the shared
   entitlement.
2. Define Windows security, atomic-write, locking, and fail-closed behavior at
   the same abstraction level as the accepted Unix contracts.
3. Record that Windows continues to use the existing loopback HTTP transport;
   named pipes remain deferred.
4. Reconcile the older ADR deferral statements and link the new decision from
   the repository overview.

### Files touched

- `adr/0001-connect-v0.md`
- `adr/0003-connect-entitlement-v1.md`
- `adr/0004-connect-entitlement-activation-v1.md`
- `adr/0005-windows-local-placement.md`
- `README.md`
- `plans/PR-Windows-Connect-Placement.md`

## Mechanism

On Windows, providers and consumers derive the shared root from an absolute
`LOCALAPPDATA` value. Registrations use
`LocalConnect/runtime/v{n}/providers`; the entitlement and its persistent
activation lock use the `LocalConnect` root. Connect-owned path components and
files reject reparse points, registration and entitlement content remain
bounded, and writes use same-directory temporary files followed by atomic
replacement. Cross-process activation and provider ownership use non-blocking
Windows file locks. OWNER RIGHTS is admitted only as the already-validated
concrete owner; Creator Owner remains inherit-only. V1 permits one active
publisher per `app_id`, holds the fixed
`.local-connect-v1-<app_id>.lock` while serving, and publishes
`local-connect-v1-<app_id>.json`; the fixed prefix prevents valid app IDs from
becoming reserved Windows device basenames. V2 uses one registration per
durable provider instance. Registration temporaries end in `.tmp`, are removed
on every handled path, and never count as candidates after a crash. Restart
cycles therefore replace rather than accumulate registration candidates.
Consumers inspect at most 256 case-insensitive `.json` names in each
protocol-specific providers directory and fail closed before probing if a 257th
is encountered.

The current-user profile ACL is the Windows owner-private boundary. Connect
must fail unavailable when it cannot establish that boundary or when the root
is missing or relative. Standalone application behavior remains available.

## Intentional

- The registration, manifest, job, artifact, and entitlement JSON formats do
  not change.
- Exact-loopback HTTP and per-process bearer tokens remain the transport and
  authentication mechanism.
- Administrators and SYSTEM are treated like Unix root; protection from a
  hostile process running as the same user remains outside this contract.
- V1 and v2 restart cycles reuse stable registration slots; a v1 slot admits
  only one active process, and authenticated reachability still determines
  availability if a crash leaves a stale slot.

## Deferred

- Windows named pipes, a broker, launch-on-demand, machine binding, online
  activation, billing UI, code signing, installers, and auto-update.
- macOS placement and packaging.
- Application-private state placement, which remains owned by each app.

## Verification

- `python3 -m unittest tests.test_contracts`
- `python3 -m unittest`
- Review every Windows path and security rule against both participating app
  implementations before either Windows package is declared Connect-capable.

## Estimated diff size

Approximately 250 documentation lines. No executable schema or fixture changes
are required because transport and wire documents remain unchanged.
