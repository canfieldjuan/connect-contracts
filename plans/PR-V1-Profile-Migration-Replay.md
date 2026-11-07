# V1 canonical-profile migration and offline replay preparation

## Authority and root cause

Status: PROPOSED, documentation only; owner: connect-runtime. Acceptance of this
contract is not authorization to implement, install dependencies, build, launch,
probe a device, tokenize, call a model, or change production or Ollama. Each later
executable slice needs separate operator authorization and exact-head review.
The selected V1 runtime remains llama.cpp
`c1d0e7a004015f23bc0233470b747b596f29b264`, Qwen3.5-9B-Q4_K_M, sequential
calls, one slot. [Issue 88](https://github.com/canfieldjuan/connect-contracts/issues/88)
remains open; experiment admission does not decide installed hardware policy.

The preparation packet is NOT RUNNABLE. This is not an admission bug:
`model-primitives::CanonicalProfile::load` accepts only the embedded profile ID
and exact bytes. The staged sequential suffix changes that identity. A second
accepted ID or an argv override would bypass the qualification boundary rather
than migrate it. Independently, the Invoice scorer environment is incomplete,
and the old replay runner binds a different resident/parallel configuration.
CLI intent is also not proof of effective settings or per-request cache policy.

This contract refines [PR107's plan](PR-V1-Sequential-Qualification.md): migration
on a reviewed development branch must precede qualification; installed adoption
remains after qualification and separate authorization. It does not treat
unqualified canonical bytes on that branch as already qualified or shipped.
Existing released artifacts, contracts canonical bytes and production stay intact
in this documentation PR. Windows remains first-release scope, with later native
proof on Juan's physical Windows machine; this Linux preparation is not that proof.

## Validated inventory and source owners

Reuse the [U1b inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port),
[observation inventory](PR-Shared-Runtime-Observation-Evidence.md), existing
301-file receipt, pre-production evaluation `20261004T175816Z-24660385746b`,
issue-73 manifest and retained seeded-corpus packet. Do not rebuild inventories,
relabel old runs or publish private documents. Evidence aliases below are durable
local receipts; hashes identify their exact contents, not a new execution.

| Receipt / owner | Confirmed evidence and limits |
| --- | --- |
| `linux3090-preparation`, REPORT SHA256 `9df156ffde836c15d46334f819e7bd819a62d08e2324cffc9e9948d96796869a` | 58 cases / 62 natural request bodies bound byte-for-byte; proposed 206 offers. Four fixed-work variants change only the output cap. Runtime presence is not a fresh binary/model integrity check or a live result. |
| `linux3090-readiness-delta`, ADDENDUM SHA256 `b48f37be27d7fe391e436b8783d314d334c94d340860253b26771bd6af473c21` | Archived Email imports pinned; 18/18 retained full score objects reproduced in separate network namespaces. This is scorer parity, not 18 new model-quality successes or proof the mutable environment stays frozen. Invoice environment/replay still blocked. |
| `linux3090-delta-review`, SHA256 `bacbba3a2c56bbfd1e11dfc351608195b91a3002f8f3d14c9fa3d368609a8b3b` | Independent acceptance of G1–G3 and retained Email comparisons; readiness evidence only. |
| [Staged candidate](../runtime/v1/candidates/sequential/profile.json) | SHA256 `a5abe4eec9434a128a2d63a5dcbc285b4b3113e71df5454c234ee681c11ad274`. Both Linux tiers preserve model, template, archive, per-file pins, context 32768 and one slot. Candidate suffix is the only profile difference. |
| [Current contracts profile](../runtime/v1/profile.json) | SHA256 `58bf361ec2d2a082931ffe19fb70dc9a22ffd8d7c10bc7837df137f843cd60d1`; no change in this PR. |
| Client canonical asset, `crates/model-primitives/assets/profile.json`; embedded by `crates/model-primitives/src/profile.rs:9` | Single native admission owner. Host consumes the pinned vendored distribution, never a separately edited policy copy. |
| Host source `bc8f46168cde990a9601fd6f0df61e0509c7d6ec`, [run_host:433][host-run], [probe_store:672][host-probe] | Both call the host wrapper and the same [primitives load:30–43][profile-load]. Normal and diagnostic paths enforce the same single identity. Source inspection does not map a future or installed binary to that source. |
| [Native transport exchange][transport] and its retained frozen-request wire regression | Caller body is passed without JSON reserialization. Preserve this owner and regression; schema field order must remain exactly as supplied by the app. No gateway schema sorting is inherited. |

The unchanged model SHA256 is
`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`,
template SHA256 `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715`,
and CUDA archive SHA256
`2d4988729ab0df576efdaa58be27c55b4de1eb574256049a0f2b6d5abe9bff10`.
Reuse the retained prompts, app temperatures, fixed per-request seeds, schemas
including property order, thinking framing, input bytes and natural output caps.
The saved Summary intermediate inputs prove input replay, not a new app-chain run.
Historical score failures, date-oracle caveats and human summary review remain visible.

## Required change surface and proposed landing order

This PR changes only this contract and its plan/README pointers. The following
are future separately authorized slices, not implementation bundled into acceptance.
Independent offline preparation may proceed without reopening runtime selection;
no dependent live step may bypass a failed identity or compatibility gate.

### A. Canonical migration contract execution

At the native client asset owner, replace the canonical profile with the exact
staged candidate bytes on a reviewed migration branch. Coordinate the contracts
canonical asset and ADR-0011 exact-argv declaration, client distribution identity,
consumer pins and host vendored distribution through reviewed PRs. Contracts is
the language-neutral authority; client primitives owns executable admission. These
are synchronized copies of one profile, not independently maintained alternatives.
Inventory every reader, embedded copy and pin before edits; include app attachment
mismatch behavior. Do not silently update installed apps or claim G0 delivered.

Preserve `CanonicalProfile::id/load` single-ID and byte-digest checks. No alternate
profile ID, second accepted profile, environment or CLI override, post-admission
argv mutation, qualification-only identity or test bypass. Cover both run_host
and probe_store delegation. Existing descriptor loader, model read lease, private
registration, authenticated socket, discovery isolation and library environment
ownership remain unchanged. Do not start the runtime directly to evade the host.

Future offline regression proof must accept the exact migrated bytes/ID and reject
old ID, wrong ID, changed bytes with expected ID, and matching attacker-selected
ID for noncanonical bytes, through the real owner and both host routes as
applicable. Verify the complete vendored distribution against its pinned source;
reuse existing identity and raw-wire tests rather than introducing parallel checks.
No such tests or host builds are run by this documentation change.

Qualify exact host/client/runtime/library/profile payloads from reviewed source
and ship those same hash-identical payloads. Capture build provenance, discovery
patch, dependency closure and every artifact digest. A common source commit alone
does not transfer evidence. A different release build requires hash equality or a
separately accepted reproducible-build equivalence proof; this contract supplies
no new equivalence mechanism. Delivery, publication, install and adoption are
separate gates. Retain the prior released artifacts as rollback; mismatched clients
must refuse attachment, not fall back to an unqualified identity.

### B. Scorer environment and retained-answer parity

Restore an isolated Invoice scorer environment from the archived dependency
specification under separate installation authorization; do not mutate installed
app environments or borrow a partial environment. Archived
`invoice-source/pyproject.toml:11` requires `pikepdf>=9,<10`; the old interpreter is
missing and the inspected replacement lacks it. Missing dependencies are not a
scorer failure and must not become skipped-success results.

Bind interpreter, package closure, actual imported source paths and file hashes.
Run retained answers through the unchanged real validators in fresh processes with
network isolation; compare full per-case scores and errors against retained
serial-2, covering Invoice/COI and issue-73 corpus cases from existing manifests.
Record every mismatch, including whether it changes an accuracy verdict. Do not
repair or loosen an oracle during this parity gate; a required oracle amendment
is separately reviewed and preserves both old and new verdicts.

The [proposed application-clock comparison amendment](PR-Retained-Scorer-Clock-Comparison.md)
defines an exact task/path exception for unscored clock metadata, a hash-bound
enclosing-attempt interval for one retained packet, and per-case intervals for
future replays. It preserves the strict verdict beside a separately checked
amended verdict. Until its exact revision is accepted and its separately
authorized implementation is verified, the strict gate here remains unchanged;
the retained receipt is evidence, not a completed gate.

Reuse the accepted Email proof and recheck import/environment identity before a
new replay; its archived source wins over the editable main tree. A changed
identity requires renewed retained-answer parity, not an existence check. Bind the
Summary scorer similarly through existing source pins and retained verdicts.
Scorer equivalence is independent of model correctness and human task quality.

### C. Sequential replay and effective capture preparation

Adapt the existing proven harness into a new durable packet; never rerun or edit
sealed historical packets. Bind occurrence IDs to input and response explicitly,
not completion order. Dispatch the next request only after the previous response
and cleanup, including app multi-call chains. No hidden retry, replacement sample,
fallback model, prompt rewrite or response reassignment. Retain offers, rejections,
timeouts, cancellations, errors and partial responses. Offline scripted transport
may prove dispatch bookkeeping, but must be labelled synthetic transport evidence.
It cannot prove native output, settings, timing, authentication or GPU behavior.

The natural lane keeps all 62 saved request bodies unchanged. Fixed-work copies
change only the already proposed output cap to 256; preserve their original-byte
bindings and field order. Realized token work and cache counts still determine
comparability. Frozen request bytes and real scorer logic are the regression guard.

`--no-cache-prompt` sets a default; [server-schema.cpp:528 and :31][request-cache]
allow per-request override. Intent/admission belongs to the app/native request-policy
owner; generic byte transport must not strip, sort or rewrite a request. All 62
natural bodies omit the field; prove effective false for each occurrence rather
than equating omission, null and true. The Doc Sum cache-true canary needs its own
owner-reviewed amendment and historical control before that dependent app lane.
No new production request rejection policy is selected here.

Bind capture to the existing [host-capture contract](PR-Shared-Runtime-Host-Capture.md),
[selected-source annex](PR-Llama-C1d0e7a-Observation-Annex.md) and
[evidence-association contract](PR-Shared-Runtime-Evidence-Association.md).
For each required observation name the reviewed producer, source revision, retained
artifact digest, load epoch, device and clock association, reset/mutation boundary
and rule membership. Missing native acquisition, executable formats or validity
rules remain blockers requiring their own authorized increment; do not replace
them with asserted manifest values or a new bespoke collector in this slice.
Preserve bounded credential-free formats and unavailable statuses. No raw secrets,
private document contents, full environment or unfiltered logs in public evidence.

### D. Exact executable packet and live approval

Only after A–C gates pass, assemble exact launch/replay/cleanup commands naming
delivered identities, read-only model/store, fresh private registration, authenticated
socket, schedule, scorers and effective capture. Use the descriptor loader's sealed
library paths, never system library-path changes. Require a runnable-command review,
not a launch as a preparation check. No automatic application discovery.

Carry forward the proposed Linux schedule: 186 natural offers plus 20 fixed-work
offers, 206 maximum, zero retries, 180 seconds per request, 900 per multi-call case,
7200 per phase. These are the preparation packet's stricter proposed bounds, not
new authority or performance targets. Inventory every departure from the historical
two-slot/65536-context/batch-512 runs and every later platform change. No same-work
speed claim from historical configuration or unequal cache/output counts.

Juan must approve the exact executable packet and finite live budget separately.
Then the approved bounded attributed preflight and resource/integrity stop rules
apply; no polling or stopping other work to force availability. Baseline task
failures remain results, not automatic aborts of independent comparisons. Record
queue versus inference boundaries honestly; no token timings inferred from a
nonstreaming response. Cleanup only experiment-owned processes under the approved
lifecycle. 4060 Ti capacity/OS, Windows native artifact delivery and per-app E2E
scenarios remain separate phases under PR107, not implicitly executed by Linux proof.

## Verification plan, differences and non-scope

Documentation verification now: relative links resolve, all receipt/profile hashes
match retained bytes, source citations match inspected owners, diff contains only
this plan and pointers. No code tests are rerun for documentation. Future A–D tests
are requirements, not claims of execution or approval.

Enumerated port differences: new canonical profile hash and explicit suffix;
one-slot/32768 total context versus historical two-slot/65536; batch 2048 versus
512; explicit cache-off default versus history-dependent reuse; newly bound host,
client, harness and scorer environment; later platform/driver/build identities.
Checkpoint/micro-batch pins preserve selected-source defaults. The runtime, model,
template, quantization, schema order, sampling and natural request bytes do not
change. Any additional difference requires a reviewed amendment before execution.

Explicit non-scope: schema/code/fixture/lockfile changes; dependency installation;
client/host/app implementation; engine or native builds; tokenizer/device/model
calls; arithmetic sandbox; runtime upgrade/fork; slots or precision experiments;
issue 88 enforcement; production, Ollama, services or business actions; eight-hour
soak; publication, cutover or performance claims. Windows profile-format migration
remains under ADR-0012; this Linux suffix is not a Windows G0 tuple.

## Implementation summary, cold diff audit and gap audit

This documentation PR adds the ownership/order/gates above, a README pointer and
PR107's migration-before-qualification clarification. No executable or profile
bytes change. Link/hash checks and a documentation-only diff audit verify those
claims. Future implementation, builds and live qualification are NOT DONE.
Acceptance requires Juan's exact-revision contract acceptance, independent oversight
and connector review, then ordinary merge gates. Acceptance/merge does not authorize
A–D execution. Human task-quality review remains pending. Before any next slice,
name its concrete scope and obtain the separately required authorization.

[host-run]: https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L433
[host-probe]: https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/src/host.rs#L672
[profile-load]: https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-primitives/src/profile.rs#L30
[transport]: https://github.com/canfieldjuan/local-connect-model-host/blob/bc8f46168cde990a9601fd6f0df61e0509c7d6ec/vendor/local-connect-model-client/crates/model-client/src/transport.rs#L112
[request-cache]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-schema.cpp#L528
