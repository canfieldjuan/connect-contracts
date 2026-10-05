# ADR-0012: Shared local model runtime on Windows

**Status:** Proposed (accepted when this decision merges). The decisions marked
**(measured: Mn)** bind only after that measurement passes on Windows. Until
every measurement passes, ADR-0011's rule stands: no Windows bundle release.

The measurements first ran on Windows 11 on 2026-10-01 (see "Results so far").
M2 failed as first decided, so "Starting a host" now uses the candidate this
decision named, and the revised start passed.

**Date:** 2026-10-01

**Amends:** ADR-0011, "Platform scope". This is the Windows amendment it requires.

## Context and scope

ADR-0011 makes the local model runtime a per-user resource of the bundle:
- one content-addressed store;
- one model host per user, which runs the single `llama-server`;
- a lease-based attach protocol;
- one canonical profile.

It binds Linux x86-64 and says a Windows bundle release needs an amendment
first. The first release ships on Linux and Windows.

ADR-0011's "Platform scope" names four questions. This decision answers them:
- placement under ADR-0005's owner-private root;
- election and leases on ADR-0005's byte-range locks;
- the transport;
- the equivalent of the read lease.

ADR-0011 also relies on other Linux mechanisms, and this decision maps them as
well:
- `F_SETLEASE`, and the model passed as `/proc/self/fd/<n>`;
- `PR_SET_PDEATHSIG`;
- `systemd-run --user`;
- `/proc` liveness with a boot id;
- `SO_PEERCRED`;
- `XDG_RUNTIME_DIR`;
- `LD_LIBRARY_PATH`;
- `SIGTERM`.

**What does not change.** Everything in ADR-0011 not named here applies on
Windows unchanged:
- the profile's meaning and vendoring;
- the attach steps;
- the single slot;
- the lease timings (10 to 12 seconds, then 8 seconds);
- the start budgets (300, 120 and 15 seconds);
- the failure codes and records;
- the canary;
- the trust model. Processes of the same user are trusted, and a hostile
  same-user process is not defended against (ADR-0001, ADR-0005).

**Scope.** Windows 10 version 1803 or later, and Windows 11, on x86-64, with
per-user installs that keep the real `%LOCALAPPDATA%` (see "Packaging"). Not
covered: ARM64, MSIX and Store packages, and macOS.

## Placement

ADR-0005 defines the root as `%LOCALAPPDATA%\LocalConnect\` and its
owner-private boundary. The runtime uses three directories under it:

| ADR-0011 on Linux | Windows |
|---|---|
| Store: `$XDG_DATA_HOME/local-connect/runtime/v1/` | `%LOCALAPPDATA%\LocalConnect\model-store\v1\` |
| Registration: `$XDG_RUNTIME_DIR/local-connect/model/v1/` | `%LOCALAPPDATA%\LocalConnect\model\v1\` |
| Log: `$XDG_STATE_HOME/local-connect/model/v1/server.log` | `%LOCALAPPDATA%\LocalConnect\model\v1\server.log` |

- **The store is not under ADR-0005's `runtime\` tree,** which holds Connect
  provider registrations. The model store and registration are not Connect wire
  documents (ADR-0011, "Out of scope").
- **The contents are ADR-0011's:**
  - in the store: `models\`, `builds\`, `verified.json` and `store.lock`;
  - in the registration directory: `host.lock`, `clients.lock`, `server.sock`,
    `server.key`, `server.json` and `failure.json`.
- **ADR-0005's boundary replaces ADR-0011's owner, mode and symlink checks:**
  - `LOCALAPPDATA` must be absolute and usable. Otherwise the shared runtime is
    unavailable, with no fallback.
  - Each directory the runtime creates gets a protected DACL for the current
    user, SYSTEM and Administrators.
  - The effective DACL and the owner of the root, and of every directory and file
    the runtime uses, are verified before they are trusted.
  - Reparse points are refused anywhere under the root.
  - An existing unsafe path is refused, never rewritten.
- **The registration directory survives reboot,** unlike `XDG_RUNTIME_DIR`.
  - A record left by a dead host is stale by liveness (see "Registration and
    trust").
  - ADR-0011's stale-socket rule is unchanged: `server.sock` is removed only
    after any orphaned server is gone and a connect to it fails.

## The store

- **Placing a file.** A file enters by ADR-0011's verify-then-rename:
  - its contents are flushed;
  - it is renamed into place with `MoveFileExW` and
    `MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH`.
- **Placing a runtime set.** Its directory is renamed onto an absent name with
  `MoveFileExW`.
- **Durability.** Windows has no directory sync (ADR-0005). The runtime claims
  no more durability than a same-volume atomic rename gives.
- **A file's identity in `verified.json`.** In place of device, inode, size and
  change time, it is:
  - the volume serial number;
  - the 128-bit file id (`FILE_ID_INFO`);
  - the size;
  - the change time (`FILE_BASIC_INFO.ChangeTime`).
- **Locks.** All locks are ADR-0005's byte-range locks: byte `0`, length `1`, on
  lock files initialized with one byte.
  - A shared lock is `LockFileEx` without `LOCKFILE_EXCLUSIVE_LOCK`; an
    exclusive lock sets it.
  - A wait is a series of `LOCKFILE_FAIL_IMMEDIATELY` attempts until a deadline,
    never an indefinite wait (ADR-0005). The deadlines are:
    - 10 seconds for `clients.lock` (ADR-0011);
    - for a download lock, the downloader's own overall deadline;
    - 30 seconds for `store.lock`, which guards only a rename and a record.
  - Windows releases a dead process's locks, but documents that the release can
    take longer under load **(measured: M6)**. On Windows 11 a killed client's
    lease was released within 7 ms on an idle machine, and within 115 ms under
    CPU and disk load.

## The model host

**Election.** The host holds an exclusive, non-blocking lock on `host.lock` for
its whole life, as in ADR-0011.

**Pinning the served files.** This replaces the read lease, the descriptor
argument and the sealed copies.
- **The host pins every served file.**
  - From its file check until the server has exited, the host holds a handle on
    the GGUF and on every file of the runtime set.
  - Each handle is opened with `FILE_SHARE_READ` only: no write sharing and no
    delete sharing. It is opened with `FILE_FLAG_OPEN_REPARSE_POINT`, and the
    file must not be a reparse point.
- **The host pins the path.** It holds handles without delete sharing on:
  - the store root, `models\`, `builds\` and the runtime set's directory.

  So no path component can be renamed or replaced while the server runs.
  - Each directory handle is opened with `FILE_LIST_DIRECTORY` access and
    `FILE_FLAG_BACKUP_SEMANTICS`. A handle with only attribute access takes no
    part in sharing checks, so it pins nothing **(measured: M4)**.
  - The rest of the store stays usable while a server runs. Other models can be
    placed by rename and removed, and other runtime sets created (measured: M4).
- **The pinned files are the verified ones.** Before the server starts, each held
  handle's identity must equal its `verified.json` identity.
- **The effect.**
  - While the server runs, a write-open, rename or delete of any served file
    fails with a sharing violation **(measured: M4)**.
  - On Linux such a write-open ends the server. On Windows it is refused.
  - Both fail closed: the server only ever reads verified bytes.
  - An open for attribute access only is not refused (measured: M4). Another
    process can still change a served file's timestamps or attributes. That
    changes the identity `verified.json` records, so the next start verifies the
    file again. The bytes cannot change.
- **`<model>` is the GGUF's absolute store path.** The server opens it itself.
  - llama.cpp at the pinned commit opens the model with `fopen` and maps it
    read-only from that handle (`src/llama-mmap.cpp`: `ggml_fopen` at lines 87
    and 219, `CreateFileMappingA` at line 543).
  - The host's read-sharing handle admits both.
  - **A non-ASCII store path is safe.** The server rebuilds its arguments as UTF-8 from the wide command
    line (`common/arg.cpp`, lines 1254 to 1266). `ggml_fopen` converts UTF-8 back to wide characters
    before `_wfopen` (`ggml/src/ggml.c`, lines 606 to 617).
- **A store on a volume that cannot pin files is refused** with
  `STORE_UNSUPPORTED`. The host checks this by probing, not by trusting the volume type:
  1. It opens a probe file in the store, `.sharing-probe`, with `FILE_SHARE_READ` only.
  2. It requires a second write-open of that file to fail with `ERROR_SHARING_VIOLATION`, and a rename
     of it to fail the same way.

  A volume where either succeeds, or that reports no file id, is refused. Examples are some network
  shares, and redirected or filter-driver filesystems.

**Running the server**, in place of `PR_SET_PDEATHSIG`:
- **It runs only inside a job that ends with the host:**
  1. The host creates the server with `CREATE_SUSPENDED`.
  2. It assigns it to a job object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, and
     breakaway forbidden.
  3. Only then does it resume it.
- **The job handle is not inheritable,** and only the host holds it. When the
  host dies, the handle closes and the server is killed **(measured: M5)**. The
  pinned server ended 265 to 327 ms after `TerminateProcess` on its host, in 8
  of 8 kills.
- **The server gets nothing else from the host.** It inherits only its standard
  handles, through an explicit handle list, writing to the log. It runs with no
  window (`CREATE_NO_WINDOW`).

**The server's environment** is allow-listed, and has nothing else:
- `SystemRoot`, which Winsock needs;
- `TEMP` and `TMP`, pointing to a host-private directory inside the registration
  directory;
- `CUDA_DEVICE_ORDER=PCI_BUS_ID`;
- exactly one `PATH`, which the host builds and never inherits:
  1. the runtime set's directory;
  2. `%SystemRoot%\System32`, where the GPU driver's own libraries are.

In particular it gets no `LLAMA_*`, `GGML_*` or `CUDA_VISIBLE_DEVICES`. The
server's own directory is first in its library search order, and that
directory's files are pinned as above.

**Stopping the server.** The server writes nothing and holds no state worth
flushing.
- So the host stops it with `TerminateJobObject` and waits until the process has
  exited. This replaces `SIGTERM`, then `SIGKILL` after 5 seconds.
- Shutdown still completes within ADR-0011's 8 seconds.
- An orphaned server from an earlier host is ended with `TerminateProcess`, and
  only when its recorded identity is alive (see "Registration and trust").

**Tier choice.** The host reads NVIDIA devices through the driver's NVML
library, and other GPUs through the system Vulkan loader (`vulkan-1.dll`). It
reads them in a child process without elevated rights, as in ADR-0011. Windows
tiers have their own runtime pins (see "Profile").

## Registration and trust

**Files.** `server.key`, `server.json` and `failure.json` take their protection
from the registration directory's owner-private DACL, not from POSIX modes.

**Identity and liveness.**
- **Identity:** `server.json` records each process by its process id and its
  creation time (a `FILETIME`, in 100-nanosecond units). There is no boot id. A
  creation time is absolute, so it already tells processes apart across reboots.
- **A process is alive when all of these hold:**
  - `OpenProcess` with `PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE`
    succeeds;
  - a zero-timeout `WaitForSingleObject` on it times out;
  - `GetProcessTimes` reports the recorded creation time.

**Transport: `AF_UNIX` (measured: M1).**
- **The server listens on `server.sock`** in the registration directory, with
  `--host <path>.sock` as on Linux.
- **Why this works with the pinned build.** At the pinned commit:
  - `llama-server` switches to `AF_UNIX` for a host ending in `.sock`
    (`tools/server/server-http.cpp`, lines 438 to 442);
  - its HTTP library binds `AF_UNIX` on Windows when the build has
    `<afunix.h>`. See `vendor/cpp-httplib/httplib.h`, lines 267 to 270, and
    `vendor/cpp-httplib/httplib.cpp`, lines 2288 to 2329, with the same
    `sun_path` length check.
- **Who can connect.** Only a process that can reach the socket file inside the
  owner-private directory, so no other local user.
- **The path limit counts UTF-8 bytes.**
  - The server receives the path as UTF-8 (`common/arg.cpp`, lines 1254 to 1266), and its HTTP library
    copies those bytes into `sun_path` unchanged (`httplib.cpp`, lines 2304 to 2305).
  - A socket path of 108 bytes or more refuses before the host starts, and 107 bytes works.
  - The host enforces this itself. Neither Windows nor the pinned server refuses 108 bytes. The HTTP
    library refuses only a path longer than `sun_path` (`httplib.cpp`, line 2291), and a 108-byte path,
    with no terminating NUL, binds and serves **(measured: M1)**. The host keeps room for the NUL, as
    on Linux, so every reader of the address sees the same name.
  - A very long user profile path therefore makes the shared runtime unavailable, and the application
    says so.
- **A non-ASCII socket path works (measured: M1).**
  - The bound name must be the same file for three components:
    - Windows `AF_UNIX`, interpreting `sun_path`'s bytes;
    - the client's connect;
    - the host's stale-socket removal, through wide Win32 calls.
  - They agree. Windows reads `sun_path` as UTF-8, whatever the ANSI code page.
    - The test system used code page 1252. Directories were named in Latin (`Zoë`, inside that code
      page), Greek and CJK (both outside it).
    - Under each, the pinned server's bind, a client's connect, the peer check and removal through
      wide calls all addressed the intended file.
  - For `Zoë`, the same path's ANSI bytes did not bind. A client passes the path's UTF-8 bytes, never
    its ANSI bytes.
  - This replaces the earlier refusal of any socket path outside ASCII, which held until M1 passed.
- **Clients frame each response by its `Content-Length` and bound every read.**
  - During startup, the pinned server can leave a connection open after a complete response, even
    one sent with `Connection: close` **(measured: M1)**.
  - In two series of starts it happened on one connection in 8 of 8 starts, then in 2 of 4. Each
    time, the model had not yet loaded.
  - A client that reads until the server closes would wait without end.
  - Whether the Linux build does the same is not yet measured. The rule costs nothing there.
- **A named pipe is rejected:** `llama-server` cannot listen on one, so it would
  need a proxy process in every request's path.
- **A loopback port is rejected,** as in ADR-0011.

**The peer check (measured: M3).** On every connection, before any request byte:
1. The client reads the peer's process id with `WSAIoctl` and
   `SIO_AF_UNIX_GETPEERPID`.
2. It reads that process's creation time.
3. It compares both with the server instance it verified and canaried.

A mismatch sends it back to ADR-0011's attach step 2. Measured: on every
connection, to a probe server and to the pinned server, the peer's process id was
the server's. On 200 of 200 connections to the probe server, its creation time
matched too.

## Attaching and leases

**The steps and timings are ADR-0011's**, on byte-range locks:
- **A lease** is a shared lock on `clients.lock`, retried until 10 seconds.
- **The host's probe** is an exclusive `LOCKFILE_FAIL_IMMEDIATELY` attempt every
  2 seconds.
- **A slow lock release** by Windows after a client dies only delays stopping. It
  never stops a host while a live lease is held.

**Starting a host**, in place of `systemd-run --user`, runs a Task Scheduler
task on demand **(measured: M2)**.
- **The task.** Each application registers one per-user task for its own host
  entry point, named `LocalConnect Model Host (<application id>)`. The task:
  - is in the root task folder, for the current user, with an interactive token
    and least privilege. It stores no password and requests no elevation;
  - has no trigger. Only an attaching client runs it;
  - has no execution time limit, and may start and keep running on battery.
    Task Scheduler's defaults would stop the host after 72 hours, or when the
    machine goes on battery;
  - ignores a new start while one instance runs (`MultipleInstances`);
  - takes ADR-0011's arguments as `$(Arg0)` to `$(Arg5)`: the profile path and
    its SHA-256, a fresh `start_id`, and the store, registration and log
    directories as the client resolved them.
- **How it starts.** The client registers the task, replacing it when its
  definition differs. It then runs the task through the Task Scheduler API,
  with the arguments. A non-elevated process can do both.
- **Where the host runs.** In the job Task Scheduler creates for the task,
  outside every application's job. The server's kill-on-close job nests inside
  it.
- **Why a task.**
  - A host must outlive the application that started it, since other
    applications use its server.
  - Windows applications put their children in kill-on-close job objects.
    Invoice Processor's packaged sidecar is one example.
  - A process Task Scheduler starts runs in a job that forbids breakaway. A
    background provider started by ADR-0007's task therefore cannot start
    anything outside that job: `CREATE_BREAKAWAY_FROM_JOB` fails with
    `ERROR_ACCESS_DENIED`.
  - A task's job is its own. The host lived on in both cases:
    - when the starting window's job closed, even a job that forbids breakaway;
    - when the starting provider's task was stopped.
- **Election is unchanged.** Two applications' tasks can start two hosts.
  ADR-0011's lock on `host.lock` keeps one.
- **Stopping.** Ending the task ends the host, and the host's death ends the
  server through its job (measured with a probe server: within 1.1 seconds). A stopped task ends only
  its own process: a child that process started survives, still in the task's
  job.
- **Without the task, the shared runtime is unavailable.** Where the task cannot
  be registered or run, attaching reports it, as on Linux without a user service
  manager. One example is a policy that disables Task Scheduler. The host is
  never started as a child.
- **Removal.** Uninstalling an application removes its task.
- **No autostart.** The host is never started at login, since its task has no
  trigger. It ends when it exits, and its task returns to ready. ADR-0011's "No
  autostart" holds.

## Profile

Windows needs its own runtime sets, since the Linux archives cannot run there.
So the canonical profile is one file per platform:
- `runtime/v1/profile.json` stays the Linux x86-64 profile;
- `runtime/v1/profile.windows-x64.json` is the Windows x86-64 profile.

**How the two files relate:**
- Each file's `PROFILE_ID` is its own SHA-256. An application vendors the file
  for the platform it is built for.
- All applications on one machine run one platform, so ADR-0011's refusal
  between different profiles is unchanged.
- **The schema change.** The profile schema gains a required `platform` field,
  `linux-x64` or `windows-x64`. It lands in the profile PR, before either file
  exists.

**What each Windows tier holds:**
- **The same as Linux:** the model pin, the context, the chat-template pin, and
  the argv.
- **Different placeholders:**
  - `<model>` is the GGUF's absolute store path, pinned as above;
  - `<socket>` is the Windows path of `server.sock`.
- **Its own runtime-set pins.** Which builds those are is Invoice Processor
  MODEL-SETUP's decision, qualified on Windows under its MS-PIN-4. The pinned
  release publishes Windows x86-64 builds for CUDA 12.4 (with a separate CUDA
  runtime archive), CUDA 13.3, Vulkan and the CPU.
- **A self-contained runtime set.** A Windows runtime set holds every library its
  binaries import that Windows does not provide. The server's `PATH` is only the
  set's directory and `System32`.
  - The pinned builds import the Visual C++ runtime: `MSVCP140.dll`,
    `VCRUNTIME140.dll` and `VCRUNTIME140_1.dll`.
  - A fresh Windows 11 lacks them. The server then exits with `0xC0000135`, a
    DLL not found (measured: M1).
  - So each set carries Microsoft's signed copies from the Visual C++
    redistributable, pinned with the rest of the set.
  - Installing the redistributable system-wide is rejected. It needs
    elevation, which per-user installs do not have.

## Packaging

The shared store and registration need applications that see the same
`%LOCALAPPDATA%`.
- Per-user native installers keep it, such as the NSIS installer Invoice
  Processor's Windows release uses.
- MSIX and Store packages redirect a package's AppData writes. Packaged
  applications would therefore share neither the store nor the registration.
  Like Flatpak and Snap on Linux (ADR-0011), they need their own amendment.

## Measurements before a Windows release

**Where they run:** on Windows 10 22H2 and Windows 11, x86-64, with the pinned
release's Windows builds. Each result goes into the host's evidence, and a
failed measurement revises this decision before any Windows release.

- **M1, transport.**
  - `llama-server` listens on `--host <...>\model\v1\server.sock`, and answers
    `/health`, `/v1/models` and `/props` with the key.
  - Another local user cannot connect.
  - A 107-byte socket path works, and a 108-byte path refuses before the host
    starts, counted in UTF-8 bytes.
  - **Non-ASCII.** On profile paths holding characters outside ASCII, inside and outside the system
    ANSI code page (one Latin name such as `Zoë`, and one CJK name), each of these addresses the same
    file:
    - bind;
    - the client's connect;
    - M3's peer check;
    - stale-socket removal.

    It passed (see "Transport"), so the non-ASCII refusal it guarded was lifted.
  - A client that frames responses by `Content-Length` is never held by a connection the server
    leaves open.
- **M2, start.** A host started through its task survives its starter, in two
  cases:
  - **from a window:** from a window's attach child inside a kill-on-close job,
    whether or not that job allows breakaway, when that job closes;
  - **from a background provider:** from a provider started by ADR-0007's Task
    Scheduler task, when that task stops.
- **M3, peer.** `SIO_AF_UNIX_GETPEERPID` returns the server's process id on a
  client's connection.
- **M4, pinning.**
  - **The store's sharing probe** passes on NTFS. Where a volume that does not enforce sharing modes is
    available, such as a mapped network drive, it refuses there with `STORE_UNSUPPORTED`.
  - **Admitted:** with the host's handles held, the server loads the model and
    serves.
  - **Refused with a sharing violation, while the server keeps serving:**
    - a write-open, a rename and a delete of the GGUF;
    - a rename of `models\`;
    - a write to a runtime-set DLL.
- **M5, parent death.** Killing the host with `TerminateProcess` ends the server
  at once, and frees its graphics memory.
- **M6, lock release.** A killed client's shared lease is released within one
  probe interval (2 seconds) on an idle machine. The delay under load is
  recorded.

**Results so far: Windows 11, 2026-10-01.** Run on Windows 11 Enterprise LTSC
24H2 (build 26100.1742, ANSI code page 1252, NTFS), in a virtual machine with no
GPU. The runtime was the pinned release's Windows CPU build (b10621), with the
Visual C++ runtime in its set, and the model was MODEL-SETUP's CPU-tier model.

| | Result |
|---|---|
| M1 | Passed. With the key, the server answered `/health`, `/v1/models` and `/props`; without it, `/v1/models` returned 401. Another local user's connect failed with `WSAEACCES`, while that user reached a socket in a directory it may use. 107 bytes worked; 108 bytes also worked, so only the host refuses it. The non-ASCII cases passed, under directories with those names inside one profile. |
| M2 | Failed as first decided: breakaway from ADR-0007's task is refused. Breakaway from a window worked, since the desktop shell starts processes in a job that allows it. The revised start passed both cases. |
| M3 | Passed on every connection. |
| M4 | Passed on NTFS. Every refused change failed with a sharing violation, and the server kept serving. Not run: a volume that does not enforce sharing modes. |
| M5 | Passed. The pinned server ended 265 to 327 ms after its host was killed, 8 of 8 times. With a probe server, it also passed with the host running in its task. Not run: graphics memory, since there is no GPU. |
| M6 | Passed. A lease was released within 7 ms idle (200 kills), and within 115 ms under CPU and disk load (100 kills). |

Still owed before a Windows release:
- all six on Windows 10 22H2;
- M4 on a volume that does not enforce sharing modes;
- M5's graphics memory, on a machine with a GPU;
- the CUDA and Vulkan tiers' qualification.

## Conformance and landing gates on Windows

**ADR-0011's demonstrations 1 to 9 apply on Windows,** with these changes:
- "A write-open of the served GGUF ends the server" becomes "is refused while the
  server keeps serving" (M4).
- "A store on a filesystem without leases" becomes "a volume that cannot pin
  files".

**ADR-0011's demonstrations 10 and 11 become:**
- **10, environment.** The server's environment block holds exactly
  `SystemRoot`, `TEMP`, `TMP`, `CUDA_DEVICE_ORDER` and the host-built `PATH`. A
  client started with `LLAMA_ARG_HF_REPO`, `LLAMA_ARG_MODEL_URL` or
  `LLAMA_ARG_MODEL` set gets a server that has none of them.
- **11, start.** The host runs in its task's job, outside every application's
  job object. Where the task cannot be registered or run, attaching reports the
  runtime unavailable, and never starts the host as a child.

**Landing order:**
1. this ADR;
2. the profile schema's `platform` field, then `runtime/v1/profile.windows-x64.json`
   once its tiers qualify on Windows;
3. the host's Windows port, in `local-connect-model-host`, with M1 to M6;
4. attaching on Windows, one application per PR;
5. the Windows bundle installer.

## Rejected alternatives

- **A named pipe.** `llama-server` cannot listen on one, so a proxy process would
  sit in every request's path. That adds a component to fail, and moves identity
  from the server to the proxy.
- **A loopback TCP port.** Rejected for ADR-0011's reasons: any local user can
  connect, and another process can bind it first.
- **A machine-wide store under ProgramData, or a Windows service.** Rejected for
  ADR-0005's reasons: it mixes users, and it needs elevation and a broker.
- **Starting the host with `CREATE_BREAKAWAY_FROM_JOB`.** Rejected after M2. A
  process that ADR-0007's task starts cannot break away, so a background
  provider could never start a host. A window can, but a second way to start
  would be a second path to test, and the task covers both.
- **A Task Scheduler task with a logon trigger.** Rejected for ADR-0011's "no
  autostart" reason: it would hold graphics memory while nothing needs the model.
- **Copying the runtime set into sealed copies for each start.** Rejected because
  the held handles give the same guarantee, that only verified bytes run,
  without copying the whole runtime set for each start.
- **One profile file for both platforms.** Rejected because every Windows-only
  pin change would give the Linux applications a new profile id, and force them
  to re-vendor, and the reverse.

## Consequences

- **The same model on both platforms.** Windows uses the same store layout,
  attach protocol and lease timings as Linux, and the same model and prompts.
  Only the mechanisms underneath differ.
- **Refused instead of ended.** A served file cannot be modified while the server
  runs on Windows; on Linux the same attempt ends the server.
- **A task per application:** each application registers a per-user task for
  its host, with no trigger, and removes it when uninstalled.
- **A larger Windows runtime set:** each carries the Visual C++ runtime DLLs.
- **Two profile files to maintain,** each qualified on its own platform.
- **No Windows bundle release until M1 to M6 pass,** on Windows 10 22H2 as
  well as Windows 11.
