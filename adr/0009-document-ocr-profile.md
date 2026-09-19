# ADR-0009: Connect v2 document OCR capability profile

**Status:** Proposed

**Date:** 2026-09-17

**Decider:** Pending

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
declaration with the 32 MiB cap, the exact produced-media set, no parameters,
and both effect flags false. Output order in the declaration is not semantic.

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
are distinct and neither aliases the input.

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

The PDF is a structurally valid text-only reconstruction. It embeds no source
page image. It preserves the source page count, order, boxes, rotation, scale,
and recognized text coordinates without reflow or repagination. Its text
objects are spatially aligned with their recognized source regions, and each
page's extracted text corresponds to the same page segment in the required
plain-text output. For this comparison, each side is normalized to Unicode NFC,
each maximal Unicode whitespace run is replaced with one U+0020 SPACE, and
leading and trailing space is removed; the normalized page strings must match.
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

A conforming consumer identifies outputs by media type, independent of array
order or display name, and applies this profile in addition to generic v2
validation before rendering, export, or chaining. Email Watcher renders the
complete validated text through the profile's 256 KiB limit without changing
the stored bytes. It offers the PDF only through its safe export path. An automatic
provider chain first applies ADR-0008 and uses the explicitly selected
downstream provider's exact capability declaration. It submits the PDF only
when that capability accepts `application/vnd.local-connect.ocr-pdf`; it never
relabels the derived artifact as `application/pdf` or submits text to a PDF-only
capability. The distinct media type is the provider-visible source-kind signal;
it does not replace ADR-0008's complete consumer-owned ancestry. When no actual
valid output is compatible, the consumer creates no downstream job. No consumer
renders, exports, or admits a downstream job when either required output is
absent, duplicated, malformed, empty, over cap, has a declared size or digest
mismatch, or fails the page-count, page-segment, geometry, or normalized
cross-output checks above. Semantic truncation within otherwise self-consistent
artifacts is not consumer-detectable; the provider's runtime evidence owns the
no-truncation proof.

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
requirements. ADR-0008 and ADR-0007 must be accepted before this decision can
be accepted.

## Required acceptance evidence

Evidence ownership is explicit. The shared contract repository proves only
portable profile semantics; each application proves its own integration.

### Shared profile fixtures

1. the exact manifest profile is accepted; image input, a different 32 MiB input
   cap, additional parameters, missing or extra produced media, and either true
   effect flag are rejected;
2. a completed status with exactly one
   `application/vnd.local-connect.ocr-pdf` output and one text output passes
   regardless of order, while either output alone, duplicate media, a third
   media type, input alias, invalid UTF-8, byte-order-mark, whitespace-only, and
   zero-byte completed results fail; and
3. `NO_OCR_TEXT` is failed, nonretryable, and carries no result.

### OCR provider runtime

4. actual input bytes at 32 MiB are admitted and 32 MiB plus one byte is rejected
   before OCR even when underdeclared; shorter and longer size mismatches and a
   same-size digest mismatch call the OCR engine zero times;
5. runtime PDFs at 1 and 100 pages reach OCR; a structurally invalid or zero-page
   PDF returns `DOCUMENT_INVALID`, and 101 pages returns
   `INPUT_PAGE_LIMIT_EXCEEDED`; each failure calls the OCR engine zero times and
   emits no partial output;
6. complete UTF-8 text at 256 KiB and a text-only PDF at 2 MiB pass. Text one
   byte over fails nonretryably as `OUTPUT_TEXT_LIMIT_EXCEEDED`; PDF one byte
   over fails nonretryably as `OUTPUT_PDF_LIMIT_EXCEEDED`; either overflow emits
   no result or partial output. Provider runtime evidence proves the complete
   artifacts were not truncated to fit; and
7. a real scanned multi-column table produces a structurally valid text-only PDF
   with preserved page geometry and aligned recognized coordinates, while its
   normalized per-page extracted text matches the plain-text segments. Installed
   background operation separately satisfies ADR-0007.

### Consumer integrations

8. Email Watcher validates the profile, retains both exact outputs, previews the
   valid text through 256 KiB, exports the OCR PDF only through its safe path,
   and atomically admits any downstream job with the ADR-0008 edge;
9. Invoice Processor explicitly accepts the OCR PDF media type and carries a
   distinct OCR source identity into the ledger before constructing span and
   table evidence. Native and OCR-derived submissions with identical bytes have
   distinct logical identities, while their content-addressed physical copy is
   removed only after its last ledger reference. A scanned table proves row,
   column, bounding-box, derived-PDF, OCR-transform, and original-scan lineage
   through the consumer edge. Race final-reference purge against creation of a
   native or OCR logical reference, and crash after reference deletion, pending
   delete persistence, unlink, and marker retirement; no committed record loses
   its copy and orphan cleanup remains idempotent;
10. Document Summarizer keeps v1 PDF-only and admits the exact
    `application/vnd.local-connect.ocr-pdf` media type only in v2. Descriptor
    vendor media with an ordinary-PDF multipart part and descriptor ordinary PDF
    with a vendor-media part both fail before document or job persistence.
    Admission atomically persists `OcrText` with the document/job before parsing,
    while migration classifies legacy rows as `NativeText`. It retains that
    source type across reopen, restart, retry, parsing, normalization, every
    text-selection path, evidence, page citations, prompts, and warnings. A real
    OCR-derived PDF completes a cited summary with page attribution without
    calling reconstructed text native, retains its immediate input artifact and
    media, and traces through the consumer-owned edge to the original scan; and
11. consumers select by exact media type and downstream capability, never array
    position or display name, and create no downstream job for incompatible,
    invalid, oversized, partial, integrity-failing, or no-text results. Provider
    evidence, rather than consumer inference, proves semantic no-truncation.

Static contract fixtures prove declaration and status semantics. Generated PDFs
at the input, page, and output boundaries require OCR provider runtime tests
because the shared JSON harness does not inspect streamed bytes. No provider
conformance run depends on a private consumer repository.

## Consequences

- Every OCR consumer has one deterministic text artifact for analysis.
- The required text-only PDF remains available for safe export and for a
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
