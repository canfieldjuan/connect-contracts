# Runtime v1 conformance fixtures (ADR-0011)

These synthetic fixtures exercise the shape and metadata rules of the shared model
runtime's documents: the canonical profile, the host's `server.json` registration, and
its `failure.json` record. Every hash, size and URL in them is invented. **Never vendor
a fixture as a profile.** The canonical profile is `runtime/v1/profile.json`. It carries
only tiers that qualified on exactly ADR-0011's argv (invoice-processor MODEL-SETUP
MS-PIN-4).

`index.json` supplies each fixture's schema, its expected validity and, for an invalid
fixture, the one fault it carries. Election, leases, the peer check, the read lease and
every other runtime behaviour remain ADR-0011 implementation gates in
`local-connect-model-host` and in each application.
