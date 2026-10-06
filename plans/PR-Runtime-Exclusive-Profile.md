# Qualified exclusive-backend runtime pins

## Root cause

The canonical runtime profile still selects native registries that can search
ambient backend locations. `ggml/src/ggml-backend-reg.cpp` treated the configured
directory as additional and independently accepted GGML_BACKEND_PATH; loading a
candidate can execute its constructor before scoring. Invoice Processor PR132
fixes that origin, and model-host PR5 binds launch to the retained verified
library directory. This slice adopts the qualified bytes in their canonical
owner rather than adding consumer filters.

The publication plan I authored also used nested release paths that the existing
fixed-revision URL contract rejects. Publication now adds root-level aliases of
the identical approved archives. URL admission remains unchanged.

## Required change surface

- `runtime/v1/profile.json`: replace both archives' immutable URLs, names,
  sizes and hashes; derive manifests from their public verified downloads.
  Preserve CUDA redistributable pins. Update Vulkan's archive root paths.
- `adr/0011-shared-local-model-runtime.md`: require the retained verified library
  directory as the child's working directory and exclusive backend discovery.
- This plan records the narrow adoption and its verification.

## Explicit non-scope

No model, template, argv, context, hardware floor, tier selection, schema,
URL validator, dependency, entitlement, registration or application changes.
No claim of broader platform qualification. Consumer vendoring follows this
canonical change; it does not create another source of runtime policy.

## Assumptions/blockers

The operator approved publication of the frozen CUDA and Vulkan packets.
Both archives reproduced and matched the established extraction reference.
The reference's service-charge withholding remains a known limitation.
Canonical consumer adoption and review are separate release gates.

## Verification plan

- Hash public immutable downloads against approved archive bytes.
- Compare every archive regular file against the new manifest and preserve
  unchanged CUDA redistributables; account for each changed payload.
- Assert all profile fields outside runtime archive/files/server_path are equal
  to the base. Existing strict URL and boundary tests continue to apply.
- Run README's required local contract unittest gate.
- After consumer vendoring, exercise the public CanonicalProfile preparation
  and native Server discovery path for both tiers; retain hostile ambient
  constructor and real device checks.
- The native origin's failing-before/passing-after regression and full model
  qualification belong to PR132; this data-only adoption uses those immutable
  results rather than inventing another parser or duplicating held-out runs.

## Implementation summary

Pending publication aliases and pin derivation.

## Cold diff audit

Pending final diff.

## Gap audit

NOT DONE: pin derivation, local verification, review and consumer proof remain.
