# V1 sequential runtime pins and proposed live qualification

## Decision, authority and status

Juan selects llama.cpp **c1d0e7a004015f23bc0233470b747b596f29b264** for V1,
with sequential model calls and **one slot**, shipping Qwen3.5-9B-Q4_K_M.
This settles the runtime-selection gate in [U1b](PR-Shared-Runtime-U1b-Consumer-Approval.md).
It does not select the separate canonical-arithmetic experiment or assert a new
speed measurement. The operator's description of the selected build as faster
is a selection rationale, not a comparative result produced by this change.

**Prepared, not live-approved.** This change pins a staged profile and proposes
the qualification below. No model, tokenizer, device preflight, host launch,
build, download, production configuration or Ollama change is authorized here.
The [issue 88 product policy](https://github.com/canfieldjuan/connect-contracts/issues/88)
remains OPEN: no refusal, warning or record-only policy for unqualified hardware
is selected. Qualification stop rules below govern experiments, not installed apps.
Previously open runtime-selection language in historical proposals describes
their original review state; this explicit decision supersedes that gate only.

## Profile, provenance and differences

The staged file is [the sequential candidate](../runtime/v1/candidates/sequential/profile.json).
Its PROFILE_ID is SHA-256 of its exact bytes, to be frozen in each run receipt.
The current [canonical profile](../runtime/v1/profile.json) remains unchanged at
`58bf361ec2d2a082931ffe19fb70dc9a22ffd8d7c10bc7837df137f843cd60d1`.
Staging avoids presenting new settings as already qualified or making consumers
silently adopt a new PROFILE_ID. The candidate is not a second production selector.
After qualification, adoption needs a separately reviewed coordinated migration.
The current ADR-0011 exact-argv conformance owner still describes the canonical
profile, so its admission check does not accept this suffix yet. The staged file
is shape-valid and independently pinned, not promised launchable by unchanged
host/client consumers. Offline launch/admission compatibility and a reviewed
profile-contract migration must precede G0 delivery or any model call.

The candidate copies the canonical CUDA and Vulkan tiers, order, context 32768,
one slot, model/template, artifact URLs, archive and per-file hashes verbatim.
CUDA reference archive SHA256 is
`2d4988729ab0df576efdaa58be27c55b4de1eb574256049a0f2b6d5abe9bff10`;
model SHA256 is `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
template SHA256 is `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715`.
This names complete existing Linux artifacts, not an arbitrary rebuild from a
short commit. Retain BUILD-INFO, library hashes and discovery-patch provenance
with the later launch. No arithmetic candidate is substituted.
Preserving the Vulkan tier's metadata does not qualify the revised Vulkan argv.
The proposed NVIDIA reference runs use CUDA; a Vulkan shipping claim needs its
own explicit backend qualification and budget, not inference from CUDA results.

Only this suffix is added to each tier's original argv:

```text
-b 2048 -ub 512 --ctx-checkpoints 32 --checkpoint-min-step 8192
--cache-ram 8192 --cache-reuse 0 --no-cache-prompt
```

| Setting | Candidate value | Evidence and change |
| --- | --- | --- |
| Logical batch | 2048 tokens | Preserves upstream default, `common_params::n_batch` [defaults][defaults]. |
| Physical micro-batch | 512 tokens | Preserves `n_ubatch`; cap is not a promise of actual physical row shapes. |
| Context checkpoints | 32 per slot; minimum spacing 8192 tokens | Preserves `n_ctx_checkpoints` and `checkpoint_min_step` [cache defaults][cache-defaults]. Checkpoint creation can still affect prompt partitioning even with reuse disabled. |
| Request prompt reuse default | false | Intentional change from default true, using `--no-cache-prompt` [CLI][cache-cli]. Motivated by retained serial cache-history variation; not a new proof of determinism. |
| RAM prompt-cache budget | 8192 MiB | Preserves the existing default; this is a ceiling, not reserved RSS or a measured footprint. Do not silently tune it for smaller hardware. |
| Shift-based chunk reuse | 0 | Preserves the existing default. Distinct from request prefix reuse and RAM cache. |

Other settings and flags stay inherited. In particular do not add `-nocb`, change
KV precision, GPU placement, graph/fusion settings, sampling, template, thinking
mode, or output limits as part of this profile pin. The first live freeze must
record effective settings and environment, including threads, K/V types and
checkpoint behavior; CLI intent alone is insufficient. All platform/driver/build
differences are independent execution identities under [ADR-0015](../adr/0015-runtime-accuracy-qualification-identity.md).

**Important source boundary:** `--no-cache-prompt` is a default, not an immutable
server prohibition. [`eval_llama_cmpl_schema`][cache-read] starts from that
default; request `cache_prompt: true` overrides it. The server uses that request
value for [prefix reuse][reuse]. Every candidate occurrence must bind its exact
request bytes and effective false policy. Do not rewrite bytes in transport or
claim omitted/null/true are interchangeable. If a frozen app uses true (the
existing proposed Doc Sum canary does), record the mismatch and prepare a separate
owner-reviewed request-policy amendment before its live lane. Keep its old bytes
and scoring as a historical control. No app code changes are made here.

One slot limits runtime capacity; it does not serialize application callers.
Qualification dispatches the next model request only after the prior response
and cleanup finish, including multi-step app graphs. Freeze actual app admission,
queue/rejection and cancellation behavior separately. No gateway cap is changed.

## Validated inventory to reuse, not reconstruct

Use [U1b's inventory](PR-Shared-Runtime-U1b-Consumer-Approval.md#validated-work-inventory-before-any-port)
and [the observation inventory](PR-Shared-Runtime-Observation-Evidence.md#verified-inventory-before-any-port)
for frozen source bindings, validators, framing and request bytes. The existing
301-file receipt, preproduction evaluation `20261004T175816Z-24660385746b`, and
issue-73 corpus manifest remain the owners. Retain private content in the private
evidence store, never a public PR or credential-bearing log.

The retained `seeded-corpus-concurrency-20261013T010124Z` packet has 25 preproduction
cases plus 33 invoices, 58 cases / 62 native calls per complete lane, including
the archived multi-call Summary chain. Its `run.py`, `COMMANDS.md`,
`corpus-manifest-reused.json`, and real app scorers are reuse points; do not run
that single-use packet again or launch its old resident setup. Its historical
configuration was two slots, total context 65536 and batch 512, so it is not a
same-configuration control for this one-slot/batch-2048 candidate. Historical
accuracy failures, date-oracle caveats and pending human reviews remain visible.

The phase0 manifest and [selected-source annex](PR-Llama-C1d0e7a-Observation-Annex.md)
bind source defaults and reporting/reset paths. That annex is source evidence,
not a currently measured effective-settings record. The retained cache diagnostic
and concurrency evidence motivate a fresh serial test; neither establishes this
new profile's corpus accuracy, cross-GPU equality or speedup.

Before freezing execution, the owners must enumerate every porting difference:
one-slot total context, logical batch, cache policy, source revisions/scorers,
profile bytes, runtime artifacts and host/client transport, platform/driver and
all request-level fields. Preserve schema property order, app temperatures,
fixed per-request seeds, prompt bytes, templates, reasoning framing and natural
completion budgets. Never silently fix an oracle or a schema during a comparison.

## Proposed qualification sequence — approval required

No phase below may execute until Juan approves its exact frozen packet and finite
budgets. Counts and time ceilings here are proposed maximums, not permission,
performance targets or promised completion times. Every offer counts toward the
cap, including failures/rejections; zero automatic retries or replacement samples.
Preparation is read-only/offline; a missing executable or owner binding is a
blocker to report, not permission to build or invent it.

| Phase | Proposed work and limit | Required result |
| --- | --- | --- |
| G0 freeze | No live calls. Bind profile, exact executable/library/model/template identities, source revisions, request/scorer manifests, environment, effective-observation producers, launch/cleanup and replay commands. Review platform differences and any cache-policy amendment. | Complete artifact and byte bindings; credential-free capture; explicit unknown observations. No mocked tokens promoted as native proof. |
| L: RTX 3090 Linux reference and determinism | Three sequential passes over the same 58-case/62-call suite (186 calls). Then five fixed-work repetitions for each of four classes (short interactive, summary, invoice extraction, business extraction/classification): at most 20 additional calls. Maximum 206 model calls, 120 minutes total. | Within-identity output bytes identical across three serial passes; every mismatch recorded with score delta. Correctness and speed reported independently. All outputs, including first-use, retained. |
| A: RTX 4060 Ti | Three serial suite passes, at most 186 calls and 120 minutes. First freeze whether the physical card is 8 GB or 16 GB, its OS/driver and complete selected backend; use identical request bytes and settings. No reduced context/offload/cache or fallback to force a fit. | Separate memory, correctness and within-identity determinism result. Compare all cross-device mismatches and scores to L; do not require or assume cross-device byte equality. A failure on 8 GB remains a V1 hardware-floor gap. |
| W: Windows 11 native | Juan's own physical Windows machine, no VM. Three serial suite passes, at most 186 calls and 120 minutes. Exact GPU/VRAM, native build artifacts, DLLs, driver, identity/transport and profile binding frozen first. | Same within-identity and task gates. Record Windows/backend differences explicitly. Linux success is not Windows proof. No automatic reuse of Linux archives/paths or launch syntax. |
| E: one end-to-end scenario per app | Email Watcher, Document Summarizer, Invoice Processor including its COI route, and one representative Connect automation. One complete scenario each, through the real isolated app → shared host → runtime → model → real validator/UI/result path. Proposed ceiling 60 minutes total and 600 seconds per scenario; exact multi-call counts/output caps supplied by owners before approval. | Correct app-level result, intact schema order and request bytes, sequential dispatch, recorded admission and response timing. Each scenario names its platform; a Linux app pass does not qualify its Windows package. Repeat the same scenario on the other shipping platform before claiming that app qualified there, with a separately frozen budget. |

Per-request ceiling for direct phases: 600 seconds including client wait, within
the phase ceiling; preserve existing stricter app deadlines. Output limits for
natural-completion requests remain frozen app values. For fixed-work cases,
propose 256 output tokens per request and frozen input lengths drawn from those
same fixture classes; finalize actual token arrays/lengths only in the separately
approved tokenizer/native preparation. A cap is not an achieved output count.
No EOS suppression or task-prompt rewrite is implied; unequal realized work
cannot support an inference-speed ranking. No eight-hour soak or overlap test
is included in this V1 sequential plan.

Repeated-prefix and cold-history evidence must be distinguished even with reuse
off: repeat the suite in the same resident epoch and identify first-use versus
later occurrences, retaining actual cached/new token counts. The final frozen
packet allocates these occurrences within the listed caps; extra starts/calls
need amended approval. Nonzero cache reuse is a failed policy/observation gate,
not a silently discarded timing sample. A fresh-start repeat may be proposed
later if the results require it, not added during the run.

Use a single bounded, attributed GPU/RAM preflight immediately before each live
phase. Stop if competing compute is active or ownership is uncertain; no polling,
unloading others' models or terminating other processes. Preserve the previously
qualified headroom criteria in the frozen packet; static swap below 1% of RSS
alone is not a failure. Watch incremental swap/page pressure, RSS, GPU memory,
errors, cancellations and recovery. Stop dispatch on OOM, identity drift, capture
integrity loss, request mismatch, active contention or phase deadline; retain
every attempted occurrence and cleanup receipt. Stop only experiment-owned
processes under the approved launch lifecycle; leave production and Ollama alone.

A baseline task failure is a result: continue independent bounded comparisons
unless a resource/integrity stop applies. It cannot become a PASS through
averaging. Schema/correctness or transport incompatibility blocks dependent app
adoption, not independent offline analysis. Use fixture accounts and inert action
sinks in E: no email sends, payment changes, real workflow execution or production
document mutations. Record this isolation as a qualification limitation.

## Measurement and acceptance

Record offer, app admission/queue, dispatch, first response bytes, first visible
answer token where streaming exists, completion and final app result separately.
Unavailable boundaries stay unavailable; nonstream responses cannot supply TTFT
or inter-token timing. Separate generated/internal reasoning from visible output.
Report sample counts, median, range, standard deviation and exploratory small-
sample p95; prompt/new/cached/generated token counts, throughput, correct jobs,
failures, rejections, cancellations and hardware pressure alongside latency.

Pass gates proposed for approval: all bindings verified; zero unexplained
within-identity byte mismatches; no new task-score regressions versus the frozen
agreed reference; required app/schema checks pass; bounded memory and recovery;
complete retained observations or explicitly incomplete qualification. Every
existing wrong answer remains in the report with a reviewed disposition. Summary
fidelity, extraction accuracy and unresolved dates need human review; JSON validity
alone is insufficient. Human quality review remains PENDING until performed.

No new speedup threshold is invented. The first reference establishes observed
latency/throughput under this profile. A speed comparison requires same-device,
same-server configuration controls with equal request/output/cache work and an
explicit comparator budget; it is not granted by these qualification phases.
The new PROFILE_ID, byte parity, speed, quality, platform coverage and release
readiness are separate findings. One slot does not prove simultaneous-user
inference capacity or cross-device deterministic arithmetic.

## Concrete remaining gates and offline proof

- Juan's exact plan/budget approval before preflight, tokenizer or model calls.
- 4060 Ti memory variant and test OS; Windows 11 GPU and availability.
- Windows native runtime/host/client artifact and transport readiness under
  [ADR-0012](../adr/0012-shared-local-model-runtime-windows.md), including its
  coordinated profile-format migration. The staged file here is a Linux v1
  profile, not a claim that the Windows G0 tuple exists. No builds authorized.
- Credential-free effective-settings/load-epoch/device observation and immutable
  binding delivery under the existing capture/association contracts. An argv
  suffix cannot implement this evidence or finish `validate_record_binding`.
- Real app request/scorer binding, any cache-true amendment, complete scenario
  and native-call budget from each app owner. No reserialization in transport.
- Separate production enforcement decision under issue 88, qualification review
  and coordinated profile adoption. Open issue 88 does not block an explicitly
  approved isolated qualification experiment; it blocks assuming product policy.

Offline verification covers schema shape, the exact candidate argv, preservation
of every existing artifact/model/template pin and the unchanged canonical profile.
The focused regression fails before the candidate file exists. It is not a server
parser, GPU-fit, live determinism, accuracy or performance test. No old sealed
receipt or fixture is relabelled. Rollback before adoption is simply not adopting
the candidate; the existing canonical profile and application copies remain intact.

[defaults]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/common/common.h#L443
[cache-defaults]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/common/common.h#L611
[cache-cli]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/common/arg.cpp#L3535
[cache-read]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-schema.cpp#L528
[reuse]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3101
