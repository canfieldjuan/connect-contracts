# Record-binding metadata format fixtures

Synthetic offline shapes for the accepted PR101 format contract. No private
request/document contents, runtime policy, rule registration or model calls.
Hashes in metadata are synthetic references, not proof of retained live artifacts.
The index SHA-256 pins each exact fixture file; it does not authenticate its claims.

## Running the offline checks

Use the repository's existing development dependencies without changing them:

```sh
python3 -m unittest -v tests.test_runtime_record_binding
python3 -m unittest tests.test_contracts tests.test_streamed_contracts tests.test_runtime_contracts tests.test_runtime_qualification tests.test_runtime_companion tests.test_runtime_numeric_ingestion tests.test_runtime_record_binding
```

## Separate proof boundaries

- The two canonical draft-2020-12 schemas own closed shapes, required fields,
  kind/field pairing, lexical definitions, source/requirement counts and unique
  request-index values. Their fixed local test registry refuses remote retrieval.
- `tests.test_runtime_record_binding.inspect_shapes` is a test-only pair runner.
  It checks the shared 256 KiB raw-byte budget before parsing, uses the unchanged
  corrected `_parse` owner, checks parsed container depth iteratively, then feeds
  those parsed values into the actual schemas. It is not a public validation API.
  This post-parse Python depth check does not prove the future client's required
  during-descent memory/depth bound. Root container is level one, limit 32.
- Canonical U64Text syntax is reused unchanged. Checked u64 conversion, interval
  ordering, unique field/occurrence identities, in-range/sorted request indices,
  host/app alias collisions, exact byte/digest binding, actual backend/clock pairing
  and valid source coverage remain the future record-binding owner's checks.
- Rule IDs and clock references are untrusted data. No rule set is registered.
  Nothing here establishes authenticity, overlap, complete qualification, task
  accuracy, byte-output parity or human review completion.

Existing qualification/companion/numeric fixtures and schemas are unchanged.
The new cases supplement their proofs; they do not substitute for oracle parity
or production/runtime qualification. App-scope source and interval rules stay open.
A `valid: true` index entry means schema-valid only, including explicit semantic
counterexamples. No expected semantic outcomes are implemented in the shape runner.

## Explicit fixture inventory

| Fixture | Schema-valid | What this case establishes / leaves open |
| --- | --- | --- |
| `app-empty.json` | true | empty offline shape; no workload or qualification claim |
| `app-paired.json` | true | ordered distinct offers of identical bytes; source attribution shape only |
| `app-invalid-kind.json` | false | source kind pairing |
| `app-invalid-indices.json` | false | indices must be unique |
| `app-semantic-alias.json` | true | shape valid; duplicate occurrence alias needs future record-binding refusal |
| `app-semantic-indices.json` | true | shape valid; unsorted out-of-range indices need future semantic refusal |
| `app-semantic-source-field.json` | true | shape valid; duplicate source field needs future semantic refusal |
| `scope-empty.json` | true | empty requirements and null clock proof; no qualification claim |
| `scope-linux-cuda.json` | true | Linux clock and CUDA path shapes; null rules are not validity proof |
| `scope-windows-vulkan.json` | true | Windows clock and Vulkan paths; unregistered rule reference remains untrusted |
| `scope-invalid-field.json` | false | closed observation path enum |
| `scope-invalid-time.json` | false | canonical decimal-string syntax |
| `scope-semantic-reversed.json` | true | shape valid; reversed interval needs future BindingMismatch |
| `scope-semantic-overflow.json` | true | shape valid; u64 overflow needs future checked conversion |
| `scope-semantic-field.json` | true | shape valid; duplicate requirement field needs future semantic refusal |
| `scope-semantic-backend.json` | true | shape valid; mixed device paths need independent instance backend comparison |
