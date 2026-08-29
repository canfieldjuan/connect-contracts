# Local Connect Contracts

This repository is the canonical, language-neutral contract authority for
interoperability between independently installed local desktop applications.

It intentionally contains no broker, executable runtime, application-private
code, or workflow engine. Applications remain independently useful and own
their private state.

Current decision:

- [ADR-0001: Connect v0 local capability interoperability](adr/0001-connect-v0.md)

The first provider's standalone summary artifact is implemented and verified,
so Connect v1 is frozen here as executable JSON Schemas and conformance
fixtures:

- `schemas/v1/manifest.schema.json`
- `schemas/v1/registration.schema.json`
- `schemas/v1/job-request.schema.json`
- `schemas/v1/job-status.schema.json`
- `schemas/v1/error.schema.json`

Run `python3 -m unittest tests.test_contracts` after installing the development
dependency in `requirements-dev.txt`.

The HTTP mapping is intentionally small:

- `GET /v1/manifest` returns the authenticated manifest.
- `POST /v1/jobs` accepts multipart fields `request` (the job-request JSON) and
  `artifact` (the single PDF byte stream).
- `GET /v1/jobs/{job_id}` returns the current job-status document.

All routes require the runtime-registration bearer token. The registration
itself is an owner-only, atomic runtime file and is availability evidence only
while its exact-loopback endpoint answers with the same instance ID.
