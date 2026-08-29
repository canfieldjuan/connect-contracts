# Local Connect Contracts

This repository is the canonical, language-neutral contract authority for
interoperability between independently installed local desktop applications.

It intentionally contains no broker, executable runtime, application-private
code, or workflow engine. Applications remain independently useful and own
their private state.

Current decision:

- [ADR-0001: Connect v0 local capability interoperability](adr/0001-connect-v0.md)

Executable JSON Schemas and conformance fixtures will be added only after the
first provider's standalone summary artifact is implemented and verified.
