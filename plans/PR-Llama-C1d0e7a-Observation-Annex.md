# llama.cpp c1d0e7a observation-source annex: comparison only

Status: PROPOSED documentation annex to [PR103's evidence map](PR-Shared-Runtime-Observation-Evidence.md).
The nominated comparison source is `c1d0e7a004015f23bc0233470b747b596f29b264`.
It is not a production runtime decision, resolution of issue88, trusted rule-set
registration, or authorization to implement or execute. Runtime selection and
budgets remain OPEN. No client/host/runtime changes, builds, model/tokenizer calls,
live tests, production or Ollama changes are part of this slice.

## Root cause, scope and source identity

PR103 identified missing evidence meanings. This annex follows the nominated
source from effective values to reporting, reset paths and the evidence needed
to support an interval claim. It does not turn build defaults, argv or matching
hashes into observations. Required change surface: this document and one forward
pointer in PR103's plan. All executable schemas, fixtures and code stay unchanged.

CONFIRMED: source was read from immutable Git objects at the full commit above,
not the working files of an arithmetic experiment. Contracts base is
`f6619f580e74b37a9ddf31585a9161841347a12f`. The historical baseline's separate
discovery patch digest is
`c04ecd7175942e00b7e4e4bca4aa466fd57505387521c64d65c3c7bea53a9fbb`;
the comparison here is upstream source, not proof that an installed binary or a
patched build behaves identically. Retain the complete build/patch identity if
this source is later nominated for qualification.

Reuse [PR103's historical inventory](PR-Shared-Runtime-Observation-Evidence.md#verified-inventory-before-any-port)
and its U1b/corpus pointers for model, quantization, template, prompts, settings,
exact request bytes and recorded results. No model file was read or rehashed,
no corpus was rebuilt, and no old result is claimed as a new measurement.
Pinned source blobs and search receipts are retained in the private review packet.
Links below resolve to the nominated commit; line numbers refer to that source.

CONFIRMED denotes source behavior. INFERRED denotes a candidate validity argument
that still needs captured evidence. UNKNOWN denotes an unestablished runtime fact.
An existing C++ value/log/API is a possible reporting path, not an implemented,
authenticated, credential-free Connect capture adapter.

## Lifecycle and reporting boundaries shared by the field map

**L1: model/context load epoch, not PID lifetime.**
[`handle_sleeping_state`][sleep] destroys the context/model on sleep and calls
`load_model(params_base)` on wake. [`load_model`][load] copies parameters and
recreates contexts and slots. [`get_props`][getprops] returns cached properties
while sleeping, with `is_sleeping` set by [`get_res_props`][props]. A surviving
PID, equal pre/post samples, or a ready response is insufficient to prove that
one model/context load covered a workload. INFERRED: context-construction values
can support a load-epoch invariant if the collector proves initialization completed,
the same model/context remained active, and no sleep/reload/restart crossed the
required interval. This epoch association is not supplied by the current canonical
instance artifact. Its evidence representation remains OPEN; no schema is changed.

**L2: request/slot state.**
[`launch_slot_with_task`][launch] installs a const task and enters STARTED or
WAIT_OTHER; [`release`][release] resets the task and returns the slot to IDLE.
[`CANCEL`][cancel] releases the matching task. Prompt clear/shift, checkpoint
restore and slot restore change cache contents, not the context's configured caps
or cache element types. A report must identify the occurrence, slot, task and L1
epoch; task IDs or slot numbers alone are not permanent request identities.

**L3: backend/device association.**
[`llama_prepare_model_devices`][selected] restricts the
selected device list, then logs backend name, hardware description and device ID.
Backend enumeration is broader than that selected list. CUDA [device properties][cuda-props]
and Vulkan [device properties][vk-props] expose name/description/device ID, not all
the canonical driver/version observations. Device enumeration/initialization,
model reload, backend/library changes, virtual-device configuration or a changed
selected-device mapping invalidate an unproven association. UNKNOWN: the actual
device and loaded libraries of any future run. Multi-device aggregation is not
invented for the canonical single-device record.

## Complete field map

All 20 canonical paths appear once below. Units are value semantics, not sampling
budgets. Reporting routes are read from source only; none were called. Source logs
are candidate producer outputs, not permission to copy entire private logs.

| Canonical field / owner | Reporting path and units (CONFIRMED) | Mutation/reset path | Validity evidence and comparison limit |
| --- | --- | --- | --- |
| `effective_settings.context_per_slot` / server | GET `/props` -> `default_generation_settings.n_ctx`, from `meta.slot_n_ctx` [props][props], [metadata getter][slotctx]; GET `/slots` -> each `n_ctx` [slotjson][slotjson]. Integer tokens per slot. [Slot construction][slots] takes `llama_n_ctx_seq` and caps to training context. | Assigned at slot construction; L1 recreates slots. Context shifting changes used contents, not this capacity. | Retain effective report plus L1/instance binding; require all relevant slots agree. Do not divide argv total context by slots: [context construction][ctxsize] pads partition sizes and handles unified KV differently. Cached sleeping props alone fail validity. |
| `effective_settings.slots` / server | GET `/props` -> `total_slots` [props][props] uses `params.n_parallel`; [slot construction][slots] creates that many slots. Integer slots. | L1 rebuilds slots; [POST `/props`][postprops] is a no-op placeholder at this commit, not a setter. | Correlate report with active slot collection/L1. This is capacity, not active users. Same source must support `concurrency.slots`. |
| `concurrency.slots` / server | Same `total_slots` and slot collection as the preceding row; integer slots. | Same L1 lifecycle; activity changes do not change configured capacity. | Must equal `effective_settings.slots`; do not independently derive or fill it from offered request count. |
| `effective_settings.logical_batch` / server | `llama_n_batch(ctx)` / `llama_context::n_batch`; constructor INFO `n_batch` [batchcaps][batchcaps], [getters][getters]. Integer token cap per logical decode. No dedicated field in `/props`'s object. Causal attention clamps to context size. | Fixed context cap within L1. Server [decode retry][retry] halves a local `n_batch` on failure, then [resets it][retryreset] after success; this does not mutate the context cap. | Bind initialized context-cap evidence to L1. Report configured effective cap separately from each realized decode width; retries and physical batch partitions cannot be inferred from this scalar. |
| `effective_settings.physical_micro_batch` / server | `llama_n_ubatch(ctx)` / getter and constructor INFO `n_ubatch` [batchcaps][batchcaps], [getters][getters]. Integer token cap; min(logical batch, requested ubatch), with zero request using logical batch. | Constructor/L1 fixes cap. Work partition and partial final batches vary per decode without changing cap. | Retain effective context output, not the CLI request. L1-bound cap does not prove the shapes used or arithmetic parity. No direct `/props` field. |
| `effective_settings.context_checkpoints` / server | `params_base.n_ctx_checkpoints`; TRACE enabled `max`/`min spacing` or disabled [checkpoint-report][checkpoint-report]. Integer maximum checkpoint count per slot, not tokens or current occupancy. | Config copied on L1. [Creation/eviction][checkpoint-create], [restore][checkpoint-restore] and [eligibility][checkpoint-gate] mutate actual saved state; completion/sequence-removal/SWA conditions gate creation. | Positive capacity is not proof any checkpoint exists. Pair configuration report with L1; for a disabled log alone do not invent an exact original negative/zero input. Actual save/restore claims need separate events. No `/props` capacity field. |
| `effective_settings.flash_attention` / server | Effective boolean is `cparams.flash_attn`. Constructor initializes it from mode; [AUTO resolution][fa] can disable it after backend assignment checks. Initial INFO prints requested mode, not necessarily resolved boolean. | Initial mode and [compatibility checks][fa-init] precede resolution; AUTO resolves and clears `auto_fa` in `resolve_fused_ops`, invoked during [graph reservation][fa-call]. L1 repeats resolution. | Capture resolved state after initialization/resolution and bind L1. Forced-on versus AUTO must be distinguished in source evidence. Do not parse `auto` as true or claim every attention operation ran a GPU kernel. No dedicated HTTP resolved field. |
| `effective_settings.kv_cache_type_k` / server | Attention K cache type from `params.type_k`, tensor creation and INFO `K (type)` [kv][kv]; labels from `ggml_type_name`, not weight quantization. | Memory construction/L1 fixes element type; clear, shift and state restore mutate contents. | Bind initialized attention-cache report to the same context. Qwen35 hybrid [memory construction][hybrid] separately uses F32 recurrent state; this field does not describe all hybrid memory. No `/props` field. |
| `effective_settings.kv_cache_type_v` / server | Attention V type from `params.type_v`, tensor creation and INFO `V (type)` [kv][kv]. Exact type label. | Same L1/content distinction as K; flash attention affects layout, not permission to infer precision. | Retain V evidence independently of K. [Context compatibility checks][fa-init] may reject unsupported type/mode combinations; a failed construction is not a valid observation. Hybrid recurrent state remains separate. |
| `effective_settings.offloaded_layers` / server | INFO `offloaded X/Y layers` [offload-log][offload-log] prints min(requested resolved layer count, total layers+output). Actual assignment uses `devices.empty()` and `act_gpu_layers` in [load_tensors][offload-map], with input layer on CPU. Units: layers under this implementation's count convention. | Model load builds layer/buffer placement; L1/model reload rebuilds it. Tensor-buffer overrides/fallbacks can differ from layer intent. | Log numerator alone is not authoritative actual placement: the print expression does not use `act_gpu_layers`. Need selected-device and actual placement/buffer evidence for this model/build, including output/input treatment. No accepted scalar conversion or HTTP actual-offload report is established here. |
| `effective_settings.prompt_cache_reuse` / request | Request `cache_prompt` -> boolean field [schema][schema]; [evaluation][cache-eval] starts from global `params_base.cache_prompt`. [Boolean parser][bool] preserves false, treats absent/null as default, rejects incompatible types. Units: policy boolean, not cache-hit count. | Per task/L2; global startup default can change through CLI/environment [cache-cli][cache-cli]. Prefix/LoRA boundaries, checkpoint restore/reset, cache shifting and slot erase/restore affect actual reuse [prefix][prefix]. | Exact original request bytes and endpoint mapping plus known effective default are necessary. Explicit booleans can establish request intent; omission/null requires default evidence. `n_cache_reuse` chunk threshold and RAM prompt cache are distinct. Mixed-policy aggregation remains OPEN, never majority/any-true. |
| `concurrency.requests_overlap` / workload | `/slots` exposes `is_processing`, `id_task`; [state test][processing] includes WAIT_OTHER/STARTED, not just inference. Metrics [count][metrics] likewise counts non-IDLE slots. [Batch assembly][assembly] and [decode][decode] own actual shared execution. Units: supported nonzero execution-overlap boolean. | L2 assignment, waiting, decode, completion/cancel/release; continuous batching and compatibility checks change which slots share work. | No complete attributed execution-interval report found in these endpoints. Need same-epoch occurrence-to-task mapping and retained batch/decode boundaries plus clock proof. Two occupied slots or overlapping HTTP times do not prove simultaneous inference; false requires complete relevant coverage. UNKNOWN from source alone. |
| `device.name` / device | Selected-device load log [selected][selected]; CUDA [description/PCI initialization][cuda-id] and Vulkan [hardware-name log][vk-name]. Units: bounded hardware label; backend selector name (e.g. a CUDA ordinal) is distinct from hardware description. | L3; backend enumeration/virtual mapping and model selected-device list can change between loads. | Associate the selected backend handle/physical ID to the description; names are not unique identifiers. Neither enumeration nor the host's prelaunch probe alone proves use by a model. |
| `device.compute_capability` / CUDA device | NVIDIA branch [CUDA device discovery][cc] reads `cudaDeviceProp.major/minor`, logs `major.minor`, internally encodes `100*major + 10*minor`. Units: capability version, not driver/toolkit version. | L3 device enumeration/cache; do not carry to a changed physical/virtual device or non-CUDA backend. | Pair enumerated capability with selected-device identity in the same epoch. Retain exact decimal components; don't interpret the internal encoding as a decimal float. No server HTTP capability field. |
| `device.nvidia_driver_version` / CUDA device | No NVIDIA release-version reporting call found in pinned server/common/CUDA sources; GGML device props contain no driver-version field [cuda-props][cuda-props]. Units required: release label. | External driver installation/reset/device association can invalidate an earlier sample; source supplies no interval proof. | UNKNOWN/unavailable until a separately reviewed device-source collector supplies release identity and validity. Driver-supported CUDA API level, compiler version and build label are not substitutes. No new collector is proposed as implemented. |
| `device.cuda_runtime_version` / CUDA device | No `cudaRuntimeGetVersion` reporting path found in pinned server/common/CUDA sources; backend [device props][cuda-props] omit it. Units required: loaded runtime version label. | Loaded library/build/backend and L3 association, reload/restart. | UNKNOWN/unavailable. Need evidence tied to the runtime library actually used by this server, not `nvcc`, image tags or the driver's supported CUDA version. No new call or dependency authorized. |
| `device.physical_device_identity` / Vulkan device | [Backend PCI query][vk-pci] -> `props.device_id` [vk-props][vk-props], nullable when extension unavailable; [UUID deduplication][vk-uuid] is internal enumeration logic. Units: exact device identity label under a reviewed encoding. | L3 selection/enumeration, driver/ICD and device replacement; ordinals may change. | Need selected physical device + identity + platform/boot association. Do not substitute enumeration index/name, or silently change PCI to UUID. Portable identity encoding/Windows acquisition remains OPEN. |
| `device.api_version` / Vulkan device | [Initialization][vk-init] stores `props2.properties` from selected physical-device `getProperties2`; its API version is internal data, not emitted in the examined server/device-props interfaces. Units: Vulkan API version components. | Physical-device/backend initialization and L3; requested instance API version is separate. | Candidate extraction would read the selected physical-device property with specified lossless Vulkan version decoding, including variant where applicable. No existing retained public report or reviewed conversion is claimed. UNKNOWN until collected. |
| `device.driver_implementation` / Vulkan device | [Initialization][vk-init] uses `driver_props.driverID`; [debug log][vk-name] includes `driverName`. Units: implementation identity/label, not driver release. | Driver/ICD/backend initialization and L3. | Retain both precise ID/name association to selected physical device; matching hardware alone is insufficient where multiple ICDs exist. Label encoding and safe evidence format remain OPEN. No server HTTP field. |
| `device.driver_version` / Vulkan device | Raw `device->properties.driverVersion` retained by [initialization][vk-init] and consumed by [driver-specific workaround][vk-driver]. Not output by the examined server/device-props interfaces. Units: vendor/implementation-defined version encoding. | Driver/ICD initialization/reset and L3. | Cannot universally apply Vulkan API-version decoding to driverVersion. Need implementation-specific, reviewed lossless mapping and raw integer evidence tied to that ICD/device. UNKNOWN/unavailable until that source exists. |

## Request-policy and overlap interpretation

Native completion parsing uses [eval_llama_cmpl_schema][cache-eval]. OpenAI
completion and chat conversion [copy remaining properties][oai-copy], [chat copy][chat-copy],
so `cache_prompt` is not stripped on those inspected paths before schema evaluation.
This does not claim all endpoints, app routes, rejected requests or adapters share
that behavior. The future app-binding rule must name the actual endpoint and
preserve original bytes; no metadata normalization may reorder response schemas.
For a per-request policy, true/false are source-defined. For a single record spanning
mixed policies, the scalar aggregation contract is still missing. Missing policies
must not be silently resolved from the compiled default alone.

`is_processing()` is explicitly `state != IDLE`; the enum includes waiting and
not-yet-prefilling states. `/slots` is queue-sampled and metrics can be handled while
decode runs on the worker. Even a synchronized occupied-slot sample is not the
complete attributed execution history required by PR103. Batch assembly includes
sequence/slot identities, but this annex supplies no public instrumentation or
trusted event format. A later proof must account for every offer, rejection,
retry, cancel, missing boundary and repeated ID; no selective successful subset.

[GGML time][clock] uses `CLOCK_MONOTONIC` microseconds on this non-Windows path and
QPC-relative microseconds on Windows. These are not the accepted scope clocks
`linux-boottime-ns` and `windows-uptime-ms`. Multiplication or relabeling does not
establish a common origin, suspend behavior or uncertainty bounds. No clock-binding
receipt is produced here. Nonstreaming durations remain incapable of establishing
internal first-token/inter-token timing.

## Validity and source-evidence admission

INFERRED candidate invariants are bounded to the relevant L1/L2/L3 lifetime, not
approved lifetime rules. Source inspection must be paired with independent evidence
of the actual load, process/start/boot identity, runtime artifacts, source producer,
device and required interval before any `observed` value is accepted. A same-PID
sleep/wake is a concrete counterexample to process-lifetime inference. `/props`
while sleeping is a concrete counterexample to treating an HTTP success as fresh
loaded-state evidence. POST `/props` is a placeholder in this revision; that does
not erase the other reload/mutation paths or prove future builds equivalent.

Reports and logs can contain model paths, templates, sampling parameters, prompt
or generated text. [`server_slot::to_json`][slotjson] includes prompt/generated
content when debug detail is enabled. No whole-log capture or new logging flag is
authorized. A later source adapter must define bounded credential-free acquisition
at the producer and preserve raw bytes/provenance for that admitted artifact;
an arbitrary edited log excerpt is not authenticated raw evidence. Privacy closure
and exact artifact formats remain blockers where existing outputs are unsuitable.

For Qwen35, the source's hybrid constructor separates attention K/V precision from
F32 recurrent state. Clear/restore checkpoints may change numerical state without
changing the reported settings. Likewise an effective batch cap does not describe
the physical row partitions that motivated this investigation. These distinctions
prevent this annex from implying output parity, cache correctness, a speedup or a
fix for concurrency-dependent arithmetic.

Keep the [accepted error boundary](PR-Shared-Client-App-Binding-Scope.md#single-owner-validation-and-errors):
asserted observations lacking applicable rules or sufficient interval/clock proof
fail `ObservationScope`; honestly unavailable values retain missing paths without
invented proof. Malformed metadata, changed identity and digest/attribution failures
retain their distinct errors. Never downgrade conflicting observed evidence to
unavailable inside validation. No rule IDs, ruleset membership or trust callbacks
are registered by these proposed mappings.

## Differences, verification and cold diff audit

Difference from PR103: exact nominated-source reporting and mutation owners are now
mapped, including load epochs, cache-policy defaults/null semantics, offload-log
limitations and native clock differences. No behavioral, prompt, model, request,
schema, test, dependency or budget changes. Public links cite source; the private
packet contains blob hashes and read-only searches, not client documents or secrets.

Documentation verification: every pinned source link/line exists; the field table
equals the canonical 20-path enum; local links resolve; full two-Markdown-file diff
and whitespace are checked. No builds, tests, fixture replay or endpoint calls are
needed or permitted. Review the complete table against cited code, not README claims.
Future authorized proof must falsify each proposed invariant with sleep/reload,
same-name devices, omitted/null/false policies, mixed requests, changed defaults,
partial logs, waiting slots, retry-size changes, offload fallback and clock mismatch.
Retain the existing corpus/scoring/byte-parity gates separately from source proof.

## Gap audit and next gate

DONE for comparison documentation preparation; NOT DONE for trusted rule closure,
capture implementation or qualification. Each field has a source path or an
explicit reporting absence, units, reset/mutation paths and evidence obligations.
Source paths do not mean observations were collected. Remaining blockers are exact
safe evidence formats; load-epoch/device/clock association; unsupported CUDA-version
reporting; Vulkan identity/version encodings; actual offload placement conversion;
mixed-policy aggregation; and attributed inference execution boundaries.

Independent oversight and exact-revision operator acceptance are separate gates.
No runtime/build choice or issue88 decision follows from acceptance. Any follow-up
representation amendment, rule registration, implementation, source instrumentation
or native/live proof requires its own authorization. Windows proof stays native on
Juan's Windows box. Production and Ollama remain unchanged.

[sleep]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L906
[load]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L958
[getprops]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L4676
[props]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L4471
[postprops]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L4688
[launch]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L1720
[release]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L498
[cancel]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L2338
[selected]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama.cpp#L157
[cuda-props]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-cuda/ggml-cuda.cu#L4825
[vk-props]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-vulkan/ggml-vulkan.cpp#L18028
[slotctx]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3905
[slotjson]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L640
[slots]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L1156
[ctxsize]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-context.cpp#L290
[batchcaps]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-context.cpp#L244
[getters]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-context.cpp#L755
[retry]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3614
[retryreset]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L2771
[checkpoint-report]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L1283
[checkpoint-create]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L2209
[checkpoint-restore]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3251
[checkpoint-gate]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3344
[fa]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-context.cpp#L504
[fa-init]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-context.cpp#L3571
[fa-call]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-context.cpp#L620
[kv]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-kv-cache.cpp#L231
[hybrid]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-model.cpp#L2444
[offload-log]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-model.cpp#L1757
[offload-map]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/src/llama-model.cpp#L1449
[schema]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-schema.cpp#L31
[cache-eval]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-schema.cpp#L515
[bool]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-schema.cpp#L582
[cache-cli]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/common/arg.cpp#L3534
[prefix]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3101
[processing]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L420
[metrics]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L2385
[assembly]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L2987
[decode]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-context.cpp#L3564
[cuda-id]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-cuda/ggml-cuda.cu#L5520
[cc]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-cuda/ggml-cuda.cu#L351
[vk-name]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-vulkan/ggml-vulkan.cpp#L7332
[vk-pci]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-vulkan/ggml-vulkan.cpp#L17948
[vk-uuid]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-vulkan/ggml-vulkan.cpp#L7494
[vk-init]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-vulkan/ggml-vulkan.cpp#L6341
[vk-driver]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml-vulkan/ggml-vulkan.cpp#L5763
[oai-copy]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-common.cpp#L1041
[chat-copy]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/tools/server/server-common.cpp#L1380
[clock]: https://github.com/ggml-org/llama.cpp/blob/c1d0e7a004015f23bc0233470b747b596f29b264/ggml/src/ggml.c#L527
