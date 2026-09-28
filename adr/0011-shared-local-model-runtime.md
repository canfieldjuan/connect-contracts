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
  it (`F_SETLEASE`) for the server's life.
  - A write-open by any process breaks the lease, and the host then stops the
    server (fail closed).
- It starts the server from the spawning thread with `PR_SET_PDEATHSIG` and a
  `getppid` check, so the server dies with the host.
- It gives the server an allow-listed environment: `HOME`, `LANG` and
  `CUDA_DEVICE_ORDER=PCI_BUS_ID`, and nothing else. In particular there is no
  `LD_LIBRARY_PATH`, and no `LLAMA_*`, `GGML_*` or `CUDA_VISIBLE_DEVICES`.
- It writes a random bearer key to `server.key` (0600) and passes it by file,
  never on the command line.
- It passes exactly the profile tier's argv (see "Canonical profile"). The
  server therefore listens only on `server.sock`, opens no TCP port, and makes
  no network request (`--offline`).

**Tier choice.** The host chooses the tier from the profile's tiers:
- It reads NVIDIA devices through NVML, and other GPUs through the system
  Vulkan loader.
- It reads them in a child process, without elevated rights and without
  loading a model.
- It refuses to start a GPU tier whose device has less free memory than the
  tier's floor (`GPU_BUSY`).
- A machine that meets no tier gets `NO_TIER`, and the application tells the
  person plainly.

**Starting.** A stale `server.sock` is removed only while `host.lock` is held,
and only when a `connect()` to it fails. A server that is not answering
`/health` within 120 seconds is a failure.

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
  - the profile id and the chosen tier;
  - the host's process id, start time and boot id;
  - the server's process id and start time;
  - the socket path;
  - the model SHA-256, the context length, and the build commit.
- `failure.json` (0600): the host's last terminal failure. It carries a code,
  the profile id, the host's identity, the time, and at most the log's last 20
  lines (4 KiB). The codes are:
  - `PROFILE_INVALID`;
  - `RUNTIME_FILES_INVALID`;
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
Before sending any request byte, a client checks that the socket's peer
(`SO_PEERCRED`) is the server process recorded in `server.json`. So no process
can stand in for the server, and a client never reaches a server it has not
verified.

## Attaching

An application that needs the model MUST:

1. **Take a lease.** It opens `clients.lock` with `O_CLOEXEC`, takes a shared
   `flock`, and waits at most 10 seconds. It holds the lease for as long as it
   may send requests. A timeout is a retryable "not ready".
2. **Find a live host.** It reads `server.json`. If the file is absent, its
   host is not alive, or its state is `stopping`, the application starts the
   host (see "Starting a host"). It then waits at most 120 seconds for `ready`
   or a new `failure.json`.
3. **Match the profile.** It requires the registration's profile id to equal
   its own vendored `PROFILE_ID`. A different id is refused, in words that say
   another application on this computer runs a different version of the
   model, and that updating both fixes it. An application never stops or
   replaces a host that serves another profile.
4. **Verify identity over the socket,** with the key:
   - `/v1/models` lists exactly one model, whose alias is the pinned GGUF's
     SHA-256;
   - its `n_ctx` equals the profile's context;
   - `/props` names the pinned build.
5. **Run its own canary** once per server instance (the server's process id
   and start time), and record the result in its own data. Each application
   qualifies its own requests.

Requests then go over the socket with the key.

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

**Starting a host.** A client starts a host detached: in a new session, with
standard streams redirected, and inheriting no descriptor beyond them. It
starts at most one host per attach.

If a `failure.json` newer than the attempt appears, the client reports that
failure and does not start another host in the same attach. A background
process retries with a positive minimum delay and a finite attempt budget, as
ADR-0007 requires of its own restarts.

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
  2. it stops the server: `SIGTERM`, then `SIGKILL` after 5 seconds;
  3. it removes `server.json` and `server.sock`;
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
- A dead host takes its server with it through parent death.
- A stale registration is detected by liveness and replaced by the next host.

**No autostart.** There is no login autostart and no service unit. A host
exists only while some running application needs the model. Installation,
login and licensing never start it.

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
- the exact server argv.

**The argv.** It is the union of what the applications need. The GPU tiers
use:

```text
-c 32768 -np 1 -ngl 999 -fa on --jinja
--chat-template-kwargs {"enable_thinking":false} --reasoning off
--alias <GGUF sha256> --api-key-file <key> --offline --no-webui
--no-warmup --host <socket>
```

The CPU tier uses `-ngl 0 -t <physical cores>` in place of `-ngl 999 -fa on`.
The placeholders are the only values a host fills in.

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

## Rejected alternatives

**A server per application.** Rejected because it means two downloads and two
loaded models on one GPU, which cannot hold both.

**A service unit or login autostart.** Rejected because it keeps graphics
memory while no application needs it, and adds process-lifecycle consent that
ADR-0007 reserves for an explicit user choice.

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
   - Killing the host kills its server.
   - The next attach starts a fresh host.
   - A stale socket is removed only under `host.lock`, and a socket that
     answers is never removed.
5. **Profiles.** A mismatched profile is refused in both directions, and no
   client stops another profile's host. A profile file whose bytes do not
   match its id is refused.
6. **The store.**
   - A file placed by one application is used by another without a download.
   - Two applications fetching the same file at once download it once, and
     never interleave writes.
   - A file whose name does not match its bytes is refused.
   - A write-open of the served GGUF stops the server.
7. **Identity.**
   - A peer credential mismatch is refused before any request byte is sent.
   - A wrong alias, context or build is refused.
   - A socket path of 108 bytes or more refuses before the host starts, and
     one of 107 bytes works.
8. **Background work.** A background process with no window open takes a
   lease only while it has work, and the model leaves the GPU once every
   client is idle.
9. **No network.** Neither the host nor the server opens a TCP listener or
   makes a network request.

Windows has no gate until its amendment exists.
