# U1b: real-consumer approval and adapter preparation

Status: PROPOSED, contract and evidence inventory only. Not implementation-ready.
Owner: connect-runtime; consumer canary/quality ownership remains ds-qualify-c9.

Parent authorities: [U1](PR-Shared-Runtime-U1.md),
[attachment/transport](PR-Shared-Runtime-U1a-Attach-Transport.md), and
[native request framing](PR-Shared-Runtime-U1b-Native-Request.md).
This proposal neither accepts nor implements [ADR-0015 / PR70](https://github.com/canfieldjuan/connect-contracts/pull/70).
The existing ADR is the qualification-identity owner; do not create another one.

## Recorded v1 product decisions — 2026-11-01

Juan's v1 decisions are:

- **Hardware floor:** NVIDIA RTX GPUs with at least 8 GB VRAM. This is a product
  requirement, not evidence of qualification on 8 GB hardware or proof that a
  particular model/runtime configuration fits or runs correctly there.
- **Model-call concurrency:** sequential model calls, one slot.

These decisions do not select a model, quantization or runtime build, accept
any other budget, or authorize execution. Runtime build selection remains OPEN
under the Runtime Identity Selection gate below. [Issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88)
remains OPEN: the hardware floor does not choose refusal, warning or record-only
behavior for unqualified execution identities. Existing qualification, acceptance,
review, enrollment and release gates remain unchanged. No implementation,
builds, tests, benchmarks, tokenizer/model calls or live changes are authorized
by this record.

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

### Existing consumer handoff (proposed, not executable)

Reuse the qualification owner's `host-32k-qualification-contract-20261029`
packet: `CONTRACT-PROPOSED-r2.md` SHA256
`b0996c8b802892d8c4621576253cf18abf331eb7ec2d6364428c8bd6a9787a05`
and `U1b-qualification-handoff-20261030.md` SHA256
`03e18f2eafbc31a2b2c40c9567f1e229af6bd37f4a3be1b7b43210695e99c2e0`.
Also reuse `U1b-base-dependency-answer-20261030.md`, SHA256
`907bdb5d245ff3a27618ccdcf51d9c8ffcb33ccaffbb6a6472dda3761a526234`:
the qualification owner integrates the delivered runtime with the held writer
stack; held summary semantics are not a prerequisite for the main-based framing
or client infrastructure. This does not release any held branch.

The existing proposed `DS-HOST-CANARY-1` selects the approved marker from a
synthetic record. Expected decoded bytes are exactly `CEDAR-17`; logical seed is
4294967295, output cap 1500, decoder schema null. Preserve the owner's verbatim
system/user strings, production framing, historical temperature 0/cache_prompt
true, normal-stop/full-envelope check and no trim or answer-forcing grammar.
Those are proposal parameters, not a live allowance or measured effective state.
The handoff names the existing writer preparation/budget-owner harness for G1,
then a separate G2 numeric annex with exact-revision operator acceptance.
The earlier 509 bound is explicitly not a new budget. No canary/request redesign
or new qualification harness is needed to replace this existing design.
Actual delivered wire/token/checker binding, G2 budgets and acceptance remain pending.

## Required change surface and sequence

This change is preparation only. The dependency owner is this sequence; other
sections refer to its gates rather than adding another ordering. None of the
future slices is dispatched or accepted by this proposal.

1. **Identity/schema prerequisite — connect-runtime, connect-contracts.** Settle
   ADR-0015 through its own review and direct operator acceptance, then its one
   qualification-record schema/fixtures. Proposed ADR landing order stays intact.
   [Decision 6 issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88)
   is the named product-decision prerequisite for real admission/adapter enforcement
   in step 5 and enrollment in step 10. It does not block independent offline
   design/synthetic proof, and no choice may be inferred while it is open.
2. **Logical canary and trust design — ds-qualify-c9 and connect-runtime.** The
   qualification owner supplies the existing r2 logical request/checker rule;
   connect-runtime specifies the single issuer/enrollment/admission owner and
   immutable binding format. Obtain exact-revision acceptance of those semantics
   and the candidate qualification interface before their code. This is design
   acceptance, NOT empirical approval. It does not require delivered executable
   hashes, rendered token arrays or final numeric execution budgets. Those follow
   delivery in steps 7-9. Specify the external enrollment identity below here;
   resolve the issuer/trust mechanism before admission implementation, without
   inventing an approval from arbitrary caller-selected hashes. Step 2 must also
   prove the qualification entry shipped in production bytes is unreachable without
   its permit, name the trust anchors for record and permit, and obtain the r2
   owner's agreement to step 8's staging refinement. These remain design obligations.
3. **Effective-settings capture — connect-runtime, private host.** After step 1,
   implement the separately reviewed host capture slice (ADR landing-order item 3)
   using the pinned server's actual reporting owners. Prove parser/schema behavior
   offline, preserve intended-versus-observed distinction and unavailable fields.
   Code delivery does not authorize starting a server or reading a live model.
   Actual observation is budgeted in step 8. No profile/argv changes bundled here.
4. **Qualification interface — connect-runtime, client/adapter seam.** After
   step 2's accepted design, deliver a bounded qualification-only entry used by
   the existing preparation/budget-owner harness. Reuse private verified attachment,
   peer checks, leases and native serialization. Its distinct, non-forgeable permit
   represents an accepted invocation/phase and finite request budget, not a task
   correctness PASS. It returns evidence, never a generally usable ReadyClient.
   No public unchecked session, arbitrary endpoint, automatic replay or fake
   production enrollment. Offline synthetic permits prove this interface before
   any real permit exists. The exact permit/trust API belongs in step 2's reviewed
   contract, not an improvised bypass during live testing.
5. **Offline admission/adapter candidate — connect-runtime, Doc Sum runtime owner.**
   After the accepted step 2 design and step 4 interface, port the bounded
   synchronous adapter through existing framing/decoder and byte transport.
   Step 3's schema/capture precedes its effective-settings consumer binding.
   Use synthetic enrollment/peers for byte and typed-error parity; a real approved
   receipt is NOT a prerequisite to building or testing this inert candidate.
   Issue #88 must be resolved before implementing its dependent real-consumer
   policy/enforcement; keep that behavior unimplemented while open. No route
   activation, real enrollment or app adoption follows from the offline candidate.
6. **Held-writer integration — ds-qualify-c9.** Integrate the delivered adapter
   candidate into its held writer qualification stack, per the base-dependency
   answer above. Freeze combined source only after its existing review/hold gates;
   prove full structured C9 order/response parity there. connect-runtime supplies
   its reviewed runtime seams, not summary logic or a blanket held-branch merge.
7. **G0 delivery — connect-runtime supplies; ds-qualify-c9 binds.** Deliver reviewed
   outputs of steps 3-6: candidate binaries/libraries, complete manifest hashes,
   native owner, schema/capture interface, immutable snapshot, sidecar/store identity
   and transport proof. Bind the accepted logical canary/checker. Identify absent
   observations explicitly. No final PASS receipt or completed live run is required
   to deliver this candidate; those are outputs of subsequent qualification.
   **Runtime Identity Selection gate — Juan, OPEN (before step 8).** Juan must
   decide which runtime identity G0 binds. Until that decision, request neither
   a preflight nor a G2 annex. Steps 1-7 may continue except where they would bind
   or freeze a specific runtime identity; today's inventory pins do not select it.
   Oversight mail `3248f3b9` cites the operator-accepted arithmetic contract
   `llama-moe-sandbox/CONTRACT-CANONICAL-ARITHMETIC.md`, local commit `4da6517`:
   the canonical build is a new pinned identity, each app requalifies, and old
   baselines do not carry over. This is a relayed citation, not a sandbox inspection
   or an implementation/result claim. That work remains unowned and untouched here.
   After selection, bind the chosen artifacts and derive that identity's budgets;
   do not carry over the prior identity's accuracy evidence or time ceilings.
8. **G1 preparation and separately authorized preflight — ds-qualify-c9.** Reuse
   the existing harness to freeze source-derived request inputs, tokenizer request
   bytes, callback/state rules and finite phase bounds from the delivered owners.
   Mock token arrays are only offline proof. Real tokenizer outputs and observed
   settings need a separately reviewed preflight annex: Juan must explicitly accept
   its exact revision, candidate/input bindings and numeric startup, identity-probe,
   tokenizer/admission-call, byte/token and wall-time ceilings BEFORE any send.
   It permits only its named operations, with zero generation allowance. A required
   host start is not free. If request inputs depend on earlier responses, bind the
   exact transition code and finite bounds before authorizing the phase. Preserve
   every response and charged/uncertain send; no replay/refund. Then freeze actual
   token/wire bytes and measurements, and review the completed G1 receipt. This is
   an explicit proposed staging refinement to r2's separate live annex, not an
   existing permission or a requirement to perform tokenization "offline".
9. **G2 bounded qualification — ds-qualify-c9.** Only after reviewed G0/G1,
   obtain Juan's exact-revision acceptance of the numeric live annex for canary,
   stage generations, any additional startup/tokenizer calls, dynamic branches,
   output/time ceilings and reservations. Run through the qualification interface
   from step 4, not a production-ready handle that would already require this
   run's PASS. Capture expected-answer scoring, exact parity and pending human
   quality review; this produces candidate evidence, not automatic adoption.
10. **Production enrollment — named issuer/admission owner from step 2.** After
    qualified evidence, required human review, explicit approval and issue #88's
    accepted resolution, create the separate enrollment against the already frozen
    bytes. Verify shipped-versus-qualified identity below. The existing per-instance
    canary still gates later ReadyClient construction; qualification PASS alone
    cannot construct it. Enrollment/publication/adoption each retain their own
    review and operator gates, and none is included in this preparation.

### Enrollment identity without a self-hash

The step 2 design must bind the fixed executable/library/asset manifests of the
consumer integration and client, plus the canonical profile, definition/checker/
expected-result and applicable limits. Build and freeze these artifacts BEFORE
step 9. The later approval/enrollment is a separate record referring to those
manifests and qualification evidence; it is outside the set of executable bytes
whose digest it asserts. Do not rebuild the app/client to embed its own final
approval or omit mutable executable bytes from the identity to make a hash fit.
The reviewed admission trust mechanism must authenticate/pin that separate record;
its issuer and mechanism remain an explicit step 2 design prerequisite, not a
new signing infrastructure or self-authorizing JSON introduced by this proposal.

At release, compare each shipped executable/library/asset byte with the qualified
manifest; report packaging/enrollment differences separately. A changed executable
is a new candidate requiring the affected proofs, never silently the qualified
binary. ADR-0015's application-route identity stays intact; artifact hashes are
additional U1 transport/port provenance, not a reinterpretation of that ADR field
or a hardware policy. If the eventual packaging cannot preserve these identities,
its exact difference needs a reviewed contract before qualification, not after it.

The downstream adapter must implement the accepted U1 snapshot/selection contract
by reference, not redefine it: explicit opt-in, unchanged existing defaults and
routes, immutable historical snapshots, complete shared binding, bounded owned
worker/cancellation and explicit unsupported platforms. Existing Windows routes
must retain their applicable build/behavior gate. No adapter implementation is
included in this preparation.

### Approval is not a cached live pass

The current implementation's `canary.rs::Binding` binds consumer, client, profile,
definition, checker, expected bytes, exchange count and tokenize/completion limits.
`Definition::admit` compares that binding and program identity; `Instance` separately
binds the live host/server/socket/model/context/template/build. Preserve those
existing owners and tests. No measured GPU/driver/CUDA field is added to Binding
or made an approval-refusal condition by this proposal.

[Issue #88](https://github.com/canfieldjuan/connect-contracts/issues/88) owns the
OPEN operator decision about unqualified execution identities. Neither hardware
refusal nor record-only behavior is selected here. It remains open pending Juan's
decision; do not touch the other session's arithmetic work. In the
meantime, only the existing shipped binding and current-instance checks exist;
no new real-consumer policy is implemented. Step 5's independent synthetic proof
may proceed under its own accepted contract; dependent enforcement stays held.

Qualification evidence and current-instance readiness remain different states.
After real enrollment is eventually admitted, the existing bounded canary must
still compare the untrimmed response for the verified live instance before normal
business generation. No persisted success, missing approval, failed canary or
qualification-only permit manufactures ReadyClient. Steps 4 and 8-10 own the
candidate-to-qualification-to-enrollment ordering; there is no second bootstrap
lane or generic bypass here.

## Differences from validated work

No runtime/model/prompt/quantization/cache/slot/context change is proposed.
That scope statement does not settle the Runtime Identity Selection gate above.
Later admission is a new trust boundary absent from synthetic tests. Later
transport changes from the old app-owned native path to the verified shared Unix
session, and later opt-in snapshot metadata follows U1. Each needs byte/typed-error
parity on the frozen inputs before behavioral experiments. Effective-setting capture
adds observed evidence; intended argv cannot substitute. Full C9 coverage is an
additional missing proof, not permission to project or alter its schema. The staged
tokenizer/settings preflight in step 8 and separate enrollment record
are explicit proposed refinements requiring review/acceptance, not claimed prior
permissions. Any other departure requires an amended contract before implementation.

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
request/expected pair and callback/checker identity; issuer/enrollment/trust API and
external-record identity; issue #88 operator
decision before dependent enforcement; reviewed qualification interface, effective-
settings capture and held-writer integration; candidate-specific preflight and G2
numeric budgets after delivery; combined release and prepared-store/sidecar identity;
full C9 parity and applicable quality approval.
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
