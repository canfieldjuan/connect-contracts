# Shared runtime companion evidence interface

Status: PROPOSED; documentation only. Owner: connect-runtime.
Juan authorized preparing this contract, not implementing it. Runtime choice,
[issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88) and live
budgets remain OPEN. No implementation, builds, model calls, Ollama or production
changes are authorized by this document.

This specifies the delivery interface deferred by the accepted
[host capture contract](PR-Shared-Runtime-Host-Capture.md#proposed-delivery-companion-publication-beside-registration).
It preserves [ADR-0015](../adr/0015-runtime-accuracy-qualification-identity.md)
and the [U1b delivery order](PR-Shared-Runtime-U1b-Consumer-Approval.md#required-change-surface-and-sequence).
It does not supply the selected-engine source-binding annex or the separate
qualification permit/issuer design. Exact-revision acceptance is required before
these proposed interface choices become the implementation contract.

## Root cause and inventory before porting

PR92 defines qualification evidence; PR93 defines its capture/delivery boundaries.
Neither fixes the companion's wire identity, bounded storage or callable interface.
Implementing against unspecified bytes would let host, client and application
independently define what the same snapshot means.

CONFIRMED source inventory: contracts base
`88d4fcd3d276da6993e08564c4ef6dec10185ada`; host main
`bc8f46168cde990a9601fd6f0df61e0509c7d6ec`. Host references below are its pinned
Git objects, not the older branch checked out locally or installed-app claims.

| Owner | Reuse and limitation |
| --- | --- |
| [Canonical qualification schema](../schemas/runtime/v1/qualification.schema.json), [fixture inventory](../fixtures/runtime/v1/qualification/README.md), [`inspect_record`](../tests/runtime_qualification.py) | Typed observation alternatives, backend variants and raw-byte/profile/instance comparisons. The offline helper neither authenticates sources nor admits a production profile. |
| [Client `Registration::read`, `Name`, `Server`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/attach.rs#L46) | Retained directory/lease, closed filenames, bounded reads and closed registration shape. The existing record limit is 16 KiB; companion limits below are new proposals, not an inherited runtime policy. |
| [Client `VerifiedSession`, `instance_live`, `verify_peer`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/transport.rs) | Independent peer/process checks. Verification can make `/v1/models`/`/props` identity requests; the proposed evidence read must not implicitly call `reverify` or make HTTP requests. |
| [Canonical file primitives](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-primitives/src/files.rs) and [host `Records::write`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L79) | Descriptor-relative no-follow reads, budget callbacks and private temporary-file replacement. Current primitives are Linux-only. Atomic rename is not proof of complete crash durability or Windows behavior. |
| [Client canary admission](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/canary.rs) | Separate private approval/ReadyClient ownership; evidence must not become an approval constructor. |
| [ADR-0012 registration prerequisites](../adr/0012-shared-local-model-runtime-windows.md#registration-and-trust) | Windows uses PID plus FILETIME creation time, without a fabricated boot id. Platform-aware registration/failure schemas and readers remain a separate prerequisite; this evidence format does not migrate them. |

Reuse PR93's [validated-work inventory and differences](PR-Shared-Runtime-Host-Capture.md#root-cause-and-current-source-inventory)
and the complete [U1b inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port):
the existing Qwen3.5-9B-Q4_K_M profile/runtime/model/template pins, original and
qualified framing, exact prompts/request bytes, sampling/settings/output budgets,
source bindings and recorded wire/task results. Reuse the 301-file receipt,
issue-73 and pre-production corpus manifests; do not rebuild them. These are
historical input identities, not selection of the next engine or new measurements.
PR92 synthetic profiles remain comparison surfaces, not executable profiles.
Its pinned-dependency replay caveat remains open.

UNKNOWN: the chosen engine's reporting fields and conversions, real observation
coverage, installed identity, native Windows delivery proof and any future task
score. No new fixture, schema, source file or public asset is added by this PR.

## Required change surface and single ownership

This PR adds only this document. Proposed implementation ownership is:

- **connect-contracts** owns proposed `schemas/runtime/v1/companion.schema.json`,
  `instance.schema.json` and `host-snapshot.schema.json` alongside qualification
  schema v1. These future schemas reference the
  existing observation definitions, not copied lexical rules. Companion version
  1 is distinct from qualification `record_version` 1 and registration protocol 1.
- **`local-connect-model-client::evidence`** is the proposed sole production
  semantic-validation owner, in the canonical shared-client repository. Its pure
  `validate_bundle` and `validate_record_binding` entry points below own cross-object
  comparisons. Host and qualification consumers call this owner; no host-only or
  app-specific copy. Closed wire parsing enforces canonical schema constraints;
  the later implementation must prove schema conformance and any language port
  against `tests.runtime_qualification.inspect_record` and its existing fixtures.
  The Python helper stays an offline oracle, not production admission.
- **Private host `capture` module** owns authorized observation collection, safe
  source adapters, interval attestations and publication. It consumes the shared
  validator; it does not export GPU probes, source parsers or host lifecycle code.
- **Shared-client evidence reader** owns directory/lease/process association and
  bounded file acquisition. **Existing qualification harnesses** own app route,
  exact request references, request/workload facts, scoring and human review.

These names define the future interface owner, not present symbols. The source
annex must implement reviewed conversions at their source parser. No dependency
or schema evaluator is installed or selected here: any needed dependency or
validator-language port must be justified and pinned in its implementation PR,
with no parallel regex checks for schema-expressible constraints.

## File layout and identity primitives

Under the already admitted registration directory, reserve the literal directory
`evidence-v1` with `current.json` and the literal subdirectory `objects`.
Temporary leaves are `.manifest-<UUID-v4>.tmp` at the evidence root and
`.object-<UUID-v4>.tmp` under `objects`, using canonical lowercase UUID text.
Only these reserved names, `current.json`, `objects` and digest leaves are allowed;
recognized orphan temporary files count toward quota and are not auto-deleted.
`server.json`, `failure.json`, `server.key`, their readers and their protocol stay
unchanged. No HTTP endpoint, watcher, daemon or automatic capture is added.

Each immutable object's leaf is its lowercase SHA-256, exactly 64 hex digits,
with no extension. A caller never supplies a pathname. The file opener derives
the leaf only after validating the digest through the canonical schema/type.
`ObjectRef` is a closed object with exactly `sha256` and `bytes`; `bytes` is an
integer from 1 through the applicable object cap. A file is addressed relative
to the retained `objects` directory handle. Aliases never resolve paths or URLs.

All metadata is UTF-8 JSON, without BOM, duplicate members at any depth, NaN or
Infinity, trailing data or unknown fields. Length is measured in original bytes,
not parsed/re-encoded text. Reject excessive nesting before unbounded allocation.
Hashes always cover the complete original object bytes. Only the instance artifact
has a unique canonical serialization (below); do not canonicalize request bytes,
raw reports, profiles or general metadata to calculate their hashes.

`Digest` and observation `Alias` reuse qualification schema definitions. `U64Text`
is a decimal ASCII string, `0` or a nonzero digit followed by digits, no leading
zeros/sign/whitespace/exponent, at most 20 characters, parsed as an unsigned
64-bit value. Its lexical shape belongs in schema; overflow comparison belongs
in the named validator. It preserves OS counters without JSON floating-point loss.
`Seq` is an integer from 1 through 9007199254740991. Exhaustion is an explicit
error, never wraparound. Version fields below are integer constants equal to 1.

## Exact instance artifact and hash

The instance artifact has these required members, in this serialization order:

| Member | Type / binding |
| --- | --- |
| `instance_version` | Constant 1 |
| `platform` | `linux-x64` or `windows-x64` |
| `start_id` | Canonical lowercase UUID v4 from admitted registration |
| `registration_sha256` | Digest of the exact admitted **ready** registration bytes |
| `profile_id` | Digest of exact independently admitted profile bytes |
| `tier`, `backend` | Canonical matched `gpu-cuda`/`cuda` or `gpu-vulkan`/`vulkan` pair |
| `runtime_archive_sha256`, `model_sha256` | Selected admitted profile/artifact digests |
| `build_commit` | 40 lowercase hex digits from admitted build provenance |
| `chat_template_sha256` | Admitted template digest |
| `host`, `server` | Closed platform-specific process objects below |

Linux process objects contain, in order, `pid`, `start_ticks`, `boot_id`.
`pid` is U64Text in 1..4194304, matching the current Linux registration reader;
`start_ticks` is U64Text equal to the OS start counter used by the admitted
identity; `boot_id` is the lowercase hyphenated OS boot UUID. Both process
identities must be independently live on that boot. Ticks are an opaque identity
counter, never converted to time or compared across clock frequencies.

Windows process objects contain, in order, `pid`, `creation_filetime`.
`pid` is U64Text in 1..4294967295; `creation_filetime` is positive U64Text in
100-nanosecond FILETIME units, checked against the retained process handle under
ADR-0012. `boot_id` and Linux tick fields are forbidden. This encoding does not
authorize a parallel relaxed registration reader; Windows capture remains blocked
until its canonical registration/profile migration and native proof land.

Canonical instance bytes use the member order above, ASCII strings with no
escapes (the closed alphabets require none), literal `1` for the version, no
spaces and exactly one LF after the final `}`. Nested objects use the specified
order. `instance_id = SHA256(canonical instance bytes)`. Reject alternative
whitespace, member order, escaping, missing LF or duplicate members for this
artifact, even if ordinary JSON would be equivalent. Construct expected instance
bytes from the independently admitted profile, ready registration and verified
host/server association, never from the candidate instance object itself.
Including the registration digest makes any registration replacement ineligible
until reattached/rebound; a stable PID alone is insufficient.

## Exact publication and host-snapshot shapes

`current.json` is a closed manifest with all these required members:

| Member | Type / rule |
| --- | --- |
| `companion_version` | Constant 1 |
| `sequence` | Seq, strictly increasing within an instance's publication history |
| `instance_id` | Digest; equals `instance.sha256` and independently expected instance id |
| `instance`, `snapshot`, `bindings` | ObjectRef each |
| `sources` | Array of 0..32 closed `{kind, alias, object}` entries; `kind` is `server` or `device`, `alias` is canonical Alias, `object` is ObjectRef |

Aliases are unique across `sources`. Multiple observations may cite one source;
distinct aliases may share a digest only when their retained bytes are identical.
`bindings` identifies the exact reviewed source-binding table bytes. The reader's
expected binding digest comes independently from the accepted capture plan, not
from this manifest. The table's engine-specific schema/mappings remain the source
annex's gate; it is an opaque, bounded artifact for file transport, not executable
configuration. No URL fetching, dynamic imports, commands or plugin loading.

The host-snapshot object is closed with exactly these required members:

| Member | Type / rule |
| --- | --- |
| `snapshot_version` | Constant 1 |
| `instance_id`, `binding_sha256` | Digests matching manifest/expected inputs |
| `sequence` | Seq equal to manifest sequence |
| `capture_window` | Closed `{clock, start, end}`; start/end are U64Text and start <= end |
| `device` | Canonical CUDA or Vulkan device observations selected by the instance backend |
| `effective_settings` | Canonical qualification settings object |
| `concurrency` | Canonical qualification concurrency object |

`capture_window.clock` is `linux-boottime-ns` for Linux (`CLOCK_BOOTTIME`, ns)
or `windows-uptime-ms` for Windows (`GetTickCount64`, ms). The closed platform
variant chooses the clock; do not compare timestamps across platforms/instances.
Linux converts `timespec` seconds/nanoseconds with checked arithmetic; Windows
retains the returned millisecond count. These are proposed OS-adapter mappings,
not observations from this PR. Clock units do not imply measurement resolution:
[Linux clock documentation](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)
and [GetTickCount64 documentation](https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-gettickcount64)
describe implementation-dependent/coarse resolution. These bounds are provenance,
not token-latency telemetry. The source-validity rule must reject ambiguous
ordering at the clock's resolution; equal ticks cannot prove overlap or order.

The host must set `effective_settings.prompt_cache_reuse` and
`concurrency.requests_overlap` to exactly
`{"state":"unavailable","reason":"not_collected"}`. Schema constrains these
host-only placeholders; they are not fabricated request/workload observations.
All other fields reuse the canonical observed/unavailable definitions. Observed
sources must have the correct server/device kind, the same instance/binding digest,
and a matching retained `sources` alias, kind and artifact digest. Every source
listed must support an observed field; safe failed-report evidence belongs in
the separate caller-owned failure receipt, not a fake observation. Unavailable
fields never carry hidden values or source objects. The two observed slot values
must agree. Zero and false remain valid wherever canonical field types allow them.

This object deliberately has no `application_route`, `intended` or `task_evidence`:
it is not a completed qualification record. Final record assembly copies identity
and host observations without altering their meaning; only the two placeholders
are supplied from the request/workload owners. App route, exact profile/request
references and task receipts come from those existing owners. Incomplete evidence,
task failures and pending human review stay distinct and retained.

## Bounded interfaces and error contract

The following are conceptual typed signatures for the named owners, not public
constructors added by this document:

| Entry | Inputs | Result / authority |
| --- | --- | --- |
| `evidence::validate_bundle` | Raw manifest/instance/snapshot/binding/source byte slices, independently supplied expected canonical instance bytes and ExpectedBinding, already admitted profile bytes | CheckedBundle or EvidenceError; pure consistency check, no I/O, source authentication, process access, model calls or approval |
| `evidence::read_current` | Borrowed existing verified attachment and its admitted directory/lease; ExpectedBinding; optional PreviousPublication; absolute deadline and cancellation | AttachedEvidence containing owned CheckedBundle and observation window, or EvidenceError; no HTTP, startup, reverify, generation or implicit retry |
| Private `capture::collect_and_publish` | Exclusive mutable borrow of the host's sole Publisher, independently verified instance, accepted source plan with trusted source adapters, and absolute deadline/cancellation | Collects only under separate capture authority; returns published manifest digest/sequence or CaptureError; invokes the same bundle validator before publication |
| `evidence::validate_record_binding` | Raw final qualification record, CheckedBundle, admitted profile bytes, exact request/workload artifact bindings and independently specified required observation interval/source-validity rules | Validated record plus missing-observation paths, or EvidenceError; consistency only, never source authentication, task PASS, permit, readiness or enrollment |

Pure validation does not authenticate its expectation inputs, just as PR92's
offline reader does not. It may inspect synthetic/historical inputs without
claiming a live association. `read_current` independently constructs expected
instance bytes from its admitted registration/profile and process association;
it never accepts those bytes or an expected instance digest from its caller.
Only that reader can construct AttachedEvidence; CheckedBundle cannot be cast
or promoted into it by an application. Host publication independently derives
its expectations from the elected host's own admitted profile and child identity.
ExpectedBinding is an equality expectation from the capture plan, not a capability
authorizing collection; it contains exactly `binding_sha256: Digest`. No new entry
to obtain a VerifiedSession is exported: the separate qualification-only permit
design remains required before that live path can be
reachable. Pure offline validation may use explicitly synthetic expectations.
`read_current` is crate-private until that separately accepted qualification
interface exposes its permitted caller; this proposal creates no public attach
or generation route. PreviousPublication is the closed triple `instance_id`,
`sequence`, `manifest_sha256` returned by an earlier successful read, not a bare
sequence number. A triple for another instance fails InstanceChanged.
AttachedEvidence is an observation-time association, not perpetual liveness. The
later qualification interface must keep its lease and verify current instance
again at each authorized use; pure record consistency cannot substitute for it.

`validate_record_binding` owns the existing offline oracle's cross-artifact rules
and adds: final identity/device/server observations equal the bundle's; source
references bind to retained artifacts; the host placeholders cannot be treated
as measured request/workload facts; and request/workload provenance is supplied
by its independent harness owner. Opaque task receipt references are retained,
not scored. The future production validator port must preserve valid incomplete
records and all existing PR92 failure cases; apps must not reimplement this owner.

The window records collection bounds, not automatic proof that settings were
constant throughout them. Per-value source rules must establish either validity
for the independently required interval or invariance for this instance lifetime.
Without that reviewed rule/evidence, return `ObservationScope` for a qualification
binding; raw historical bundle inspection remains possible. No TTL/default grace,
no inference from liveness alone, no widening intervals to make a run pass.
Selected-engine validity mappings cannot be fixed until runtime selection.
This check applies to asserted observed values. A canonical unavailable value
stays a valid incomplete observation and is returned in the missing-path list;
it is not converted into an interval error or a claim of complete qualification.

EvidenceError is a closed enum with distinct variants:

- `Unavailable` (no publication), `Cancelled`, `Deadline`;
- `Limit` (byte/depth/count cap), `Malformed` (JSON/schema/unknown version),
  `DuplicateMember`, `NonFiniteNumber`, `NonCanonicalInstance`;
- `UnsafeFile` (owner/type/link/path admission), `Integrity` (size/digest mismatch);
- `InstanceChanged`, `BindingMismatch`, `PublicationChanged`, `SequenceRegression`,
  `SequenceConflict`, `ObservationScope`, and `Io` (bounded OS error category).

Only an absent initial current pointer is Unavailable. A missing referenced object
is Integrity; a pointer missing on the final comparison is PublicationChanged.

CaptureError preserves those error meanings and adds `StorageFull`,
`CaptureBusy`, `SequenceExhausted` and `CommitUncertain`. No variant means both cancellation
and source absence. Error diagnostics contain static categories/field identifiers,
never raw inputs, secrets, document text or arbitrary paths. An individual safe
source read/conversion failure is recorded as canonical `source_error` where
allowed; bad identity/provenance fails the bundle and is never downgraded to
an unavailable observation. The caller retains the failed attempt and task
receipts. Neither error class changes current production hardware admission.

## File, parser and storage limits

These proposed constants bound evidence transport, not model context, concurrency,
GPU/RAM policy, request count, runtime startup time or live execution budgets.
KiB/MiB mean 1024/1048576 bytes. Inclusive maximums:

| Resource | Maximum | Reason |
| --- | --- | --- |
| Manifest / instance object | 16 KiB each | Small closed metadata; matches the existing reader's record-size scale, not its schema |
| Host snapshot | 64 KiB | Fixed observation field set and bounded source labels |
| Binding table | 256 KiB | Reviewed mapping metadata; oversize requires a separately reviewed format change |
| Individual raw source object | 256 KiB | Credential-free reporting surface only; no whole logs or prompts |
| Source entries / JSON nesting | 32 entries / 32 container levels | Finite manifest traversal and parser stack, root container is level 1 |
| Aggregate acquired bundle | 9 MiB | All referenced bytes, counted per reference before allocation, plus manifest; checked arithmetic |
| Final qualification record / admitted profile / app-binding metadata | 256 KiB each | Bounds the pure record-binding input; app-binding metadata carries independently checked hashes/aliases/intervals, never request bodies or document text |
| Entire `evidence-v1` directory | 64 MiB and 1024 regular-file entries | Includes objects, manifest and temporary files, across instances, not just current references |

All arrays are bounded by the enclosing byte cap as well as any canonical count
constraint; no recursive reference chasing. A zero/negative/wrong-type declared
size fails. Schema caps
and bounded reads must both enforce limits; read at most cap+1 to detect overrun,
compare pre/post file metadata and exact observed byte count, then hash the bytes
actually returned. Filesystem block slack is outside the byte accounting; caps
bound file contents/entry count, not a guaranteed allocation footprint. All byte
sums use checked arithmetic. Deadlines are required caller inputs, never defaulted
from zero/empty values; no numeric timeout is selected here.

The existing host election lease excludes competing host processes; it does not
serialize concurrent calls inside one elected host. That host owns exactly one
non-Clone Publisher, constructed once with its retained election ownership.
`collect_and_publish` requires its exclusive mutable borrow throughout capture
and commit. Any later concurrent entry returns CaptureBusy instead of queueing
unbounded work or constructing another Publisher. This evidence-only exclusion
does not alter application admission or inference slots. No second writer service
is introduced. Before admitting a new publication, account for final and
temporary bytes/entries and orphaned objects from prior interrupted attempts.
Quota exhaustion returns StorageFull, never evicts a referenced or historical
object. V1 performs no automatic object garbage collection, including across
restart. Cleanup/export is a separately authorized maintenance action, not
permission inferred from this cap. Disk pressure cannot trigger model unloading,
service restarts, deletion of evidence or changes to the application route.

## Publication, reading and restart rules

Linux uses the retained registration/directory descriptors, owner-only 0700
directories, and owner-only regular 0600 single-link files with no symlinks.
Windows uses owner-private DACLs, retained handles and no reparse traversal under
ADR-0012; POSIX mode checks are not a substitute. Other file kinds or unexpected
entries in the reserved directory fail closed for capture, not by deleting them.
Current Linux primitives do not establish Windows conformance.

1. Explicitly authorized capture obtains the existing host election ownership and
   admitted profile/ready-instance binding. Startup never triggers capture merely
   because this interface exists. A caller needs its separate live permission.
2. Before beginning a replacement capture, unlink only the mutable `current.json`
   pointer under the writer's retained directory. Missing is allowed. This prevents
   a failed new attempt from masquerading as the latest successful measurement.
   Immutable prior objects remain readable as historical evidence; readers already
   acquiring a publication must perform the final pointer comparison below.
3. The host assigns an increasing Seq for each attempt within that verified
   instance, including failed attempts; gaps are valid. If it loses this counter
   without a new verified instance, fail SequenceRegression rather than reuse it.
   Collect bounded safe reports only under the separate capture plan. Credentials,
   prompts and business documents must never enter these reporting inputs.
4. Validate the complete proposed bundle and independently recheck instance and
   registration. Write immutable objects to owner-private temporary files, flush
   them, and install each digest leaf without replacing existing content. Existing
   leaves are reused only after full size/hash/type checks. No in-place rewriting.
   The raw binding table/source objects are passive bytes, not executable inputs.
5. Publish a complete temporary manifest by a same-directory atomic replacement
   only after all objects are installed and verified. Recheck cancellation,
   deadline and instance immediately before this commit point. Before commit,
   failure leaves no current pointer; remove only this attempt's private temporary
   files. Already installed objects remain quota-counted historical/orphan evidence.
6. A reader pins the admitted directories, reads bounded current manifest bytes,
   opens every referenced object once relative to the retained directory, copies
   exact bounded bytes into its owned bundle and validates them. No borrowed path
   is reopened as authority. Then re-read the manifest and independent ready
   registration/process association. Changed/missing pointer means
   PublicationChanged; changed registration/instance means InstanceChanged.
   A lower Seq than the caller's previous accepted Seq is SequenceRegression;
   same Seq is valid only with the same manifest digest, otherwise SequenceConflict.
   No retry/poll loop.
7. Readers that succeed retain immutable owned bytes; later pointer changes do
   not mutate their run snapshot or make it current for a different interval.
   Snapshot completeness confers no permission to run. Historical inspection
   must be labelled historical and cannot satisfy a new live-instance check.
8. On shutdown/restart, unlink the mutable pointer under existing host ownership.
   A crash can leave a stale pointer: readers reject it through independent process
   and ready-registration verification. Retain immutable objects, failed attempt
   receipts and application quality results. Do not manufacture a new instance
   id by swapping one digest in old evidence.

Cancellation/drop owns and releases its file/lease work; no detached worker may
publish after the caller reports cancellation. A deadline/cancellation observed
after the atomic commit point does not retroactively roll back the pointer:
return the committed identity if known, otherwise CommitUncertain with the attempt
identity and reconcile by a bounded explicit read, not automatic recollection.
Retain the ambiguous result. This is publication outcome uncertainty, never
"generation delivery unknown" or an instruction to retry an inference request.

Flushes and atomic replacement do not claim power-loss durability on every OS.
After crash a reader may see prior bytes, new bytes or no eligible publication;
missing/torn/hash-invalid references are refused, never silently reconstructed.
Native crash/replacement proof must establish the actual supported filesystem
behavior before any stronger claim. Durable experiment receipts are copied to
the existing evidence owner outside worktrees; this runtime directory is not a
replacement for that retained evidence packet.

## Asset closure and compatibility

The proposed addition to the [U1 public client closure](PR-Shared-Runtime-U1.md#complete-allowed-public-source-and-asset-closure)
is limited to these owners and symbols:

| Public-package path | Allowed content |
| --- | --- |
| `crates/model-client/src/evidence.rs` | Closed wire types, ExpectedBinding/PreviousPublication, CheckedBundle and opaque AttachedEvidence, EvidenceError, `validate_bundle`, `validate_record_binding`, crate-private `read_current`; no source collector or approval constructor |
| Existing `crates/model-client/src/{lib,attach}.rs` | Module declaration and private adapter from already admitted registration/lease to evidence expectations; no new public attachment route |
| `crates/model-client/src/evidence_tests.rs` | Synthetic conformance, immutable-byte and fake-peer tests for this interface only |
| `crates/model-primitives/assets/{qualification,companion,instance,host-snapshot}.schema.json` | Exact canonical contract assets, complete local reference closure, origin commit/hash; no independently edited schema copy |
| Existing Cargo/provenance/source/release manifests and release-verifier inputs | Enumerate the above exact files, synthetic fixture leaves and pins; no hidden download, host checkout or new feature route |

No files are created by this proposal. Add the actual exact paths/bytes to the
release manifest and pin the release before host vendoring; never patch only the
vendored copy. Any further primitive/API/dependency expansion needs its own
declared justification and review. Schema references must resolve within the
complete pinned asset bundle, with no network schema resolution.

Host capture adapters, GPU/driver probes, process supervision, approved real
source-binding tables, actual observations, instance records, raw reports,
credentials and corpus/task receipts remain private. The public release uses
synthetic instances and source aliases only. No qualification permit, issuer,
production approval constructor or app business validator enters this extension.

The legacy registration path is unchanged when evidence is absent or invalid.
No capture reader repairs registration, changes ready state or falls back to
Ollama/gateway/TCP. Request/response-schema bytes never pass through metadata
serialization; retain the existing byte-level frozen replay guard against EW#317.
No changes to model, templates, thinking, sampling, contexts, slots, app validators
or task expectations are proposed. Windows remains in the first release with
native proof later on Juan's Windows box, not a VM; no Linux-only release implied.

## Differences and verification plan

New proposals relative to PR93 are exact filenames, closed wire member sets,
canonical instance serialization, native identity/clock representations, evidence
size/storage caps, typed entry points/errors, pointer invalidation and no automatic
GC, and the bounded public-client asset extension. These are delivery choices,
not measured engine behavior or a change to app requests. Profile intent and
engine reporting encodings are not substituted for observed values.

For this PR, inspect the one-document diff; check cited source symbols and links;
cross-check every observation with PR92; audit field/digest dependencies for
cycles and self-authentication; check bounds/units and lifecycle/error transitions;
run whitespace and no-unrelated-diff checks. No code tests, implementation,
fixture generation, builds, tokenizer or model calls.

Before later implementation sign-off, require offline evidence:

- Reuse PR92 valid/incomplete CUDA/Vulkan inputs and per-field negative controls;
  exact origin errors, not "any error". Schema-only probes must not be masked by
  later semantic validation. Compare the production validator to the offline
  oracle on the retained common cases before adding delivery-specific behavior.
- Canonical instance vectors for both platforms: exact bytes/hash repeated across
  independent encoders; wrong order/whitespace/escape/LF, duplicate/missing/mixed
  fields, integer-string bounds/overflow and PID/boot/creation-time mismatches.
  No real platform qualification is implied by synthetic Windows JSON.
- Each reference and provenance edge independently corrupted; repeated sources,
  unknown bindings, mismatched slots, valid unavailable/zero/false controls, source
  failures and forbidden host request/workload observations. Preserve failing and
  human-review-pending task receipts unchanged.
- Every byte/count/depth cap at min-1/min/max/max+1, mixed valid/invalid entries,
  0/empty/false/wrong types, checked sums and allocation bounds. Size-changing
  files, short/overreads, same-length tampering, hardlinks, symlinks/reparse points,
  wrong owner and ancestor replacement must fail at the file/identity owner.
- Fresh-process fake-peer tests: restart/PID reuse/registration replacement during
  each phase; two readers spanning pointer invalidation/replacement; cancellation,
  failure and crash before/after each commit boundary; orphan quota exhaustion,
  sequence gaps/exhaustion/regression and CommitUncertain retention; concurrent
  capture calls within one host cannot both publish or race quota accounting.
  No GPU/model.
- Source interval rules must reject a live-but-stale/mutable setting and admit
  the independently proved valid interval; no offered-concurrency inference.
- Exact native-wire request replay remains unchanged; legacy attachment without
  companion works; evidence-only APIs cannot obtain approval or generation access.
  Public package builds require only its pinned public closure. Native Windows
  file/process/publication proof remains a later, separately authorized step.

These are future tests, not tests run or authority granted by this document.

## Assumptions, blockers and gap audit

DONE: documentation preparation, exact interface proposal and source inventory.
NOT DONE: independent review/exact acceptance; executable schemas and semantic
validator port; selected-runtime source-binding annex (including per-value interval
validity); platform registration/profile migration; private capture and shared
reader implementation; trust/permit design; G0; native-platform proof; live capture,
task qualification and human review. No historical result closes those gates.

The implementation sequence is: accept this interface; separately select the
runtime and review its source mappings; implement and prove the authorized offline
schema/reader/capture slices with their own contracts and asset pins; deliver G0
under U1b; only then request the separately controlled live phases. Independent
offline schema preparation may be proposed earlier, but this acceptance does not
dispatch it. Issue #88 gates dependent policy/enrollment, not this evidence design.
Live time/count/compute budgets remain the later operator-owned phase decisions.
No implementation, builds, model calls, Ollama or production changes in this PR.
