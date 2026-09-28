# ADR-0011: Shared local model runtime

**Status:** Proposed (accepted when this decision merges)

**Date:** 2026-09-27

## Context and scope

The three applications all read documents with one local model:
Qwen3.5-9B Q4_K_M on a GPU, and Qwen3.5-4B Q4_K_M on the CPU below the GPU
floor. They serve it with `llama-server` from llama.cpp at a pinned commit.
The operator chose that runtime on 2026-09-27 (invoice-processor#70): one
pinned runtime and model set, downloaded once; one owner of the running
server; and Document Summarizer's existing supervisor reused.

Today each application would carry its own copy. Document Summarizer has an
in-process supervisor (`src-tauri/src/pipeline/llama_cpp.rs`). Invoice
Processor's accepted setup contract (MODEL-SETUP revision 7) planned a second
one. Two copies mean two 5.6 GB downloads, and two servers competing for one
GPU. That GPU can hold one loaded model, not two.

This decision makes the runtime a per-user resource of the bundle:
- one content-addressed store;
- one model host per user, which runs the single server;
- a lease-based protocol by which any application attaches;
- one canonical profile that every application pins.

Invoice Processor's MODEL-SETUP revision 8, section 3, proposed it, and the
operator accepted that revision on 2026-09-27.

**Out of scope.** This decision does not change the Connect v1, v2 or v3 wire
protocols, discovery, entitlement, or ADR-0007's background-provider
lifecycle. The model host mediates no capability exchange and holds no
application state. The host program lives in its own repository,
`local-connect-model-host` (operator, 2026-09-27). This repository holds only
the protocol and the canonical profile.

This decision covers Linux x86-64. Windows needs the amendment described in
"Platform scope" before any Windows bundle release.

## Store

The store is one per-user directory:

```text
$XDG_DATA_HOME/local-connect/runtime/v1/
```

or, when `XDG_DATA_HOME` is unset, `$HOME/.local/share/local-connect/runtime/v1/`.
It must be owned by the current user, must not be a symlink, and must not grant
group or other permissions, as ADR-0003 requires of the licence file. It holds:

- `models/<sha256>.gguf`, one file per pinned model;
- `builds/<archive sha256>/`, one extracted runtime set per pinned archive,
  including NVIDIA's libraries where the tier needs them;
- `verified.json`, a record of each placed file: its path relative to the
  store, size, SHA-256, and file identity (device, inode, size, change time);
- `store.lock`.

**How a file enters.** Only a file named by a profile pin enters the store,
and only by verify-then-rename:
1. The downloader takes an exclusive lock on `.<name>.lock` in the
   destination directory, and holds it for the whole download. A second
   application downloading the same file waits for that lock, then uses the
   placed file. So no two writers ever share a `.part` file.
2. The file is downloaded to `.<name>.part` in its destination directory.
3. Its size and SHA-256 are checked against the pin.
4. The file is renamed into place while `store.lock` is held exclusively.
5. `verified.json` is replaced atomically, still under the lock.
6. The directory is synced.

Any bundle application may add a pinned file.

**How a runtime set enters.** A `builds/<archive sha256>/` directory enters
the same way, as one unit:
1. The archive's download lock is held throughout.
2. The archive is extracted into `builds/.<archive sha256>.<random>/`.
3. The result is checked against the pinned per-file manifest.
4. The directory and its files are synced.
5. The directory is renamed into place under `store.lock`, and its record is
   added to `verified.json`.

A temporary directory left by a crash is not a placed entry, and the next
extractor of that archive may remove it. A placed directory is therefore
always complete.

**What happens to a placed file.**
- It is never opened for writing again.
- Before using a file, a reader checks it against its `verified.json` identity,
  and re-hashes it when the identity differs.
- Nothing is deleted in v1. Store cleanup is a later bundle decision.

## One model host per user

The model host is the only program that starts `llama-server`. Any number of
copies may be installed, because each application ships one beside itself,
but only one runs per user.

**Election.** It holds an exclusive `flock` on `host.lock`, in the
registration directory, for its whole life. A host that cannot take the lock
exits 0 and changes nothing.

**Profile.** A host serves exactly one profile for its whole life:
- The application that starts it passes the path of its vendored profile and
  that file's SHA-256.
- The host refuses a file whose bytes do not hash to that value.

**How the host runs the server.** The host keeps Document Summarizer's
mechanics:
- It runs the server and its libraries only from sealed, read-only copies of
  files verified against the pins.
- It opens the GGUF without following links, and holds a kernel read lease on
  it (`F_SETLEASE`) until the server has exited. The server receives the model
  through that descriptor (the argv's `<model>`).
  - The lease-break signal is delivered to the server, whose default action
    ends it. So a write-open by any process ends the server (fail closed).
  - A store on a filesystem that grants no lease is refused with
    `STORE_UNSUPPORTED`.
- It starts the server from the spawning thread with `PR_SET_PDEATHSIG` set to
  `SIGKILL`, plus a `getppid` check. The server dies with the host at once, and
  cannot keep serving or holding graphics memory while exiting.
- It gives the server an allow-listed environment and nothing else:
  - `HOME`, `LANG` and `CUDA_DEVICE_ORDER=PCI_BUS_ID`;
  - exactly one `LD_LIBRARY_PATH`, which the host builds to point only at its
    private directory of sealed library copies, and never inherits.

  In particular it passes no `LLAMA_*`, `GGML_*` or `CUDA_VISIBLE_DEVICES`.
- It writes a random bearer key to `server.key` (0600) and passes it by file,
  never on the command line.
- It passes exactly the profile tier's argv (see "Canonical profile"),
  including the chosen device. The server therefore listens only on
  `server.sock`, opens no TCP port, and makes no network request (`--offline`).
- **A host runs exactly one server for its whole life.** Any server exit that
  is not part of the host's own shutdown is terminal:
  1. the host writes `failure.json` (`SERVER_FAILED`);
  2. it removes `server.json` and `server.sock`;
  3. it releases `host.lock`, and exits.

  The next attach then starts a fresh host.

**Tier choice.** The host chooses the tier from the profile's tiers:
- It reads NVIDIA devices through NVML, and other GPUs through the system
  Vulkan loader.
- It reads them in a child process, without elevated rights and without
  loading a model.
- It names exactly one device to the server. With several GPUs, the model is
  never split across devices whose memory floor was not checked.
- It refuses to start a GPU tier whose device has less free memory than the
  tier's floor (`GPU_BUSY`).
- A machine that meets no tier gets `NO_TIER`, and the application tells the
  person plainly.

**Starting.** A new host, holding `host.lock`, clears what an earlier host
left, in this order:
1. **An orphaned server.** A server recorded in `server.json` that is still
   alive (pid, start time and boot id) is killed. The new host waits, for at
   most 5 seconds, until it is gone. If it is still alive after that, the new
   host fails with `SERVER_FAILED` and never starts a second server beside it.
2. **A stale socket.** `server.sock` is removed only after that, and only when
   a `connect()` to it fails.

Then, before any file check or tier probe, the host writes `state: starting`
with a `ready_by` deadline at most 300 seconds away. That budget covers:
- its file checks, including a re-hash when a file's identity changed;
- the tier choice;
- the server's start.

The server must answer `/health` within 120 seconds of starting, and before
`ready_by`. Otherwise the start is `SERVER_FAILED`.

**Logging.** The host writes the server's output to:

```text
$XDG_STATE_HOME/local-connect/model/v1/server.log
```

The default is under `$HOME/.local/state`. The log is capped at 8 MiB and
truncated when the host starts.

**Downloads.** The host downloads nothing. Applications place pinned files in
the store with their own verified downloaders, before they start a host.

## Registration and trust

The registration directory is:

```text
$XDG_RUNTIME_DIR/local-connect/model/v1/
```

It must be mode 0700 and owned by the current user, following ADR-0001's
registration pattern. Without `XDG_RUNTIME_DIR` the shared runtime is
unavailable, and there is no fallback directory. The directory holds:

- `host.lock`: the host's election lock.
- `clients.lock`: the client leases.
- `server.sock`: the server's socket. The whole path must fit in the 108-byte
  `sun_path`, or the host refuses to start.
- `server.key` (0600): the bearer key.
- `server.json` (0600), written atomically by the host. It carries:
  - `protocol: 1`;
  - `state`: `starting`, `ready` or `stopping`;
  - the `start_id` the starting client passed, and the `ready_by` deadline;
  - the profile id, the chosen tier, and the chosen device;
  - the host's process id, start time and boot id;
  - the server's process id and start time;
  - the socket path;
  - the model SHA-256, the context length, the build commit, and the chat
    template's SHA-256.
- `failure.json` (0600): the host's last terminal failure. It carries:
  - a code;
  - the `start_id` it was started with;
  - the profile id;
  - the host's identity;
  - the time;
  - at most the log's last 20 lines (4 KiB).

  The codes are:
  - `PROFILE_INVALID`;
  - `RUNTIME_FILES_INVALID`;
  - `STORE_UNSUPPORTED`;
  - `NO_TIER`;
  - `GPU_BUSY`;
  - `SERVER_FAILED`.

**Liveness.** A process is alive when all of the following hold:
- the boot id is the recorded one;
- `/proc/<pid>/stat` exists;
- its state is not `Z`;
- its start time, field 22 counted after the last `)`, equals the recorded one.

**Trust.** Same-user processes are trusted, as in ADR-0001, and the key is
possession evidence only. Only processes of the same user can reach the socket.

**The peer check.** On every connection, before sending any request byte, a
client checks that the socket's peer (`SO_PEERCRED`, with the peer's start
time, or `SO_PEERPIDFD` where available) is the **server instance that client
verified and canaried**. It is never simply whatever `server.json` names now.
A mismatch sends the client back to attach step 2. So a client never sends a
request to a replacement server it has not verified, even one another
application started under another profile.

This defends against stale and replaced servers. Like ADR-0001, it does not
defend against a hostile process running as the same user, which can rewrite
these files.

## Attaching

An application that needs the model MUST:

1. **Take a lease.** It opens `clients.lock` with `O_CLOEXEC`, takes a shared
   `flock`, and waits at most 10 seconds. It holds the lease for as long as it
   may send requests. A timeout is a retryable "not ready".
2. **Find a live host.** It reads `server.json`. If the file is absent, its
   host is not alive, or its state is `stopping`, the application starts a
   host (see "Starting a host").
   - **What counts as ready:** a `ready` record whose host **and** server are
     both alive. Any other record is stale.
   - **How long it waits:**
     - at most 15 seconds for a `starting` record from a live host;
     - then until that record's `ready_by`, plus 10 seconds.
   - **It stops waiting at once when:**
     - the host it is waiting on is no longer alive;
     - or a `failure.json` names its own `start_id`, or that host's identity.

     It then reports the recorded failure, or "the model host exited without
     a record".
3. **Match the profile.** It requires the registration's profile id to equal
   its own vendored `PROFILE_ID`. A different id is refused, in words that say
   another application on this computer runs a different version of the
   model, and that updating both fixes it. An application never stops or
   replaces a host that serves another profile.
4. **Verify identity over the socket,** with the key and the peer check:
   - `/v1/models` lists exactly one model, whose alias is the pinned GGUF's
     SHA-256;
   - its `n_ctx` equals the profile's context;
   - `/props` names the pinned build, and its chat template hashes to the
     profile's pin.

   The model path is not compared: the server receives the model through a
   descriptor.
5. **Run its own canary** once per server instance (the server's process id
   and start time). The application records the result in its own data. Each
   application qualifies its own requests.

Requests then go over the socket with the key, and every connection passes
the peer check against that verified instance.

**One slot.** The server has one slot, so requests from different applications
queue in it. Each application bounds its wait with its own request timeout,
and a timeout while another application's request holds the slot is a
retryable runtime error.

**Who takes a lease:**
- a desktop window, through a child process bound to it by parent death;
- a foreground command;
- an ADR-0007 background provider, or an ADR-0006 unattended consumer.

The last two hold a lease only while they have work that needs the model. They
take it when such a job starts and release it when their queue is empty, so an
idle background process never keeps the model on the GPU.

**Starting a host.** A client starts the host as a transient service of the
user's service manager (`systemd-run --user --collect`). It passes:
- the path of its vendored profile, and that file's SHA-256;
- a fresh random `start_id`;
- the store, registration and log directories, as the client resolved them.
  The host never re-derives them from the service manager's environment,
  which may not carry the session's `XDG_*` variables.

What the transient service guarantees:
- **Why a transient service.** ADR-0007 stops a provider unit by ending its
  whole process tree, so a host started as the provider's child would die with
  it. A transient service belongs to no application's process tree or control
  group.
- **It is not an installed unit.** A transient service is never enabled, is
  never started at login, and disappears when the host exits.
- **Without a reachable user service manager,** the shared runtime is
  unavailable. It never falls back to a child of the application.
- **Descriptors.** The host inherits no descriptor beyond its standard
  streams.

A client starts at most one host per attach. A failure recorded under its
`start_id` is reported, and the client does not start another host in the same
attach. A background process retries with a positive minimum delay and a
finite attempt budget, as ADR-0007 requires of its own restarts.

## Lifetime and leases

**The host runs while any client lease is held,** and begins stopping 10 to 12
seconds after the last lease a probe observed has ended. It never holds a
shared lease itself, and never inherits one.

**Probing.** Every 2 seconds the host tries `clients.lock` exclusively, without
waiting.
- When the attempt succeeds, the host releases the lock at once, unless every
  probe of the last 10 seconds has also succeeded.
- On that last probe it keeps the lock, and it holds it through shutdown:
  1. it writes `state: stopping`;
  2. it stops the server: `SIGTERM`, then `SIGKILL` after 5 seconds, and waits
     until the server has exited;
  3. it releases the lease on the GGUF, and removes `server.json` and
     `server.sock`;
  4. it releases `host.lock` and then `clients.lock`, and exits.
- Shutdown completes within 8 seconds of taking the lock.
- **Why `host.lock` goes first.** A client is admitted only once
  `clients.lock` is released. By then `host.lock` is free, so the host that
  client starts can win the election. The other order would let that new host
  lose to the leaving one and exit 0, and the client would then wait for a
  registration that never comes.

**Why no application attaches to a leaving host.** A client that arrives
during shutdown waits on its shared lease (at most 10 seconds). When it gets
the lease it finds no live host, and starts a new one.

**Crashes leave nothing running.**
- The kernel releases a dead client's lease.
- A dead host takes its server with it through `SIGKILL` parent death.
- A server that dies ends its host (see "One model host per user").
- A stale registration is detected by liveness, and the next host replaces it
  after clearing any orphan.

**No autostart.** There is no login autostart and no installed or enabled unit.
A host exists only while some running application needs the model.
Installation, login and licensing never start it.

## Canonical profile

**The file.** The profile is one data file in this repository:
`runtime/v1/profile.json`. The schema `schemas/runtime/v1/profile.schema.json`
validates it.

**What each tier holds:**
- the device class;
- the model pin: file name, size, SHA-256, and a source URL at a fixed
  revision;
- the runtime-set pins: archive name, size and SHA-256, the per-file manifest,
  and NVIDIA library archives where needed;
- the context length, 32768;
- the memory floors;
- the SHA-256 of the chat template;
- the exact server argv.

**The argv.** It is the union of what the applications need. The GPU tiers
use:

```text
-m <model> --device <device> -c 32768 -np 1 -ngl 999 -fa on --jinja
--chat-template-kwargs {"enable_thinking":false} --reasoning off
--alias <GGUF sha256> --api-key-file <key> --offline --no-webui
--no-warmup --host <socket>
```

The CPU tier uses `-ngl 0 -t <physical cores>` in place of
`--device <device> -ngl 999 -fa on`.

The placeholders are the only values a host fills in:
- `<model>`: the path of the leased descriptor;
- `<device>`: the one chosen device, as the pinned server's `--list-devices`
  names it;
- `<GGUF sha256>`, `<key>`, `<socket>` and `<physical cores>`.

**Vendoring.** Each application vendors the file's exact bytes, and its
`PROFILE_ID` is their SHA-256.
- An application never edits its copy.
- Any change to a pin or to the argv makes new bytes, and so a new id. Every
  application must ship the new file, or attaching refuses on the mismatch.
- Each application qualifies its own requests against exactly the argv in the
  profile it ships.

## Platform scope

This decision binds Linux x86-64. A Windows bundle release needs an amendment
to this ADR first. The amendment must decide:
- placement under ADR-0005's owner-private `%LOCALAPPDATA%\LocalConnect\`
  root, with ADR-0005's checks;
- election and leases on ADR-0005's byte-range locks;
- the transport, measured with the pinned `llama-server`. The candidates are
  `AF_UNIX` or a named pipe, and never a loopback port that other users can
  reach;
- the equivalent of the read lease, for example a no-write sharing mode on
  the GGUF.

macOS remains a later platform decision.

**Packaging.** This decision assumes native packages that share the user's
process and runtime namespaces, such as `.deb` and AppImage. Flatpak and Snap
sandboxes change process ids and the runtime directory. They would break
liveness, the peer check and the shared registration, so they need their own
amendment.

## Relationship to earlier decisions

**ADR-0001 and ADR-0007.** Both deferred "a broker", "launch on demand" and "a
third runtime". The model host is launched on demand, but it is not a Connect
broker:
- it registers no capability;
- it handles no job or artifact;
- it holds no application state;
- it exists only while a lease holds.

The Connect broker stays deferred.

**ADR-0007's consent rule is unchanged.** Only an application that is already
running with the user's consent starts the host: a window, or a background
provider the user enabled.

**ADR-0003 to ADR-0006.** The host checks no licence. Standalone use of each
application reads documents with the model whatever the entitlement state.

## Amendments to invoice-processor MODEL-SETUP revision 8

MODEL-SETUP adopts this ADR once it is accepted. Where the two differ, this
ADR governs, and MODEL-SETUP's next revision aligns to it:

- **Lifetime.** MS-SHARE-4 and section 7 say the server stops "at most 10 s
  after the last" lease. Here the host begins stopping 10 to 12 seconds after
  the last lease a probe observed, and the server is gone within 8 seconds
  after that. Revision 8's "keeps holding it when it gets the lock" would give
  no grace at all.
- **Identity (MS-LIVE-1):**
  - The canary record lives in each application's own data, not in the
    shared `server.json`.
  - The model path is not compared, because the model is passed by
    descriptor. Identity is the alias (the GGUF's SHA-256), `n_ctx`, the
    build, and the chat template's SHA-256.
- **Canary binding (MS-SHARE-3 step 5).** Revision 8 binds the canary to the
  host instance; here it is bound to the server instance. The two are
  equivalent, because a host runs exactly one server for its life.
- **The peer check (MS-RUN-4).** The check is against the verified instance,
  not against whatever `server.json` records now.
- **Extraction (MS-FETCH-6).** A failed extraction deletes its temporary
  directory. A placed `builds/` entry is never deleted.
- **Start and log.** The host starts as a transient user service, and logs to
  `$XDG_STATE_HOME`.

## Rejected alternatives

**A server per application.** Rejected because it means two downloads and two
loaded models on one GPU, which cannot hold both.

**An installed service unit or login autostart.** Rejected because it keeps
graphics memory while no application needs it, and adds process-lifecycle
consent that ADR-0007 reserves for an explicit user choice. The transient
service used to start the host is neither installed nor enabled, and ends with
the host.

**The host as a Connect provider.** Rejected because wrapping every inference
request in a Connect job would add job and artifact handling per request. The
applications need direct, qualified access to the server's API with their own
prompts.

**A loopback TCP port.** Rejected because any local user can connect to it,
another process can bind it first, and identity would rest on what answers.
A 0700 Unix socket plus a peer credential check rests identity on the
filesystem and the kernel.

**Ollama.** Rejected by the operator (invoice-processor#70). On the 33-invoice
reference set, llama-server matched 271 of 273 rows, where Ollama matched 267.
Ollama's built-in parser also drops the response schema when thinking is off.

**Starting the host as a child of the application.** Rejected because an
ADR-0007 provider unit's stop or restart kills its whole process tree. That
would take down the server every other application is using.

**Sharing whichever application's server started first.** Rejected because
closing that application's window would cut off every other application's
work.

**Hosting the program in an application's repository or in
`local-inference-gateway`.** Rejected by the operator (2026-09-27) in favour of
a new repository. In an application's repository, one application's releases
would carry every application's runtime. The gateway is a network appliance
with a different deployment and trust model.

## Consequences

- The bundle downloads the model once, and loads it on the GPU once.
- Applications that ship different profiles refuse each other plainly. The
  bundle installer ships one profile. A single-application update that changes
  the profile needs the other applications updated too.
- The store only grows in v1.
- Document Summarizer's in-process supervisor is replaced by attaching, after
  the extraction.
- Every application ships a copy of the host.

## Conformance and landing gates

**Landing order.**
1. This ADR.
2. `runtime/v1/profile.json`, with schemas for the profile, `server.json` and
   `failure.json`, fixtures, and offline checks, in this repository. These
   checks prove shape only.
3. The host, in `local-connect-model-host`, extracted from Document Summarizer
   after document-summarizer#71 merges, with its own contract and tests.
4. Attaching, one application per PR, Invoice Processor first.
5. The bundle installer.

**What the host and the applications must demonstrate:**

1. **One server.** Two applications attached at once share exactly one host,
   one server and one loaded model. Graphics memory is measured.
2. **Racing starts.** Several clients starting at once start one host, and the
   losing hosts exit 0.
3. **Lease timing.** The host begins stopping no sooner than 10 seconds, and
   no later than 12 seconds, after the last lease ends. The server is gone
   within 8 seconds after that.
   - A lease taken and released between two probes does not extend the life.
   - A client arriving during shutdown gets a new host, never the leaving one,
     and that host wins the election.
4. **Crashes.**
   - Killing a client releases its lease.
   - Killing the host kills its server at once.
   - Killing the server ends its host with `SERVER_FAILED`, and the next
     attach starts a fresh host, even while another client holds a lease.
   - A new host kills and waits out an orphaned server before removing the
     socket, and a socket that answers is never removed.
   - Stopping or restarting an ADR-0007 provider unit that started the host
     leaves the server running for a window that holds a lease.
5. **Profiles.** A mismatched profile is refused in both directions, and no
   client stops another profile's host. A profile file whose bytes do not
   match its id is refused.
6. **The store.**
   - A file placed by one application is used by another without a download.
   - Two applications fetching the same file at once download it once, and
     never interleave writes.
   - A crash mid-extraction leaves no partial `builds/` entry, and the next
     extraction succeeds.
   - A store on a filesystem without leases is refused with
     `STORE_UNSUPPORTED`.
   - A file whose name does not match its bytes is refused.
   - A write-open of the served GGUF ends the server, and the host with
     `SERVER_FAILED`.
7. **Identity.**
   - A peer credential mismatch is refused before any request byte is sent.
   - A client whose verified server was replaced by another application's
     host, even under another profile, re-attaches and never sends it a
     request.
   - A stale `ready` record left by a dead host is never accepted.
   - A wrong alias, context or build is refused.
   - A socket path of 108 bytes or more refuses before the host starts, and
     one of 107 bytes works.
8. **Background work.** A background process with no window open takes a
   lease only while it has work, and the model leaves the GPU once every
   client is idle.
9. **No network.** Neither the host nor the server opens a TCP listener or
   makes a network request.
10. **Start.** The host runs as a transient user service, outside every
    application's control group. Without a reachable user service manager,
    attaching reports the runtime unavailable, and never starts the host as
    a child.

Windows has no gate until its amendment exists.
