# Runtime observation evidence: source and validity contract

Status: PROPOSED, documentation only. Owner: connect-runtime.
Juan authorized this source-grounded proposal after the PR102 schema increment.
This is not acceptance of a runtime/build, an executable rule set, or permission
to implement or collect evidence. Runtime choice, issue88 and live budgets remain
OPEN. Client/host changes, builds, tokenizer/model calls, production and Ollama
changes remain on hold. Windows remains in the first release; native proof runs
later on Juan's Windows box, not a VM.

## Root cause and required change surface

The remaining gap is evidence meaning, not JSON shape. A digest proves byte
identity; a collection window bounds collection. Neither proves that a reported
value describes the selected server throughout the independently required interval.
The [record-binding prerequisite](PR-Shared-Client-Record-Binding.md#assumptions-and-explicit-blockers)
therefore remains open after the executable app-binding/scope schemas land.

Change only this plan and a forward pointer in
[the format contract](PR-Shared-Client-App-Binding-Scope.md). Define the source
inventory, per-field proof obligations, rule-admission boundary and remaining
gates. No schema, parser, fixture, oracle, client, host, runtime or dependency
changes. This proposal is a reviewable requirements map, not a complete
selected-engine source annex. It registers no trusted rule ID or ruleset digest.

## Verified inventory before any port

CONFIRMED source pins: contracts `3ceef9751a2d12058f42b5906a6bf54bf9a513d6`,
host `bc8f46168cde990a9601fd6f0df61e0509c7d6ec`, client
`fe1a15742f7b676251b35fdca9e13fd817aa4415`. Host and client entries below were
read from these Git objects, not assumed from the active worktree. They are not
installed-product identities. No live endpoint or device was inspected.

| Owner at those pins | CONFIRMED behavior and limit |
| --- | --- |
| [Host `run_host`, registration and argv](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L478) | Records selected probe name and profile model/context/build/template, then expands launch arguments. These are intent/selection bindings, not runtime-effective observations. |
| [Host `health`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L312), [`run_host` readiness](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L560) | Checks socket peer UID/PID/start time and health status before publishing ready. This path publishes registration, not a companion qualification snapshot or interval proof. |
| [Host `Device`, `probe`, `nvml`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/gpu.rs#L9) | Probe joins backend names and platform facts by PCI identity. `nvml` at line168 obtains compute capability and `nvmlSystemGetCudaDriverVersion_v2`; `driver_cuda` is not the NVIDIA driver release string or proof of the CUDA runtime loaded by the server. The probe runs before server launch. |
| [Host `vulkan`](https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/gpu.rs#L233) | Uses PCI identity and memory-budget information, returning name/PCI/memory in `Device`. It does not retain the qualification API/driver fields. The requested Vulkan instance API version is not a measured device API version. |
| [Client `Props`, `Settings`, `verify_identity`](https://github.com/canfieldjuan/local-connect-model-client/blob/fe1a15742f7b676251b35fdca9e13fd817aa4415/crates/model-client/src/transport.rs#L305) | Compares model/context/build/template against the attached instance; `Settings` models only `n_ctx`. This proves neither per-slot interpretation nor absence of other reporting fields in the engine. |
| [Client `Attached::exchange`](https://github.com/canfieldjuan/local-connect-model-client/blob/fe1a15742f7b676251b35fdca9e13fd817aa4415/crates/model-client/src/transport.rs#L112) | Verifies the peer and passes caller bytes to `Full::new(body)` without JSON reserialization. No observation adapter may rewrite those request bytes or schema property order. |
| [Client `validate_bundle`](https://github.com/canfieldjuan/local-connect-model-client/blob/fe1a15742f7b676251b35fdca9e13fd817aa4415/crates/model-client/src/evidence.rs#L423) | Checks independent instance/binding expectations, raw references, source attribution and collection-window ordering. Binding bytes are checked by digest; their semantic rule membership and source-value extraction are not evaluated here. |
| [Canonical observations](../schemas/runtime/v1/qualification.schema.json), [scope shape](../schemas/runtime/v1/observation-scope.schema.json), [shape fixtures](../fixtures/runtime/v1/record-binding/README.md), [`inspect_record`](../tests/runtime_qualification.py) | Closed types, field paths and existing cross-artifact checks. Shape-valid semantic counterexamples remain intentional. No runtime rule is made trusted by passing these tests. |

Reuse the [U1b validated-work inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port)
and [host-capture inventory](PR-Shared-Runtime-Host-Capture.md#root-cause-and-current-source-inventory)
for exact prompts, request bytes, settings, validators, corpus manifests and prior
results. Do not reconstruct the 301-file binding receipt or issue-73 corpus.
The historical baseline identifies Qwen3.5-9B-Q4_K_M, model digest
`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`,
runtime commit `c1d0e7a004015f23bc0233470b747b596f29b264`, profile digest
`58bf361ec2d2a082931ffe19fb70dc9a22ffd8d7c10bc7837df137f843cd60d1`
and template digest `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715`.
Those are historical experiment pins, not this proposal's engine selection.
Build discovery patch digest is
`c04ecd7175942e00b7e4e4bca4aa466fd57505387521c64d65c3c7bea53a9fbb`;
a source commit alone cannot substitute for that complete build identity.

Read-only historical artifacts inspected for this proposal:

| Alias | SHA-256 | Use and limitation |
| --- | --- | --- |
| `phase0-manifest` | `e38402ce869f1283fcb361f8558e90ad55bf31dd29b86340c187b6d59110c744` | Existing accumulated baseline inventory; not a refreshed installation audit. |
| `phase0-baseline-source` | `05cd72137a6dfd2a6928a1ec637b60ba1a988ff8a2eeead7509af501d644fa04` | `Replay.submit`, lines240–338, retains request bytes and records offer/response/completion using `perf_counter_ns`. Admission timestamp is explicitly unavailable. This is client observation, not a server execution interval. |
| `phase0-fixture-inventory` | `81b010b22c4e85badfc35874f7addbe4feed1b873a27142da436d62052079783` | Existing fixture inventory retained; no rescoring or private content copied. |

Private paths and the complete alias resolution are in this slice's durable
review packet, outside worktrees. Historical samples are not rerun, reclassified
as authenticated observations, or counted as new proof here. INFERRED: these
owners can support later capture work. UNKNOWN: selected-engine mappings,
validity periods, clock association and full native Windows evidence.

## Per-field source obligations

Each path in the canonical scope enum appears below. Rows describe the proof a
later source annex must supply, not implemented collectors or accepted runtime
rules. Host sources remain `server`/`device`; app sources remain `request`/`workload`.

| Fields | Owner / required evidence | Current gap and rule requirement |
| --- | --- | --- |
| `effective_settings.context_per_slot` | Host / server | `Settings.n_ctx` comparison exists; selected engine must establish per-slot units and effective capacity. Do not divide total context by slots without source proof. |
| `effective_settings.slots`, `concurrency.slots` | Host / server | One effective slot-count observation must support both equal values. Launch `-np` is intent; capacity does not prove use or overlap. |
| `effective_settings.logical_batch`, `effective_settings.physical_micro_batch` | Host / server | Need effective configured caps, with exact source meanings. Caps are not actual physical batch shapes and do not establish batch-invariant arithmetic. |
| `effective_settings.context_checkpoints` | Host / server | Need effective checkpoint-setting semantics, units and supported range; do not infer saved/restored state from an enabled setting. |
| `effective_settings.flash_attention` | Host / server | Need resolved effective mode, including auto/fallback meaning. A launch flag or hardware capability is insufficient. |
| `effective_settings.kv_cache_type_k`, `effective_settings.kv_cache_type_v` | Host / server | Need actual effective cache formats; model weight quantization does not establish cache precision or recurrent-state format. |
| `effective_settings.offloaded_layers` | Host / server | Need actual offload outcome with exact layer-count semantics, not requested `-ngl` or generic GPU utilization. |
| `effective_settings.prompt_cache_reuse` | App harness / request | Bind original request occurrences and selected endpoint/default semantics. A cache policy is not evidence of a cache hit. Omitted fields, mixed policies and aggregate meaning require an explicit reviewed rule; no truthiness or majority fallback. |
| `concurrency.requests_overlap` | App harness / workload | Need correlated, same-instance runtime execution boundaries for distinct request occurrences. Client HTTP intervals/offer concurrency can include queue time and cannot alone establish simultaneous inference. Definition of execution stages and event source remains OPEN. |
| `device.name`, `device.compute_capability` | Host / device (compute capability CUDA only) | Probe has name/PCI/compute, but needs retained association to the device actually used by this server plus validity proof. Selection by name is not a unique physical-device proof. |
| `device.nvidia_driver_version`, `device.cuda_runtime_version` | Host / device, CUDA | Driver CUDA capability is not either value. Need NVIDIA release evidence and the runtime version associated with server-loaded libraries, with exact version decoding. Compiler/build toolkit version cannot fill them. |
| `device.physical_device_identity`, `device.api_version`, `device.driver_implementation`, `device.driver_version` | Host / device, Vulkan | Need server-selected physical device, API and implementation-specific driver evidence/decoding. Existing PCI probe can inform association, not establish all fields or portability to Windows. |

All rows remain unregistered until reviewed source/build-specific mappings exist.
No inference that a runtime feature is absent follows from the current client's
limited reporting types. Every applicable asserted value needs proof; no rule
may pass merely because another field or platform was validated.

## Admission of a later source rule

A later selected-build annex must provide, for each finite rule ID:

1. Exact runtime source commit, patch set, artifact/profile applicability and
   platform/backend; the canonical field, source kind, units and supported values.
2. Source symbol and reporting path, parser/closed type, lossless conversion,
   omission/error behavior, and retained credential-free raw artifact format.
   Caller-supplied selectors, code, URLs or expressions are not executable policy.
3. Independent source acquisition and instance association: process start identity,
   boot/time origin where applicable, selected device and artifact digests. A
   self-consistent caller-supplied manifest is not source authentication.
4. The value derivation plus either evidence of coverage of the required interval
   or a source-grounded lifetime-invariance argument. Identify all mutation/reset/
   reload paths that could invalidate it; a live PID or equal endpoint snapshots
   alone do not exclude an intervening change.
5. Original retained byte/alias attribution, occurrence indices and any aggregation
   rule. Bind every occurrence relevant to the claim; retries remain distinct.
6. Positive and negative offline proof vectors and the exact failure category,
   followed separately by native collection proof when authorized.

The trusted rule membership owner must be independently reviewed and pinned; the
candidate record cannot select a permissive ruleset. The existing ruleset digest
and ID syntax is a reference, not the registry. Host `binding_sha256` continues
to identify its reviewed source table; app `binding_sha256` continues to hash the
original app-bindings document. Neither silently becomes `ruleset_sha256`.
The eventual representation must specify their relationship and single canonical
owner before implementation. No policy DSL, plugin system, callback supplied by
an untrusted caller or duplicated host/client rule copies is introduced here.

## Time, concurrency and incomplete evidence

Reuse the [accepted scope semantics](PR-Shared-Client-App-Binding-Scope.md#proposed-observation-scope-object).
The harness fixes the required interval independently; the candidate cannot shrink
it to fit its sample. Preserve canonical integer timestamps and checked conversion;
do not turn historical floating duration measurements into exact clock evidence.
The historical harness's `perf_counter_ns` timestamps have no retained association
in `Replay.submit` to the contract's `linux-boottime-ns` clock. Relabeling them is
not a valid port. Windows uptime and process-creation identity also remain distinct;
matching clock labels are not proof of a shared origin.

For a later overlap rule, state the execution stage and granularity explicitly.
A positive claim needs a demonstrably nonzero overlap between attributed runtime
intervals, after accounting for clock resolution/uncertainty. Equal ticks are
insufficient. A negative claim requires complete coverage of the relevant offers
and outcomes; absence of a positive event in a partial log is not `false`.
Rejections, timeouts, cancellations and missing end events remain evidence, not
discarded samples or successful executions. No output-token timings may be inferred
from nonstreaming completion. This requirement does not choose an engine event API.

Existing failure meanings remain: invalid metadata/binding is not harmless absence.
For an asserted observed value, absent/unrecognized/inapplicable rule or inadequate
validity/clock evidence means `ObservationScope`. An honestly unavailable value
retains its missing path and needs no validity claim; malformed supplied metadata
still fails. Never downgrade a conflicting observed value to unavailable inside
validation to make it pass. Capture-time source absence/error uses the existing
unavailable alternatives when applicable. Source authentication/identity failures
invalidate capture rather than becoming benign source absence.

Task accuracy, byte-output parity, performance, human review, qualification permit
and production readiness stay separate. A correct observation report does not
establish any of those outcomes. Preserve all task receipts unchanged.

## Schema ownership and differences from prior work

Use schemas for every expressible shape constraint; parsed cross-artifact equality
and source-validity evaluation belong to their named semantic owner. Oversight's
PR102 follow-up identified that per-field uniqueness can use per-field `contains`
with `minContains: 0` and `maxContains: 1`. The accepted format currently assigns
duplicate-field refusal to `BindingMismatch`, and its fixtures deliberately pass
shape validation. Moving this constraint into schemas changes the accepted error
boundary and fixtures: a separate explicit amendment must reconcile that before
implementation. This proposal neither makes that amendment nor adds a parallel
regex/validator. Interval ordering and cross-document correspondence remain
semantic obligations.

Difference from validated work: this document adds a source/validity review map
and distinguishes historical client timing from future qualified execution timing.
It changes no prompts, framing, template, sampling, budgets, schemas, original
request bytes, response-schema order, scoring, runtime pins or task expectations.
The eventual private source adapters and shared rule semantics are new unproven
work; an accepted requirements map cannot count as their parity or qualification.

## Verification plan and cold diff audit

For this documentation slice: inspect pinned symbols, resolve local document links,
compare the field matrix with the existing scope enum, check the two-file diff and
whitespace, and retain inventory hashes and readthrough outside worktrees. No builds,
fixture replay, code tests or live calls are appropriate for Markdown-only edits.

Future authorized proof must cover valid complete and valid incomplete records;
zero/false; omitted/mixed request policies; repeated/retried occurrence attribution;
wrong platform/backend/build/device/instance; unsupported versions; boundary and
reversed/overflow intervals; clock-origin mismatch and equal/uncertain ticks;
setting changes between identical samples; rejected/cancelled offers; missing
events; and source bytes altered without changing the claimed value. Remove each
new source/coverage guard in isolated mutation controls. Reuse the corrected oracle
and frozen fixtures, with original-byte transport/property-order regression proof.
Synthetic evidence tests mechanics, never runtime authentication or task quality.

Cold diff audit scope: this new document supplies the inventory, field map and
gates above; the format contract receives only a forward pointer. Any executable
or fixture diff fails this slice's scope. Review and acceptance are separate from
later schema, client, host, capture and live-test authorization.

## Assumptions, blockers and gap audit

The proposed [llama.cpp c1d0e7a source annex](PR-Llama-C1d0e7a-Observation-Annex.md)
maps the nominated source for comparison only. It does not choose the runtime,
register trusted rules or authorize implementation or execution.

DONE for preparation only: source inventory, historical receipt reuse and explicit
per-field evidence obligations. NOT DONE for source-rule closure or implementation.
The next gates are:

- Operator runtime/build decision under issue88, or separate authorization to
  inspect a specifically nominated candidate as a comparison only. This proposal
  does not nominate an engine or choose budgets.
- Selected-source annex with exact field extraction, mutable-setting lifecycle,
  request-default/aggregation and execution-event meaning. No trusted rule IDs
  can be registered from this map alone.
- Reviewed passive evidence formats, clock/instance association and canonical rule
  membership/distribution ownership; explicit resolution of the uniqueness/error
  boundary before any implementation that touches it.
- Separate implementation authority and offline parity proof, then separately
  budgeted native capture/qualification on supported platforms. The full public
  record validator must not be replaced with a partial/all-rejecting stub.

Documentation review can proceed with these gaps visible. They are not approvals,
and this PR does not deliver G0, adopt a runtime or qualify concurrent inference.
