# V3 metadata conformance fixtures

These synthetic fixtures exercise JSON shape and cross-document metadata semantics only.
The large OCR descriptor intentionally carries metadata without an artifact body; it is
not proof of a real PDF, download integrity, OCR quality or production behavior.
`index.json` supplies expected validity, selected manifest and original request.
Runtime streaming/integrity/crash/concurrency proofs remain ADR-0010 implementation gates.
Existing v1/v2 fixture bytes remain unchanged.
