# Raw evidence numeric fixtures

PR98 numeric-ingestion policy, synthetic inputs only. These files preserve raw
lexemes, including intentionally invalid JSON. Never parse/re-serialize them to
prepare a replay. The index pins bytes, SHA-256, ingestion result, and the separate
canonical-schema result (null means not run/not applicable). Semantics, task
quality and runtime behavior are not tested by these scalar/shape fixtures.

`sequence` uses qualification's positive_count definition; `profile` uses its
profile_binding definition; `companion` uses the complete canonical companion
schema. `none` has no schema assertion. Accepted expected_json is oracle data,
not an evidence-input bypass. Schema/index documents use ordinary JSON loading.

The positive/negative 4301-digit cases exceed the finite conversion limit used in
a fresh interpreter. The numeric hook must refuse before int(); no application
process setting changes. Profile-extra cases exercise unbounded schema members.
The original companion/qualification fixtures and scores are unchanged.

Run `python3 -m unittest tests.test_runtime_numeric_ingestion` with the pinned
repository development dependencies. Existing byte/depth owners are unchanged;
this is numeric admission, not the future bounded Rust bundle validator.
