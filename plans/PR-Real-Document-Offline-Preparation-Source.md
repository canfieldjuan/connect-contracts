# Selected-source annex: real-document offline preparation

This is source inventory and static call-path evidence, not a build, execution,
installed-product identity or whole-application behavioral equivalence claim.
Selected source: `e5000cf20fdd65d53804d17f93f6f7683e6e2aad` in
`canfieldjuan/document-summarizer`. All line citations below use that exact revision.
Root Git tree `1c1fc61b1fb1aa72b69abc2a476137fa1bb68204`;
crate tree `7847821b43147ff2a81f667cd40e7eee5495ed6b`.

## Scope and provenance

The new inventory covers **every tracked src-tauri blob**, including platform/test
alternatives, assets, build script, manifests and lockfile. Compared with the previously
retained `summary-replay-identity-native-build-20261107T201219Z/source-copy-before.json`
receipt (its digest and archived revision are bound in SOURCE-INVENTORY.json): 51 unchanged, 31 changed, 16 added and 5 archive-only
files. The selected tracked crate contains 4,851,394 bytes. This conservative inventory
covers more than the executed preparation path; it is not a claim that excluded model
or app-startup functions are unreachable by compilation. The future harness's closed
entry points and kernel isolation must prove the execution boundary separately.

The complete locked-package inventory has 593 packages with identity/source/checksum
and dependency declarations preserved. It binds registry resolution, not cached source
integrity, compiler/linker identity or target-specific native library provenance; those
require the later authorized build receipt. No dependency is installed or changed.
The archived baseline's generated gen/schemas files are archive-only; they cannot be
silently inserted into the selected source or claimed to be tracked in this revision.

Evidence packet alias: `real-document-preparation-contract-20261108T225436Z`. Artifacts are durable outside worktrees;
no private filenames or document contents are published here.

| Artifact | SHA-256 |
| --- | --- |
| SOURCE-SELECTION.json | 89a30208416930722511720ad121742dfeb956486d0074f0af3e04acc0bb123a |
| SOURCE-INVENTORY.json | 4ec84c8c9b41180639e683be2f697df7b64cd0c28241a102f5cfea865291aaa5 |
| LOCK-INVENTORY.json | cbd618140ed0606763335c6cd629d17c73d269473624d23c35eaae22da7ab908 |
| PREPARATION-SOURCE-DELTA.diff | bfb7906a2d607728d19942716e20f8c85af69db7bdc9fcb4e415501cc13d4e20 |
| REFERENCES.json | ada8935b8916bb5580bf0aec69a9c3c74098db7f511c2a82b50094f31a66f88a |

The expected selected tree is independently pinned by the operator selection; do not
accept a replacement manifest merely because it hashes itself. The inventory reads
Git object bytes and retained source metadata only, never imports/executes app code.

## Preparation call paths and transitive owners

Paths are below `src-tauri/`. Each direct/transitive Rust source is in the complete
inventory; Cargo.toml and Cargo.lock bind its third-party dependencies.

| File / symbol | Why it belongs in the preparation boundary |
| --- | --- |
| src/lib.rs:1 / test_store; connect/mod.rs; pipeline/mod.rs | Library/test module roots; main/desktop bootstrap must not be called. |
| src/pipeline/ingest.rs:88 / prepare_pdf_ingestion_with_source_type; :153 / prepare_received_run | Verified source/name and Received identity constructor. |
| src/pipeline/contracts.rs:270 / ParsedDocument::requires_ocr | Native source plus any unread page, not the archived document-wide warning. |
| src/pipeline/db.rs:1810 / persist_ingestion_with_profiles | Matching document identity, Received/version1 and transactional profile creation. |
| src/pipeline/db.rs:384 / prepare_ocr_handoff; :637 in OCR consumer / validate_saved_request | Durable input/request association; fixture must validate exact request before transport. |
| src/pipeline/db.rs:783/:828 / ensure/get_run_model_profile; :842/:883 summary profile | Explicit root snapshot and child inheritance, no model client. |
| src/pipeline/parser.rs:902/:914 / parse_document / parse_started_document | State transition, parser selection, validation and persistence. |
| src/pipeline/corrections.rs:259 / load_for_document | Parser checks correction ownership first; new store must have none, not imported production edits. |
| src/pipeline/parser.rs:70/:154 / parse_inner / verified_source_bytes | Complete native pages and byte identity; pdf-extract/lopdf own PDF parsing. |
| src/pipeline/parser.rs:989 / validate_parsed_document | Existing parsed artifact invariants before commit. |
| src/pipeline/db.rs:2102/:2126 / start_parsing / complete_parsing | State/version, artifacts, warnings and events; state.rs:27 transition owner. |
| src/pipeline/db/lifecycle.rs:57/:328/:487/:490 | Initialization/runtime SQLite floor, private store/WAL, owned readers/writers; db/access.rs holds shared access state. |
| src/pipeline/schema.rs:1057/:1351 / migrate / validate; tests/support/store.rs | Schema and setup ownership; public fixture lifecycle helper. |
| src/connect/contracts.rs; src/connect/v2.rs | Request/status/profile data models and shared protocol validators. |
| src/connect/ocr_consumer.rs:351/:468/:637 | Handoff/request, phase machine, saved-request binding. Startup discovery/recovery excluded. |
| src/connect/ocr_consumer/streamed.rs:34/:126/:228/:440 | Duplicate-safe metadata, HTTP decoding, status association, streamed retrieval. |
| src/connect/ocr_consumer/streamed.rs:557/:602 / download / download_async | Own HTTP client outside OcrTransport: saved-loopback fixture required. |
| src/connect/ocr_consumer.rs:846/:1090 / validate_pair_bytes / materialize_derived | UTF-8/page count/canonical pair, private derived file identity. |
| src/connect/ocr_consumer.rs:913; src/pipeline/db.rs:530 / admit_child / admit_ocr_child | Typed child and one-lineage/profile inheritance; no raw row insertion. |
| src/pipeline/parser.rs:188/:211/:254 | TaggedOcrParser and canonical tagged-page validation on derived bytes. |
| src/pipeline/control.rs:5/:24/:33 | Cancellation owner used during handoff/retrieval; no uncontrolled replacement for cancelled work. |
| build.rs; Cargo.toml; Cargo.lock; tauri configs/capabilities/assets | Build inputs: build.rs embeds a bounded public keyring or empty default and invokes tauri-build; future environment/output must be bound. No real entitlement read is authorized. |

The test-only lexical location, exact source gate and platform restrictions have one
owner: [the contract overlay surface](PR-Real-Document-Offline-Preparation.md#exact-future-overlay-surface).
That child test module can reach private ancestors without exporting a production API.
No binary is built here to claim that path compiles; that proof is a later gate.

## Differences that affect interpretation

- contracts.rs adds parser-owned mixed-page requires_ocr; OCR consumer/db use it rather
  than the old whole-document warning. Mixed inputs can therefore take another route.
- db adds lifecycle/access owners and selects an updated rusqlite/SQLite stack.
  Initialization checks the SQLite runtime floor and uses FULL synchronous/WAL state.
  Old DB-copy or old-binary success does not qualify the selected lifecycle.
- OCR startup recovery gains cancellation ownership. This adapter calls only the
  bounded saved handoff, not app startup/discovery/recovery.
- parser.rs adds mixed-page tests; schema.rs adds test setup counters. Hash differences
  are retained even when they do not change this preparation's production algorithm.
- Cargo.toml changes rusqlite configuration, enables Tokio time, and adds a Windows
  API feature. Cargo.lock adds hashlink0.12.2/libsqlite3-sys0.38.2/rusqlite0.40.2 and
  removes the archived hashbrown0.14.5/hashlink0.9.1/libsqlite3-sys0.28.0/rusqlite0.31.0
  identities. These are already in selected source, not proposed dependency upgrades.
- New native framing, gateway/model, desktop, package and service changes are fully
  inventoried but not executed by the two adapter operations. Their functional
  equivalence, production service and inference behavior are outside this contract.

The table below enumerates every non-identical file (not just hand-picked examples).
Complete old/new hashes and blob modes are in SOURCE-INVENTORY.json. Category is
file-level comparison only; it does not declare a change harmless.

| Path | Comparison |
| --- | --- |
| `src-tauri/Cargo.lock` | changed |
| `src-tauri/Cargo.toml` | changed |
| `src-tauri/linux/debian/postinst` | added |
| `src-tauri/linux/debian/postrm` | added |
| `src-tauri/linux/debian/preinst` | added |
| `src-tauri/linux/debian/prerm` | added |
| `src-tauri/linux/document-summarizer-connect.service` | added |
| `src-tauri/src/connect/lifecycle.rs` | added |
| `src-tauri/src/connect/lifecycle_control.rs` | added |
| `src-tauri/src/connect/mod.rs` | changed |
| `src-tauri/src/connect/ocr_consumer.rs` | changed |
| `src-tauri/src/connect/ocr_consumer/streamed/tests.rs` | changed |
| `src-tauri/src/connect/package_control.rs` | added |
| `src-tauri/src/connect/provider.rs` | changed |
| `src-tauri/src/connect/store.rs` | changed |
| `src-tauri/src/connect/windows_storage.rs` | changed |
| `src-tauri/src/desktop.rs` | changed |
| `src-tauri/src/desktop_startup.rs` | added |
| `src-tauri/src/lib.rs` | changed |
| `src-tauri/src/main.rs` | changed |
| `src-tauri/src/pipeline/chunk.rs` | changed |
| `src-tauri/src/pipeline/contracts.rs` | changed |
| `src-tauri/src/pipeline/db.rs` | changed |
| `src-tauri/src/pipeline/db/access.rs` | added |
| `src-tauri/src/pipeline/db/lifecycle.rs` | added |
| `src-tauri/src/pipeline/gateway_runtime.rs` | changed |
| `src-tauri/src/pipeline/gateway_store.rs` | changed |
| `src-tauri/src/pipeline/llama_cpp.rs` | changed |
| `src-tauri/src/pipeline/llama_cpp_framing_tests.rs` | added |
| `src-tauri/src/pipeline/mod.rs` | changed |
| `src-tauri/src/pipeline/model.rs` | changed |
| `src-tauri/src/pipeline/model_settings.rs` | changed |
| `src-tauri/src/pipeline/native_request.rs` | added |
| `src-tauri/src/pipeline/native_request_fixtures.json` | added |
| `src-tauri/src/pipeline/native_response_fixtures.json` | added |
| `src-tauri/src/pipeline/normalize.rs` | changed |
| `src-tauri/src/pipeline/parser.rs` | changed |
| `src-tauri/src/pipeline/recovery.rs` | changed |
| `src-tauri/src/pipeline/schema.rs` | changed |
| `src-tauri/src/pipeline/service.rs` | changed |
| `src-tauri/src/pipeline/structure.rs` | changed |
| `src-tauri/src/pipeline/summary.rs` | changed |
| `src-tauri/src/pipeline/workspace.rs` | changed |
| `src-tauri/tauri.linux.conf.json` | changed |
| `src-tauri/tests/office_acceptance.rs` | changed |
| `src-tauri/tests/release_contract.rs` | changed |
| `src-tauri/tests/support/store.rs` | added |
| `src-tauri/examples/model_eval.rs` | archive_only |
| `src-tauri/gen/schemas/acl-manifests.json` | archive_only |
| `src-tauri/gen/schemas/linux-schema.json` | archive_only |
| `src-tauri/gen/schemas/desktop-schema.json` | archive_only |
| `src-tauri/gen/schemas/capabilities.json` | archive_only |

## Reused evidence and limits

| Existing artifact alias | SHA-256 |
| --- | --- |
| `real-document-adapter-contract-r1-20261108T225124Z/CONTRACT-DRAFT.md` | 5c787d4b41e86d6eb7525c7b2d8c27676505cc0e371a414ef351471fd4f5e098 |
| `oversight-reviews/real-document-adapter-draft-r1-review.md` | 9bbb393225a9b8cf12238234fcf9a2b9aba53babeb541cc3616cab9f311fff5b |
| `owner-agreements-ocr-plan-20261108T192053Z/PADDLEOCR-CAPTURE-PLAN.md` | 52e14b474a3d6f47d26f5b4885ff0c75431476a0d195bdef6aae3d03ed239de9 |
| `real-document-binding-20261108T172954Z/BINDING.json` | 98ca7765befa78c1fa8f9b7a614d392249164e388aec4105e1df704d8583bdaa |
| `c9-ocr-offline-admission-20261027/qualification-tests.rs` | 66fdbdbf4816f9e16fb34de8860aee1ce9f0d24e2548dd229ae18a4ff211e36d |
| `c9-ocr-offline-admission-20261027/oversight-pass.json` | dacf70457b8bd62aec8083b9d425aecc024f770660113b86f88402ec63c06cf3 |

Prior binding review passed; draft/R1 reviews passed design direction. None is exact-head
acceptance of this final PR. Human gold, budgets, implementation, builds, model/OCR
calls and production changes remain held. Source selection is the only newly settled
operator decision. No additional source/behavior difference may be hidden during port.
