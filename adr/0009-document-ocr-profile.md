# ADR-0009: Connect v2 document OCR capability profile

**Status:** Proposed (accepted when this decision merges)

**Date:** 2026-09-17

**Decider:** Juan Canfield

## Context

Connect v2 can describe a generic local capability and carry integrity-checked
output bytes, but its generic schemas do not define OCR-specific input limits,
page limits, output cardinality, text encoding, no-text behavior, or deterministic
selection when a provider returns text and a text-only PDF.

Invoice Processor and Document Summarizer currently reach their native-text
parsers with scanned PDFs and produce no useful result. A standalone OCR provider
must present one narrow contract that those apps and Email Watcher can consume
without adding a broker, workflow grammar, provider-authored UI, or new wire
fields.

## Decision

### Capability declaration

A conforming provider declares this exact semantic profile:

```json
{
  "id": "document.ocr",
  "version": "1.0",
  "action": {
    "label": "Recognize text",
    "description": "Recognize text in a PDF on this device."
  },
  "accepts": [
    {"media_type": "application/pdf", "max_bytes": 33554432}
  ],
  "produces": ["application/vnd.local-connect.ocr-pdf", "text/plain"],
  "parameters": [],
  "effects": {
    "external": false,
    "confirmation_required": false
  }
}
```

Labels and descriptions remain bounded untrusted presentation text and may vary.
The semantic requirements are the capability identity, exactly one PDF input
declaration with the 32 MiB cap, exactly two `produces` entries containing
`application/vnd.local-connect.ocr-pdf` exactly once and `text/plain` exactly
once, no parameters, and both effect flags false. Output order in the
declaration is not semantic. A duplicate required media type is invalid even
when the set of distinct declared media types still matches this profile.

Version 1.0 accepts no image media types and performs no external effect. A
provider bounds the actual streamed artifact before admission and verifies that
its decoded byte count and SHA-256 match the request metadata. Non-PDF input,
an actual stream larger than 32 MiB, a declared/actual size mismatch, or a digest
mismatch fails before admission and calls the OCR engine zero times. Manifest
selection checks alone do not establish streamed-byte integrity.

### Page boundary

The provider derives page count from the verified streamed PDF bytes. It does
not trust a filename, display name, or caller parameter. Documents from 1
through 100 pages, inclusive, may be processed. A structurally invalid or
zero-page PDF fails before OCR work begins with no result:

```json
{
  "code": "DOCUMENT_INVALID",
  "message": "The PDF is not a readable document with at least one page.",
  "retryable": false
}
```

A document with 101 or more pages fails before OCR work begins, is never
truncated, and emits no partial result:

```json
{
  "code": "INPUT_PAGE_LIMIT_EXCEEDED",
  "message": "The PDF has more than 100 pages.",
  "retryable": false
}
```

### Completed output

A completed `document.ocr` 1.0 job contains exactly one
`application/vnd.local-connect.ocr-pdf` output and exactly one `text/plain`
output, with no duplicate or additional media type. The two output artifact IDs
are distinct and neither aliases the input. The decoded PDF payload is nonempty,
and its declared `byte_size` is nonzero and equals its decoded byte count.

Every output retains v2's canonical base64, decoded size, and SHA-256. The
required text is strict UTF-8 without a byte-order mark, contains at least one
non-whitespace Unicode character, and is at most 262,144 decoded bytes so Email
Watcher presents every successful text output instead of classifying it as
opaque. It contains exactly one text segment for every source page, in source
order, separated by U+000C FORM FEED. U+000C occurs only as the page separator,
so a consumer can recover the page boundary even when an individual page has no
recognized text. The provider never truncates recognized text to fit the cap.
If the complete UTF-8 text exceeds 262,144 bytes, the job fails with no result:

```json
{
  "code": "OUTPUT_TEXT_LIMIT_EXCEEDED",
  "message": "The recognized text is larger than this provider can return.",
  "retryable": false
}
```

The PDF is a structurally valid searchable reconstruction. It preserves the
source page count and order, page boxes, rotation, scale, and visible appearance
without reflow or repagination. Its OCR text objects do not change that visible
appearance and are spatially aligned with their recognized source regions.

The PDF carries one canonical text order using Tagged PDF logical structure as
defined by ISO 32000. The document catalog has `MarkInfo/Marked` set to true and
a `StructTreeRoot`. That root has exactly one `Document` structure element whose
`K` array has exactly one `Sect` child for each source page, in source page
order. Each page `Sect` has a `Pg` entry bound to that page. Its descendant
structure elements use their `K` arrays to state logical reading order
independently of content stream, object, glyph, or coordinate order. Recognized
tables use the standard
`Table`, `TR`, `TH`, and `TD` structure types so row and cell membership remain
explicit.

The logical structure uses this closed grammar, where `+` means one or more and
`*` means zero or more:

```text
Document := Sect+
Sect     := (P | Table)*
P        := Span+
Table    := TR+
TR       := (TH | TD)+
TH       := Span+
TD       := Span+
Span     := one marked-content reference
```

`P` and `Table` are the only page reading-order blocks. `TR` appears only under
`Table`; `TH` and `TD` appear only under `TR`; and `Span` appears only under
`P`, `TH`, or `TD`. No other structure role, table grouping wrapper, direct
marked-content child, empty nonterminal, or additional nesting is valid in this
profile. A page with no recognized text has an empty `Sect`; the document still
must contain non-whitespace text somewhere to complete successfully.

Every terminal OCR text leaf is a `Span` structure element with an `ActualText`
text string and exactly one marked-content reference to the visible page. That
marked-content sequence encloses only the aligned glyphs represented by the
leaf. Its MCID is unique on that page, the page's `StructParents` and the
structure tree's `ParentTree` map it back to the same `Span`, and the reference
is neither unresolved, omitted, duplicated, nor used from a different page
`Sect`. Parent structure elements do not carry `ActualText`, so no replacement
text can override a child. Source appearance content outside the OCR layer is
marked as an artifact and does not enter the logical text traversal.

Canonical extraction processes source pages in order. On each page it walks
the page `Sect` depth first, processes every `K` array in array order, decodes
each terminal `Span/ActualText` with the PDF text-string Unicode rules, and
concatenates those Unicode values without inserting, removing, or normalizing
characters. Every decoded value is a valid Unicode scalar sequence and contains
no U+000C. Encoding the concatenated page value as UTF-8 must reproduce that
page's exact `text/plain` segment byte for byte. Joining those page values with
one U+000C between adjacent pages must reproduce the complete plain-text output.
A coordinate sort, content-stream walk, PDF-object walk, or parser-specific
reading-order heuristic is noncanonical even when it produces plausible text.

The OCR provider validates appearance preservation, recognized-region
alignment, complete tagged structure, canonical extraction equivalence, and
semantic no-truncation before completing the job. Before Email Watcher derives
an OCR PDF-only handoff to Document Summarizer, Email Watcher independently
implements the same tag-tree traversal and byte-compares its extracted UTF-8
with the paired retained plain-text artifact. A mismatch is an invalid OCR
result and creates no lineage edge or downstream child job. Document Summarizer
independently implements that traversal again on the already validated OCR PDF
it receives and uses only those extracted canonical bytes for summarization and
evidence. It does not receive the paired plain-text artifact in the single-input
v2 request and therefore does not perform a runtime paired-output comparison.
Neither consumer reruns OCR, calls the provider's extractor, or shares an
extraction or traversal helper with the provider or the other consumer.
Wire-only and export-only consumers are not required to parse the PDF and do
not claim spatial validation.

The complete PDF is at most 2 MiB. If the provider cannot produce and validate
the complete PDF within that cap, the job fails with no result:

```json
{
  "code": "OUTPUT_PDF_LIMIT_EXCEEDED",
  "message": "The reconstructed PDF is larger than this provider can return.",
  "retryable": false
}
```

The provider emits neither output when either output exceeds its cap. It never
truncates either artifact to convert an overflow into success.

A conforming consumer enforces only evidence available in the manifest, request,
status, retained bytes, and its private ADR-0008 state. It validates the exact
profile declaration; generic v2 schema, integrity, and authorization; output
cardinality and exact media types; distinct non-aliased artifact IDs; canonical
base64, actual decoded byte counts, declared sizes, and SHA-256 digests; the
actual input page bound; the actual text and PDF output byte bounds; strict
UTF-8, no byte-order mark, non-whitespace text; and one form-feed-delimited text
segment per admitted source page. It identifies outputs by media type,
independent of array order or display name.

A consumer that extracts the OCR PDF's text additionally validates the complete
Tagged PDF requirements above and uses only the canonical logical-structure
procedure. A consumer that holds both outputs uses those bytes for cross-output
comparison. A PDF-only downstream provider uses the extracted bytes as its
analysis text. Failure is an invalid OCR result and creates no downstream
analysis result.

Email Watcher renders the complete validated text through the profile's 256 KiB
limit without changing the stored bytes. It offers the PDF through its safe
export path; export alone does not require parsing for geometry. Before a
Document Summarizer handoff, Email Watcher's independent canonical extractor
must reproduce the paired retained text bytes exactly. Any structure or byte
mismatch rejects the OCR result before the ADR-0008 edge and child job are
created. Email Watcher does not rerun OCR. An automatic provider chain first
applies ADR-0008 and uses the explicitly selected downstream provider's exact
capability declaration. It submits the PDF only when that capability accepts
`application/vnd.local-connect.ocr-pdf`; it never relabels the derived artifact
as `application/pdf` or submits text to a PDF-only capability. The distinct
media type is the provider-visible source-kind signal; it does not replace
ADR-0008's complete consumer-owned ancestry. When no actual valid output is
compatible, the consumer creates no downstream job.

No consumer renders, exports, or admits a downstream job when either required
output is absent, duplicated, empty, over its actual byte cap, has an invalid
encoding or a declared-size or digest mismatch, follows an input outside the
admitted page bound, has invalid text-page segmentation, is not declared and
compatible for the selected capability, or lacks the required authorization and
ADR-0008 state. Recognized-region alignment, source-appearance preservation,
and semantic no-truncation remain provider-owned proof obligations. Canonical
tag-tree extraction equivalence is independently consumer-verifiable.

A downstream provider that accepts the OCR PDF persists the exact vendor media
type or a closed OCR source kind before parsing and carries that classification
through every evidence identity and result. Content digest alone cannot collapse
a native PDF and an OCR-derived PDF into one logical record. A provider may keep
one content-addressed physical copy for identical bytes, but deletion removes it
only after the last logical source reference. Legacy provider records without a
source kind migrate as native; retry and restart never reclassify OCR input as
native text. Logical-reference creation, reference deletion, last-reference
decision, and physical-copy unlink use one serialized store boundary. A durable
pending-delete marker owns the crash interval after the last logical reference
is removed. Before unlink, cleanup rechecks under that boundary that no logical
reference was created; a concurrent creator either cancels the marker while the
bytes still exist or restores and verifies the content-addressed bytes before
its logical record commits. Unlink precedes marker retirement, so a crash never
leaves a committed logical reference pointing at an absent copy.

### No recognized text

When OCR finds no non-whitespace text, the job terminates as failed with no
result or outputs:

```json
{
  "code": "NO_OCR_TEXT",
  "message": "No text was detected in the document.",
  "retryable": false
}
```

A successful zero-byte text output remains valid under generic v2, but it is not
valid for this capability profile. This profile uses an explicit terminal
failure so automatic consumers cannot mistake an empty artifact for analysis
input.

### Profile error policy

Every deterministic failure condition defined by this profile uses `failed`
status, carries no `result`, and has the exact error object stated below. All
five conditions are nonretryable; changing the message or retry flag is not the
same profile error.

| Code | Exact message | Retryable |
|---|---|---:|
| `DOCUMENT_INVALID` | `The PDF is not a readable document with at least one page.` | false |
| `INPUT_PAGE_LIMIT_EXCEEDED` | `The PDF has more than 100 pages.` | false |
| `OUTPUT_TEXT_LIMIT_EXCEEDED` | `The recognized text is larger than this provider can return.` | false |
| `OUTPUT_PDF_LIMIT_EXCEEDED` | `The reconstructed PDF is larger than this provider can return.` | false |
| `NO_OCR_TEXT` | `No text was detected in the document.` | false |

This map is exhaustive for deterministic conditions defined by this profile; it
is not a closed set of every provider failure. A provider may use another
v2-conforming code for a failure condition this profile does not define, but it
does not substitute another code for one of the five conditions above.

### Provenance and lifecycle

ADR-0008 governs any OCR output submitted to another provider. Its lineage edge
retains the original scan identity, OCR provider instance and job, selected OCR
output, and downstream job. The downstream provider receives the distinct OCR
PDF media type and records an OCR source kind, but it does not receive the
consumer-local ancestry or workflow state. Together, the downstream record and
consumer edge trace its evidence back to the original scan without calling OCR
text native.

A background OCR provider follows ADR-0007. This profile does not silently
enable it, change per-user consent, or weaken provider ownership and recovery
requirements. Accepted ADR-0007 and ADR-0008 are prerequisites for this
decision.

## Required acceptance evidence

Evidence ownership is explicit. The shared contract repository proves only
portable profile semantics; each application proves its own integration.

### Shared profile fixtures

1. the exact manifest profile is accepted in either produced-media order; image
   input, a different 32 MiB input cap, additional parameters, missing or extra
   produced media, either required media type repeated, and either true effect
   flag are rejected;
2. a completed status with exactly one
   `application/vnd.local-connect.ocr-pdf` output and one text output passes
   regardless of order, while either output alone, duplicate media, a third
   media type, input alias, invalid UTF-8, byte-order-mark, whitespace-only, and
   zero-byte completed results fail; and
3. every profile-defined error uses the exact code, message, and nonretryable
   shape in the profile error-policy map and carries no result; and
4. the versioned canonical-text proof vectors accept tag-tree order for a
   multi-column table and reject the different text produced by a coordinate
   sort. Both the schema and an independent walker reject `Table` > `TD` > `TH`,
   a cell outside `TR`, `TR` outside `Table`, and canonical text beginning with
   U+FEFF or containing U+000C in an `ActualText` leaf. Duplicate MCID
   references, cross-page references, unresolved or omitted leaves, empty
   nonterminals, terminal nesting, and page `Sect` reordering also fail.

### OCR provider runtime

5. actual input bytes at 32 MiB are admitted and 32 MiB plus one byte is rejected
   before OCR even when underdeclared; shorter and longer size mismatches and a
   same-size digest mismatch call the OCR engine zero times;
6. runtime PDFs at 1 and 100 pages reach OCR; a structurally invalid or zero-page
   PDF returns `DOCUMENT_INVALID`, and 101 pages returns
   `INPUT_PAGE_LIMIT_EXCEEDED`; each failure calls the OCR engine zero times and
   emits no partial output;
7. complete UTF-8 text at 256 KiB and a searchable PDF at 2 MiB pass. Text one
   byte over fails nonretryably as `OUTPUT_TEXT_LIMIT_EXCEEDED`; PDF one byte
   over fails nonretryably as `OUTPUT_PDF_LIMIT_EXCEEDED`; either overflow emits
   no result or partial output. Provider runtime evidence proves the complete
   artifacts were not truncated to fit; and
8. a real scanned multi-column table produces a structurally valid Tagged PDF
   with preserved page appearance and geometry, aligned recognized coordinates,
   one source-ordered page `Sect` per page, table roles, unique page MCIDs, and
   terminal `Span/ActualText` leaves. The provider's canonical traversal matches
   the plain-text segments byte for byte. The provider runtime proves the
   spatial and semantic properties. Installed background operation separately
   satisfies ADR-0007.

### Consumer integrations

9. Email Watcher validates the wire-visible profile evidence listed above,
   retains both exact outputs, previews the valid text through 256 KiB, and
   exports the OCR PDF only through its safe path without rerunning OCR. Before
   admitting a Document Summarizer handoff, an Email Watcher implementation
   independent of the provider and Document Summarizer extracts the canonical
   text from the retained PDF and byte-compares it with the paired retained
   text. A mismatch creates neither the ADR-0008 edge nor a child job; a match
   permits the edge and child to be committed atomically;
10. Invoice Processor explicitly accepts the OCR PDF media type and carries a
   distinct OCR source identity into the ledger before constructing span and
   table evidence. Native and OCR-derived submissions with identical bytes have
   distinct logical identities, while their content-addressed physical copy is
   removed only after its last ledger reference. A scanned table proves row,
   column, bounding-box, derived-PDF, OCR-transform, and original-scan lineage
   through the consumer edge. Race final-reference purge against creation of a
   native or OCR logical reference, and crash after reference deletion, pending
   delete persistence, unlink, and marker retirement; no committed record loses
   its copy and orphan cleanup remains idempotent;
11. Document Summarizer keeps v1 PDF-only and admits the exact
    `application/vnd.local-connect.ocr-pdf` media type only in v2. Descriptor
    vendor media with an ordinary-PDF multipart part and descriptor ordinary PDF
    with a vendor-media part both fail before document or job persistence.
    Admission atomically persists `OcrText` with the document/job before parsing,
    while migration classifies legacy rows as `NativeText`. It retains that
    source type across reopen, restart, retry, parsing, normalization, every
    text-selection path, evidence, page citations, prompts, and warnings. Its
    independent consumer implementation performs the canonical tag-tree
    traversal on the admitted PDF without provider or Email Watcher code and
    without a shared extraction helper. It uses the extracted UTF-8 bytes for
    summary input, evidence, and citations, and its isolated proof rejects
    malformed tagged structure and proves a coordinate sorter cannot substitute
    for that traversal. The paired-output comparison occurs in Email Watcher
    before this single-input child request, not in Document Summarizer. A real
    OCR-derived PDF then completes a cited summary with page attribution without
    calling reconstructed text
    native, retains its immediate input artifact and media, and traces through
    the consumer-owned edge to the original scan; and
12. consumers select by exact media type and downstream capability, never array
    position or display name, and create no downstream job for incompatible,
    invalid, oversized, partial, integrity-failing, or no-text results. Provider
    evidence proves spatial fidelity and semantic no-truncation; Email Watcher
    independently proves canonical cross-output fidelity before a PDF-only
    handoff, and Document Summarizer independently proves that it analyzes the
    PDF's canonical logical text.

### Installed same-scan vertical proof

13. under accepted ADR-0008, one exact-package installed proof uses one retained
    scanned multi-column table and one installed OCR provider instance across
    the complete path. Record the operating system, exact source commit and
    package SHA-256 for the OCR provider, Email Watcher, Invoice Processor, and
    Document Summarizer, plus the discovered OCR provider app and durable
    instance IDs. Installed Email Watcher discovers that installed provider and
    submits the exact same retained scan bytes and digest as two independently
    admitted OCR executions with distinct consumer-owned execution identities.
    The first OCR job and its selected retained output create one ADR-0008 edge
    and exactly one reconciled downstream child for installed Invoice Processor.
    The second OCR job and its distinct selected retained output create one
    separate ADR-0008 edge and exactly one reconciled downstream child for
    installed Document Summarizer. No producer job, selected output, execution
    identity, or lineage edge is reused across the two downstream children, so
    each execution is a linear one-parent, one-child path and this proof does not
    require the branching semantics deferred by ADR-0008.

    Email Watcher renders the retained text preview for each OCR execution and
    exports its exact source-preserving PDF through the safe export path. For the
    Document Summarizer execution, record the retained plain-text bytes, Email
    Watcher's independently extracted canonical bytes before child admission,
    and Document Summarizer's independently extracted canonical bytes used for
    summarization and evidence. The proof observer verifies all three byte
    sequences are equal; the Document Summarizer runtime still receives only
    the PDF. Run the intentionally noncanonical coordinate-order proof vector
    through Email Watcher's paired comparison and prove it creates no child.
    Separately run it through Document Summarizer's extraction proof and prove
    the canonical tag order, rather than coordinate order, supplies analysis
    text. Provider, Email Watcher, and Document Summarizer use three independent
    implementations with no shared extraction or traversal helper. A comparison
    that calls provider code, reuses another participant's helper, or compares
    two provider-produced values does not satisfy this proof.

    Restart the provider and each application across admission and lost-response
    recovery boundaries, then prove reconciliation creates no duplicate OCR
    job, edge, or child within either execution. Invoice Processor shows
    buyer-visible reconstructed rows, columns, and source provenance; Document
    Summarizer shows a buyer-visible cited summary bound to the OCR media and
    source kind; Email Watcher shows both retained previews, exported artifact
    identities, and downstream lineage outcomes. Every displayed provenance
    chain identifies the same original scan bytes and digest, its own OCR
    provider instance and job, selected output, downstream provider instance and
    job, and exact artifact digest. No chaining control or automatic admission
    is enabled before ADR-0008 is accepted. Isolated repository fixtures,
    different scans per application, development binaries, or separately
    packaged demonstrations cannot substitute for this proof.

Static contract fixtures prove declaration, status, and canonical logical-order
semantics. Generated PDFs at the input, page, and output boundaries require OCR
provider runtime tests because the shared JSON harness models the ISO structure
objects but does not inspect streamed PDF bytes. No provider conformance run
depends on a private consumer repository. Those isolated checks are
prerequisites, not substitutes for the independent consumer extraction in the
exact-package same-scan installed proof.

## Consequences

- Every OCR consumer has one deterministic text artifact for analysis.
- The required source-appearance-preserving searchable PDF remains available for
  safe export and carries one interoperable logical text order for a
  lineage-protected downstream capability that explicitly accepts its OCR media
  type.
- Ordinary `application/pdf` inputs retain native-PDF semantics; a downstream
  provider opts into OCR-derived input explicitly.
- The existing v2 schemas and routes remain unchanged.
- Provider implementations must add profile-specific semantic validation and
  runtime page counting beyond generic schema validation.

## Deferred

- JPEG, PNG, TIFF, and other image inputs;
- aggregate output limits below v2's existing per-artifact cap;
- language selection, deskew, confidence thresholds, and OCR engine controls;
- shared scheduling, workflow, retry, and compensation grammar;
- PDF viewing outside the existing safe export path; and
- OCR quality scoring and optional hardening beyond the proved blocker path.
