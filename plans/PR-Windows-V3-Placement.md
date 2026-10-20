# PR contract: reconcile Windows v3 placement

## Root cause

At baseline `f00aad8aa3d53285c5b96afd34ecc5ec59030991`, ADR-0005 lists only
v1/v2 placement. ADR-0010 already defines the complete Windows v3 extension:
the v3 provider directory and fixed registration/temporary names, reuse of the
v2 durable-instance ownership lock, bounded discovery and cross-protocol
identity cleanup. The missing decision claimed in issue #73 is contradicted
by ADR-0010; the remaining defect is an incomplete entry point in ADR-0005.

The v3 path originated in `ba48fe08`; the shared v2 lock and mixed-version
ownership rules originated in `4aa3eaa5`. Both predate this audit. The audit
read ADR-0005 in isolation and incorrectly generalized its omission into a
missing repository-wide decision. Correct that finding at its source.

## Required change surface

- Amend `adr/0005-windows-local-placement.md` to enumerate the existing v3
  transport and provider directory, and link its ownership/reset obligations
  to ADR-0010 as the existing owner of the v3 extension.
- Explicitly distinguish v3's provider directory from its shared v2 ownership
  lock. A new v3 lock directory would incorrectly allow simultaneous owners of
  one durable instance across installed protocol versions.
- Preserve ADR-0010's rules exactly. This is documentation reconciliation,
  not a new protocol, filesystem layout or migration.
- Correct issue #73 and the audit's dependent summaries to remove the false
  contract-blocker claim. Windows app implementation and native proof remain
  separate, incomplete work.

## Validated-work inventory and port differences

This slice ports no runtime or model behavior. The baseline contains v3 wire
schemas, fixtures and offline semantic tests; they do not prove native Windows
file ownership. Existing v3 placement semantics are in ADR-0010's
"Version, discovery, and compatibility" section. Their paths, identity,
lock namespace, cleanup order and admission policy are preserved without a
behavioral difference. No app pin changes are required merely to understand
rules already present at its contract revision; implementation adoption must
still name and verify the revision it actually uses.

## Explicit non-scope

- No changes to ADR-0010, v1/v2/v3 schemas, fixtures, tests, runtime profiles,
  entitlement material, dependencies or executable tools.
- No new Windows lock namespace, wire member, output cap or lifecycle policy.
- No provider, consumer, installer, OCR, inference or application code changes.
- No native qualification or installed-compatibility claim from this diff.
- No declaration that the broader installed-conformance issue is complete.

## Assumptions/blockers

The merged ADR-0010 extension is the rule being indexed, not an unmerged
proposal to redesign. Its stale "Proposed (accepted when this decision merges)"
header does not erase the merged content. Runtime behavior remains established
only by source and native proof in the implementation slices. No Windows host
is required for this documentation reconciliation; native proof is still a
separate mandatory goal gate.

## Verification plan

- Compare each amended path/ownership statement directly to ADR-0010.
- Check Markdown links and `git diff --check`.
- Prove all executable contracts, fixtures and tests remain byte-identical to
  the baseline. Reuse the baseline's recorded contract-test evidence; do not
  rerun code tests for this documentation-only reconciliation.
- No source-text assertion test: it would only mirror prose and could not
  prove Windows locks. Native mixed-version contention, path admission and
  cleanup regressions belong to each implementation owner.
- Read back every edited issue and preserve states, labels and unrelated text.

## Implementation summary

The separate contract commit preceded the ADR edit. ADR-0005 now lists v3
transport and provider placement, explicitly preserves the existing shared v2
lock, and points to ADR-0010 for the extension's ownership and cleanup rules.
Eight affected issue bodies/tracking maps were corrected and independently
read back; states, labels and historical text were preserved.

## Cold diff audit

- ADR-0005 transport and provider-directory entries match ADR-0010's existing
  version/discovery section. Its new link resolves to that section.
- The lock paragraph points to ADR-0010 and preserves the v2 namespace even
  for a v3-only publisher. Entitlement placement and all executable contracts,
  fixtures, tests, profiles, dependencies and tools are unchanged from the
  baseline, confirmed by a scoped Git diff.
- Consequences now identify v3 without promising native implementation.
- This plan records the correction and verification; it introduces no runtime
  requirement. Whitespace validation passed.
- Code tests were not rerun for this documentation-only change. The earlier
  audit's contract-test results apply to the unchanged baseline artifacts;
  neither those tests nor this document check prove Windows runtime behavior.

## Gap audit

NOT DONE: the documentation change and issue corrections are locally verified;
PR review and merge remain. The Windows implementation goal is independently
NOT DONE, including native ownership and installed-workflow qualification.
