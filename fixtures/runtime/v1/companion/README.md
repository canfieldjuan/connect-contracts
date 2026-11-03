# Offline companion schema conformance

Implements only the schema slice in the accepted
[implementation contract](../../../../plans/PR-Shared-Runtime-Companion-Schemas.md).
The [companion interface](../../../../plans/PR-Shared-Runtime-Companion-Interface.md)
remains the complete delivery specification. These synthetic examples prove wire
shape only, not CheckedBundle, AttachedEvidence, task PASS or live qualification.
Runtime choice, issue #88 and live budgets remain open.

## Files and ownership

The canonical schemas are `schemas/runtime/v1/{companion,instance,host-snapshot}.schema.json`.
Qualification owns Digest, Alias, Seq and observation definitions; instance owns
the new U64Text/process/UUID lexical definitions; companion owns ObjectRef.
All references resolve through the test's explicit local registry. No network
retrieval, filesystem source reader, collector or production validator is added.

`index.json` enumerates the flat fixture set with target schema, raw SHA-256,
expected schema validity and constraint. Negative entries name the failing JSON
path and schema keyword; recursive branch diagnostics establish the intended
error. The test uses its own fixed fixture/schema allowlist, never paths supplied
by a candidate. The existing runtime fixture inventory remains the single
exhaustive inventory owner and rejects unlisted or duplicated companion entries.

- `instance-{linux,windows}-{cuda,vulkan}.json`: independent platform/backend
  combinations; synthetic host/server identities only. Not native-platform proof.
- `snapshot-{linux,windows}-{cuda,vulkan}.json`: host observations with either
  clock variant. Backend/clock association with an instance remains semantic.
- `snapshot-unavailable-{cuda,vulkan}.json`: valid incomplete host evidence.
- `manifest-{empty,sources}.json`: empty and mixed server/device source lists.
- `manifest-invalid-bytes.json`, `instance-invalid-{pair,process}.json` and
  `snapshot-invalid-{placeholder,device}.json`: specific schema negatives.
- `instance-semantic-overflow.json`, `manifest-semantic-mismatch.json` and
  `snapshot-semantic-reversed.json`: deliberately schema-valid counterexamples
  that require later numeric, cross-object or interval rejection. Never admit
  them as validated bundles.

New snapshot values reuse the existing qualification fixtures without rewriting
them. The tests compare every retained observation and exercise unavailable
observations from the earlier incomplete fixtures. The only two observation
changes are the interface-required host placeholders: `prompt_cache_reuse` and
`requests_overlap` are exactly `unavailable/not_collected`.

| Reused input under `qualification/` | Original byte SHA-256 |
| --- | --- |
| `cuda-complete.json` | `ab7d3bc4f34df7d892116abdd56986173c229585a2170c20086f6efbac321d54` |
| `cuda-incomplete.json` | `9ef93c7fb2693925cf7e0311d1b6d99d963c629a90a19543e786113e9b6d1fb5` |
| `vulkan-complete.json` | `de3b7f3730d3d44671caf0d09c18dc8618a92e800d41d7bb16a9c927bfbe1113` |
| `vulkan-incomplete.json` | `692c2205c17720421307d71392f002b6ea49bcc6e1ae55323b428011b0c3d9b0` |

All source aliases, hashes and process ids are synthetic. Manifest examples need
not reference fixture bytes; they are standalone shape inputs, not authenticated
or integrity-checked bundles. Original qualification/task fixtures and real
corpus inventories remain unchanged and are not rescored.

## Verification and limits

With the repository's pinned `jsonschema==4.25.1` and its existing dependencies:

```text
python3 -B -m unittest tests.test_runtime_companion
python3 -B -m unittest tests.test_runtime_qualification tests.test_runtime_contracts
```

The tests check schema validity and reference closure; closed/missing/mixed/wrong
type fields; lexical forms; declared size/count/sequence limits; the two exact
host placeholders; unavailable observations; zero/false controls; frozen bytes;
inventory negatives; and in-memory guard mutations killed by direct assertions.
The registry refuses missing references without fetching them. A runtime reader
cannot mask schema omissions because none participates in these tests.

No parsed-JSON test proves duplicate-member detection, BOM/nonfinite rejection,
parser depth, raw byte budgets, canonical instance serialization, hash integrity,
U64/PID numeric ranges, source authentication, clock/instance association, slot
equality, alias uniqueness, process liveness, cancellation, publication races,
file safety or storage quotas. Those remain obligations of the later shared
validator, reader and private publisher, not extra Python validators here.
Windows native proof remains later on Juan's Windows box. No engine, model,
tokenizer, GPU or installed app is called. Request/response-schema byte order,
the existing transport guard, Ollama and production remain unchanged.

Exact commands, environment versions, fail-first and passing receipts, preserved
input hashes and the cold diff audit are retained in the durable review packet.
Older qualification-run environment caveats are historical; a current pinned
rerun does not change those earlier receipts or imply live/task qualification.
