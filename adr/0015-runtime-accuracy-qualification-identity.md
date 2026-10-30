# ADR-0015: Runtime accuracy qualification identity

**Status:** Proposed. Docs only. It amends ADR-0011 and needs direct operator acceptance before any schema, profile, host or application change.

**Date:** 2026-10-19

## Context and scope

ADR-0011 pins the shared runtime: the llama.cpp commit, the runtime archive and its per-file manifest, the model, the context length and the exact server argv. It requires each application to "qualify its own requests against exactly the argv in the profile it ships."

The local Connect Runtime investigation reproduced answer changes for byte-identical requests on the pinned model and engine. Evidence aliases are under `connect-runtime/phase0-20261011T053523Z/`; raw tokens and outputs are private.

- **Concurrency.** With two requests in flight, every simultaneous target run changed its answer, while delayed arrivals matched serial (`delayed-partner-20261019T000010Z`, `microbatch-trace-20261019T002410Z`).
- **Serial is not automatically safe.** Serial runs were repeatable within a fixed configuration. But changing only the physical micro-batch cap (512 versus 32) changed a serial answer to a previously recorded wrong answer (`microbatch-cap-20261019T004127Z`). Consistent output can be consistently wrong.
- **Mechanism, partly traced.**
  - Partition boundaries alone reproduce a first-score difference, with no concurrent partner (`prefill-partition-replay-20261019T013814Z`).
  - The earliest named difference is the first-layer QKV projection, inside the CUDA MMQ path. That path's kernel configuration is selected per GPU architecture at compile time.
  - A partition of 12+4 versus 16 K-blocks changes floating-point accumulation order. The difference has been linked byte-exactly into the full-model trace (`mmq-arithmetic-instance-20261019T151226Z`, `mmq-model-link-20261019T152153Z`).
  - Not yet established: that this arithmetic difference alone causes every changed task answer. That work continues separately and is not needed for this decision.

This exposes three gaps in what a qualification proves:

1. **Implicit settings.** The argv leaves output-affecting settings to the pinned binary's defaults: logical batch, physical micro-batch, context checkpoints and prompt-cache reuse.
2. **Support versus accuracy.** A tier's requirements list every GPU compute capability the build supports. Accuracy evidence exists for fewer. Because kernel selection depends on architecture, passing on one GPU does not qualify another.
3. **Intended versus effective.** Qualification evidence records the intended argv, not the settings and build the running server actually used.

Out of scope:
- the remaining causal trace;
- slot or concurrency adoption (still open in issue #68);
- product behavior on unqualified hardware (see Decision 6);
- any change to the current pins, argv, host, applications or their existing gates.

## Decision

1. **Supported is not qualified.** A tier's `requirements` keep meaning build and runtime support only. Accuracy qualification is a separate record keyed by `PROFILE_ID`. A pass qualifies exactly one execution identity and no other. The identity is:
   - the `PROFILE_ID`;
   - the runtime archive SHA-256;
   - the model SHA-256;
   - the GPU device name and compute capability;
   - the driver and CUDA runtime versions;
   - the effective server settings (Decision 2);
   - the concurrency mode (slots, and whether requests overlap);
   - the application route: the application, its capability, and its request profile or prompt version.

2. **Effective settings are measured, not assumed.** Every qualification run captures the settings the running pinned server reports, not just the argv it was given. At minimum:
   - context per slot and slot count;
   - logical batch and physical micro-batch;
   - context checkpoints;
   - prompt-cache reuse policy;
   - flash attention;
   - KV cache types;
   - offloaded layers.

   The implementation PR fixes the exact field list from what the pinned server reports. It must not rely on documentation of defaults.

3. **Explicit argv at the next profile revision.** The next profile revision that already requires a new `PROFILE_ID` makes the output-affecting settings from Decision 2 explicit in the argv. Their values equal the measured effective settings of the current pin, so the change alone does not alter outputs. This ADR does not force a standalone profile change or an application release.

4. **What a qualification checks.**
   - **Expected answers.** Frozen requests are scored against independently reviewed expected answers and the application's deterministic checks: dates, amounts, missing fields, claim meaning and source references. Valid JSON and a successful request are not a pass.
   - **Byte identity.** It stays required wherever a runtime change is claimed to be transparent.
   - **Schedule variation.**
     - For a profile with more than one slot, it is part of qualification: serial, the shipped overlap mode and a partition-boundary case, against the same expected answers.
     - For the current single-slot profile, the partition settings in the recorded identity are fixed. A change to them is a new identity.
   - **Verify.** A second model pass, such as a verification stage, can share the same runtime sensitivity. Its PASS never replaces independent expected answers, deterministic checks or operator adjudication.

5. **First-divergence triage.** When a qualified answer changes, the first divergence is located before anything is fixed:
   - input preparation;
   - native model output for an identical request;
   - application interpretation of an identical model output.

   The fix goes to that owner. Downstream validators are not taught to accommodate an unstable upstream result.

6. **Unqualified identities are an open product decision.** This ADR records qualification; it does not decide what an installed application does on hardware or settings outside every qualified identity. Whether it refuses, warns or runs as unqualified is a separate operator decision, tracked as an issue before any enforcement lands.

## Consequences

- Each application's next live qualification contract binds to a recorded identity under Decision 1 and keeps its existing independent labels and gates. This currently means the Document Summarizer whole-writer qualification and the Invoice Processor amount-due qualification.
- Existing pass records stay valid only for the identity they actually ran on. No current gate is weakened or reopened.
- Unrelated findings with their own demonstrated causes are not re-attributed to the runtime.

## Landing order

1. This ADR.
2. A qualification-record schema, fixtures and offline shape checks in this repository.
3. Effective-settings capture by the host (`local-connect-model-host`), exposed to applications with the registration it already publishes.
4. Application qualification contracts bind to it, one application per PR.
5. The explicit-argv profile revision, with the next profile change (Decision 3).

## Rejected alternatives

- **Forcing serial execution.** It reduces one source of variation, but a serial configuration can still be consistently wrong, and partition settings still change answers.
- **Treating build support as accuracy qualification.** The GPU kernel configuration depends on the architecture.
- **Recording only intended argv.** Defaults and device-dependent effective settings would stay invisible.
