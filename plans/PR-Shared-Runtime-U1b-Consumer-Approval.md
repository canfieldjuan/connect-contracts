# U1b: real-consumer approval and adapter preparation

Status: PROPOSED, contract and evidence inventory only. Not implementation-ready.
Owner: connect-runtime; consumer canary/quality ownership remains ds-qualify-c9.

Parent authorities: [U1](PR-Shared-Runtime-U1.md),
[attachment/transport](PR-Shared-Runtime-U1a-Attach-Transport.md), and
[native request framing](PR-Shared-Runtime-U1b-Native-Request.md).
This proposal neither accepts nor implements [ADR-0015 / PR70](https://github.com/canfieldjuan/connect-contracts/pull/70).
The existing ADR is the qualification-identity owner; do not create another one.

## Root cause

The missing capability is deliberate, not an application defect. The merged
client can verify attachment, transport and a synthetic canary, but cannot admit
an approved real consumer. `model-client/src/canary.rs::{Approval,Definition,Program}`
remain private, `Definition::admit` requires the complete approved binding and
program identity, and `lib.rs` exposes no production approval constructor.
Document Summarizer `native_request.rs::FramingPolicy::qualified_fixture` is
`cfg(test)`. Exporting that fixture constructor or accepting caller-chosen hashes
would bypass the intended gate rather than supply the missing evidence.

## Validated-work inventory (before any port)

| Owner / exact revision | Reusable evidence and limit |
|---|---|
| Host merge `bc8f46168cde990a9601fd6f0df61e0509c7d6ec` | PR20 integrates canonical client `f841cde2b44ec99bc860359a88d06d6ae27309da`; readiness mechanism only, no enrolled production approval. |
| Doc Sum merge `e5000cf20fdd65d53804d17f93f6f7683e6e2aad`, implementation `46daeffeffd9cb1952fe54d0fadbd3abeecae139` | `src-tauri/src/pipeline/native_request.rs::{PromptFraming,CompletionResponse,FramingPolicy}` is the merged framing/raw decoding owner. This is a pinned merged checkout, not a claim about the installed app or latest app main. |
| Original main `7911f4375772fbc2e6c063a4e4a82aea7d638751`; reference `e12ac4a72330bb6eb000119e77806ecce313d591` | Existing legacy and qualified-open/closed framing baselines. Preserve both; do not replace the legacy baseline with the qualified one. |
| Framing receipt alias `framing-receipt`, SHA256 `bfc8eefceed2ee95fbdb22782a8731222e723aa0c58d39582ea5aa5c5c7c87ff` | Records 18 wire cases / 108 payloads, 23 typed response cases and 10 mutation controls. This preparation rechecked all 108 payload hashes and all 7 source hashes against the merged checkout; it did not rerun tests. Historical receipt predates the merge. Full structured C9 parity remains PENDING. |
| Canonical profile SHA256 `58bf361ec2d2a082931ffe19fb70dc9a22ffd8d7c10bc7837df137f843cd60d1` | GPU-CUDA intent: Qwen3.5-9B-Q4_K_M, context 32768, one slot, runtime `c1d0e7a004015f23bc0233470b747b596f29b264`. This is file identity, not a current loaded-runtime observation. |
| Runtime/model/template | Model SHA256 `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`; CUDA archive SHA256 `2d4988729ab0df576efdaa58be27c55b4de1eb574256049a0f2b6d5abe9bff10`; template SHA256 `a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715`. Values reused from canonical profile; model/archive not reread or downloaded. |
| Existing corpus bindings | Reuse parent U1's 301-file receipt, issue-73 and pre-production corpus references when relevant. Do not rebuild them, substitute synthetic quality evidence, or copy private contents here. |

Prompts, request bytes, schema property order/omission, tokenizer flags, sampling,
thinking framing, response envelopes and scoring remain owned by the frozen
fixtures and native owner. The wire matrix covers analyze/synthesize/verify,
text and explicitly non-C9 structured inputs, with legacy/qualified-open/qualified-closed
policies. It does not prove full C9 schema parity or summary quality.

## Required change surface and sequence

This commit changes only this proposal. Later steps are separately reviewed slices:

1. **Qualification identity prerequisite.** Settle the existing ADR-0015 at its
   own reviewed revision and direct operator acceptance. Then define its one
   qualification-record schema and offline fixtures in connect-contracts.
   Its proposed order is ADR, schema, effective host-settings capture, consumer
   bindings. Do not silently implement its registration/profile amendment here.
2. **Consumer approval contract.** Obtain the real consumer-owned canary definition,
   native request sequence, raw response checker, exact expected bytes, numeric
   exchange/body/token/deadline budgets, and frozen consumer/client artifacts.
   Specify the sole approval issuer/enrollment owner and how accepted evidence
   binds the trusted callback implementation. A file that merely says PASS,
   an arbitrary success callback, or self-selected matching hashes is not authority.
   Recommendation: immutable reviewed enrollment tied to release/consumer bytes,
   with no user-editable approval bypass; exact API/trust delivery remains blocked
   on the receipt/consumer handoff. No signing service or dependency is introduced.
3. **Offline admission and adapter proof.** After that exact contract is accepted,
   implement receipt admission at one canonical owner, then Doc Sum's bounded
   synchronous-trait adapter using the existing native framing/decoder and shared
   byte transport. The client owns identity/lease/readiness; Doc Sum owns business
   prompts, decoding, qualification and task scoring. Never maintain a second
   canary formatter or a private fork of the public client.
4. **Separately authorized live qualification.** Freeze the combined artifact and
   measured execution identity, approved canary and finite run budget. Preserve
   the qualification owner's G0/G1/G2 gates; no model call follows from accepting
   this preparation document or merging infrastructure.

The downstream adapter must implement the accepted U1 snapshot/selection contract
by reference, not redefine it: explicit opt-in, unchanged existing defaults and
routes, immutable historical snapshots, complete shared binding, bounded owned
worker/cancellation and explicit unsupported platforms. Existing Windows routes
must retain their applicable build/behavior gate. No adapter implementation is
included in this preparation.

### Approval is not a cached live pass

Separate reviewed qualification evidence from current-instance readiness.
An admitted receipt can authorize only its exact consumer/client/profile/definition/
checker/expected-result and measured execution identity. It cannot manufacture a
live-ready client. The existing canary gate must still verify the bound instance,
perform the bounded real sequence and compare the untrimmed raw result before
business generation. Current server PID/start/boot/socket identity stays ephemeral,
not persisted as reusable success. Missing, malformed, partial or mismatched
approval refuses the new route before canary/business bytes; existing routes
remain unchanged. Product behavior on otherwise unqualified hardware remains
ADR-0015's separate operator decision, not implicitly decided by this proposal.

Avoid circular approval: the qualification owner must specify a separately
reviewed, explicitly budgeted qualification lane that produces candidate evidence
without granting general business readiness. This proposal provides no public
unchecked session, arbitrary endpoint, generic plugin or approval constructor to
bootstrap that lane. Its exact design and authority are a required handoff item.

## Differences from validated work

No runtime/model/prompt/quantization/cache/slot/context change is proposed.
Later admission is a new trust boundary absent from synthetic tests. Later
transport changes from the old app-owned native path to the verified shared Unix
session, and later opt-in snapshot metadata follows U1. Each needs byte/typed-error
parity on the frozen inputs before behavioral experiments. Effective-setting capture
adds observed evidence; intended argv cannot substitute. Full C9 coverage is an
additional missing proof, not permission to project or alter its schema. Any
other departure requires an explicit amended contract before implementation.

## Verification plan

For this preparation: verify source pins and saved payload/source hashes, current
merge/open-ADR status, inventory references, local Markdown links and diff scope.
No build/model test is appropriate for a documentation-only change.

For later accepted code: reuse the native wire/response corpus and existing real
isolated Unix-peer tests. Prove valid enrollment succeeds and wrong/missing/partial/
extra/duplicate receipt fields, stale release/profile, wrong callback or expected
bytes, whitespace changes and altered budget fail at the owning boundary. Use
closed types/schema constraints; cross-field comparison has one named owner.
Probe zero/empty/falsy and min/max boundaries, each binding field independently,
failed/cancelled leaders and followers, changed server/reconnect, no replay after
unknown delivery, lease/worker cleanup and no early business sends. Compare exact
bytes, typed failures and independent task scores; JSON validity is insufficient.
Synthetic tests cannot approve real expected answers. Human quality review stays
pending where required. Use fail-first intended-cause mutations and reuse existing
proofs rather than constructing a parallel harness. Public release/build identity,
Linux and applicable Windows gates remain distinct from live correctness.

## Assumptions/blockers

CONFIRMED: PR70 is open at `664f3f7bed43c7a0542a248203a147f2e378868b`;
ADR-0015 and its schema are absent from inspected contracts main
`72b7311bf7179d7e860589b74f9127af69f44e98`. The inspected merged client has no
production enrollment; the framing receipt marks full C9 parity pending.

UNKNOWN / REQUIRED before dependent implementation or execution: accepted
qualification schema and measured-settings delivery; owner-approved real canary
request/expected pair and callback/checker identity; issuer/enrollment/trust API;
qualification-only lane; numeric live and request budgets; combined release and
prepared-store/sidecar identity; full C9 parity and applicable quality approval.
No absence across every other workstream is inferred from this inspected packet.
Exact acceptance of this proposal would not fill those missing values or accept
PR70. Prepare independent documentation while these are pending; do not weaken
the existing gate, infer approval from hashes, or switch app routes.

## Explicit non-scope

No source implementation, schema generation, profile/argv change, dependencies,
public release, private app change, model/tokenizer call, GPU allocation, install,
service start/stop, canary approval, live execution, Ollama change, production
admission/cutover, kernel/fork/upgrade, concurrency expansion or performance claim.
No changes to other owners' worktrees, summary logic, OCR, schema projection or
business validators. Existing OCR/Paddle and historical snapshot behavior stay
outside this slice.

## Implementation summary / cold diff audit

One new planning document; no source/test/configuration edits. The inventory and
missing-owner table are grounded in inspected code and existing durable receipts.
A separate durable inventory stores source paths/hashes and intended profile argv;
no private corpus or credentials are embedded in this proposal.

## Gap audit

DONE: preparation inventory and dependency/ownership proposal.
NOT DONE: exact contract acceptance, ADR/schema/settings prerequisites, approved
consumer enrollment, adapter implementation/parity, live qualification or adoption.
Do not treat this document as an implementation-ready contract until the named
handoff items are supplied and reviewed at an exact revision.
